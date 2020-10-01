from psycopg2._psycopg import AsIs

from pytitle.pg import OUTPUT_DATE
from pytitle.util import get_value, slugify

SINGLE_TITLE_SQL = '''
select 
t.title_id,
ti.title_instance_id,
ti.title_metadata_id,
ti.publish_date,
ti.latest_change_date,
b.title,
b.num_pages,
b.num_images,
i.isbn13,
pb.publisher_name,
cp.date as copyright_date,
la.iso_639_code as "language",
ts.description as title_source_desc,
ta.title_artifact_id as source_artifact_id,
taf."type" as source_artifact_format
from title t
join title_instance ti using (title_id)
join title_metadata tm using (title_metadata_id)
join title_metadata_to_language using (title_metadata_id)
join book_metadata b using (title_metadata_id) 
join title_source ts using (title_source_id)
join publisher pb using (publisher_id)
join copyright cp using (copyright_id)
join "language" la using (language_id)
join isbn i using (isbn_id)
join title_artifact ta using (title_instance_id)
join title_artifact_format taf using(title_artifact_format_id)
where ti.title_instance_status_id=5 
and ta.parent_title_artifact_id is null 
and taf."type" <> 'IMAGES'
and title_id=
'''

SINGLE_TITLE_ORDER_BY = '''
 order by ta.date_created desc
'''

def osep_book_already_loaded(wh_cur, title_id):
    osep_book_select = 'select book_id from osep_book where title_id='  + title_id
    wh_cur.execute(osep_book_select)
    if wh_cur.rowcount > 0:
        return True
    else:
        return False


def get_osep_insert_title(bks_row, download_count):
    if bks_row['copyright_date'] is None:
        copyright_date = None
    else:
        try:
            copyright_date = bks_row['copyright_date'].year
        except:
            copyright_date = None
    insert_title = {'title': bks_row['title'][0:256],
                    'publisher': bks_row['publisher_name'][0:256],
                    'title_source': bks_row['title_source_desc'],
                    'copyright_year': copyright_date,
                    'submitted': bks_row['publish_date'].strftime(OUTPUT_DATE),
                    'last_indexed': bks_row['latest_change_date'].strftime(OUTPUT_DATE),
                    'source_format': bks_row['source_artifact_format'][0:8],
                    'title_instance_id': bks_row['title_instance_id'],
                    'title_id': bks_row['title_id'],
                    'num_pages': bks_row['num_pages'],
                    'num_images': bks_row['num_images'],
                    'language': bks_row['language'],
                    'isbn': bks_row['isbn13'],
                    'download_count': download_count,
                    'source_artifact_id': bks_row['source_artifact_id']}
    return insert_title


def osep_insert_categories(bks_cat_cursor, wh_cursor, title_instance_id, title_metadata_id):
    osep_cat_insert = 'insert into title_instance_to_category (%s) values %s on conflict do nothing'
    bks_cat_select = 'select category_id from book_metadata_to_category where title_metadata_id='

    bks_cat_cursor.execute(bks_cat_select + str(title_metadata_id))
    categories = bks_cat_cursor.fetchall()
    for category_row in categories:
        out_category = {
            'category_id': category_row['category_id'],
            'title_instance_id': title_instance_id
        }
        row_columns = out_category.keys()
        row_values = [out_category[col] for col in row_columns]
        wh_cursor.execute(osep_cat_insert, (AsIs(','.join(row_columns)), tuple(row_values)))

def get_basename_from_row_result(result):
    copyright_year = get_value(result, 'copyright_year', 'noyear')
    isbn = get_value(result, 'isbn', 'noisbn')
    title = get_value(result, 'title', 'notitle')
    source_format = get_value(result, 'source_format', 'noformat')
    download_count = str(get_value(result, 'download_count', 'nocount'))

    title = title[:100]
    publisher = get_value(result, 'publisher', 'nopublisher')
    publisher = publisher[:100]
    raw_filename = source_format + '-' + isbn + '-' + download_count + '-' + title + '-' + \
                   publisher + '-' + str(copyright_year) \
                   + '-' + str(result['title_instance_id'])
    return slugify(raw_filename)