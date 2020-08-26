import csv
import logging
import os
import re

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# [02 Jun 2020 03:27:29,697] INFO ContentAcquisitionTask - processing file [org.bookshare.domain.ContentProcessingItem@31fa5038[contentProcessingId=1962017,source=sweetcherryrnib,contentProcessingType=METADATA,contentProcessingStatus=QUEUED,fileName=SweetCherryPublishing20200602103338.xml,fileSize=87798,releaseDate=<null>,sentDate=Tue Jun 02 10:33:00 PDT 2020,titleInstanceId=<null>]]
log_pattern = re.compile(r'contentProcessingId=([^,]*),source=([^,]*),contentProcessingType=([^,]*),contentProcessingStatus=([^,]*),fileName=([^,]*),fileSize=([^,]*),releaseDate=([^,]*),sentDate=([^,]*),titleInstanceId=([^,\]]*)', re.MULTILINE)

insights_filename = "insights-cat-sweetcherryrnib.csv"
insights_outfilename = "insights-out.csv"
log_entries = []
row_count = 0
if os.path.exists(insights_filename):
    with open(insights_filename, 'r') as insights_file:
        with open(insights_outfilename, 'w') as out_file:
            log_entries = list(csv.reader(insights_file))
            log_writer = csv.writer(out_file)
            for row in log_entries:
                new_row = {}
                for log_match in log_pattern.finditer(row[1]):
                    root_match = log_match.group(0)
                    contentProcessingId = log_match.group(1)
                    source = log_match.group(2)
                    contentProcessingType = log_match.group(3)
                    contentProcessingStatus = log_match.group(4)
                    fileName = log_match.group(5)
                    fileSize = log_match.group(6)
                    releaseDate = log_match.group(7)
                    sentDate = log_match.group(8)
                    titleInstanceId = log_match.group(9)
                    new_row['contentProcessingId'] = contentProcessingId
                    new_row['source'] = source
                    new_row['contentProcessingType'] = contentProcessingType
                    new_row['contentProcessingStatus'] = contentProcessingStatus
                    new_row['fileName'] = fileName
                    new_row['fileSize'] = fileSize
                    new_row['releaseDate'] = releaseDate
                    new_row['sentDate'] = sentDate
                    new_row['titleInstanceId'] = titleInstanceId
                print(str(new_row))
                if row_count == 1:
                    log_writer.writerow(new_row.keys())
                log_writer.writerow(new_row.values())
                row_count = row_count + 1








