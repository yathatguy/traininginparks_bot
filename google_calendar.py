# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function

import datetime
import json
import os

import pymongo
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client.service_account import ServiceAccountCredentials


def dump_calendar(num):
    """
    Dump events from Google Calendar
    :param num: number of events to request from Google Calendar
    :return: list of dicts with events
    """

    # Set up variables for connection to Google Calendar API
    scope_list = []
    scope_list.append(os.environ['SCOPES'])
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(os.environ['GOOGLE_CREDENTIALS']),
                                                                   scope_list)

    # Set up http connection with API
    http_auth = credentials.authorize(Http())
    service = build(serviceName='calendar', version='v3', http=http_auth, cache_discovery=False)
    now = datetime.datetime.utcnow().isoformat() + '+03:00'

    # Request events
    eventsResult = service.events().list(calendarId=os.environ['CALENDAR_ID'], timeMin=now, maxResults=10,
                                         singleEvents=True, orderBy='startTime').execute()
    events = eventsResult.get('items', [])
    google_events = []
    if events:
        for event in events:
            google_event = service.events().get(calendarId=os.environ['CALENDAR_ID'], eventId=event["id"]).execute()
            google_events.append(google_event)
    return google_events


# TODO: разнести обновение календаря и базы в разные вызовы.


def dump_mongodb(events):
    """
    Get list of dicts with events and update Mongo DB with actual information
    :param events: list of dicts with events
    :return: N/A
    """

    # Set up connection with Mongo DB
    connection = pymongo.MongoClient(os.environ['MONGODB_URI'])
    db = connection["heroku_r261ww1k"]

    # Insert or update events in Mongo DB
    for event in events:
        db.events.update({"id": event["id"]}, {"$set": {"id": event["id"],
                                                        "status": event["status"],
                                                        "kind": event["kind"],
                                                        "end": event["end"],
                                                        "created": event["created"],
                                                        "iCalUID": event["iCalUID"],
                                                        "reminders": event["reminders"],
                                                        "htmlLink": event["htmlLink"],
                                                        "sequence": event["sequence"],
                                                        "updated": event["updated"],
                                                        "summary": event["summary"],
                                                        "start": event["start"],
                                                        "etag": event["etag"],
                                                        "organizer": event["organizer"],
                                                        "creator": event["creator"]
                                                        }}, upsert=True)
    connection.close()


def get_events(num):
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
    events = db.events.find({'start.dateTime': {
        '$gt': (datetime.datetime.utcnow() + datetime.timedelta(hours=3)).isoformat()[:19] + '+03:00'}},
        limit=num).sort("start", pymongo.ASCENDING)
    for event in events:
        events_list.append(event)
    return events_list


def main():
    pass


if __name__ == '__main__':
    main()


# https://www.googleapis.com/calendar/v3/calendars/kaf5qkq0jeas32k56fop5k0ci0%40group.calendar.google.com/events?maxResults=5&orderBy=startTime&singleEvents=true&key={YOUR_API_KEY}
# DOC: https://developers.google.com/api-client-library/python/auth/service-accounts
# DOC: https://developers.google.com/resources/api-libraries/documentation/calendar/v3/python/latest/index.html
