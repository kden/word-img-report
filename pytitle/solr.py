"""
Solr escaping:
https://dzone.com/articles/escaping-solr-query-characters
Author Doug Turnbull
"""

escape_rules ={'+': r'\+', '-': r'\-', '&': r'\&', '|': r'\|', '!': r'\!', '(': r'\(', ')': r'\)', '{': r'\{', '}': r'\}', '[': r'\[', ']': r'\]', '^': r'\^', '~': r'\~', '*': r'\*', '?': r'\?', ':': r'\:', '"': r'\"', ';': r'\;', ' ': r'\ '}


def escaped_sequence(term):
    """ Yield the next string based on the next character (either this char or escaped version """
    for char in term:
        if char in escape_rules.keys():
            yield escape_rules[char]
        else:
            yield char


def escape_solr_arg(term):
    """ Apply escaping to the passed in query terms escaping special characters like : , etc """
    term = term.replace('\\',r'\\') # escape \ first
    return "".join([nextStr for nextStr in escaped_sequence(term)])
