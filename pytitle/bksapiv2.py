import requests
from oauthlib.oauth2 import LegacyApplicationClient
from requests_oauthlib import OAuth2Session
import os
import logging


def fetch_token():
    oauth = OAuth2Session(client=LegacyApplicationClient(client_id=BKS_CLIENT_ID))
    oauth.params = BKS_API_KEY_PARAM
    oauth.headers = BKS_HEADERS
    try:
        token = oauth.fetch_token(token_url=BKS_TOKEN_URL,
                                  username=BKS_USERNAME, password=BKS_PASSWORD,
                                  client_id=BKS_CLIENT_ID, client_secret='')
        return (oauth, token)
    except Exception as e:
        logger.error("Can't get OAuth2 Token for " + BKS_USERNAME)
        logger.error(str(e))

logger = logging.getLogger()
logger.setLevel(logging.INFO)

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





