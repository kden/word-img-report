import logging
import os
import psycopg2

from pytitle.fileutil import get_dir, get_filename_from_row_result

logger = logging.getLogger()
logger.setLevel(logging.INFO)

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

    source_filename = get_filename_from_row_result(result)
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


