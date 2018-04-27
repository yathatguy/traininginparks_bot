# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function

import datetime
import json
import os
import logging

import pymongo
from bson import json_util


def get_things(db_name, *args, **kwargs):
    """
    Get list of dicts with events from Mongo DB
    :param num: number of event to request and possible return
    :return: list of dicts with events
    """

    user = kwargs.get("user", None)
    activity = kwargs.get("activities", None)

    # Set up connection with Mongo DB

    connection = pymongo.MongoClient(os.environ['MONGODB_URI'])
    db = connection["heroku_20w2cn6z"]

    # Get events

    things_list = list()
    today = datetime.date.today().isoformat()
    if user:
        things = db[db_name].find({'start.date': {'$gte': today}, 'type': {'$in': [activity]}, 'attendee': {'$in': [user]}}).sort("start.date", pymongo.ASCENDING)
    elif activity:
        things = db[db_name].find({'start.date': {'$gte': today}, 'type': {'$in': [activity]}}).sort("start.date", pymongo.ASCENDING)
    else:
        things = db[db_name].find({'start.date': {'$gte': today}, }).sort("start.date", pymongo.ASCENDING)
    for thing in things:
        things_list.append(thing)
    connection.close()
    return things_list


def get_thing(db_name, id):
    connection = pymongo.MongoClient(os.environ['MONGODB_URI'])
    db = connection["heroku_20w2cn6z"]
    event = db[db_name].find_one({"id": id})
    event = json.loads(json_util.dumps(event))
    connection.close()
    return event


def main():
    """
    Main function
    :return: N/A
    """

    pass


if __name__ == '__main__':
    main()
