# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function

import pymongo
import os


def create_list():
    connection = pymongo.MongoClient(os.environ['MONGODB_URI'])
    db = connection["heroku_20w2cn6z"]
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
    return True


def main():
    create_list()


if __name__ == '__main__':
    main()
