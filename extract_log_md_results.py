'''
Given an AWS Cloudwatch Insights log of the format @timestamp,@message,@log,@logStream
Extract timing data and write to a new .csv file
'''
import csv
import os
import re
from datetime import datetime


date_pattern = r'^(\[[^\]]*\])'
start_title_pattern = re.compile(date_pattern + r'.*Starting reprocessing of titleInstanceId ([\d]*)')
start_md_pattern = re.compile(date_pattern + r'.*Successful submission for batch UUID')
end_md_pattern = re.compile(date_pattern + r'.*Successful Image Count:[\s]*([\d\w]*).*Usable Image Count:[\s]*([\d\w]*).*'
                             + r'Error Image Count:[\s]*([\d\w]*)', re.MULTILINE|re.DOTALL)

insights_filename = "logs-math-detective-processing-times.csv"
insights_outfilename = "logs-md-out.csv"
log_entries = []
row_count = 0
start_title= False
start_md = False
end_md = False
start_md_time = None
end_md_time = None
title_instance_id = None
usable_images = 0
error_images = 0
success_images = 0

if os.path.exists(insights_filename):
    with open(insights_filename, 'r') as insights_file:
        with open(insights_outfilename, 'w') as out_file:
            log_entries = list(csv.reader(insights_file))
            log_writer = csv.writer(out_file)
            out_row = ['title_instance_id', 'seconds', 'success_images', 'error_images', 'usable_images']
            log_writer.writerow(out_row)
            for row in log_entries:
                start_title_match = start_title_pattern.search(row[1])
                start_md_match = start_md_pattern.search(row[1])
                end_md_match = end_md_pattern.search(row[1])
                if start_title_match is not None:
                    print("Starting Title")
                    for re_group in start_title_match.groups():
                        print(re_group)
                    title_instance_id = start_title_match.group(2)
                elif start_md_match is not None :
                    print("Starting MD Run")
                    start_md_time = datetime.fromisoformat(row[0])
                    for re_group in start_md_match.groups():
                        print(re_group)
                elif end_md_match is not None:
                    print("Ending MD Run")
                    end_md_time = datetime.fromisoformat(row[0])
                    for re_group in end_md_match.groups():
                        print(re_group)
                    success_images = end_md_match.group(2)
                    usable_images = end_md_match.group(3)
                    error_images = end_md_match.group(4)

                    print([success_images, error_images, usable_images])
                    diff = end_md_time - start_md_time
                    out_row = [title_instance_id, diff.total_seconds(), success_images, error_images, usable_images]
                    log_writer.writerow(out_row)

                    print(str(diff))
                else:
                    pass
                new_row = {}









