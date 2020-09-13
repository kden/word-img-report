import os
import shutil

import requests
import re
from bs4 import BeautifulSoup

from pytitle.dateutil import get_now_iso8601_datetime_cst
from pytitle.util import exists

ARTIFACT_ID_PATTERN = re.compile(r'artifactId=(\d+)&')
ADDED_ALT_TEXT_PATTERN = re.compile(r'Added alt text to images')


CATALOG_URL="https://catalog.bookshare.org"
BKS_USERNAME = os.environ.get('V2_API_USERNAME', 'Missing')
BKS_PASSWORD = os.environ.get('V2_API_PASSWORD', 'Missing')
X_BOOKSHARE_ORIGIN = os.environ.get('X_BOOKSHARE_ORIGIN', '12345678')
BKS_HEADERS = {'X-Bookshare-Origin': X_BOOKSHARE_ORIGIN}

login_params = {
    'j_userName': BKS_USERNAME,
    'j_password': BKS_PASSWORD,
    'signInSubmit': "Sign In"
}


def get_session():
    s = requests.Session()
    return refresh_login(s)


def refresh_login(s):
    s.headers.update(BKS_HEADERS)
    login_response = s.post(CATALOG_URL + '/login', params=login_params)

    print("Login Response: " + str(login_response.status_code))
    if login_response.status_code != 200:
        print(login_response.content)
        return None
    return s


def reprocess_book(s, title_instance_id):
    reprocess_url = CATALOG_URL + '/bookReprocess?titleInstanceId=' + str(title_instance_id)
    reprocess_page = s.get(reprocess_url)
    soup = BeautifulSoup(reprocess_page.content, features="lxml")
    reprocessing_requested_message = re.compile("Background title processing requested")
    reprocess_check = None
    try:
        reprocess_check = soup.find(string=reprocessing_requested_message)
        print("Request sent for " + str(title_instance_id))
    except Exception as e:
        print("Error getting result page for reprocessing")
        print(e)
    if reprocess_check:
        print(str(title_instance_id) + " reprocessing requested")
    else:
        print("Something else happened.")
        print(str(reprocess_page.status_code))
        print(reprocess_page.content)


def get_latest_history_link(s, title_instance_id, artifact_format):
    history_url = CATALOG_URL + '/bookActionHistory?titleInstanceId=' + str(title_instance_id)
    history_page = s.get(history_url)
    soup = BeautifulSoup(history_page.content, features="lxml")
    if alt_text_updated(history_page.content):
        print("Alt text was updated.")
    else:
        print("Alt text was not updated.")
        return None
    source_links = soup.find_all(title='Download title source file',
                                 href=re.compile("artifactFormat=" + artifact_format))
    if source_links:
        return source_links[1].get('href')
    return None


def alt_text_updated(body):
    return ADDED_ALT_TEXT_PATTERN.search(str(body)) is not None


def get_artifact_id(s, title_instance_id, artifact_format):
    source_link = get_latest_history_link(s, title_instance_id, artifact_format)
    if source_link is not None:
        match = ARTIFACT_ID_PATTERN.search(source_link)
        return match.group(1)
    return None


def get_source_from_history(s, title_instance_id, source_filename, fail_file):
    history_url = CATALOG_URL + '/bookActionHistory?titleInstanceId=' + str(title_instance_id)
    history_page = s.get(history_url)
    soup = BeautifulSoup(history_page.content, features="lxml")
    new_epub_td_pattern = re.compile("Source is EPUB3, archiving derived EPUB3")
    epub3_source_check = None
    source_link = None
    success = False
    try:
        epub3_source_check = soup.find(string=new_epub_td_pattern).parent.parent.find(
            title='Download title source file').get('href')
        print("Using updated EPUB3 source")
    except Exception as e:
        pass
        # print("No updated link for EPUB3 source download")
        # print(e)
    if epub3_source_check:
        source_link = epub3_source_check
    else:
        source_links = soup.find_all(title='Download title source file')
        if source_links:
            source_link = source_links[-1].get('href')
    if source_link:
        download_url = CATALOG_URL + source_link
        connect_timeout_seconds = 60
        read_timeout_seconds = 180
        try:
            print("Retrieving " + source_filename + " " + source_link)
            download_response = s.get(download_url, stream=True, timeout=(connect_timeout_seconds, read_timeout_seconds))
            if exists(download_response.headers, 'Content-Length'):
                content_length_bytes = int(download_response.headers.get('Content-length'))
                if content_length_bytes > 0:
                    content_length_mb = round(content_length_bytes / 1048576, 1)
                print("Content length: " + str(download_response.headers.get('Content-length')) + " (" + str(
                    content_length_mb) + " MB)")
            if download_response.status_code == 200:
                with open(source_filename, 'wb') as outfile:
                    shutil.copyfileobj(download_response.raw, outfile)
                del download_response
                success = True
            else:
                print("Download response: " + str(download_response.status_code))
                print(download_response.content)
                fail_file.write(str(title_instance_id) + "," + str(
                    download_response.status_code) + ',' + get_now_iso8601_datetime_cst() + ',' + download_url + '\n')
                fail_file.flush()
        except Exception as e:
            print('Source download or save failure for ' + download_url)
            print(str(e))
            fail_file.write(str(title_instance_id) + ',exception,' + get_now_iso8601_datetime_cst() + '\n')
            fail_file.flush()
    else:
        print("No last source link, here is page: ")
        print(history_page.content)
        fail_file.write(str(title_instance_id) + ',nosourcelink,' + get_now_iso8601_datetime_cst() + '\n')
        fail_file.flush()
    return success