"""
Given a list of book_ids for titles that contain images that don't fall into a well-defined
image group, try to cluster the alt text of the images for that title.
Repeated patterns are used for non-meaningful subtext (p01a, p01b, p02a, or eqn1233,e qn8323f).
Maybe this can help us find patterns that can be substituted with new alt text.
Work in progress: This doesn't work well right now.
"""

import distance
import numpy as np
import psycopg2
from psycopg2.extras import DictCursor
from sklearn.cluster import AffinityPropagation

from pytitle.data import histogram_hash, weight_strings_by_prefix
from pytitle.fileutil import get_rows_from_file


CANDIDATE_TITLE_FILE = 'no_group_titles.csv'

title_list = get_rows_from_file(CANDIDATE_TITLE_FILE)
# Remove header row
title_list.pop(0)
title_shortlist = [title for title in title_list if 1300 < int(title[0]) < 1500]
print('Number of titles in short list: ' + str(len(title_shortlist)))

con = psycopg2.connect(database="warehouse", user="bookshare", password="", host="127.0.0.1", port="5432",
                       cursor_factory=DictCursor)

print("Database opened successfully")

book_cursor = con.cursor()
con.rollback()


row_count = 0
for book_row in title_shortlist:
    book_id = book_row[1]
    print("book_id: " + str(book_id))
    img_cursor = con.cursor()
    img_cursor.execute("select img_id, left(lowercase, 30) as lowercase, length(alt) as len_alt, left(alt, 30) as alt, "
                       + "alt_text_group, title_instance_id, source_format, title_source, title, publisher, "
                       + "copyright_year, isbn from img where alt_text_group ='no group' and book_id=%s", [book_id])

    if img_cursor.rowcount > 20:
        img_rows = img_cursor.fetchall()
        img_list = [sublist['alt'][:20] for sublist in img_rows]
        img_hash = histogram_hash(img_list)
        for w in sorted(img_hash, key=img_hash.get, reverse=True)[:10]:
            print(str(img_hash[w]) + ': ' + w)

        print("Values, unique values: " + str(len(img_list)) + ', ' + str(len(img_hash.keys())))
        alt_texts = np.asarray(list(img_hash.keys()))
        print("Alt texts:")
        print(alt_texts)
        preferences = weight_strings_by_prefix(alt_texts)
        print("Preferences")
        print(preferences)
        print("Computing Levenshtein distance")
        lev_similarity = -1 * np.array([[distance.levenshtein(alt1, alt2) for alt1 in alt_texts] for alt2 in alt_texts])
        print(lev_similarity)

        print("Computing Affinity Propagation")

        affprop = AffinityPropagation(affinity="precomputed", damping=0.5, preference=preferences)
        affprop.fit(lev_similarity)
        for cluster_id in np.unique(affprop.labels_):
            exemplar = alt_texts[affprop.cluster_centers_indices_[cluster_id]]
            print("Building cluster for " + exemplar)
            cluster = np.unique(alt_texts[np.nonzero(affprop.labels_ == cluster_id)])
            cluster_str = ", ".join(cluster)
            print(" - *%s:* %s" % (exemplar, cluster_str))
        break
        row_count += 1




