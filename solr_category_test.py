"""
Retrieve a list of titles from Solr and save as a JSON file.
"""
import csv
import random

import requests

from pytitle.solr import escape_solr_arg

OUTPUT_FILENAME = 'timing_results'

SOLR_URL = 'http://search1.qa.bookshare.org:8983/solr/core0/select'

SOLR_FIELDS = ['musical_key',
               'content_type',
               'title',
               'title_id',
               'author',
               'shared',
               'format',
               'submitter',
               'proofreader',
               'id',
               'score',
               'index_date',
               'site',
               'category',
               'grade',
               'language',
               'title_source_description',
               'submit_date',
               'usage_restriction',
               'title_instance_id',
               'replacement_id',
               'isbn',
               'external_format',
               'series_title',
               'title_simple',
               'subtitle',
               'series_subtitle',
               'series_number',
               'copyright_date',
               'copyright_name',
               'publisher',
               'category_bisac',
               'quality',
               'region',
               'allow_recommend',
               'external_category_code',
               'synopsis',
               'edition',
               'reading_age_min',
               'reading_age_max',
               'marrakesh_available',
               'content_warning',
               'notes',
               'music_score_type',
               'instruments',
               'opus',
               'has_chord_symbols',
               'movement_number',
               'movement_title',
               'vocal_parts',
               'state',
               'isbn_related',
               'publish_date',
               'checkin_date',
               'checkout_date',
               'withdrawal_date',
               'conversion_date',
               'adult',
               'b4e_significant',
               'user_availability',
               'source_format',
               'pending_reason',
               'num_images',
               'embedded_image_descriptions',
               'latest_change_date',
               'dtbook_size'
               ]

SOLR_PARAMS = {'q.alt': '*:*',
               'qt': 'browse',
               'fl': 'musical_key,content_type,title,title_id,author,shared,format,submitter,proofreader,id,score,index_date,site,category,grade,language,title_source_description,submit_date,usage_restriction,title_instance_id,replacement_id,isbn,external_format,series_title,title_simple,subtitle,series_subtitle,series_number,copyright_date,copyright_name,publisher,category_bisac,quality,region,allow_recommend,external_category_code,synopsis,edition,reading_age_min,reading_age_max,marrakesh_available,content_warning,notes,music_score_type,instruments,opus,has_chord_symbols,movement_number,movement_title,vocal_parts,state,isbn_related,publish_date,checkin_date,checkout_date,withdrawal_date,conversion_date,adult,b4e_significant,user_availability,source_format,pending_reason,num_images,embedded_image_descriptions,latest_change_date,dtbook_size,[child parentFilter="*:* -solr_record_type:[2 TO 5]"]',
               'rows': '100',
               'start': '0',
               'fq': ['-solr_record_type:[2 TO 5]',
                      '-author_exact_first_last:Heinlein AND -author_exact_first_last:Hubbard AND -author_exact_last_first:Heinlein AND -author_exact_last_first:Hubbard',
                      'language:2',
                      ' NOT adult:true AND  NOT user_availability:2 AND (quality:2 OR quality:3 OR (*:* NOT quality:*)) AND state:5',
                      'format:37'],
               'sort': 'publish_date desc,title_sort asc,id asc',
               'debugQuery': 'false',
               'wt': 'json'
               }




CATEGORIES = ["History",
              "Children's Books",
              "Entertainment",
              "Horror",
              "Military",
              "Nonfiction",
              "Reference",
              "Romance",
              "Science",
              "Sports",
              "Teens",
              "Travel",
              "Westerns",
              "Animals",
              "Poetry",
              "Disability-Related",
              "Self-Help",
              "Art and Architecture",
              "Biographies and Memoirs",
              "Computers and Internet",
              "Cooking, Food and Wine",
              "Health, Mind and Body",
              "Home and Garden",
              "Literature and Fiction",
              "Mystery and Thrillers",
              "Outdoors and Nature",
              "Parenting and Family",
              "Religion and Spirituality",
              "Science Fiction and Fantasy",
              "Business and Finance",
              "Textbooks",
              "Study Guides",
              "Technology",
              "Philosophy",
              "Politics and Government",
              "Sociology",
              "Gay, Lesbian, Bisexual and Transgender",
              "Psychology",
              "Education",
              "Social Studies",
              "Drama, Plays and Theater",
              "Language Arts",
              "Earth Sciences",
              "Humor",
              "Law, Legal Issues and Ethics",
              "Mathematics and Statistics",
              "Medicine",
              "Communication",
              "Foreign Language Study",
              "Music"
              ]


def get_include_list(number):
    cats = random.sample(ESCAPED_CATEGORIES, number)
    prefixed = list(map(lambda cat: 'category:' + cat , cats))
    clauses = ' OR '.join(prefixed)
    return clauses


def get_exclude_list(number):
    cats = random.sample(ESCAPED_CATEGORIES, number)
    prefixed = list(map(lambda cat: '-category:' + cat , cats))
    clauses = ' AND '.join(prefixed)
    return clauses


ESCAPED_CATEGORIES = list(map(lambda cat: escape_solr_arg(cat), CATEGORIES))

TRIALS = 1000
done = False

for number in [5,10]:
    with open(OUTPUT_FILENAME + '-' + str(number) + '.csv', 'w') as out_file:
        headers = ['q_time', 'elapsed', 'num_found', 'include_list', 'exclude_list']
        csv_writer = csv.DictWriter(out_file, fieldnames=headers)
        csv_writer.writeheader()
        for i in range(0, TRIALS):
            if i % 100 == 0:
                print("Trial " + str(i) + " for categories " + str(number) )
            params = SOLR_PARAMS.copy()
            fq = params['fq'].copy()
            include_list = get_include_list(number)
            exclude_list = get_exclude_list(number)
            fq.append(include_list)
            fq.append(exclude_list)
            params['fq'] = fq
            r = requests.get(url=SOLR_URL, params=params)
            try:
                results = r.json()
            except Exception as e:
                print(str(r.status_code))
                print(r.content)
            q_time = results['responseHeader']['QTime']
            elapsed = r.elapsed
            out_row = {}
            out_row['q_time'] = q_time
            out_row['elapsed'] = elapsed
            out_row['num_found'] = results['response']['numFound']
            out_row['include_list'] = include_list
            out_row['exclude_list'] = exclude_list
            csv_writer.writerow(out_row)
