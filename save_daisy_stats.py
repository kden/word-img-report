import json
import logging
import os
import re

import psycopg2
from psycopg2.extensions import AsIs

from pytitle.fileutil import format_map, get_dir, get_filename_from_solr_result
from pytitle.util import exists


def copy_rec(source, destination, source_name, dest_name):
    if exists(source, source_name):
        destination[dest_name] = source[source_name]

def get_shared(solr_result, source_format):
    shared = {}

    copy_rec(solr_result, shared, 'title', 'title')
    copy_rec(solr_result, shared, 'title_source_description', 'title_source')
    copy_rec(solr_result, shared, 'publisher', 'publisher')
    copy_rec(solr_result, shared, 'id', 'title_instance_id')
    copy_rec(solr_result, shared, 'isbn', 'isbn')
    shared['source_format'] = source_format

    if exists(solr_result, 'copyright_date'):
        shared['copyright_year'] = int(solr_result['copyright_date'][0:4])
    return shared


logger = logging.getLogger()
logger.setLevel(logging.INFO)

img_pattern = re.compile(r'<img([^>]*>)', re.MULTILINE)
attr_pattern = re.compile(r'(\w+)=[\'"]((\\\'|\\""|[^\'"])*)[\'"]', re.MULTILINE)
#mathml_pattern = re.compile(r'<[^>]*math[^>]*>.*?</[^>]*math[^>]*>', re.MULTILINE|re.IGNORECASE)
mathml_pattern = re.compile(r'www.w3.org/1998/Math/MathML')

book_insert = 'insert into book (%s) values %s returning book_id'
img_insert = 'insert into img (%s) values %s returning img_id'
attr_insert = 'insert into attributes (%s) values %s'


solr_results = {}

con = psycopg2.connect(database="warehouse", user="bookshare", password="", host="127.0.0.1", port="5432")

print("Database opened successfully")

cursor = con.cursor()
con.rollback()

with open('solr_results_under_100_updated_isbns.json', 'r') as infile:
    solr_results = json.load(infile)

for book_format in format_map:
    format_list = solr_results.get(str(book_format))
    for solr_result in format_list:
        dtbookfilename = get_dir(solr_result, book_format) + get_filename_from_solr_result(solr_result,"-DAISY.xml" )

        if not os.path.exists(dtbookfilename):
            print("There is no " + dtbookfilename)
        else:
            print("Loading " + dtbookfilename)
            with open(dtbookfilename, 'r') as dtbookfile:
                filetext = dtbookfile.read()
                dtbookfile.close()

            shared = get_shared(solr_result, format_map[book_format])

            alt_text = ''
            src_text = ''
            other_atts = {}

            if filetext:
                try:
                    book = shared.copy()
                    copy_rec(solr_result, book, 'num_images', 'num_images')
                    book['filename'] = dtbookfilename
                    book['has_mathml'] = False
                    for mathml_match in mathml_pattern.finditer(filetext):
                        book['has_mathml'] = True
                        break
                    book_columns = book.keys()
                    book_values = [book[col] for col in book_columns]
                    cursor.execute(book_insert, (AsIs(','.join(book_columns)), tuple(book_values)))
                    book_id = cursor.fetchone()[0]

                    for img_match in img_pattern.finditer(filetext):
                        for attr_match in attr_pattern.finditer(img_match.group(1)):
                            attr_name = attr_match.group(1)
                            attr_value = attr_match.group(2)
                            if attr_name == 'src':
                                src_text = attr_value
                            elif attr_name == 'alt':
                                alt_text = attr_value
                            else:
                                other_atts[attr_name] = attr_value[0:4096]
                        img = shared.copy()
                        img['book_id'] = book_id
                        img['src'] = src_text
                        img['alt'] = alt_text[0:4096]
                        img['start'] = img_match.start()
                        img_columns = img.keys()
                        img_values = [img[col] for col in img_columns]
                        print(AsIs(','.join(img_columns)))
                        print(tuple(img_values))
                        cursor.execute(img_insert, (AsIs(','.join(img_columns)), tuple(img_values)))
                        img_id = cursor.fetchone()[0]
                        for attr_name in other_atts:
                            attr = {}
                            attr['img_id'] =img_id
                            attr['name'] = attr_name
                            attr['value'] = other_atts[attr_name]
                            attr_columns = attr.keys()
                            attr_values = [attr[col] for col in attr_columns]
                            print(AsIs(','.join(attr_columns)))
                            print(tuple(attr_values))
                            cursor.execute(attr_insert, (AsIs(','.join(attr_columns)), tuple(attr_values)))
                    con.commit()
                except psycopg2.Error as error:
                    print(error)
                    print(error.pgcode)
                    print(error.pgerror)
                    con.rollback()










