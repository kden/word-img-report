import os
import errno
import csv
from glob import iglob
import shutil
from datetime import datetime
from pytitle.util import exists, slugify, get_value
from pytitle.util import normalize_file_path



EPUB2 = 11
EPUB3 = 37
NIMAS = 8
DAISY = 3

format_map = {
    EPUB2: 'EPUB2',
    EPUB3: 'EPUB3',
    NIMAS: 'NIMAS',
    DAISY: 'DAISY'
}

extension_map = {
    'EPUB2': ".epub",
    'EPUB3': ".epub",
    'NIMAS': ".zip",
    'DAISY': ".zip"
}


def get_basename_from_row_result(result):
    print(result)
    copyright_year = get_value(result, 'copyright_year', 'noyear')
    isbn = get_value(result, 'isbn', 'noisbn')
    title = get_value(result, 'title', 'ntitle')
    title = title[:100]
    publisher = get_value(result, 'publisher', 'nopublisher')
    publisher = publisher[:100]
    raw_filename = isbn + '-' + title + '-' + \
                   publisher + '-' + str(copyright_year) \
                   + '-' + str(get_value(result, 'num_images', -1)) + '-' + str(result['title_instance_id'])
    return slugify(raw_filename)


def get_filename_from_row_result(result, suffix):
    return get_basename_from_row_result(result) + suffix


def get_filename_from_solr_result(result, suffix):
    if exists(result, 'copyright_date'):
        copyright_date = datetime.fromisoformat(result['copyright_date'].replace('Z', ''))
        copyright_year = copyright_date.strftime("%Y")
    else:
        copyright_year = 'noyear'
    isbn = result.get('isbn', 'noisbn')
    title = result.get('title', 'notitle')
    title = title[:100]
    publisher = result.get('publisher', 'nopublisher')
    publisher = publisher[:100]
    raw_filename = isbn + '-' + title + '-' + \
                   publisher + '-' + copyright_year \
                   + '-' + str(result.get('num_images', -1)) + '-' + result['id']
    return slugify(raw_filename) + suffix


def get_dir(prefix, result, source_format):
    output_path = prefix + os.sep + format_map[source_format] + os.sep \
                  + get_img_bucket(result.get('num_images', -1)) + os.sep
    make_dir(output_path)
    return output_path


def make_dir(path_name):
    if not os.path.exists(os.path.dirname(path_name)):
        try:
            os.makedirs(os.path.dirname(path_name))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise


def get_img_bucket(num_images):
    print(num_images)
    if num_images == 0:
        return '0'
    elif 0 < num_images <= 100:
        return '1-100'
    elif 100 < num_images <= 500:
        return '101-500'
    elif 500 < num_images <= 1000:
        return '501-1000'
    elif 1000 < num_images <= 5000:
        return '1001-5000'
    elif 5000 < num_images <= 10000:
        return '5001-10000'
    elif num_images > 10000:
        return '10001-up'
    else:
        return 'None'


def get_list_from_file(filename):
    reprocess_rows = get_rows_from_file(filename)
    result_set = [int(row[0]) for row in reprocess_rows]
    return result_set


def get_rows_from_file(filename):
    reprocess_rows = []
    if os.path.exists(filename):
        with open(filename, 'r') as input_file:
            reprocess_rows = list(csv.reader(input_file))

    return reprocess_rows


def normalize_image_filenames(basename):
    print("Normalizing " + basename)
    for img_path in iglob(basename + '/images/*'):
        normalized = normalize_file_path(img_path)
        if img_path != normalized:
            print("Normalizing " + img_path + " to " + normalized)
            shutil.move(img_path, normalized)