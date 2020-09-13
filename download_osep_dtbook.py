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

(oauth, token) = fetch_token()

row_count = 0

if oauth is not None and token is not None:
    for row in rows:
        out_filename =  'osep_books/dtbook/' + get_basename_from_row_result(row) + '.xml'
        ncx_filename =  'osep_books/ncx/' + get_basename_from_row_result(row) + '.ncx'

        if os.path.exists(out_filename):
            print("Skipping " + out_filename)
        else:
            download_dtbook_file(oauth, row['title_instance_id'], out_filename, ncx_filename)
            update_sql = "update osep_book set dtbook_filename='" + out_filename + "' where title_instance_id=" + str(row['title_instance_id'])
            run_update(con, update_sql)