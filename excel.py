#!/usr/bin/env python

"""
Given a list of title instance IDs, create an Excel spreadsheet that contains
the images that title and the Math Detective results from transcribing that title.
The spreadsheet is intended to be shared for collecting crowdsourced verifications
of the Math Detective transcriptions.
"""

import re
import xlsxwriter
import os
from botocore.exceptions import ClientError
from glob import iglob

from pytitle.bksapiv2 import fetch_token, download_daisy_file
from pytitle.bksbot import get_session, get_artifact_id
from pytitle.excelutil import insert_img
from pytitle.fileutil import get_list_from_file, normalize_image_filenames
from pytitle.s3log import get_artifact_log
from pytitle.util import run_command, exists, slugify, normalize_file_path
from pytitle.xml import get_attrs, get_title_from_opf

'''
Working directory
'''
BASE_DIR =  './excel-test'
print('dir ' + BASE_DIR)

S3_BUCKET = "qa-bookshare-diff"
S3_PREFIX = "image-alt"
S3_REPOSITORY = "s3://" + S3_BUCKET + "/" + S3_PREFIX + "/"

'''
Bookshare API V2 Connection
'''
(oauth, token) = fetch_token()

img_pattern = re.compile(r'<img([^>]*)>', re.MULTILINE)

'''
Open file list of title instance IDs which have been reprocessed.
'''
title_instance_id_list = get_list_from_file("reprocessed_ids.csv")
title_artifact_map = {}
for title_instance_id in title_instance_id_list:
    try:
        title_instance_id = str(title_instance_id)
        browser_session = get_session()
        '''
        Get artifact ID from book history page
        '''
        artifact_id = get_artifact_id(browser_session, title_instance_id, 'DAISY')
        if artifact_id is not None and artifact_id != "":
            print(artifact_id + "\n")
            title_artifact_map[title_instance_id] = artifact_id
            '''
            Get artifact Math alt text log from S3
            '''
            img_log_data = get_artifact_log(S3_BUCKET, S3_PREFIX, artifact_id, BASE_DIR)
            basename =  BASE_DIR + '/' + title_instance_id + '-'+ artifact_id
            zippath = basename + '.zip'
            if os.path.exists(zippath):
                print("Already downloaded " + zippath + ", skipping download")
            else:
                download_daisy_file(oauth, title_instance_id, zippath)

            '''
            Clean up old directory if it exists and explode DAISY file
            '''
            run_command('rm -rf ' + basename)
            run_command('mkdir ' + basename)
            run_command('unzip -d ' + basename + ' ' + zippath)
            run_command('mkdir ' + basename + '/temp-images')

            (title, isbn) = get_title_from_opf(basename)

            workbook_path = basename + '-' + slugify(title) + '-report.xlsx'
            if (os.path.exists(workbook_path)):
                print("Already generated " + workbook_path + ", skipping")
            else:
                workbook = xlsxwriter.Workbook(workbook_path)
                worksheet = workbook.add_worksheet()

                headers = ['image', 'image_alt_attribute_before', 'spoken_text', 'ocr_conf', 'math_conf', 'OK', 'comments']
                col = 0
                worksheet.set_column('A:A', 40)
                worksheet.set_column('C:C', 40)
                for header in headers:
                    worksheet.write(0, col, header)
                    col += 1

                row = 1
                alt_text_cell_format = workbook.add_format()
                alt_text_cell_format.set_text_wrap(True)
                normalize_image_filenames(basename)

                '''
                Open DAISY XML file
                Generalized to all .xml files so that this script can be used with EPUB3 files
                with minimal modification.
                '''
                for xmlpath in iglob(basename + '/*.xml'):
                    print(xmlpath + '\n')
                    with open(xmlpath, 'r') as file:
                        file_data = file.read()
                        '''
                        Get list of image elements
                        '''
                        all_image_matches = []
                        image_matches = img_pattern.finditer(file_data)
                        for match in image_matches:
                            atts = match.group(1)
                            att_map = get_attrs(atts)
                            img_src = att_map.get('src', "NA")
                            '''
                            Get around some historic filename normalization issues by normalizing 
                            the filename from the DAISY file and from the log data
                            '''
                            normalized_src = normalize_file_path(os.path.basename(img_src))
                            if exists(img_log_data, normalized_src):
                                log_data = img_log_data[normalized_src]
                            else:
                                log_data = {
                                    'image_alt_attribute_before': "No log",
                                    'spokentext': "No log",
                                    'ocr_confidence': "No log",
                                    'math_confidence': "No log"
                                }

                            if exists(log_data, 'ocr_confidence'):
                                ocr_conf = log_data['ocr_confidence']
                                if isinstance(ocr_conf, float) \
                                    and float(log_data['ocr_confidence']) >= 0.9 \
                                    and float(log_data['ocr_confidence']) <= 0.998:
                                    if img_src != "NA":
                                        insert_img(row, basename, img_src, worksheet)
                                    worksheet.write(row,1, log_data.get('image_alt_attribute_before', "NA"), alt_text_cell_format)
                                    worksheet.write(row,2, log_data.get('spokentext', "NA"), alt_text_cell_format)
                                    worksheet.write(row,3, log_data.get('ocr_confidence', "NA"))
                                    worksheet.write(row,4, log_data.get('math_confidence', "NA"))
                                    row = row + 1
                    workbook.close()
    except OSError as err:
        print("OS error: {0}".format(err))
    except ClientError as err:
        print("S3 error: {0}".format(err))



