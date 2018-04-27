# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function

import json
import logging
import os

import pymongo
import telegram


def keyboard(db_name):
    connection = pymongo.MongoClient(os.environ['MONGODB_URI'])
    db = connection["heroku_20w2cn6z"]
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


def main():
    pass


if __name__ == '__main__':
    main()
