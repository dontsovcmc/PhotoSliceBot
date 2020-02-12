# -*- coding: utf-8 -*-
__author__ = 'dontsov'

import os
from PIL import Image
import exifread
import tempfile
from logger import log

tempdir = tempfile.gettempdir()

MOVE_UP_UP = 'upup'
MOVE_UP = 'up'
MOVE_CENTER = 'center'
MOVE_DOWN = 'down'
MOVE_DOWN_DOWN = 'downdown'

def make_square(img):
    """
    Делаем фотографию квадратной
    """
    width, height = img.size
    if width == height:
        return img
    elif width > height:
        j = (width - height) / 2
        box = (j, 0, width - j, height)
    else:
        i = (height - width) / 2
        box = (0, i, width, height - i)
    return img.crop(box)


def piece_dim(width, height):
    """
    Получаем размер куска панорамы
    """
    num = width / height
    if num <= 3:
        piece = width / 3
    else:
        end = width - (height * num)
        if end > height / 4:
            num += 1

        piece = width / num

    if piece > height:
        piece = height

    return piece


def slice_pano(path, image_name, move):
    """
    Разрезаем картинку на горизонтальную панораму
    """
    img = Image.open(path)
    width, height = img.size

    piece = piece_dim(width, height)

    if move == MOVE_UP_UP:
        y0 = 0
    elif move == MOVE_UP:
        y0 = (height - piece)/4
    elif move == MOVE_CENTER:
        y0 = (height - piece)/2
    elif move == MOVE_DOWN:
        y0 = (height - piece)*3/4
    elif move == MOVE_DOWN_DOWN:
        y0 = height - piece

    id = 1
    pieces = []
    for j in range(0, width - width % piece, piece):
        box = (j, y0, j + piece, piece + y0)

        piece_path = os.path.join(tempdir, image_name + "-" + str(id) + '.JPG')
        img = img.convert("RGB")  #  error if png
        img.crop(box).save(piece_path, 'JPEG', quality=75)
        pieces.append(piece_path)
        id += 1

    return pieces


def slice_9(path, image_name):
    """
    Разрезаем картинку на 9 частей. В EXIF смотрим, нужно ли перевернуть фото.
    """
    with open(path, 'r') as f:
        tags = exifread.process_file(f)

    img = Image.open(path)

    if 'Image Orientation' in tags.keys():
        direction = tags['Image Orientation'].values[0]
        if direction == 3:  # из описания EXIF
            img = img.transpose(Image.ROTATE_180)
        if direction == 6:
            img = img.transpose(Image.ROTATE_270)  # (Image.ROTATE_90)
        elif direction == 8:
            img = img.transpose(Image.ROTATE_90)

    img = make_square(img)

    width, height = img.size

    piece_h = height / 3
    piece_w = width / 3
    height -= height % 3
    width -= width % 3

    pieces = []
    id = 1
    for i in range(0, height, piece_h):
        for j in range(0, width, piece_w):
            box = (j, i, j + piece_w, i + piece_h)

            piece_path = os.path.join(tempdir, image_name + "-" + str(id) + '.JPG')
            img = img.convert("RGB")  #  error if png
            img.crop(box).save(piece_path, 'JPEG', quality=75)
            pieces.append(piece_path)
            id += 1

    return pieces