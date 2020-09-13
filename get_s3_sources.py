"""
Given a list of title instance IDs, attempt to download them from S3.
This does not currently work because we do not have read access to these source files.
"""
import csv
import os

import boto3
import psycopg2

from pytitle.fileutil import get_basename_from_row_result, get_dir, EXTENSION_MAP, make_dir


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

        source_basename = get_basename_from_row_result(result)
        outdirname = get_dir('source', num_images,source_format) + source_basename
        outfilename = outdirname + EXTENSION_MAP[source_format]

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

