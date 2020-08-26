import csv
import logging

from pytitle.util import exists

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









