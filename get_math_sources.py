import logging
import os
import re
import errno
import requests
import psycopg2
from bs4 import BeautifulSoup
import shutil
import time
import random
import csv
import pytz
from datetime import datetime, timezone



def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to underscores.
    """
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    value = re.sub(r'[\s]+', '_', value)
    # ...
    return value

def get_img_bucket(num_images):
    if num_images == 0:
        return '0'
    elif num_images > 0 and num_images <=100:
        return '1-100'
    elif num_images > 100 and num_images <=500:
        return '101-500'
    elif num_images > 500 and num_images <=1000:
        return '501-1000'
    elif num_images > 1000 and num_images <=5000:
        return '1001-5000'
    elif num_images > 5000 and num_images <=10000:
        return '5001-10000'
    elif num_images > 10000:
        return '10001-up'
    else:
        return 'None'

def get_filename(result):
    print(result)
    copyright_year = get_value(result, 'copyright_year', 'noyear')
    isbn = get_value(result, 'isbn', 'noisbn')
    title = get_value(result, 'title', 'notitle')
    title = title[:100]
    publisher = get_value(result, 'publisher', 'nopublisher')
    publisher = publisher[:100]
    raw_filename = isbn + '-' + title + '-' + \
                   publisher + '-' + str(copyright_year) \
                   + '-' + str(get_value(result, 'num_images', -1)) + '-' + str(result['title_instance_id'])
    return slugify(raw_filename) + extension_map[source_format]

def get_dir(num_images, source_format):
    output_path = 'source' + os.sep + source_format + os.sep \
                  + get_img_bucket(num_images) + os.sep
    if not os.path.exists(os.path.dirname(output_path)):
        try:
            os.makedirs(os.path.dirname(output_path))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise
    return output_path


def get_img_bucket(num_images):
    #print("Number of images: " + str(num_images))
    if num_images == 0:
        return '0'
    elif num_images > 0 and num_images <=100:
        return '1-100'
    elif num_images > 100 and num_images <=500:
        return '101-500'
    elif num_images > 500 and num_images <=1000:
        return '501-1000'
    elif num_images > 1000 and num_images <=5000:
        return '1001-5000'
    elif num_images > 5000 and num_images <=10000:
        return '5001-10000'
    elif num_images > 10000:
        return '10001-up'
    else:
        return 'None'

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

EPUB2 = 11
EPUB3 = 37
NIMAS = 8
DAISY = 3

extension_map = {
    'EPUB2': ".epub",
    'EPUB3': ".epub",
    'NIMAS': ".zip",
    'DAISY': ".zip"
}

BKS_USERNAME = os.environ.get('V2_API_USERNAME', 'Missing')
BKS_PASSWORD = os.environ.get('V2_API_PASSWORD', 'Missing')
X_BOOKSHARE_ORIGIN = os.environ.get('X_BOOKSHARE_ORIGIN', '12345678')
BKS_HEADERS = {'X-Bookshare-Origin': X_BOOKSHARE_ORIGIN}

CATALOG_URL="https://catalog.bookshare.org"

con = psycopg2.connect(database="warehouse", user="bookshare", password="", host="127.0.0.1", port="5432")

print("Database opened successfully")

cursor = con.cursor()
con.rollback()

cursor.execute("select book_id, filename, title_instance_id, source_format, num_images, "
               "title, publisher, copyright_year, isbn from book "
               # "and title_instance_id not in (1689090,1653548,2177103)")
)
rows = cursor.fetchall()

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

        source_filename = get_filename(result)
        outfilename = get_dir(num_images,source_format) + source_filename

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
            # reconnect
            login_response = s.post(CATALOG_URL + '/login', params=login_params)
            print("Login Response: " + str(login_response.status_code))
            if login_response.status_code != 200:
                print(login_response.content)
            print("")

        row_count = row_count + 1

