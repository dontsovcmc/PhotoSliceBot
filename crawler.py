# -*- coding: utf-8 -*-

import urllib
import os
import tempfile
import time
import requests
from random import randint
from datetime import datetime, timedelta

from InstagramAPI import InstagramAPI
import instagram_explore as ie
from instagram_explore import InstagramExploreResponse

from logger import log
from report import report

BOT_ID = u'6113630349'  # чтобы не постить свои же кадры


class Post(object):
    def __init__(self, **kwargs):
        self.caption = kwargs.get('caption')
        self.username = kwargs.get('username')
        self.location = kwargs.get('location')
        self.urls = kwargs.get('urls')
        self.date = kwargs.get('date')
        self.code = kwargs.get('code')


def search(timestamp, tag='photoslicebot'):
    '''
    Ищет фотографии по хэштегу
    :param timestamp:
    :param tag:
    :return:
    '''
    posts = []

    url = "https://www.instagram.com/explore/tags/%s/" % tag
    payload = {'__a': '1'}

    res = requests.get(url, params=payload).json()
    edges = res['graphql']['hashtag']['edge_hashtag_to_media']['edges']

    #res = ie.tag(tag)

    codes = []

    for data in edges:
        # тут уже сортированные по дате посты
        data = data['node']
        if data['taken_at_timestamp'] > timestamp:
            if not data['is_video']:
                codes.append(data['shortcode'])
            else:
                log.info('CRAWLER: There is a video {}'.format(data['shortcode']))

    for code in codes:
        image = ie.media(code)
        try:
            if 'edge_media_to_caption' in image.data:
                if 'edges' in image.data['edge_media_to_caption']:
                    if len(image.data['edge_sidecar_to_children']['edges']) > 1:

                        p = Post(username=image.data['owner']['username'],
                                 caption=image.data['edge_media_to_caption']['edges'][0]['node']['text'],
                                 location=image.data['location'],
                                 urls=list(x['node']['display_url'] for x in image.data['edge_sidecar_to_children']['edges']),
                                 date=image.data['taken_at_timestamp'],
                                 code=code)
                        posts.append(p)
            else:
                log.warning('CRAWLER: Post {} isn\'t a panorama'.format(code))

        except Exception, err:
            log.error('CRAWLER: Get post {0} info error {1}'.format(code, err))

    return posts


def download(urls):
    files = []

    try:
        for url in urls:
            name = url.split("/")[-1]
            path = os.path.join(tempfile.gettempdir(), name)
            urllib.urlretrieve(url, path)
            files.append(path)
    except Exception, err:
        # log
        for f in files:
            os.unlink(f)

    return files


def last_post_time():
    data = ie.user("photoslicebot")
    return data.data['media']['nodes'][0]['date']


def post_once(bot, job):
    try:
        username, password = job.context.split(':')

        log.info('CRAWLER: start post')
        t = time.time()
        posts = search(last_post_time())
        posts.reverse()
        log.info('CRAWLER: found {} posts, for {} sec'.format(len(posts), round(time.time() - t, 2)))

        if posts:
            ig = InstagramAPI(username, password)
            ig.login()

            log.info('CRAWLER: login ok')
            for p in posts:

                try:
                    files = download(p.urls)
                    media = list({'type': 'photo', 'file': f} for f in files)

                    caption = u'Panorama from @' + p.username + u'\n' + p.caption
                    caption = caption.replace(u'#photoslicebot', u'')
                    # проверить на длину caption
                    ig.uploadAlbum(media, caption=caption)
                    log.info('CRAWLER: upload {} from user {} successfully'.format(p.code, p.username))
                    report.track_event(0, 'crawler', 'new post')

                except Exception, err:
                    log.error('CRAWLER: download or upload album error: {}'.format(err))
                    report.track_event(0, 'crawler', 'download or upload error')

                finally:
                    for f in files:
                        os.unlink(f)

            ig.logout()
            log.info('CRAWLER: logout ok')

    except Exception, err:
        log.error('CRAWLER: get posts error: {}'.format(err))
        report.track_event(0, 'crawler', 'get posts error')


def post_job(bot, job):

    post_once(bot, job)

    job.interval = randint(3600, 7200)
    t = datetime.now() + timedelta(seconds=job.interval)
    log.info("CRAWLER: next post_job at {0} (after {1} sec)".format(t.strftime('%d.%m.%Y %H.%M'), job.interval))



