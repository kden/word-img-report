import logging
import os
import re

import requests
import psycopg2
from bs4 import BeautifulSoup

import csv
import pytz
from datetime import datetime, timezone


def exists(record, field_name):
    """
    Our definition of whether a field exists in a Python dict
    """
    return field_name in record and record[field_name] is not None and record[field_name] != ''

def get_value(record, field_name, default_value):
    if exists(record, field_name):
        return record[field_name]
    else:
        return default_value

def get_now_iso8601_datetime_cst():
    utc_dt = datetime.now(timezone.utc)
    CST = pytz.timezone('US/Central')
    return utc_dt.astimezone(CST).isoformat()

logger = logging.getLogger()
logger.setLevel(logging.INFO)


BKS_USERNAME = os.environ.get('V2_API_USERNAME', 'Missing')
BKS_PASSWORD = os.environ.get('V2_API_PASSWORD', 'Missing')
X_BOOKSHARE_ORIGIN = os.environ.get('X_BOOKSHARE_ORIGIN', '12345678')
BKS_HEADERS = {'X-Bookshare-Origin': X_BOOKSHARE_ORIGIN}

CATALOG_URL="https://catalog.qa.bookshare.org"

s = requests.Session()

login_params = {
    'j_userName': BKS_USERNAME,
    'j_password': BKS_PASSWORD,
    'signInSubmit': "Sign In"
}

s.headers.update(BKS_HEADERS)

login_response = s.post(CATALOG_URL + '/login', params=login_params)

print("Login Response: " + str(login_response.status_code))
if login_response.status_code != 200:
    print(login_response.content)

reprocess_set_filename = "reprocess_set.csv"
reprocess_set = []
if os.path.exists(reprocess_set_filename):
    with open(reprocess_set_filename, 'r') as reprocess_file:
        reprocess_rows = list(csv.reader(reprocess_file))
        print(str(reprocess_rows))
        reprocess_set = [int(row[0]) for row in reprocess_rows]
print("List of title instance ids to be reprocessed: " + str(reprocess_set))

row_count = 0
success_count = 0
for title_instance_id in reprocess_set:

    # https://catalog.qa.bookshare.org/bookReprocess?titleInstanceId=784744
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


