import json
import os
import time

import requests
from oauthlib.common import CaseInsensitiveDict
from requests import HTTPError
from requests_toolbelt.utils import dump
from oauthlib.oauth2 import LegacyApplicationClient
from requests_oauthlib import OAuth2Session

from pytitle.util import slugify, exists


def default_nocompression_headers():
    """
    :rtype: requests.structures.CaseInsensitiveDict
    """
    return CaseInsensitiveDict({
        'User-Agent': 'python-requests/2.24.0',
        'Accept': '*/*',
        'Connection': 'keep-alive',
    })


def fetch_token(compression=True):
    oauth = OAuth2Session(client=LegacyApplicationClient(client_id=BKS_CLIENT_ID))
    if not compression:
        oauth.headers = default_nocompression_headers()
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
BKS_BASE_URL = os.environ.get('BKS_API_BASE_URL', 'https://api.staging.bookshare.org/v2')
BKS_TOKEN_URL = os.environ.get('BKS_API_TOKEN_URL', 'https://auth.staging.bookshare.org/oauth/token')

uncompressed_mime_types  = ['application/json', 'application/x-dtbook+xml', 'application/x-dtbncx+xml']


DTBOOK_MIME_TYPE = 'application/x-dtbook+xml'
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


def download_dtbook_file(oauth, id, out_file_name, ncx_file_name):
    url = BKS_BASE_URL + '/titles/' + str(id) + '/DAISY/resources'
    bookshare_start = 0
    next_token = ""
    dtbook_done = False
    ncx_done = False
    dtbook_resource = {}
    ncx_resource = {}
    while not dtbook_done or not ncx_done:
        params = BKS_PARAMS.copy()
        print("Page starts with " + str(bookshare_start))
        params['start'] = next_token
        print(url)
        print(params)
        r = oauth.get(url=url, params=params)
        if r.status_code == 200:
            results = r.json()
            bookshare_start = bookshare_start + BKS_PAGE_SIZE
            next_token = results.get("next", "")
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
        elif r.status_code in [403, 500]:
            seconds = 60
            print("Sleeping " + str(seconds) + " seconds")
            time.sleep(seconds)
            return "retry"
        else:
            print(r.status_code)
            print(r.content)
        end_of_resources = next_token == "" or bookshare_start >= results['totalResults']
        dtbook_done = dtbook_done or end_of_resources
        ncx_done = ncx_done or end_of_resources
    resource_to_file(dtbook_resource, out_file_name, "dtbook")
    resource_to_file(ncx_resource, ncx_file_name, "ncx")
    return "continue"


def make_oauth_get_request(url, params, mime_type_filter, compression):
    (oauth, token) = fetch_token(compression)
    response = oauth.get(url=url, params=params)
    print("Dumping oauth connection headers for " + url)
    dump_headers(response, mime_type_filter, compression)
    return response


def make_get_request(url, mime_type_filter, compression):
    headers = default_nocompression_headers()
    if compression:
        headers['Accept-Encoding'] = 'gzip,deflate'

    session = requests.Session()
    session.headers = headers

    req = requests.Request('GET', url, headers=headers)
    preq = req.prepare()
    response = session.send(preq)

    print("\nDumping regular request headers for " + url)
    dump_headers(response, mime_type_filter, compression)
    return response


def dump_all(response):
    data = dump.dump_all(response)
    print(data.decode('utf-8'))


def dump_headers(response, mime_type_filter, expect_compressed):
    request_compressed = False
    response_compressed = False
    json_response = False
    request = response.request
    for name in sorted(request.headers.keys()):
        if 'Accept-Encoding' in name:
            prefix = '>>> '
            request_compressed = True
        else:
            prefix = '> '
        print(prefix+ name + ': ' + request.headers.get(name))

    raw = response.raw
    headers = raw.headers

    for name in sorted(headers.keys()):
        for value in headers.getlist(name):
            if 'Content-Encoding' in name:
                prefix = '<<< '
                response_compressed = True
            else:
                prefix = '< '
            if 'Content-Type' in name and 'application/json' in value:
                json_response = True
            print(prefix + name + ': ' + value)

    if expect_compressed :
        not_compressed = ''
    else:
        not_compressed = ' not'


    if expect_compressed == request_compressed:
        print("☑ Request encoding header sent CORRECTLY for" + not_compressed + " compressed resource")
    else:
        print("☒ Request encoding header sent INcorrectly for" + not_compressed + " compressed resource")

    if mime_type_filter in uncompressed_mime_types and not response_compressed:
        print(mime_type_filter + " response sent uncompressed")
    elif json_response and not response_compressed:
        print('application/json' + " response sent uncompressed")
    else:
        if expect_compressed == response_compressed:
            print("☑ Response encoding header sent CORRECTLY for" + not_compressed + " compressed resource")
        else:
            print("☒ Response encoding header sent INcorrectly for" + not_compressed + " compressed resource")


def download_resource_file(title_id, title_instance_id, out_file_name, mime_type_filter, compression):
    #url = BKS_BASE_URL + '/periodicals/' + str(title_id) + '/editions/' + str(title_instance_id) + '/DAISY/resources'
    url = BKS_BASE_URL + '/titles/' + str(title_instance_id) + '/DAISY/resources'
    bookshare_start = 0
    next_token = ""
    retrieval_done = False
    title_resource = {}
    print("### Get resource list from API")
    while not retrieval_done:
        params = BKS_PARAMS.copy()
        #print("Page starts with " + str(bookshare_start))
        params['start'] = next_token
        r = make_oauth_get_request(url, params, mime_type_filter, compression)
        if r.status_code == 200:
            results = r.json()
            #print(json.dumps(results, indent=4))
            bookshare_start = bookshare_start + BKS_PAGE_SIZE
            next_token = results.get("next", "")
            for resource in results['titleFileResources']:
                local_uri = resource['localURI']
                mime_type = resource['mimeType']
                if mime_type == mime_type_filter:
                    # print("Found " + mime_type_filter)
                    # print(local_uri)
                    # print(mime_type)
                    title_resource = resource
                    retrieval_done = True
                    break
        elif r.status_code in [403, 500]:
            seconds = 60
            print("Sleeping " + str(seconds) + " seconds")
            time.sleep(seconds)
            return "retry"
        else:
            print(r.status_code)
            print(r.content)
        end_of_resources = next_token == "" or bookshare_start >= results['totalResults']
        retrieval_done = retrieval_done or end_of_resources
    print("### Attempt to download resource " + mime_type_filter + " from API")
    resource_to_file(title_resource, out_file_name, mime_type_filter, compression)

    return "continue"


def resource_to_file(resource, out_file_name, mime_type_filter, compression=True):
    if resource:
        download_url = resource['links'][0]['href']
        r = make_get_request(download_url, mime_type_filter, compression)
        try:
            r.raise_for_status()
            print("Written to file as: " + out_file_name)
            with open(out_file_name, 'wb') as out:
                out.write(r.content)
        except HTTPError as e:
            print(str(e))

    else:
        print("Could not find " + mime_type_filter + " for " + out_file_name)

