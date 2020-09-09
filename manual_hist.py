#!/usr/bin/env python

import re
from glob import iglob
import xlsxwriter
import os

from botocore.exceptions import ClientError

from pytitle.bksapiv2 import fetch_token, download_daisy_file
from pytitle.bksbot import get_session, get_artifact_id
from pytitle.excelutil import insert_img
from pytitle.fileutil import get_list_from_file, normalize_image_filenames
from pytitle.s3log import get_artifact_log
from pytitle.util import run_command, exists, slugify, normalize_file_path
from pytitle.xml import get_attrs, get_title_from_opf

BASE_DIR =  './excel-test'
print('dir ' + BASE_DIR)

S3_BUCKET = "qa-bookshare-diff"
S3_PREFIX = "image-alt"
S3_REPOSITORY = "s3://" + S3_BUCKET + "/" + S3_PREFIX + "/"

(oauth, token) = fetch_token()

# Create Word file


# <img src="images/cover.jpg" alt="Illustration" xml:space="preserve" id="img_00000" />

img_pattern = re.compile(r'<img([^>]*)>', re.MULTILINE)

title_instance_id_list = get_list_from_file("reprocessed_ids.csv")
title_artifact_map = {}
for title_instance_id in title_instance_id_list:
    try:
        title_instance_id = str(title_instance_id)
        browser_session = get_session()
        artifact_id = get_artifact_id(browser_session, title_instance_id, 'DAISY')
        if artifact_id is not None and artifact_id != "":
            print(artifact_id + "\n")
            title_artifact_map[title_instance_id] = artifact_id
            img_log_data = get_artifact_log(S3_BUCKET, S3_PREFIX, artifact_id, BASE_DIR)
            basename =  BASE_DIR + '/' + title_instance_id + '-'+ artifact_id
            zippath = basename + '.zip'
            if os.path.exists(zippath):
                print("Already downloaded " + zippath + ", skipping download")
            else:
                download_daisy_file(oauth, title_instance_id, zippath)

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

                headers = ['image', 'image_alt_attribute_before', 'spoken_text', 'ocr_conf', 'math_conf']
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
                # Open DAISY XML file
                for xmlpath in iglob(basename + '/*.xml'):
                    print(xmlpath + '\n')
                    with open(xmlpath, 'r') as file:
                        file_data = file.read()
                        # Get list of img elements
                        all_image_matches = []
                        image_matches = img_pattern.finditer(file_data)
                        for match in image_matches:
                            atts = match.group(1)
                            att_map = get_attrs(atts)
                            img_src = att_map.get('src', "NA")
                            if img_src != "NA":
                                insert_img(row, basename, img_src, worksheet)
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



