import logging
import os
import json
import requests

from oauthlib.oauth2 import LegacyApplicationClient
from requests_oauthlib import OAuth2Session


def fetch_token():
    try:
        token = oauth.fetch_token(token_url=BKS_TOKEN_URL,
                                  username=BKS_USERNAME, password=BKS_PASSWORD,
                                  client_id=BKS_CLIENT_ID, client_secret='')
        return token
    except Exception as e:
        logger.error("Can't get OAuth2 Token for " + BKS_USERNAME)
        logger.error(str(e))


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
        url = BKS_BASE_URL + '/titles/' + id
        book_record = {}
        r = oauth.get(url, headers=BKS_HEADERS)
        bks_result = r.json()
        book_record['bisacCategories'] = ['MAT000000']
        book_record['copyrightYear'] = bks_result['copyrightDate']
        book_record['countries'] = bks_result['countries']
        book_record['edition'] = bks_result['edition']
        book_record['englishTitle'] = bks_result['title']
        book_record['externalCategoryCode'] = bks_result['externalCategoryCode']
        book_record['isbn'] = bks_result['isbn13']
        book_record['languages'] = bks_result['languages']
        book_record['notes'] = bks_result['notes']
        book_record['onixRecordType'] = 'GENERIC'
        book_record['publicationDate'] = bks_result['publishDate']
        book_record['publisherName'] = bks_result['publisher']
        book_record['readingAgeHigh'] = bks_result['readingAgeMaximum']
        book_record['readingAgeLow'] = bks_result['readingAgeMinimum']
        book_record['seriesNumber'] = bks_result['seriesNumber']
        book_record['seriesTitle'] = bks_result['seriesTitle']
        book_record['synopsis'] = bks_result['synopsis']
        book_record['title'] = bks_result['title']

        print(json.dumps(bks_result, indent=4))
        print(json.dumps(book_record, indent=4))

        break
