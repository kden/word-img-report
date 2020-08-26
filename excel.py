#!/usr/bin/env python

import os
import re
from glob import iglob
import xlsxwriter
from PIL import Image
import shutil
import bz2
import json

BASE_DIR = '/home/caden/CadenProjects/word-img-report/excel-test'


def run_command(command):
    print(command)
    return os.system(command + ">/dev/null 2>&1")


def normalize_file_path(pathname):
    path, filename = os.path.split(pathname)
    filename = filename.lower().replace('-', '_')
    base = filename[0:-4]
    extension = filename[-3:]
    base = base.replace('.', '_')
    new_pathname = '/'.join([path, '.'.join([base, extension])])
    return new_pathname

def exists(record, field_name):
    """
    Our definition of whether a field exists in a Python dict
    """
    return field_name in record and record[field_name] is not None and record[field_name] != ''

# Create Word file

id_pattern_string = r'<dc:Identifier[^>]*>([0-9][^<]+)<'
id_pattern = re.compile(id_pattern_string)
title_pattern_string = r'<dc:Title[^>]*>([^<]*)<'
title_pattern = re.compile(title_pattern_string)
# <img src="images/cover.jpg" alt="Illustration" xml:space="preserve" id="img_00000" />

img_pattern = re.compile(r'<img([^>]*)>', re.MULTILINE)
attr_pattern = re.compile(r'([A-Za-z\-\_]+)=[\'"]((\\\'|\\""|[^\'"])*)[\'"]', re.MULTILINE)


# For each DAISY file, unzip file
for zippath in iglob(BASE_DIR + '/*.zip'):
    path, filename = os.path.split(zippath)
    basename = zippath.replace('.zip', '')
    json_filename = zippath.replace('.zip', '.json.bz2')

    json_file = bz2.BZ2File(json_filename, "r")
    img_log_data = {}
    for img_entry_json in json_file:
        img_entry = json.loads(img_entry_json)
        if (exists(img_entry, 'image_src_attribute')):
            img_log_data[img_entry['image_src_attribute']] = img_entry


    workbook = xlsxwriter.Workbook(basename + '-report.xlsx')
    worksheet = workbook.add_worksheet()

    run_command('rm -rf ' + basename)
    run_command('mkdir ' + basename)
    run_command('unzip -d ' + basename + ' ' + zippath)
    run_command('mkdir ' + basename + '/temp-images')


    headers = ['image', 'after', 'ocr_conf', 'math_conf']
    col = 0
    worksheet.set_column('A:B', 40)
    for header in headers:
        worksheet.write(0, col, header)
        col += 1

    print(basename + '/images/*.*')
    for img_path in iglob(basename + '/images/*.*'):
        os.rename(img_path, normalize_file_path(img_path))

    for opfpath in iglob(basename + '/*.opf'):
        print(opfpath + '\n')
        # Get DAISY file metadata
        with open(opfpath, 'r') as file:
            file_data = file.read()
            identifiers = re.findall(id_pattern, file_data)
            for identifier in identifiers:
                print(identifier + '\n')
                isbn = identifier
            titles = re.findall(title_pattern, file_data)
            title = titles[0]
            print(title + '\n')

    row = 1
    alt_text_cell_format = workbook.add_format()
    alt_text_cell_format.set_text_wrap(True)
    # Open DAISY XML file
    for xmlpath in iglob(basename + '/*.xml'):
        print(xmlpath + '\n')
        with open(xmlpath, 'r') as file:
            file_data = file.read()
            # Get list of img elements
            all_image_matches = []
            image_matches = img_pattern.finditer(file_data)
            att_map = {}
            for match in image_matches:
                atts = match.group(1)
                for attr_match in attr_pattern.finditer(atts):
                    attr_name = attr_match.group(1)
                    attr_value = attr_match.group(2)
                    print("name= " + attr_name + "value= " + attr_value)

                    att_map[attr_name] = attr_value[0:4096]

                img_src = att_map.get('src', "NA")
                img_path = normalize_file_path(basename + "/" + img_src)
                tmp_img_path = normalize_file_path(basename + "/temp-" + img_src)
                with Image.open(img_path) as img:
                    width, height = img.size
                    img.save(tmp_img_path, dpi=(96,96))
                shutil.move(tmp_img_path, img_path)
                if  height > 200 :
                    scale = round(200.0/height, 2)
                else:
                    scale = 1
                print('Scale: ' + str(scale) + ' ' + str(width) + ' ' +  str(height) + ' ' + img_src)
                worksheet.set_row(row, 160)
                worksheet.insert_image(row, 0, img_path, {'x_scale': scale, 'y_scale': scale})
                worksheet.write(row,1, att_map.get('alt', "NA"), alt_text_cell_format)
                worksheet.write(row,2, att_map.get('data-ocr-confidence', "NA"))
                worksheet.write(row,3, att_map.get('data-math-confidence', "NA"))
                row = row + 1

    workbook.close()

