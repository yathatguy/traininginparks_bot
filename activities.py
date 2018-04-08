# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function

import json
import logging
import os

import pymongo
import telegram


def create_list():
    connection = pymongo.MongoClient(os.environ['MONGODB_URI'])
    db = connection["heroku_r261ww1k"]
    db["activities"].remove()

    for name in ["trains", "events"]:
        activity_list = list()
        for event_db in db[name].find({}):
            if event_db["type"]:
                for activity in event_db["type"]:
                    if activity not in activity_list:
                        activity_list.append(activity)
        db["activities"].update({"db": name}, {"$set": {"db": name, "activities": activity_list}}, upsert=True)
    connection.close()


def keyboard(db_name):
    connection = pymongo.MongoClient(os.environ['MONGODB_URI'])
    db = connection["heroku_r261ww1k"]
    kb = []
    for item in db["activities"].find({"db": db_name}):
        for activity in item["activities"]:
            if db_name == "trains":
                button = telegram.InlineKeyboardButton(text=activity, callback_data="701;" + activity)
            elif db_name == "events":
                button = telegram.InlineKeyboardButton(text=activity, callback_data="702;" + activity)
            else:
                logging.critical("Incorrect DB seceltion.")
            kb.append([button])
    kb_markup = telegram.InlineKeyboardMarkup(kb)
    connection.close()
    return kb_markup
