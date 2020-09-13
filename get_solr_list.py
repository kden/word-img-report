"""
Retrieve a list of titles from Solr and save as a JSON file.
"""
import json
import requests


solr_results = {
}

SOLR_PAGE_SIZE = 100

SOLR_URL = 'http://search1.qa.bookshare.org:8983/solr/core0/select'

SOLR_FIELDS = ['title',
                 'format',
                 'source_format',
                 'isbn',
                 'title_source_description',
                 'publisher',
                 'author',
                 'copyright_date',
                 'latest_change_date',
                 'num_images',
                 'category',
                 'category_bisac',
                 'id',
                 'submit_date'
                 ]

SOLR_PARAMS = {#'q': 'num_images:[1 TO *] category:"Mathematics and Statistics" state:5 site:1 index_date:[2020-08-01T00:00:00Z TO *]',
               'q': 'num_images:[1 TO *] category:"Mathematics and Statistics" state:5 site:1',
               'fl': ','.join(SOLR_FIELDS),
               'rows': SOLR_PAGE_SIZE,
               'wt': 'json'
               }


solr_start = 0
done = False
while not done:
    params = SOLR_PARAMS.copy()
    params['start'] = solr_start
    r = requests.get(url=SOLR_URL, params=params)
    results = r.json()
    response = results['response']
    solr_start = solr_start + SOLR_PAGE_SIZE
    print(str(solr_start))
    for doc in response['docs']:
        source_format = doc['source_format']
        if source_format not in solr_results:
            solr_results[source_format] = []
        solr_results[source_format].append(doc)
    done = solr_start >= response['numFound'] #or solr_start >= 500

for source_format, item_list in solr_results.items():
    print(source_format, str(len(item_list)))

with open('solr_results_with_dates.json', 'w') as outfile:
    json.dump(solr_results, outfile, indent=4, sort_keys=True)