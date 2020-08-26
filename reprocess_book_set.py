import csv
import logging
import os
import re

import requests
from bs4 import BeautifulSoup

from pytitle.bksbot import get_session, CATALOG_URL

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s = get_session()

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


