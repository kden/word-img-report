"""
Run SQL statements on the img alt text database that classify the images into several groups
"""

import psycopg2

from pytitle.pg import run_update

con = psycopg2.connect(database="warehouse", user="bookshare", password="", host="127.0.0.1", port="5432")

print("Database opened successfully")

cursor = con.cursor()
con.rollback()

row_count = 0

group_update_stmts = [
    "update img set lowercase = lower(left(trim(alt),256)) where lowercase='' and alt <> ''",
    "update img set alt_text_group='placeholders' where alt_text_group is null and lowercase in ('equation', 'image', 'images', 'img', 'inline', 'math', 'jpg', 'alt')",
    "update img set alt_text_group='num placeholder' where alt similar to '[A-Za-z]+ [0-9]+.?'",
    "update img set alt_text_group='filename' where alt_text_group is null and right(lowercase, 4) in('.png','.gif','.jpg','.svg','.tif')",
    "update img set alt_text_group='filename' where alt_text_group is null and right(lowercase, 5) in('.jpeg','.tiff')",
    "update img set alt_text_group='unicode' where alt_text_group is null and left(lowercase,2) = 'u+'",
    "update img set alt_text_group='dollar_sign' where  alt_text_group is null and lowercase like '%$$%'",
    "update img set alt_text_group='dollar_sign' where alt_text_group is null and alt_text_group is null and left(lowercase, 1) ='$'",
    "update img set alt_text_group='math symbol'  where alt similar to '%[∀∁∂∃∄∅∆∇∈∉∊∋∌∍∎∏∐∑−∓∔∕∖∗∘∙√∛∜∝∞∟∠∡∢∣∤∥∦∧∨∩∪∫∬∭∮∯∰∱∲∳∴∵∶∷∸∹∺∻∼∽∾∿≀≁≂≃≄≅≆≇≈≉≊≋≌≍≎≏≐≑≒≓≔≕≖≗≘≙≚≛≜≝≞≟≠≡≢≣≤≥≦≧≨≩≪≫≬≭≮≯≰≱≲≳≴≵≶≷≸≹≺≻≼≽≾≿⊀⊁⊂⊃⊄⊅⊆⊇⊈⊉⊊⊋⊌⊍⊎⊏⊐⊑⊒⊓⊔⊕⊖⊗⊘⊙⊚⊛⊜⊝⊞⊟⊠⊡⊢⊣⊤⊥⊦⊧⊨⊩⊪⊫⊬⊭⊮⊯⊰⊱⊲⊳⊴⊵⊶⊷⊸⊹⊺⊻⊼⊽⊾⊿⋀⋁⋂⋃⋄⋅⋆⋇⋈⋉⋊⋋⋌⋍⋎⋏⋐⋑⋒⋓⋔⋕⋖⋗⋘⋙⋚⋛⋜⋝⋞⋟⋠⋡⋢⋣⋤⋥⋦⋧⋨⋩⋪⋫⋬⋭⋮⋯⋰⋱⋲⋳⋴⋵⋶⋷⋸⋹⋺⋻⋼⋽⋾⋿]%'",
    "update img set alt_text_group='blank' where alt_text_group is null and lowercase is null",
    "update img set alt_text_group='blank' where  alt_text_group is null and lowercase =''",
    "update img set alt_text_group='no group' where alt_text_group is null",
    "update img set alt_text_group='no group' where alt_text_group =''",
]


for stmt in group_update_stmts:
    run_update(con, stmt)

cursor.execute("select count(img_id) as group_count, alt_text_group from img group by alt_text_group")

for row in cursor.fetchall():
    print(str(row[1]) + ": " + str(row[0]))