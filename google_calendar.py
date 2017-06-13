# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function

import datetime
import json
import os

import pymongo
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client.service_account import ServiceAccountCredentials


def setup_cal():
    # Set up variables for connection to Google Calendar API

    scope_list = list()
    scope_list.append(os.environ['SCOPES'])
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(os.environ['GOOGLE_CREDENTIALS']),
                                                                   scope_list)

    # Set up http connection with API

    http_auth = credentials.authorize(Http())
    service = build(serviceName='calendar', version='v3', http=http_auth, cache_discovery=False)

    return service


def dump_calendar(calendar, num):

    """
    Dump events from Google Calendar
    :param calendar: Google Calendar ID
    :param num: number of events to request from Google Calendar
    :return: list of dicts with events
    """

    # Request events

    service = setup_cal()

    now = datetime.datetime.utcnow().isoformat() + '+03:00'
    eventsResult = service.events().list(calendarId=calendar, timeMin=now, maxResults=num,
                                         singleEvents=True, orderBy='startTime').execute()
    events = eventsResult.get('items', [])

    google_events = []
    if events:
        for event in events:
            google_event = service.events().get(calendarId=calendar, eventId=event["id"]).execute()
            google_events.append(google_event)

    return google_events


def dump_calendar_event(calendar, event):
    """
    Get info about specific calendar event from Google Calndar API
    :param calendar: Google Calendar ID
    :param event: event from MongoDB
    :return: 
    """

    service = setup_cal()
    cal_event = service.events().get(calendarId=calendar, eventId=event["id"]).execute()

    return cal_event


def dump_mongodb(name, events):
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
        db[name].update({"id": event["id"]}, {"$set": {"id": event["id"],
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

    # Remove useless events

    for event_db in db[name].find({}):
        exists = False
        for event in events:
            if event_db["id"] == event["id"]:
                exists = True
        if not exists:
            db[name].delete_one({"id": event_db["id"]})

    connection.close()


def get_events(name, num):
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
    events = db[name].find_one({'start.dateTime': {
        '$gt': (datetime.datetime.utcnow() + datetime.timedelta(hours=3)).isoformat()[:19] + '+03:00'}},
        limit=num).sort("start", pymongo.ASCENDING)
    print("get_events:", events)
    for event in events:
        print("get_events:", event)
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


# https://www.googleapis.com/calendar/v3/calendars/kaf5qkq0jeas32k56fop5k0ci0%40group.calendar.google.com/events?maxResults=5&orderBy=startTime&singleEvents=true&key={YOUR_API_KEY}
# DOC: https://developers.google.com/api-client-library/python/auth/service-accounts
# DOC: https://developers.google.com/resources/api-libraries/documentation/calendar/v3/python/latest/index.html
# DOC: http://pythonhosted.org/python-telegram-bot/
# DOC = "https://python-telegram-bot.readthedocs.io"
# https://maps.googleapis.com/maps/api/geocode/json?address=CrossfitDozen&key=AIzaSyDY9JokHXZsH5yanc-lWUsiexVtuCls27k
