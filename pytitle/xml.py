import re
from glob import iglob

IMG_PATTERN = re.compile(r'<img([^>]*)>', re.MULTILINE)
ATTR_PATTERN = re.compile(r'([A-Za-z\-\_]+)=[\'"]((\\\'|\\""|[^\'"])*)[\'"]', re.MULTILINE)
ID_PATTERN_STRING = r'<dc:Identifier[^>]*>([0-9][^<]+)<'
ID_PATTERN = re.compile(ID_PATTERN_STRING)
TITLE_PATTERN_STRING = r'<dc:Title[^>]*>([^<]*)<'
TITLE_PATTERN = re.compile(TITLE_PATTERN_STRING)


def get_attrs(string_to_parse):
    att_map = {}
    for attr_match in ATTR_PATTERN.finditer(string_to_parse):
        attr_name = attr_match.group(1)
        attr_value = attr_match.group(2)
        att_map[attr_name] = attr_value[0:4096]
    return att_map


def get_title_from_opf(basename):
    title = 'notitle'
    isbn = 'noisbn'
    for opfpath in iglob(basename + '/*.opf'):
        print(opfpath + '\n')
        # Get DAISY file metadata
        with open(opfpath, 'r') as file:
            file_data = file.read()
            identifiers = re.findall(ID_PATTERN, file_data)
            for identifier in identifiers:
                print(identifier + '\n')
                isbn = identifier
            titles = re.findall(TITLE_PATTERN, file_data)
            title = titles[0]
            print(title + '\n')
    return (title, isbn)