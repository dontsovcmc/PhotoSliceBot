# -*- coding: utf-8 -*-

'''Using Webhook and self-signed certificate'''

# This file is an annotated example of a webhook based bot for
# telegram. It does not do anything useful, other than provide a quick
# template for whipping up a testbot. Basically, fill in the CONFIG
# section and run it.
# Dependencies (use pip to install them):
# - python-telegram-bot: https://github.com/leandrotoledo/python-telegram-bot
# - Flask              : http://flask.pocoo.org/
# Self-signed SSL certificate (make sure 'Common Name' matches your FQDN):
# $ openssl req -new -x509 -nodes -newkey rsa:1024 -keyout server.key -out server.crt -days 3650
# You can test SSL handshake running this script and trying to connect using wget:
# $ wget -O /dev/null https://$HOST:$PORT/

import os
import sys
import argparse
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from storage import db

from bot import start_handler, split_handler, move_handler, photo_handler, switch_handler
from logger import log
from report import report

from crawler import post_job

# CONFIG
TOKEN = os.environ['BOT_TOKEN'] if 'BOT_TOKEN' in os.environ else sys.argv[1]

CERT = 'server.crt'
CERT_KEY = 'server.key'


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='PhotoSliceBot')
    parser.add_argument('key')
    parser.add_argument('-i', '--host', default='', help='Webhook mode. Write your IP address')
    parser.add_argument('-p', '--port', type=int, default=8443, help='Webhook port. 443, 80, 88 or 8443')
    parser.add_argument('-t', '--track', default=None, help='Google TRACK_ID')
    parser.add_argument('-u', '--auth', default=None, help='Instagram username:password')
    parser.add_argument('-a', '--admin_id', type=int, default=1234, help='admin user id')

    args = parser.parse_args()

    log.info("BOT:\ntoken: %s\nhost: %s\nport: %d" % (TOKEN, args.host, args.port))

    updater = Updater(token=TOKEN)

    updater.dispatcher.add_handler(CommandHandler('start', start_handler))
    updater.dispatcher.add_handler(CommandHandler('mode', switch_handler))
    updater.dispatcher.add_handler(MessageHandler(Filters.document, split_handler))
    updater.dispatcher.add_handler(MessageHandler(Filters.photo, photo_handler))
    updater.dispatcher.add_handler(CallbackQueryHandler(move_handler))

    if args.auth:
        log.info('Post to Instagram turn on')
        updater.job_queue.run_repeating(post_job, 0, context=args.auth)


        def check_handler(bot, update, job_queue):
            from crawler import post_once
            if update.message.from_user.id == args.admin_id:
                job_queue.run_once(post_once, 0, context=args.auth)
                update.message.reply_text('Обновляем')

        updater.dispatcher.add_handler(CommandHandler('check', check_handler, pass_job_queue=True))

    else:
        log.warning('Post to Instagram OFF (no auth)')

    if args.track:
        report.TRACK_ID = args.track

    if args.host:
        updater.start_webhook(listen=args.host,
                              port=args.port,
                              url_path=TOKEN,
                              key=CERT_KEY,
                              cert=CERT,
                              webhook_url='https://%s:8443/%s' % (args.host, TOKEN))

        #updater.bot.set_webhook(url='https://%s:8443/%s/' % (args.host, TOKEN))
        #                                certificate=open(CERT, 'rb'))
        log.info('webhook started')

    else:
        updater.start_polling()
        log.info('start polling')

    updater.idle()
    db.close()

    log.info("correct exit")
