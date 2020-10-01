"""
Given a list of books in the database known to include MathML and the already-downloaded
DTBook files for those books, extract the MathML and write to the database.
"""
import os
import re
from glob import iglob
from lxml import etree

import psycopg2
from lxml.etree import XMLSyntaxError
from psycopg2.extensions import AsIs
from psycopg2.extras import DictCursor

from pytitle.osepbooks import get_basename_from_row_result
from pytitle.util import exists

solr_results = {}
namespaces = {
    'epub': 'http://www.idpf.org/2007/ops',
    'xhtml': 'http://www.w3.org/1999/xhtml',
    'ncx': 'http://www.daisy.org/z3986/2005/ncx/',
    'opf': 'http://www.idpf.org/2007/opf',
    'dtbook': 'http://www.daisy.org/z3986/2005/dtbook/'
}

pagenum_fails = "pagenum_fails.txt"

ncx_pagelist_xpath="//ncx:pageList"
ncx_page_xpath="//ncx:pageList/ncx:pageTarget"
opf_toc_xpath1="/opf:package/opf:manifest/opf:item[@properties='nav']"
opf_toc_xpath2="/opf:package/opf:guide/opf:reference[@type='toc']"
toc_nav_xpath="//xhtml:nav[@epub:type='page-list']"
toc_pages_xpath = toc_nav_xpath + '//xhtml:li'
pagenum_xpath="//*[local-name()='pagenum']"
pagebreak_xpath="//*[@epub:type='pagebreak']"
pagebreak_role_xpath="//*[@xhtml:role='doc-pagebreak']"

pagebreak_pattern = re.compile(r'role=[\'"]doc-pagebreak[\'"]')
pageid_pattern = re.compile(r'id=[\'"]page.?\d+[\'"]')
pagebreak_class_pattern= re.compile(r'class=[\'"]pagebreak[\'"]')


osep_book_insert = 'insert into book_page_summary (%s) values %s on conflict do nothing'


def check_ncx(ncx_path, out_row):
    try:
        ncx_root =  etree.parse(ncx_path)
        print("Loaded " + ncx_path)
        pagelist = ncx_root.xpath(ncx_pagelist_xpath, namespaces=namespaces)
        if pagelist is not None:
            out_row['has_ncx'] = True
        pages = ncx_root.xpath(ncx_page_xpath, namespaces=namespaces)
        if pages is not None and type(pages) == list and len(pages) > 0:
            out_row['has_ncx_pagelist'] = True
            out_row['ncx_pagelist_count'] = len(pages)
    except XMLSyntaxError as e:
        print("XML Syntax Error, too bad." + str(e))

def get_toc_path(opf_path):
    opf_root = etree.parse(opf_path)
    print("Loaded " + opf_path)
    toc = opf_root.xpath(opf_toc_xpath1, namespaces=namespaces)
    toc_href = None
    toc_path = None
    if type(toc) is list and len(toc) > 0:
        print("TOC HREF 1 " + toc[0].attrib['href'])
        toc_href = toc[0].attrib['href']
    else:
        toc = opf_root.xpath(opf_toc_xpath2, namespaces=namespaces)
        if type(toc) is list and len(toc) > 0:
            print("TOC HREF 2 " + toc[0].attrib['href'])
            toc_href = toc[0].attrib['href']
    if toc_href is not None:
        rel_dir = os.path.dirname(opf_path)
        toc_path = rel_dir + '/' + toc_href
    return toc_path

def check_opf(opf_path, out_row):
    try:
        toc_path = get_toc_path(opf_path)
        if toc_path is not None and os.path.exists(toc_path):
            toc_root =  etree.parse(toc_path)
            nav = toc_root.xpath(toc_nav_xpath, namespaces=namespaces)
            if nav is not None:
                out_row['has_epub3_nav'] = True
                page_list = toc_root.xpath(toc_pages_xpath, namespaces=namespaces)
                if page_list is not None and type(page_list) == list and len(page_list) > 0:
                    out_row['has_epub3_pagelist'] = True
                    out_row['epub3_nav_pagelist_count'] = len(page_list)
    except XMLSyntaxError as e:
        print("XML Syntax Error, too bad." + str(e))

def check_html(html_path, out_row):
    try:
        html_root = etree.parse(html_path)
        pagenum_elements = html_root.xpath(pagenum_xpath, namespaces=namespaces)
        if pagenum_elements is not None and type(pagenum_elements) == list and len(pagenum_elements) > 0:
            out_row['has_pagenum'] = True
            if exists(out_row, 'pagenum_element_count'):
                out_row['pagenum_element_count'] += len(pagenum_elements)
            else:
                out_row['pagenum_element_count'] = len(pagenum_elements)

        pagebreak_elements = html_root.xpath(pagebreak_xpath, namespaces=namespaces)
        if pagebreak_elements is not None and type(pagebreak_elements) == list and len(pagebreak_elements) > 0:
            out_row['has_epub3_pagebreak'] = True
            if exists(out_row, 'pagebreak_element_count'):
                out_row['pagebreak_element_count'] += len(pagebreak_elements)
            else:
                out_row['pagebreak_element_count'] = len(pagebreak_elements)

        with open(html_path, 'r') as look_again_file:
            filetext = look_again_file.read()
            look_again_file.close()
        if pagebreak_pattern.search(filetext) is not None:
            out_row['has_pagebreak_role'] = True
        if pageid_pattern.search(filetext) is not None:
            out_row['has_page_ids'] = True
        if pagebreak_class_pattern.search(filetext) is not None:
            out_row['has_pagebreak_class'] = True

    except XMLSyntaxError as e:
        print("XML Syntax Error, too bad." + str(e))



con = psycopg2.connect(database="warehouse", user="bookshare", password="", host="127.0.0.1", port="5432",  cursor_factory=DictCursor)

print("Database opened successfully")

cursor = con.cursor()
insert_cursor = con.cursor()
con.rollback()

cursor.execute("select book_id, download_count, title_instance_id, source_format, "
               "title, publisher, copyright_year, isbn from osep_book where source_filename is not null "
               "and source_filename <> '' "
               "and source_format <> 'RTF'")
rows = cursor.fetchall()

for row in rows:
    out_row = {
        'book_id': row['book_id'],
        'has_ncx': False,
        'has_ncx_pagelist': False,
        'has_pagenum': False,
        'has_epub3_pagebreak': False,
        'has_epub3_pagelist': False,
        'has_epub3_nav': False,
        'has_pagebreak_role': False,
        'has_page_ids': False,
        'has_pagebreak_class': False
    }
    basename = get_basename_from_row_result(row)
    exploded_result =  'osep_books/source_exploded/' + basename
    print(exploded_result)

    for ncx_path in iglob(exploded_result + '/**/*.ncx', recursive=True):
        check_ncx(ncx_path, out_row)

    for opf_path in iglob(exploded_result + '/**/*.opf', recursive=True):
        check_opf(opf_path, out_row)

    for extension in ('html','xhtml','xml'):
        for html_path in iglob(exploded_result + '/**/*.'+extension, recursive=True):
            check_html(html_path, out_row)
    print(out_row)
    row_columns = out_row.keys()
    row_values = [out_row[col] for col in row_columns]
    insert_cursor.execute(osep_book_insert, (AsIs(','.join(row_columns)), tuple(row_values)))
    con.commit()








