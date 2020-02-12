# -*- coding: utf-8 -*-
__author__ = 'dontsov'


import os
import sys
from UniversalAnalytics import Tracker

APP_VERSION = '0.1'
APP_NAME = 'PhotoSliceBot'


class RTracker(object):
    def __init__(self, track_id, client_id):
        self.client_id = client_id
        self.name = APP_NAME
        self.tracker = Tracker.create(track_id, client_id=client_id)

    def track_event(self, category, action):
        self.tracker.send('event', category, action)

    def track_path(self, path, title):
        self.tracker.send('pageview', path=path, title=title)

    def track_screen(self, screenName):
        self.tracker.send('screenview', appName=self.name, screenName=screenName, appVersion=APP_VERSION)


class ReportTrackers(object):

    def __init__(self):
        self.TRACK_ID = ''
        self.trackers = {}

    def add_tracker(self, client_id):
        self.trackers[str(client_id)] = RTracker(self.TRACK_ID, client_id)

    def remove_tracker(self, client_id):
        if str(client_id) in self.trackers:
            del self.trackers[str(client_id)]

    def track_event(self, client_id, category, action):
        if not self.TRACK_ID:
            return
        if not str(client_id) in self.trackers: self.add_tracker(client_id)

        self.trackers[str(client_id)].track_event(category, action)

    def track_path(self, client_id, path, title):
        if not self.TRACK_ID:
            return
        if not str(client_id) in self.trackers: self.add_tracker(client_id)

        self.trackers[str(client_id)].track_path(path, title)

    def track_screen(self, client_id, screenName):
        if not self.TRACK_ID:
            return
        if not str(client_id) in self.trackers: self.add_tracker(client_id)

        self.trackers[str(client_id)].track_screen(screenName)

report = ReportTrackers()
