#!/usr/bin/env python

from glob import iglob
import xlrd
import xlsxwriter

BASE_DIR =  './manual_review'
print('dir ' + BASE_DIR)

out_path = BASE_DIR + '/manual-histogram.xlsx'
with xlsxwriter.Workbook(out_path) as out_book:
    out_sheet = out_book.add_worksheet()

    headers = ['ocr_conf', 'math_conf', 'truth', 'filename']
    col = 0
    for header in headers:
        out_sheet.write(0, col, header)
        col += 1
    row = 1
    for xlpath in iglob(BASE_DIR + '/*.xlsx'):
        print("xlpath: " + xlpath)
        with xlrd.open_workbook(xlpath) as workbook:
            worksheet = workbook.sheet_by_index(0)
            for i in range(0, worksheet.nrows):
                truth = str(worksheet.cell_value(i,5)).strip().upper()
                if truth in ['T','F'] :
                    result = [worksheet.cell_value(i,3), worksheet.cell_value(i,4), truth, xlpath]
                    print(str(result))
                    for col, data in enumerate(result):
                        out_sheet.write(row, col, data)
                    row += 1


