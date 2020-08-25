import logging
import os
import re
import errno
import requests
import psycopg2
from bs4 import BeautifulSoup
import shutil
import time
import random
import csv
import pytz
from datetime import datetime, timezone


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

def get_now_iso8601_datetime_cst():
    utc_dt = datetime.now(timezone.utc)
    CST = pytz.timezone('US/Central')
    return utc_dt.astimezone(CST).isoformat()



logger = logging.getLogger()
logger.setLevel(logging.INFO)



insights_filename = "title_instance_ids.txt"
insights_outfilename = "histogram.txt"
log_entries = []
row_count = 0


histogram = {}

with open(insights_filename, 'r') as insights_file:
        log_entries = list(csv.reader(insights_file))
        for row in log_entries:
            title_instance_id = row[0];
            if exists(histogram, title_instance_id):
                histogram[title_instance_id] = histogram[title_instance_id] + 1
            else:
                histogram[title_instance_id] = 1

sorted_histogram = sorted(histogram.items(), key=lambda x: x[1], reverse=True)

with open(insights_outfilename, 'w') as out_file:
    out_file.write("|| title_instance_id || count ||\n")
    for i in sorted_histogram:
        out_file.write('| ' + i[0] + ' | ' + str(i[1])+ ' |\n')









