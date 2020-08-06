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
import math



def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
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

CATALOG_URL="https://catalog.staging.bookshare.org"

con = psycopg2.connect(database="warehouse", user="bookshare", password="", host="127.0.0.1", port="5432")

print("Database opened successfully")

cursor = con.cursor()
con.rollback()

cursor.execute("select book_id, filename, title_instance_id, source_format, num_images, "
               "title, publisher, copyright_year, isbn from book")
rows = cursor.fetchall()

row_count = 0

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
        byte_size = os.path.getsize(outfilename)
        print("Size: " + str(byte_size))
        try:
            sql = "update book set size_bytes=" + str(byte_size) + " where title_instance_id=" + str(title_instance_id)
            cursor.execute(sql)
            con.commit()
        except psycopg2.Error as error:
            print(error)
            print(error.pgcode)
            print(error.pgerror)
            con.rollback()


