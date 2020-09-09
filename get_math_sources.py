"""
Using the Bookshare web app scraper/bot, download the source files for a list of titles
retrieved from the image alt text database.
"""
import csv
import logging
import os
import random
import re
import shutil
import time

import psycopg2
from bs4 import BeautifulSoup

from pytitle.bksbot import get_session, refresh_login, CATALOG_URL
from pytitle.dateutil import get_now_iso8601_datetime_cst
from pytitle.fileutil import get_filename_from_row_result, extension_map, get_dir
from pytitle.util import exists

logger = logging.getLogger()
logger.setLevel(logging.INFO)

con = psycopg2.connect(database="warehouse", user="bookshare", password="", host="127.0.0.1", port="5432")

print("Database opened successfully")

cursor = con.cursor()
con.rollback()

cursor.execute("select book_id, filename, title_instance_id, source_format, num_images, "
               "title, publisher, copyright_year, isbn from book "
               # "and title_instance_id not in (1689090,1653548,2177103)")
)
rows = cursor.fetchall()

s = get_session()

source_fail_filename = "source_fails.txt"
previous_fails = []
if os.path.exists(source_fail_filename):
    with open(source_fail_filename, 'r') as fail_file:
        failed_id_rows = list(csv.reader(fail_file))
        previous_fails = [int(row[0]) for row in failed_id_rows]
print("Previously failed title instance ids: " + str(previous_fails))

with open(source_fail_filename, 'a') as fail_file:
    row_count = 0
    success_count = 0

    for row in rows:
        book_id = row[0]
        dtbookfilename = row[1]
        title_instance_id = row[2]
        source_format = row[3]
        num_images = int(row[4])
        title = row[5]
        publisher = row[6]
        copyright_year = row[7]
        isbn = row[8]
        result = {}
        result['title_instance_id'] = title_instance_id
        result['source_format'] = source_format
        result['num_images'] = num_images
        result['title'] = title
        result['publisher'] = publisher
        result['copyright_year'] = copyright_year
        result['isbn'] = isbn

        source_filename = get_filename_from_row_result(result, extension_map[source_format])
        outfilename = get_dir('source', num_images, source_format) + source_filename

        if os.path.exists(outfilename):
            print("Skipping already downloaded " + outfilename)
        elif int(title_instance_id) in previous_fails:
            print("Skipping because previously failed: " + outfilename)
        else:
            history_url = CATALOG_URL + '/bookActionHistory?titleInstanceId=' + str(title_instance_id)
            history_page = s.get(history_url)
            soup = BeautifulSoup(history_page.content, features="lxml")
            new_epub_td_pattern = re.compile("Source is EPUB3, archiving derived EPUB3")
            epub3_source_check = None
            source_link = None
            try:
                epub3_source_check = soup.find(string=new_epub_td_pattern).parent.parent.find(title='Download title source file').get('href')
                print("Using updated EPUB3 source")
            except Exception as e:
                pass
                #print("No updated link for EPUB3 source download")
                #print(e)
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
                    print("Retrieving " + source_filename  + " " + source_link)
                    download_response = s.get(download_url, stream=True, timeout=(connect_timeout_seconds, read_timeout_seconds))
                    if exists(download_response.headers, 'Content-Length'):
                        content_length_bytes = int(download_response.headers.get('Content-length'))
                        if content_length_bytes > 0:
                            content_length_mb = round(content_length_bytes / 1048576, 1)
                        print("Content length: " + str(download_response.headers.get('Content-length')) + " (" + str(content_length_mb) + " MB)")
                    if download_response.status_code == 200:
                        with open(outfilename, 'wb') as outfile:
                            shutil.copyfileobj(download_response.raw, outfile)
                        del download_response
                        success_count = success_count + 1
                    else:
                        print("Download response: " + str(download_response.status_code))
                        print(download_response.content)
                        fail_file.write(str(title_instance_id) + "," + str(download_response.status_code) + ',' + get_now_iso8601_datetime_cst()  + ',' + download_url + '\n')
                        fail_file.flush()
                except Exception as e:
                    logger.error('Source download or save failure for ' + download_url)
                    logger.error(str(e))
                    fail_file.write(str(title_instance_id) + ',exception,' + get_now_iso8601_datetime_cst() + '\n')
                    fail_file.flush()
            else:
                print("No last source link, here is page: ")
                print(history_page.content)
                fail_file.write(str(title_instance_id) + ',nosourcelink,' + get_now_iso8601_datetime_cst() + '\n')
                fail_file.flush()

            seconds = random.randrange(2,10)
            print("Sleeping " + str(seconds) + " seconds")
            time.sleep(seconds)
        print("")

        if success_count > 0 and success_count % 100 == 0:
            refresh_login(s)

        row_count = row_count + 1

