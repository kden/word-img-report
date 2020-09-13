import json
import os
import time

import requests
from oauthlib.oauth2 import LegacyApplicationClient
from requests_oauthlib import OAuth2Session


def fetch_token():
    oauth = OAuth2Session(client=LegacyApplicationClient(client_id=BKS_CLIENT_ID))
    oauth.params = BKS_API_KEY_PARAM
    try:
        token = oauth.fetch_token(token_url=BKS_TOKEN_URL,
                                  username=BKS_USERNAME, password=BKS_PASSWORD,
                                  client_id=BKS_CLIENT_ID, client_secret='')
        return (oauth, token)
    except Exception as e:
        print("Can't get OAuth2 Token for " + BKS_USERNAME)
        print(str(e))



BKS_CLIENT_ID = os.environ.get('V2_API_KEY', 'Missing')
BKS_USERNAME = os.environ.get('V2_API_USERNAME', 'Missing')
BKS_PASSWORD = os.environ.get('V2_API_PASSWORD', 'Missing')
#BKS_BASE_URL = os.environ.get('BKS_API_BASE_URL', 'https://api.qa.bookshare.org/v2')
#BKS_TOKEN_URL = os.environ.get('BKS_API_TOKEN_URL', 'https://auth.qa.bookshare.org/oauth/token')
BKS_BASE_URL =  'https://api.bookshare.org/v2'
BKS_TOKEN_URL = 'https://auth.bookshare.org/oauth/token'

DTBOOK_MIME_TYPE='application/x-dtbook+xml'
BKS_PAGE_SIZE = 100
BKS_API_KEY_PARAM = {'api_key': BKS_CLIENT_ID}
BKS_PARAMS = {'limit': BKS_PAGE_SIZE}

def download_daisy_file(oauth, title_instance_id, zippath):
    url = BKS_BASE_URL + '/titles/' + title_instance_id + '/DAISY'
    params = BKS_PARAMS.copy()
    r = oauth.get(url=url, params=params, allow_redirects=True)
    while r.status_code == 202:
        time.sleep(10)
        r = oauth.get(url=url, params=params, allow_redirects=True)
        print(str(r.status_code))

    print("daisy file path: " + zippath)
    with open(zippath, 'wb') as daisy_file:
        daisy_file.write(r.content)



def download_dtbook_file(oauth, id, outfilename, ncxfilename):
    url = BKS_BASE_URL + '/titles/' + str(id) + '/DAISY/resources'
    bookshare_start = 0
    next = ""
    dtbook_done = False
    ncx_done = False
    dtbook_resource = {}
    ncx_resource = {}
    while not dtbook_done or not ncx_done:
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
                if local_uri.endswith('.xml') or local_uri.endswith('.ncx'):
                    print(local_uri)
                    print(mime_type)
                if mime_type == DTBOOK_MIME_TYPE:
                    print("Found DT Book")
                    dtbook_resource = resource
                    dtbook_done = True
                if local_uri.endswith('.ncx'):
                    print("Found NCX file")
                    ncx_resource = resource
                    ncx_done = True
        else:
            print(r.status_code)
            print(r.content)
        end_of_resources = next == "" or bookshare_start >= results['totalResults']
        dtbook_done = dtbook_done or end_of_resources
        ncx_done = ncx_done or end_of_resources
    resource_to_file(dtbook_resource, outfilename, "dtbook")
    resource_to_file(ncx_resource, ncxfilename, "ncx")


def resource_to_file(resource, outfilename, description):
    if resource:
        download_url = resource['links'][0]['href']
        r = requests.get(download_url)
        r.raise_for_status()
        print(outfilename)
        with open(outfilename, 'wb') as out:
            out.write(r.content)
    else:
        print("Could not find " + description + " for " + outfilename)