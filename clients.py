# -*- coding: utf-8 -*-

from __future__ import unicode_literals, division, print_function

import logging

import pymongo

# connection = pymongo.MongoClient(os.environ['MONGODB_URI'])
# db = connection["heroku_r261ww1k"]

connection = pymongo.MongoClient()
db = connection["clients"]

if "clients" not in db.collection_names() or db.clients.count() == 0:
    db.clients.insert({"username": "", "name": "", "surname": ""})


def log_client(bot, update):
    client = {"username": update.message.chat.username}
    client_db = db.clients.find_one({"username": client["username"]})
    logging.critical(client_db)
    if client_db is None:
        if update.message.chat.first_name:
            client["name"] = update.message.chat.first_name
        if update.message.chat.last_name:
            client["surname"] = update.message.chat.last_name
        db.clients.insert(client)


def main():
    pass


if __name__ == '__main__':
    main()
