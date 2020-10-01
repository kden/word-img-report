import os
import psycopg2
from psycopg2.extras import DictCursor

from pytitle.bksapiv2 import fetch_token, download_dtbook_file
from pytitle.osepbooks import get_basename_from_row_result
from pytitle.pg import run_update


con = psycopg2.connect(database="warehouse", user="bookshare", password="", host="127.0.0.1", port="5432",
                       cursor_factory=DictCursor)

print("Database opened successfully")

cursor = con.cursor()
con.rollback()

cursor.execute("select book_id, filename, download_count, title_instance_id, source_format, "
               "title, publisher, copyright_year, isbn from osep_book order by download_count desc")
rows = cursor.fetchall()


row_count = 0
update_count = 0
(oauth, token) = fetch_token()

for row in rows:
    if update_count % 20 == 1:
        (oauth, token) = fetch_token()

    basename = get_basename_from_row_result(row)
    out_filename =  'osep_books/dtbook/' + basename + '.xml'
    ncx_filename =  'osep_books/ncx/' + basename + '.ncx'
    row_count += 1

    if os.path.exists(out_filename):
        print("Skipping " + out_filename)
    else:
        retry_status = ""
        total_retries = 5
        retries = 0
        while retry_status != 'continue' and retries < total_retries:
            download_dtbook_file(oauth, row['title_instance_id'], out_filename, ncx_filename)
            retries += 1
            if retry_status == 'retry':
                (oauth, token) = fetch_token()

        if os.path.exists(out_filename):
            update_sql = "update osep_book set dtbook_filename='" + out_filename + "' where title_instance_id=" + str(row['title_instance_id'])
            run_update(con, update_sql)
            update_count += 1
        else:
            print('Unable to download dtbook ' + out_filename)