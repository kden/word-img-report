"""
Given a list of books in the database known to include MathML and the already-downloaded
DTBook files for those books, extract the MathML and write to the database.
"""
import os
import re

import psycopg2
from psycopg2.extensions import AsIs


solr_results = {}

mathml_pattern = re.compile(r'(<[^>]+?>)([^<>]*?)(<!--[\s]*)?((<[a-z: ]*math[^>]*>).*?</[a-z: ]*math[^>]*>)', re.MULTILINE|re.IGNORECASE)

attr_pattern = re.compile(r'(\w+)=[\'"]((\\\'|\\""|[^\'"])*)[\'"]', re.MULTILINE)

mathml_insert = 'insert into mathml (%s) values %s returning mathml_id'
attr_insert = 'insert into mathml_attributes (%s) values %s'

con = psycopg2.connect(database="warehouse", user="bookshare", password="", host="127.0.0.1", port="5432")

print("Database opened successfully")

cursor = con.cursor()
con.rollback()

cursor.execute("select book_id, filename from book where has_mathml = true")
rows = cursor.fetchall()

for row in rows:
    book_id = row[0]
    dtbookfilename = row[1]
    if not os.path.exists(dtbookfilename):
        print("There is no " + dtbookfilename)
    else:
        print("Loading " + dtbookfilename)
        with open(dtbookfilename, 'r') as dtbookfile:
            filetext = dtbookfile.read()
            dtbookfile.close()
        if filetext:
            try:
                for mathml_match in mathml_pattern.finditer(filetext):
                    match = mathml_match.group(0)
                    parent_element = mathml_match.group(1)[0:255]
                    parent_el_text = mathml_match.group(2)[0:255]
                    mathml_text = mathml_match.group(4)[0:4096]
                    start_element = mathml_match.group(5) [0:255]
                    is_comment = str(mathml_match.group(3))
                    print("-------")
                    print("whole match: " +match)
                    print("start element: " + start_element)
                    print("parent element: " + parent_element)
                    print("parent element text: " + parent_el_text)
                    print("is_comment: " +  is_comment)
                    print("mathml_text: " + mathml_text)
                    print("------")
                    altimg = ''
                    alttext = ''
                    other_atts = {}
                    for attr_match in attr_pattern.finditer(start_element):
                        attr_name = attr_match.group(1)
                        attr_value = attr_match.group(2)
                        if attr_name == 'altimg':
                            altimg = attr_value
                        elif attr_name == 'alttext':
                            alttext = attr_value
                        else:
                            other_atts[attr_name] = attr_value[0:4096]
                    mathml = {}
                    mathml['book_id'] = book_id
                    mathml['mathml'] = mathml_text
                    mathml['start'] = mathml_match.start()
                    mathml['start_element'] = start_element
                    mathml['parent_element']  = parent_element
                    mathml['parent_element_text'] = parent_el_text
                    mathml['alttext'] = alttext
                    mathml['altimg'] = altimg
                    if '<!--' in is_comment:
                        mathml['in_comment'] = True
                    else:
                        mathml['in_comment'] = False
                    mathml_columns = mathml.keys()
                    mathml_values = [mathml[col] for col in mathml_columns]
                    cursor.execute(mathml_insert, (AsIs(','.join(mathml_columns)), tuple(mathml_values)))
                    mathml_id = cursor.fetchone()[0]
                    for attr_name in other_atts:
                        attr = {}
                        attr['mathml_id'] = mathml_id
                        attr['name'] = attr_name
                        attr['value'] = other_atts[attr_name]
                        attr_columns = attr.keys()
                        attr_values = [attr[col] for col in attr_columns]
                        cursor.execute(attr_insert, (AsIs(','.join(attr_columns)), tuple(attr_values)))
                con.commit()
            except psycopg2.Error as error:
                print(error)
                print(error.pgcode)
                print(error.pgerror)
                con.rollback()










