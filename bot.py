# -*- coding: utf-8 -*-

import tempfile
import os
from emoji import emojize

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import ParseMode

from storage import db
from slice import slice_9, slice_pano, MOVE_CENTER, MOVE_DOWN, MOVE_UP, MOVE_UP_UP, MOVE_DOWN_DOWN
from logger import log
from report import report

MODE_PANO = '0'
MODE_9 = '1'


def photo_handler(bot, update):
    if len(update.message.photo):
        update.message.reply_text('Check \"send file\" not \"photo\" to better quality\n'
                                  'Выберите \"отослать файл\", а не фотографию, чтобы не ухудшилось качество')
        report.track_screen(update.message.from_user.id, 'check_file_not_photo_message')


MOVE_UP_UP_EMOJI = emojize(':arrow_double_up:', use_aliases=True)
MOVE_UP_EMOJI = emojize(':arrow_up_small:', use_aliases=True)
MOVE_CENTER_EMOJI = emojize(':o2:', use_aliases=True)
MOVE_DOWN_EMOJI = emojize(':arrow_down_small:', use_aliases=True)
MOVE_DOWN_DOWN_EMOJI = emojize(':arrow_double_down:', use_aliases=True)
SIGH_EMOJI = emojize(':small_blue_diamond:', use_aliases=True)

def move_reply(mode, move):

    def sign(state, move):
        return SIGH_EMOJI if move == state else ''

    def inline_button(state, move, name):
        return InlineKeyboardButton(sign(state, move) + name + sign(state, move),
                                    parse_mode=ParseMode.MARKDOWN,
                                    callback_data=state)

    if mode == MODE_9:
        return InlineKeyboardMarkup([])
    else:
        return InlineKeyboardMarkup(
                [[inline_button(MOVE_UP_UP, move, MOVE_UP_UP_EMOJI),
                  inline_button(MOVE_UP, move, MOVE_UP_EMOJI),
                  inline_button(MOVE_CENTER, move, MOVE_CENTER_EMOJI),
                  inline_button(MOVE_DOWN, move, MOVE_DOWN_EMOJI),
                  inline_button(MOVE_DOWN_DOWN, move, MOVE_DOWN_DOWN_EMOJI)]])


def send_photo_parts(bot, chat_id, user_id, image_path, image_title):

    move = db.get(chat_id, 'move', MOVE_CENTER)
    mode = db.get(chat_id, 'mode', MODE_PANO)
    if mode == MODE_9:
        report.track_screen(user_id, 'nine_piece')
        pieces = slice_9(image_path, image_title)
    else:
        report.track_screen(user_id, 'panorama')
        pieces = slice_pano(image_path, image_title, move)
        report.track_event(user_id, 'panorama pieces', str(len(pieces)))

    try:
        if pieces:
            for piece in pieces:
                try:
                    with open(piece, 'rb') as f:
                        caption = 'Part №{0} of {1}'.format(pieces.index(piece) + 1, image_title)
                        bot.send_document(chat_id, document=f, caption=caption)
                except Exception, err:
                    report.track_screen(user_id, 'panorama/send_piece_exception')
                    log.error('send_piece_exception: {}'.format(err))

            db.set(chat_id, 'image_path', image_path)
            db.set(chat_id, 'image_title', image_title)

    finally:
        for p in pieces:
            os.unlink(p)


def split_handler(bot, update):

    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    image_title = update.message.document.file_name
    image_title = ''.join(image_title.split('.')[:-1]).encode('utf-8')
    image_file = bot.get_file(update.message.document.file_id)

    try:
        move = db.get(chat_id, 'move', MOVE_CENTER)

        image_path = tempfile.mktemp()
        with open(image_path, 'wb') as f:
            image_file.download(out=f)

        send_photo_parts(bot, chat_id, user_id, image_path, image_title)

    except Exception, err:
        log.error('slice9_handler error: {}'.format(err))
        update.message.reply_text('Error: {}'.format(err))
        report.track_screen(user_id, 'panorama/slice9_handler')

    mode = db.get(chat_id, 'mode', MODE_PANO)
    update.message.reply_text('Thanks!',
                              reply_markup=move_reply(mode, move),
                              parse_mode=ParseMode.MARKDOWN)


def move_handler(bot, update):
    query = update.callback_query
    chat_id = query.message.chat_id
    user_id = query.message.from_user.id

    move = query.data
    report.track_screen(query.message.from_user.id, 'move_' + move)
    db.set(chat_id, 'move', move)

    image_path = db.get(chat_id, 'image_path')
    image_title = db.get(chat_id, 'image_title')

    mode = db.get(chat_id, 'mode', MODE_PANO)
    if image_path and os.path.exists(image_path):
        send_photo_parts(bot, chat_id, user_id, image_path, image_title)

        text = 'You can move pieces row up or down:' \
               '\n---\nВы можете передвинуть ряд фото выше или ниже:'
        bot.edit_message_text(text=text,
                              parse_mode=ParseMode.MARKDOWN,
                              chat_id=chat_id,
                              message_id=query.message.message_id)

        bot.send_message(text=text,
                              parse_mode=ParseMode.MARKDOWN,
                              chat_id=chat_id,
                              message_id=query.message.message_id,
                              reply_markup=move_reply(mode, move))
    else:
        bot.send_message(text='Please, upload a photo',
                              parse_mode=ParseMode.MARKDOWN,
                              chat_id=chat_id,
                              message_id=query.message.message_id)


def switch_handler(bot, update):

    chat_id = update.message.chat_id

    mode = db.get(chat_id, 'mode')
    mode = MODE_9 if mode == MODE_PANO else MODE_PANO

    db.set(chat_id, 'mode', mode)
    text = 'Текущий режим: '
    text += 'Панорама' if mode == MODE_PANO else ' 9 фото'

    update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


def start_handler(bot, update):

    report.track_screen(update.message.from_user.id, 'start')

    text = 'Hello!\n' \
           'Send me a picture as a file, I split it into parts for Instagram. ' \
           'I make 3 parts for 2x3 photo, >3 for panoramic photo.\n-----\n' \
           'Привет!\n' \
           'Пришли мне фотографию и я разделю ее на части для Инстаграмма. ' \
           'Я сделаю 3 части из обычного фото 2х3 и больше 3-х для панорамной фотографии\n'

    update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


if __name__ == '__main__':
    pass

