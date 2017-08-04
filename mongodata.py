# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function

import datetime
import os

import pymongo


def get_events(name):
    """
    Get list of dicts with events from Mongo DB
    :param num: number of event to request and possible return 
    :return: list of dicts with events
    """

    # Set up connection with Mongo DB

    connection = pymongo.MongoClient(os.environ['MONGODB_URI'])
    db = connection["heroku_r261ww1k"]

    # Get events

    events_list = list()

    events = db[name].find({'start.dateTime': {
        '$gt': (datetime.datetime.utcnow() + datetime.timedelta(hours=3)).isoformat()[:19] + '+03:00'}}).sort("start",
                                                                                                              pymongo.ASCENDING)
    for event in events:
        events_list.append(event)

    return events_list


def main():
    """
    Main function
    :return: N/A
    """

    pass


if __name__ == '__main__':
    main()
