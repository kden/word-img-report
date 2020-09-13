"""
Parse a print-formatted Salesforce page of Book Quality Reports
"""
import re
from datetime import datetime
from glob import iglob

import psycopg2
from psycopg2._psycopg import AsIs

input_dir = "salesforce"
log_entries = []
row_count = 0

TABLE_ROW_PATTERN = re.compile(r'<tr class=" dataRow.*?</tr>')
TABLE_CELL_PATTERN = re.compile(r'<td.*?>(.*?)</td>')
TABLE_HEADER_CELL_PATTERN = re.compile(r'<th.*?>(.*?)</th>')

INPUT_DATE = "%m/%d/%Y"
OUTPUT_DATE = "%Y-%m-%d"

report_insert = 'insert into quality_report (%s) values %s'

con = psycopg2.connect(database="warehouse", user="bookshare", password="", host="127.0.0.1", port="5432")

print("Database opened successfully")

cursor = con.cursor()
con.rollback()

histogram = {}

row_count = 0

for html_path in iglob(input_dir + '/*.html', recursive=True):
    with open(html_path, 'r') as html_file:
        print("Reading " + html_path)
        for line in html_file:
            if TABLE_ROW_PATTERN.search(line) is not None:
                row = {}
                cells = re.findall(TABLE_CELL_PATTERN, line)
                ths = re.findall(TABLE_HEADER_CELL_PATTERN, line)

                cells = list(map(lambda cell: cell.replace('&nbsp;',''), cells))

                input_date = datetime.strptime(cells[3],INPUT_DATE)
                opened_date = input_date.strftime(OUTPUT_DATE)
                row['isbn'] = cells[13]
                row['format'] = cells[12][0:32]
                row['report_text'] = cells[5]
                row['platform'] = cells[11]
                row['resolution'] = cells[6]
                row['title_instance_id'] = int(cells[10])
                row['opened'] = opened_date
                row['support_request_number'] = int(ths[0])
                row_columns = row.keys()
                row_values = [row[col] for col in row_columns]
                row_count += 1
                cursor.execute(report_insert, (AsIs(','.join(row_columns)), tuple(row_values)))
        html_file.close()
        print("Total rows: " + str(row_count))

con.commit()







