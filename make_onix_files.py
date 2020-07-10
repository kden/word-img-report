import logging
import os
import json
from os.path import dirname
from oauthlib.oauth2 import LegacyApplicationClient
from requests_oauthlib import OAuth2Session
import dicttoxml
import re
import errno
import csv
from datetime import datetime
import lxml.etree as ET


def fetch_token():
    try:
        token = oauth.fetch_token(token_url=BKS_TOKEN_URL,
                                  username=BKS_USERNAME, password=BKS_PASSWORD,
                                  client_id=BKS_CLIENT_ID, client_secret='')
        return token
    except Exception as e:
        logger.error("Can't get OAuth2 Token for " + BKS_USERNAME)
        logger.error(str(e))


def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to underscores.
    """
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    value = re.sub(r'[\s]+', '_', value)
    # ...
    return value


def get_onix_filename(result, isbn=None):
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

def get_dir(num_images, source_format):
    output_path =  'output' + os.sep + format_map[source_format]+ os.sep \
                   + get_img_bucket(num_images) + os.sep
    if not os.path.exists(os.path.dirname(output_path)):
        try:
            os.makedirs(os.path.dirname(output_path))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise
    return output_path


def get_img_bucket(num_images):
    print(num_images)
    if num_images == 0:
        return '0'
    elif num_images > 0 and num_images <=100:
        return '1-100'
    elif num_images > 100 and num_images <=500:
        return '101-500'
    elif num_images > 500 and num_images <=1000:
        return '501-1000'
    elif num_images > 1000:
        return '1001-up'
    else:
        return 'None'

def exists(record, field_name):
    """
    Our definition of whether a field exists in a Python dict
    """
    return field_name in record and record[field_name] is not None and record[field_name] != ''


get_child_element = lambda parent: XML_CHILD_MAP.get(parent)

THIS_DIR = dirname(__file__)
ONIX_XSL_FILE = 'onixFile20.xsl'
logger = logging.getLogger()
logger.setLevel(logging.INFO)

EPUB2 = 11
EPUB3 = 37
NIMAS = 8
DAISY = 3

format_map = {
    EPUB2: 'EPUB2',
    EPUB3: 'EPUB3',
    NIMAS: 'NIMAS',
    DAISY: 'DAISY'
}

solr_results = {
}

BKS_CLIENT_ID = os.environ.get('V2_API_KEY', 'Missing')
BKS_USERNAME = os.environ.get('V2_API_USERNAME', 'Missing')
BKS_PASSWORD = os.environ.get('V2_API_PASSWORD', 'Missing')
BKS_BASE_URL = os.environ.get('BKS_API_BASE_URL', 'https://api.qa.bookshare.org/v2')
BKS_TOKEN_URL = os.environ.get('BKS_API_TOKEN_URL', 'https://auth.qa.bookshare.org/oauth/token')

BKS_API_KEY_PARAM = {'api_key': BKS_CLIENT_ID}

X_BOOKSHARE_ORIGIN = os.environ.get('X_BOOKSHARE_ORIGIN', '12345678')
BKS_HEADERS = {'X-Bookshare-Origin': X_BOOKSHARE_ORIGIN}

oauth = OAuth2Session(client=LegacyApplicationClient(client_id=BKS_CLIENT_ID))
oauth.params = BKS_API_KEY_PARAM
oauth.headers = BKS_HEADERS

XML_CHILD_MAP = {
    'bisacCategories': 'bisacCategory',
    'contributors': 'contributor',
    'countries': 'country',
    'languages': 'language',
    'onixRecords': 'onixRecord'
}

fetch_token()

solr_results = {}

with open('solr_results.json', 'r') as infile:
    solr_results = json.load(infile)

for book_format in format_map:
    format_list = solr_results.get(str(book_format))
    for solr_result in format_list:
        num_images = solr_result.get('num_images', -1)
        outfilename = get_dir(num_images, book_format) + get_onix_filename(solr_result)
        if os.path.exists(outfilename):
            print("Skipping " + outfilename)
        else:
            id = solr_result['id']
            url = BKS_BASE_URL + '/titles/' + id
            book_record = {}
            r = oauth.get(url, headers=BKS_HEADERS)
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

            outfilename = get_dir(num_images, book_format) + get_onix_filename(solr_result, book_record['isbn'])
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
        
with open('solr_results_updated_isbns.json', 'w') as outfile:
    json.dump(solr_results, outfile, indent=4, sort_keys=True)