from pytitle.util import exists
import re
import numpy as np


def histogram_hash(in_list):
    out_hash = {}
    for item in in_list:
        if exists(out_hash, item):
            out_hash[item] = out_hash[item] + 1
        else:
            out_hash[item] = 1
    return out_hash


def weight_strings_by_prefix(in_list):
    result_list = np.ones_like(in_list, dtype=int)
    weight_indices = {}
    for idx, item in enumerate(in_list):
        prefix = item[:2]
        if not exists(weight_indices, prefix):
            weight_indices[prefix] = idx
    for prefix in weight_indices.keys():
        result_list[weight_indices[prefix]] = 10
    return result_list

def num_spaces(in_string):
    SPACE_PATTERN = r'[ ]'
    return len(re.findall(SPACE_PATTERN, in_string))

def num_text_hints(in_string):
    TEXT_HINTS_PATTERN = r'[^,: ]'
    return len(re.findall(TEXT_HINTS_PATTERN, in_string))

def num_slug_hints(in_string):
    NON_ALPHA_PATTERN = r'[A-Za-z0-9][_-]|[_-][A-Za-z0-9]|[A-Za-z][0-9]|[0-9][A-Za-z]'
    return len(re.findall(NON_ALPHA_PATTERN, in_string))

def num_capitals(in_string):
    CAPITALS_PATTERN = r'[A-Z]'
    return len(re.findall(CAPITALS_PATTERN, in_string))

def vote_to_keep(in_string, length):
    votes = 0
    votes = votes + num_spaces(in_string)
    votes = votes - num_slug_hints(in_string)
    if num_capitals(in_string) > 1:
        votes = votes + 1
    if num_text_hints(in_string) >1:
        votes = votes + 1
    if length > 12:
        votes = votes + 1
    return votes
