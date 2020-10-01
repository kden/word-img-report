"""
Using the Bookshare web app scraper/bot, download the source files for a list of titles
retrieved from the image alt text database.
"""
import csv
import os
import random
import time

import psycopg2

from pytitle.bksbot import get_session, refresh_login, get_source_from_history
from pytitle.fileutil import get_filename_from_row_result, EXTENSION_MAP, get_dir

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

        source_filename = get_filename_from_row_result(result, EXTENSION_MAP[source_format])
        outfilename = get_dir('source', num_images, source_format) + source_filename

        if os.path.exists(outfilename):
            print("Skipping already downloaded " + outfilename)
        elif int(title_instance_id) in previous_fails:
            print("Skipping because previously failed: " + outfilename)
        else:
            get_source_from_history(s, title_instance_id, source_format, source_filename, fail_file)

            seconds = random.randrange(2,10)
            print("Sleeping " + str(seconds) + " seconds")
            time.sleep(seconds)
        print("")

        if success_count > 0 and success_count % 100 == 0:
            refresh_login(s)

        row_count = row_count + 1

