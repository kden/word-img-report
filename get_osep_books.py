import csv
import os

import psycopg2
from psycopg2._psycopg import AsIs
from psycopg2.extras import DictCursor

from pytitle.bksapiv2 import fetch_token
from pytitle.osepbooks import SINGLE_TITLE_SQL, get_osep_insert_title, osep_insert_categories, osep_book_already_loaded, \
    SINGLE_TITLE_ORDER_BY

in_filename = 'osep_books/osep_books.csv'
out_filename = 'output_data/out_failed_submission.csv'
(oauth, token) = fetch_token()

print("I hope you have port forwarding set up.")
'''
Port forwarding to postgres
ssh -L 6665:localhost:6432 someone@somewhere.org
Then connect
psql -h localhost -p 6665 -U dbuser databasename
'''
bks_conn = psycopg2.connect(database="bksdb", user="bookshare", host="localhost", port="6665", cursor_factory=DictCursor)
print("Database bksdb opened successfully")
bks_cursor: DictCursor = bks_conn.cursor()
bks_cat_cursor: DictCursor = bks_conn.cursor()

wh_conn = psycopg2.connect(database="warehouse", user="bookshare", password="", host="127.0.0.1", port="5432",
                       cursor_factory=DictCursor)
print("Database warehouse opened successfully")
wh_cursor: DictCursor = wh_conn.cursor()

osep_book_insert = 'insert into osep_book (%s) values %s on conflict do nothing'

row_count = 0


if os.path.exists(in_filename):
    with open(in_filename, 'r') as in_file:
        csv_reader = csv.DictReader(in_file)
        headers = csv_reader.fieldnames
        for in_row in csv_reader:
            title_id = in_row['Title ID']
            download_count = in_row['Raw Book Download Count']

            try:
                bks_cursor.execute(SINGLE_TITLE_SQL + title_id + SINGLE_TITLE_ORDER_BY)
                result = bks_cursor.fetchall()
                if result is not None and bks_cursor.rowcount > 0:
                    if bks_cursor.rowcount > 1:
                        print("Warning, " + str(bks_cursor.rowcount) + " results for title_id " + title_id)
                    if osep_book_already_loaded(wh_cursor, title_id):
                        print("Book already loaded, " + title_id)
                    else:
                        bks_row = result[0]
                        insert_title = get_osep_insert_title(bks_row, download_count)
                        title_metadata_id = bks_row['title_metadata_id']
                        title_instance_id = bks_row['title_instance_id']
                        row_columns = insert_title.keys()
                        row_values = [insert_title[col] for col in row_columns]
                        wh_cursor.execute(osep_book_insert, (AsIs(','.join(row_columns)), tuple(row_values)))
                        osep_insert_categories(bks_cat_cursor, wh_cursor, title_instance_id, title_metadata_id)
                        row_count += 1
                        if row_count % 100 == 0:
                            print("CSV row " + str(row_count))
                        wh_conn.commit()
            except psycopg2.Error as error:
                print('Postgres failure on title_id '+ title_id)
                print(error)
                print(error.pgcode)
                print(error.pgerror)
            except ValueError as error:
                print('ValueError on title_id '+ title_id)
                print(error)
