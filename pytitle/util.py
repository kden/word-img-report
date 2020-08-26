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