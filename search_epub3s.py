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

BASE_DIR =  './source-exploded'
print('dir ' + BASE_DIR)
output_basename = './source-exploded/EPUB3'
print('output_basename ' + output_basename)

input_basename = './source/EPUB3'
print('input_basename ' + input_basename)

img_pattern = re.compile(r'<img([^>]*>)', re.MULTILINE)
attr_pattern = re.compile(r'(\w+)=[\'"]((\\\'|\\""|[^\'"])*)[\'"]', re.MULTILINE)

row_count = 0

with open('epub3_list', 'w') as out_file:

    for epub3_path in iglob(input_basename + '/*/*.epub'):
        epub3_filename = os.path.basename(epub3_path)
        epub3_basename = epub3_filename[0:-5]
        output_dirname = output_basename + '/' + epub3_basename
        extension = epub3_filename[-3:]
        if os.path.exists(output_dirname):
            #print(output_dirname + " already exists")
            pass
        else:
            print("Creating " + output_dirname)
            run_command('mkdir ' + output_dirname)
            run_command('unzip -d ' + output_dirname + ' ' + epub3_path)

        rel_count = 0
        match_count = 0
        sample = None
        for html_path in iglob(output_dirname + '/**/*.xhtml', recursive=True):
            with open(html_path, 'r') as html_file:
                filetext = html_file.read()
                html_file.close()
            if filetext:
                re.sub("(<!--.*?-->)", "", filetext, flags=re.DOTALL)

                atts = {}
                for img_match in img_pattern.finditer(filetext):
                    for attr_match in attr_pattern.finditer(img_match.group(1)):
                        attr_name = attr_match.group(1)
                        attr_value = attr_match.group(2)
                        atts[attr_name] = attr_value[0:80]
                    if atts['src'][0:3] == '../':
                        rel_count += 1
                        sample = img_match.group(0)
                    if not exists(atts, 'alt'):
                        match_count += 1
                    elif atts['alt'] in ['',"equation", "image", "images", "img", "inline", "math", "jpg", "alt"]:
                        match_count += 1
        if rel_count > 20 and match_count > 20:
            print(str(rel_count) + " " + sample + " " + epub3_basename)
            out_file.write(str(rel_count) + " " + sample + " " + epub3_basename)
            row_count += 1
        if row_count == 20:
            break





