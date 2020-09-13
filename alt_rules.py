"""
Attempt a voting scheme to determine whether image alt text should be replaced with
Math Detective alt text.
Takes a list of book_id's containing alt texts which don't fit into a well-defined group
Work in progress: doesn't work well right now.
"""


import psycopg2
from psycopg2.extras import DictCursor

from pytitle.data import histogram_hash, vote_to_keep
from pytitle.fileutil import get_rows_from_file


CANDIDATE_TITLE_FILE = 'no_group_titles.csv'

title_list = get_rows_from_file(CANDIDATE_TITLE_FILE)
# Remove header row
title_list.pop(0)
title_shortlist = [title for title in title_list if 1000 < int(title[0]) < 5000]
print('Number of titles in short list: ' + str(len(title_shortlist)))

con = psycopg2.connect(database="warehouse", user="bookshare", password="", host="127.0.0.1", port="5432",
                       cursor_factory=DictCursor)

print("Database opened successfully")

book_cursor = con.cursor()
con.rollback()


row_count = 0
for book_row in title_shortlist:
    book_id = book_row[1]
    print("book_id: " + str(book_id))
    img_cursor = con.cursor()
    img_cursor.execute("select img_id, left(lowercase, 64) as lowercase, length(alt) as len_alt, left(alt, 64) as alt, "
                       + "alt_text_group, title_instance_id, source_format, title_source, title, publisher, "
                       + "copyright_year, isbn from img where alt_text_group ='no group' and book_id=%s", [book_id])

    if img_cursor.rowcount > 20:
        img_rows = img_cursor.fetchall()
        img_list = [sublist['alt'][:20] for sublist in img_rows]
        img_hash = histogram_hash(img_list)
        for w in sorted(img_hash, key=img_hash.get, reverse=True)[:10]:
            print(str(img_hash[w]) + ': ' + w)

        for w in img_rows:
            score = vote_to_keep(w['alt'], w['len_alt'])
            print(w['alt'] + " ==> " + str(score))






