"""
Given a JSON file containing Solr results,
using the Bookshare V2 API, download the DTBook file from the DAISY version of each book.
"""
import json
import os

from pytitle.bksapiv2 import fetch_token, download_dtbook_file
from pytitle.fileutil import format_map, get_dir, get_filename_from_solr_result

solr_results = {}

(oauth, token) = fetch_token()

solr_results = {}

with open('solr_results_after_aug_1_updated_isbns.json', 'r') as infile:
    solr_results = json.load(infile)

for book_format in format_map:
    print(str(book_format))
    format_list = solr_results.get(str(book_format))
    for solr_result in format_list:
        outfilename = get_dir('daisy', solr_result, book_format) + get_filename_from_solr_result(solr_result, "-DAISY.xml")

        if os.path.exists(outfilename):
            print("Skipping " + outfilename)
        else:
            id = solr_result['id']
            download_dtbook_file(oauth, id, outfilename)


