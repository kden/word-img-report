import boto3
import bz2
import json
import os

from pytitle.util import exists, normalize_file_path


def get_artifact_log(bucket, prefix, artifact_id, base_dir):
    s3 = boto3.client('s3')
    filename = prefix + '/' + artifact_id + '.json.bz2'
    print(bucket + '/' + filename)
    json_filename = base_dir + os.sep + artifact_id + '.json.bz2'
    if os.path.exists(json_filename):
        print(json_filename + " already downloaded, using existing file")
    else:
        s3.download_file(bucket, filename, json_filename)
    json_file = bz2.BZ2File(json_filename, "r")
    img_log_data = {}
    for img_entry_json in json_file:
        img_entry = json.loads(img_entry_json)
        if (exists(img_entry, 'image_src_attribute')):
            img_log_data[normalize_file_path(os.path.basename(img_entry['image_src_attribute']))] = img_entry
    return img_log_data