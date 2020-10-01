"""
Given the title instance IDs of some books
Download the DTBook and .ncx files to make sure compression and inserted text is correct
"""
import json
import os
import logging

#logging.basicConfig(level=logging.DEBUG)

from pytitle.bksapiv2 import fetch_token, BKS_USERNAME, download_resource_file
from pytitle.util import slugify

#title_ids = [[2025051,3612031],[1995284,3612174],[1976303,3611968]]
title_ids = [[2027258,3612871],[2027250,3612870],[2027241,3612869]]

title_instance_ids=[3612992,3612991]

compression = [True, False]
all_mime_types = ['application/x-dtbook+xml', 'application/x-dtbncx+xml', 'audio/mpeg', 'text/xml', 'application/smil', 'image/jpeg']
#all_mime_types = ['application/x-dtbook+xml']



daisy_mime_extensions = {
    'application/x-dtbook+xml': '-dtbook.xml',
    'application/x-dtbncx+xml': '.ncx',
    'image/jpeg': '.jpg',
    'audio/mpeg': '.mp3',
    'text/xml': '-text.xml',
    'application/smil': '.smil',
}


print("Logged on as: " + BKS_USERNAME)

title_id = None
#for [title_id, title_instance_id] in title_ids:
for title_instance_id in title_instance_ids:
    for mime_type in all_mime_types:
        for compressed in compression:
            out_file_name = 'test/' + slugify(BKS_USERNAME) + '-' + str(title_instance_id) + '-' + str(compressed) + daisy_mime_extensions[mime_type]
            print( \
                 #"\n\n### Title Id: " + str(title_id) +
                " ### Title Instance Id: " + str(title_instance_id)+ " ### Mime type: " + mime_type + " ###  Compressed: " + str(compressed) + " ###")
            download_resource_file(title_id, title_instance_id, out_file_name, mime_type, compressed)




