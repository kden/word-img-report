import os

import psycopg2
from psycopg2.extras import DictCursor

from pytitle.bksbot import get_source_from_history, get_session
from pytitle.fileutil import EXTENSION_MAP
from pytitle.osepbooks import get_basename_from_row_result
from pytitle.pg import run_update
from pytitle.util import run_command

source_fail_filename = "osep_books/source_fails.txt"


con = psycopg2.connect(database="warehouse", user="bookshare", password="", host="127.0.0.1", port="5432",
                       cursor_factory=DictCursor)

print("Database opened successfully")

cursor = con.cursor()
con.rollback()

cursor.execute("select book_id, filename, download_count, title_instance_id, source_format, "
               "title, publisher, copyright_year, isbn from osep_book order by download_count desc")
rows = cursor.fetchall()

s = get_session()


row_count = 0
success_count = 0
with open(source_fail_filename, 'a') as fail_file:
    for row in rows:
        if success_count % 20 == 1:
            s = get_session()
        basename = get_basename_from_row_result(row)
        out_filename =  'osep_books/source/' + basename + EXTENSION_MAP.get(row['source_format'],'.xxx')

        if os.path.exists(out_filename):
            print("Skipping " + out_filename)
        else:
            success = get_source_from_history(s, row['title_instance_id'], out_filename, fail_file)
            if success:
                success_count += 1
                update_sql = "update osep_book set source_filename='" + out_filename + "' where title_instance_id=" + str(row['title_instance_id'])
                run_update(con, update_sql)
                byte_size = os.path.getsize(out_filename)
                print("Size: " + str(byte_size))

                update_size_sql = "update osep_book set size_bytes=" + str(byte_size) + " where title_instance_id=" + str(row['title_instance_id'])
                run_update(con, update_size_sql)

                if row['source_format'] != 'rtf':
                    output_dirname = 'osep_books/source_exploded/' + basename
                    print("Creating " + output_dirname)
                    run_command('mkdir ' + output_dirname)
                    run_command('unzip -d ' + output_dirname + ' ' + out_filename)

        row_count += 1
        print("row count: " + str(row_count) + " success count: " + str(success_count))
