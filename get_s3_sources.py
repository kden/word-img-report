import logging
import os
import re
import errno
import psycopg2
import json
from bs4 import BeautifulSoup

import csv
import pytz
from datetime import datetime, timezone
import boto3



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

def get_basename(result):
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
    return slugify(raw_filename)

def get_dir(num_images, source_format):
    output_path = 'source' + os.sep + source_format + os.sep \
                  + get_img_bucket(num_images) + os.sep
    make_dir(os.path.dirname(output_path))
    return output_path

def make_dir(path_name):
    if not os.path.exists(os.path.dirname(path_name)):
        try:
            os.makedirs(os.path.dirname(path_name))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise


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



con = psycopg2.connect(database="warehouse", user="bookshare", password="", host="127.0.0.1", port="5432")

print("Database opened successfully")

cursor = con.cursor()
con.rollback()

cursor.execute("select book_id, filename, title_instance_id, source_format, num_images, "
               "b.title, publisher, copyright_year, isbn, sa.title_artifact_id, sa.related_title_artifact_id from book b join source_artifact sa using (title_instance_id) "
               "join source_format sf on sa.format_id = sf.source_format_id "
               "where sf.name = b.source_format and (size_bytes = 0 or size_bytes is null) "
               # "and title_instance_id not in (1689090,1653548,2177103)")
)
rows = cursor.fetchall()



S3_REPOSITORY = "s3://bookshare-versioned/repository/"
S3_BUCKET = "bookshare-versioned"
S3_PREFIX = "repository"

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
        title_artifact_id = row[9]
        related_title_artifact_id = row[10]

        result = {}
        result['title_instance_id'] = title_instance_id
        result['source_format'] = source_format
        result['num_images'] = num_images
        result['title'] = title
        result['publisher'] = publisher
        result['copyright_year'] = copyright_year
        result['isbn'] = isbn
        result['title_artifact_id'] = title_artifact_id
        result['related_title_artifact_id'] = related_title_artifact_id


        s3 = boto3.client('s3')

        source_basename = get_basename(result)
        outdirname = get_dir(num_images,source_format) + source_basename
        outfilename = outdirname + extension_map[source_format]

        if os.path.exists(outfilename):
            print("Skipping already downloaded " + outfilename)
        else:
            if not os.path.exists(outdirname):
                make_dir(outdirname)


            prefix = S3_PREFIX + '/' + str(title_artifact_id) + '/'
            resp = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=prefix)
            for obj in resp['Contents']:
                s3key = obj['Key']
                filename = s3key.split('/')[-1]
                out_resource_name = outdirname + '/' + filename
                print("Downloading " + s3key)
                s3.download_file(S3_BUCKET, s3key, out_resource_name)
            if related_title_artifact_id is not None and related_title_artifact_id != '':
                image_dir_name = outdirname + '/images'
                make_dir(image_dir_name)
                prefix = S3_PREFIX + '/' + str(related_title_artifact_id) + '/'
                resp = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=prefix)
                for obj in resp['Contents']:
                    s3key = obj['Key']
                    filename = s3key.split('/')[-1]
                    out_resource_name = image_dir_name + '/' + filename
                    print("Downloading " + s3key)
                    s3.download_file(S3_BUCKET, s3key, out_resource_name)


        row_count = row_count + 1
        if row_count == 1:
            break

