import logging
import os
import json
from oauthlib.oauth2 import LegacyApplicationClient
from requests_oauthlib import OAuth2Session
import re
import errno
from datetime import datetime
import requests

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


def get_filename(result):
    if exists(result, 'copyright_date'):
        copyright_date = datetime.fromisoformat(result['copyright_date'].replace('Z', ''))
        copyright_year = copyright_date.strftime("%Y")
    else:
        copyright_year = 'noyear'
    isbn = result.get('isbn', 'noisbn')
    title = result.get('title', 'notitle')
    title = title[:100]
    publisher = result.get('publisher', 'nopublisher')
    publisher = publisher[:100]
    raw_filename = isbn + '-' + title + '-' + \
                   publisher + '-' + copyright_year \
                   + '-' + str(result.get('num_images', -1)) + '-' + result['id']
    return slugify(raw_filename) + "-DAISY.xml"

def get_dir(result, source_format):
    output_path = 'daisy' + os.sep + format_map[source_format] + os.sep \
                  + get_img_bucket(result.get('num_images', -1)) + os.sep
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
    elif num_images > 1000 and num_images <=5000:
        return '1001-5000'
    elif num_images > 5000 and num_images <=10000:
        return '5001-10000'
    elif num_images > 10000:
        return '10001-up'
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
#BKS_BASE_URL = os.environ.get('BKS_API_BASE_URL', 'https://api.qa.bookshare.org/v2')
#BKS_TOKEN_URL = os.environ.get('BKS_API_TOKEN_URL', 'https://auth.qa.bookshare.org/oauth/token')
BKS_BASE_URL =  'https://api.bookshare.org/v2'
BKS_TOKEN_URL = 'https://auth.bookshare.org/oauth/token'

BKS_PAGE_SIZE = 100
BKS_API_KEY_PARAM = {'api_key': BKS_CLIENT_ID}
BKS_PARAMS = {'limit': BKS_PAGE_SIZE}

X_BOOKSHARE_ORIGIN = os.environ.get('X_BOOKSHARE_ORIGIN', '12345678')
BKS_HEADERS = {'X-Bookshare-Origin': X_BOOKSHARE_ORIGIN}

oauth = OAuth2Session(client=LegacyApplicationClient(client_id=BKS_CLIENT_ID))
oauth.params = BKS_API_KEY_PARAM
oauth.headers = BKS_HEADERS

DTBOOK_MIME_TYPE='application/x-dtbook+xml'

fetch_token()

solr_results = {}

with open('solr_results_under_100_updated_isbns.json', 'r') as infile:
    solr_results = json.load(infile)

for book_format in format_map:
    print(str(book_format))
    format_list = solr_results.get(str(book_format))
    for solr_result in format_list:
        outfilename = get_dir(solr_result, book_format) + get_filename(solr_result)

        if os.path.exists(outfilename):
            print("Skipping " + outfilename)
        else:
            id = solr_result['id']
            url = BKS_BASE_URL + '/titles/' + id + '/DAISY/resources'
            bookshare_start = 0
            next = ""
            done = False
            dtbook_resource = {}
            while not done:
                params = BKS_PARAMS.copy()
                print("Page starts with " + str(bookshare_start))
                params['start'] = next
                print(url)
                print(params)
                r = oauth.get(url=url, params=params)
                if r.status_code == 200:
                    results = r.json()
                    bookshare_start = bookshare_start + BKS_PAGE_SIZE
                    next = results.get("next", "")
                    for resource in results['titleFileResources']:
                        local_uri = resource['localURI']
                        mime_type = resource['mimeType']
                        if local_uri.endswith('.xml'):
                            print(local_uri)
                            print(mime_type)
                        if mime_type == DTBOOK_MIME_TYPE:
                            dtbook_resource = resource
                            done = True
                            break
                else:
                    print(r.status_code)
                    print(r.content)
                done = done or next == "" or bookshare_start >= results['totalResults']

            print(json.dumps(dtbook_resource, indent=2))
            if dtbook_resource:
                download_url = dtbook_resource['links'][0]['href']
                r = requests.get(download_url)
                r.raise_for_status()
                print(outfilename)
                with open(outfilename, 'wb') as out:
                    out.write(r.content)
            else:
                print("Could not find dtbook for " + outfilename)


