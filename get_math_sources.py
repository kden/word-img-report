import logging
import os
import json
from os.path import dirname
from oauthlib.oauth2 import LegacyApplicationClient
from requests_oauthlib import OAuth2Session
import dicttoxml
import re
import errno
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
    and converts spaces to hyphens.
    """
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    value = re.sub(r'[\s]+', '_', value)
    # ...
    return value


def get_filename(result, source_format):
    if source_format == EPUB2:
        extension = '.epub'
    elif source_format == EPUB3:
        extension = '.epub3'
    else:
        extension = '.zip'
    if exists(result, 'copyright_date'):
        copyright_date = datetime.fromisoformat(result['copyright_date'].replace('Z', ''))
        copyright_year = copyright_date.strftime("%Y")
    else:
        copyright_year = 'noyear'
    raw_filename = str(result['isbn']) + '-' + result['title'] + '-' + result['publisher'] + '-' \
                   + copyright_year + '-' + str(result.get('num_images', -1)) + '-' + result['id']
    return slugify(raw_filename) + extension


def get_dir(result, source_format):
    output_path = 'output' + os.sep + format_map[source_format] + os.sep \
                  + get_img_bucket(result.get('num_images', -1)) + os.sep
    if not os.path.exists(os.path.dirname(output_path)):
        try:
            os.makedirs(os.path.dirname(output_path))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise
    return output_path


def get_img_bucket(num_images):
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


fetch_token()

solr_results = {}

with open('solr_results.json', 'r') as infile:
    solr_results = json.load(infile)

for book_format in format_map:
    print(str(book_format))
    format_list = solr_results.get(str(book_format))
    for solr_result in format_list:
        id = solr_result['id']
        url = BKS_BASE_URL + '/titles/' + id + '/source'
        book_record = {}
        r = oauth.get(url, headers=BKS_HEADERS)
        r.raise_for_status()
        outfilename = get_dir(solr_result, book_format) + get_filename(solr_result, book_format)
        print(outfilename)
        with open(outfilename, 'wb') as out:
            out.write(r.content)
        break

