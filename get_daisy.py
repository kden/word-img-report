"""
Given a JSON file containing Solr results,
using the Bookshare V2 API, download the DTBook file from the DAISY version of each book.
"""
import json
import os
import requests

from pytitle.bksapiv2 import fetch_token, BKS_BASE_URL, BKS_PARAMS, BKS_PAGE_SIZE
from pytitle.fileutil import format_map, get_dir, get_filename_from_solr_result

solr_results = {}

DTBOOK_MIME_TYPE='application/x-dtbook+xml.py'

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
            url = BKS_BASE_URL + '/titles/' + id + '/DAISY/resources'
            bookshare_start = 0
            next = ""
            done = False
            dtbook_resource = {}
            while not done:
                params = BKS_PARAMS.copy()
                print("Page starts with " + str(bookshare_start))
                params['start'] = next
                print(url)
                print(params)
                r = oauth.get(url=url, params=params)
                if r.status_code == 200:
                    results = r.json()
                    bookshare_start = bookshare_start + BKS_PAGE_SIZE
                    next = results.get("next", "")
                    for resource in results['titleFileResources']:
                        local_uri = resource['localURI']
                        mime_type = resource['mimeType']
                        if local_uri.endswith('.xml'):
                            print(local_uri)
                            print(mime_type)
                        if mime_type == DTBOOK_MIME_TYPE:
                            dtbook_resource = resource
                            done = True
                            break
                else:
                    print(r.status_code)
                    print(r.content)
                done = done or next == "" or bookshare_start >= results['totalResults']

            print(json.dumps(dtbook_resource, indent=2))
            if dtbook_resource:
                download_url = dtbook_resource['links'][0]['href']
                r = requests.get(download_url)
                r.raise_for_status()
                print(outfilename)
                with open(outfilename, 'wb') as out:
                    out.write(r.content)
            else:
                print("Could not find dtbook for " + outfilename)


