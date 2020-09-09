"""
Update previously created records in the img alt text database with the submitted and index last updated dates.
"""

import csv
import json
import logging

import psycopg2
from psycopg2.extras import DictCursor

from pytitle.bksapiv2 import fetch_token
from pytitle.fileutil import format_map
from pytitle.util import exists

logger = logging.getLogger()
logger.setLevel(logging.INFO)

OUTPUT_FILENAME='books_by_date.csv'



(oauth, token) = fetch_token()


with open('solr_results_with_dates.json', 'r') as infile:
    solr_results = json.load(infile)

if solr_results:
    con = psycopg2.connect(database="warehouse", user="bookshare", password="", host="127.0.0.1", port="5432",
                           cursor_factory=DictCursor)
    print("Database opened successfully")

    with open(OUTPUT_FILENAME, 'w') as out_file:
        headers = ['title_instance_id', 'publisher', 'title_source', 'source_format', 'submit_date']
        csv_writer = csv.DictWriter(out_file, fieldnames=headers)
        csv_writer.writeheader()

        for book_format in format_map:
            format_list = solr_results.get(str(book_format))
            for solr_result in format_list:
                out_row = {}
                out_row['title_instance_id'] = solr_result.get('id', 'NA')
                out_row['publisher'] = solr_result.get('publisher', 'NA')
                out_row['title_source'] = solr_result.get('title_source_description', 'NA')
                out_row['source_format'] = format_map[book_format]
                out_row['submit_date'] = solr_result.get('submit_date', '')[0:10]
                csv_writer.writerow(out_row)

                if exists(solr_result, 'submit_date') :
                    sql = "update book set submitted='" + solr_result['submit_date'][0:10] \
                         + "' where title_instance_id=" + solr_result['id']
                    #run_update(con, sql)
                if exists(solr_result, 'latest_change_date') :
                    sql = "update book set last_indexed='" + solr_result['latest_change_date'][0:10] \
                         + "' where title_instance_id=" + solr_result['id']
                    #run_update(con, sql)
