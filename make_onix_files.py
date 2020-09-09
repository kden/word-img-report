"""
Given a json file containing Solr search results,
connect to the Bookshare V2 API and create ONIX metadata files from the results.
"""
import json
import logging
import os
from datetime import datetime
from os.path import dirname

import dicttoxml
import lxml.etree as ET

from pytitle.bksapiv2 import fetch_token, BKS_BASE_URL
from pytitle.fileutil import get_dir, format_map
from pytitle.util import exists, slugify

def get_onix_filename(result, isbn=None):
    """
    Create a descriptive filename for the ONIX output file
    :param result: metadata record
    :param isbn:
    :return:
    """
    if exists(result, 'copyright_date'):
        copyright_date = datetime.fromisoformat(result['copyright_date'].replace('Z', ''))
        copyright_year = copyright_date.strftime("%Y")
    else:
        copyright_year = 'noyear'
    if isbn is None:
        best_isbn = result.get('isbn', 'noisbn')
    else:
        best_isbn = isbn
    title = result.get('title', 'notitle')
    title = title[:100]
    publisher = result.get('publisher', 'nopublisher')
    publisher = publisher[:100]
    raw_filename = best_isbn + '-' + title + '-' + \
                   publisher + '-' + copyright_year \
                   + '-' + str(result.get('num_images', -1)) + '-' + result['id']
    return slugify(raw_filename) + ".xml"


get_child_element = lambda parent: XML_CHILD_MAP.get(parent)

ONIX_XSL_FILE = 'onixFile20.xsl'
logger = logging.getLogger()
logger.setLevel(logging.INFO)

solr_results = {
}

XML_CHILD_MAP = {
    'bisacCategories': 'bisacCategory',
    'contributors': 'contributor',
    'countries': 'country',
    'languages': 'language',
    'onixRecords': 'onixRecord'
}

(oauth, token) = fetch_token()

solr_results = {}

with open('solr_results_after_aug_1.json', 'r') as infile:
    solr_results = json.load(infile)

for book_format in format_map:
    format_list = solr_results.get(str(book_format))
    for solr_result in format_list:
        num_images = solr_result.get('num_images', -1)
        outfilename = get_dir('onix', solr_result, book_format) + get_onix_filename(solr_result)
        if os.path.exists(outfilename):
            print("Skipping " + outfilename)
        else:
            '''
            Get the metadata from the Bookshare V2 API
            '''
            id = solr_result['id']
            url = BKS_BASE_URL + '/titles/' + id
            book_record = {}
            r = oauth.get(url)
            if r.status_code == 200:
                bks_result = r.json()
                book_record['bisacCategories'] = ['MAT000000']
                if exists(bks_result, 'categories'):
                    for category in bks_result['categories']:
                        if category['categoryType'] == 'BISAC':
                            book_record['bisacCategories'].append(category['code'])
                book_record['copyrightYear'] = bks_result['copyrightDate']
                book_record['countries'] = bks_result['countries']
                book_record['edition'] = bks_result['edition']
                book_record['englishTitle'] = bks_result['title']
                book_record['externalCategoryCode'] = bks_result['externalCategoryCode']
                book_record['isbn'] = bks_result['isbn13']
                book_record['languages'] = bks_result['languages']
                book_record['notes'] = bks_result['notes']
                book_record['onixRecordType'] = 'GENERIC'
                if exists(bks_result, 'publishDate'):
                    publish_date = datetime.fromisoformat(bks_result['publishDate'].replace('Z', ''))
                    book_record['publicationDate'] = publish_date.strftime("%Y%m%d")
                book_record['publisherName'] = bks_result['publisher']
                book_record['readingAgeHigh'] = bks_result['readingAgeMaximum']
                book_record['readingAgeLow'] = bks_result['readingAgeMinimum']
                book_record['seriesNumber'] = bks_result['seriesNumber']
                book_record['seriesTitle'] = bks_result['seriesTitle']
                book_record['synopsis'] = bks_result['synopsis']
                book_record['title'] = bks_result['title']

                outfilename = get_dir('onix', solr_result, book_format) + get_onix_filename(solr_result, book_record['isbn'])
                if os.path.exists(outfilename):
                    print("Skipping updated " + outfilename)
                else:
                    book_file = {
                        'onixRecords': [book_record]
                    }
                    if (exists(book_record,'isbn')):
                        solr_result['isbn'] = book_record['isbn']
                    print(json.dumps(bks_result, indent=4))
                    print(json.dumps(book_record, indent=4))
                    '''
                    Convert the title metadata to XML and transform it into ONIX
                    '''
                    plain_old_xml = dicttoxml.dicttoxml(book_file, attr_type=False, custom_root='onixFile',
                                                        item_func=get_child_element)
                    xml_dom = ET.fromstring(plain_old_xml)
                    xslt = ET.parse(ONIX_XSL_FILE)
                    transform=ET.XSLT(xslt)
                    onix_record = transform(xml_dom)
                    print(plain_old_xml)
                    print(onix_record)
                    print("Writing " + outfilename)
                    with open(outfilename, 'w') as out:
                        out.write(ET.tostring(onix_record, encoding='unicode', pretty_print=True))

            else:
                print("Couldn't retrieve ONIX.  API result:")
                print(r.text)

'''
We may have found some corrected ISBNs in the API results, overwrite the old ISBNs with these new ones.
'''
with open('solr_results_after_aug_1_updated_isbns.json', 'w') as outfile:
    json.dump(solr_results, outfile, indent=4, sort_keys=True)