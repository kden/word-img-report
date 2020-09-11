import os
import re

def run_command(command):
    print(command)
    return os.system(command + ">/dev/null 2>&1")

def normalize_file_path(pathname):
    path, filename = os.path.split(pathname)
    filename = filename.lower().replace('-', '_')
    base = filename[0:-4]
    extension = filename[-3:]
    base = base.replace('.', '_')
    new_pathname = '/'.join([path, '.'.join([base, extension])])
    return new_pathname

def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    """
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    value = re.sub(r'[\s]+', '_', value)
    # ...
    return value

def exists(record, field_name):
    """
    Our definition of whether a field exists in a Python dict
    """
    return field_name in record and record[field_name] is not None and record[field_name] != ''

def get_value(record, field_name, default_value):
    if exists(record, field_name):
        return record[field_name]
    else:
        return default_value


def copy_rec(source, destination, source_name, dest_name):
    """
    In a null-safe way, copy a field from a source dictionary to a destination dictionary
    :param source:
    :param destination:
    :param source_name:
    :param dest_name:
    :return:
    """
    if exists(source, source_name):
        destination[dest_name] = source[source_name]


def get_shared(solr_result, source_format):
    """
    Create a new record from a Solr result record, mapping the Solr
    fields to fields used in the database
    :param solr_result:
    :param source_format:
    :return:
    """
    shared = {}

    copy_rec(solr_result, shared, 'title', 'title')
    copy_rec(solr_result, shared, 'title_source_description', 'title_source')
    copy_rec(solr_result, shared, 'publisher', 'publisher')
    copy_rec(solr_result, shared, 'id', 'title_instance_id')
    copy_rec(solr_result, shared, 'isbn', 'isbn')
    shared['source_format'] = source_format
    if exists(solr_result, 'submit_date'):
        shared['submitted'] = solr_result.get('submit_date', '')[0:10]
    if exists(solr_result, 'submit_date'):
        shared['last_indexed'] = solr_result.get('latest_change_date', '')[0:10]
    if exists(solr_result, 'copyright_date'):
        shared['copyright_year'] = int(solr_result['copyright_date'][0:4])
    return shared

