import shutil
from PIL import Image


def insert_img(row, basename, img_src, worksheet):
    try:
        img_path = basename + "/" + img_src
        tmp_img_path = basename + "/temp-" + img_src
        with Image.open(img_path) as img:
            width, height = img.size
            img.save(tmp_img_path, dpi=(96, 96))
        shutil.move(tmp_img_path, img_path)
        if height > 200:
            scale = round(200.0 / height, 2)
        else:
            scale = 1
        print('Scale: ' + str(scale) + ' ' + str(width) + ' ' + str(height) + ' ' + img_src)
        worksheet.set_row(row, 160)
        worksheet.insert_image(row, 0, img_path, {'x_scale': scale, 'y_scale': scale})
    except OSError as err:
        print("OS error: {0}".format(err))
