import os
import requests
import re
from bs4 import BeautifulSoup

ARTIFACT_ID_PATTERN = re.compile(r'artifactId=(\d+)&')
ADDED_ALT_TEXT_PATTERN = re.compile(r'Added alt text to images')

CATALOG_URL="https://catalog.qa.bookshare.org"
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