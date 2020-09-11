"""
Given a JSON file containing the results of a Solr query,
Extract information about the image references in the corresponding DAISY
DTBook file and save it to a PostgreSQL database.
"""

import json
import logging

import psycopg2
from psycopg2.extensions import AsIs

from pytitle.fileutil import format_map
from pytitle.util import get_shared, copy_rec

logger = logging.getLogger()
logger.setLevel(logging.INFO)


book_insert = 'insert into book (%s) values %s returning book_id'


solr_results = {}

con = psycopg2.connect(database="warehouse", user="bookshare", password="", host="127.0.0.1", port="5432")

print("Database opened successfully")

cursor = con.cursor()
con.rollback()

with open('solr_results_with_dates.json', 'r') as infile:
    solr_results = json.load(infile)

for book_format in format_map:
    format_list = solr_results.get(str(book_format))
    for solr_result in format_list:
        shared = get_shared(solr_result, format_map[book_format])
        try:
            book = shared.copy()
            copy_rec(solr_result, book, 'num_images', 'num_images')
            book_columns = book.keys()
            book_values = [book[col] for col in book_columns]
            cursor.execute(book_insert, (AsIs(','.join(book_columns)), tuple(book_values)))
            book_id = cursor.fetchone()[0]
            con.commit()
        except psycopg2.Error as error:
            print(error)
            print(error.pgcode)
            print(error.pgerror)
            con.rollback()










