"""
Given a list of title instance IDs in a file,
use the webapp scraper/bot to trigger DAISY reprocessing of each file
"""

from pytitle.bksbot import get_session, reprocess_book
from pytitle.fileutil import get_list_from_file


s = get_session()

reprocess_set_filename = "reprocess_set.csv"
reprocess_set = get_list_from_file(reprocess_set_filename)

row_count = 0
success_count = 0
for title_instance_id in reprocess_set:
    reprocess_book(s, title_instance_id)


