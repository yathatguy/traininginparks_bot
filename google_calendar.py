# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function

import datetime
import json
import os
import random
import time
import logging

import pymongo
from apiclient import errors
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client.service_account import ServiceAccountCredentials


def setup_cal():
    """
    Set up variables for connection to Google Calendar API 
    :return: service - connection to Google Calendar API 
    """

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
            for n in range(0, 5):
                try:
                    google_event = service.events().get(calendarId=calendar, eventId=event["id"]).execute()
                    google_events.append(google_event)
                except errors.HttpError, error:
                    if error.resp.reason in ['userRateLimitExceeded', 'quotaExceeded', 'internalServerError',
                                             'backendError']:
                        time.sleep((2 ** n) + random.random())
                    else:
                        break
                    print("There has been an error, the request never succeeded.")

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


def parse_activities(text):
    if text == "":
        return None
    if text[0] == "[":
        activities_raw = str()
        for char in text[1:]:
            if char != "]":
                activities_raw += char
            else:
                activities_list = activities_raw.split(",")
                activities = list()
                for activity in activities_list:
                    activities.append(activity.strip(" "))
                return activities
    else:
        return ["Без категории"]

def dump_mongodb(name, events):
    """
    Get list of dicts with events and update Mongo DB with actual information
    :param name: Name for MongoDB collection
    :param events: list of dicts with events
    :return: N/A
    """

    # Set up connection with Mongo DB

    connection = pymongo.MongoClient(os.environ['MONGODB_URI'])
    db = connection["heroku_20w2cn6z"]

    # Insert or update events in Mongo DB

    for event in events:

        # Enriching with 'date' and 'dateTime' for 'start' key

        if "date" in event["start"].keys():
            event["start"]["dateTime"] = event["start"]["date"] + "T00:00:00+03:00"
        else:
            event["start"]["date"] = event["start"]["dateTime"].split("T")[0]

        # Get event type

        event["type"] = parse_activities(event["summary"])

        # Update MongoDB

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
                                                       "type": event["type"],
                                                       "organizer": event["organizer"],
                                                       "creator": event["creator"]
                                                       }}, upsert=True)

    # Remove useless events

    for event_db in db[name].find({}):

        # Remove removed events

        exists = False
        for event in events:
            if event_db["id"] == event["id"]:
                exists = True
        if not exists:
            db[name].delete_one({"id": event_db["id"]})

    connection.close()


def main():
    """
    Main function
    :return: N/A
    """

    pass


if __name__ == '__main__':
    main()


# DOC: https://developers.google.com/api-client-library/python/auth/service-accounts
# DOC: https://developers.google.com/resources/api-libraries/documentation/calendar/v3/python/latest/index.html
# DOC: http://pythonhosted.org/python-telegram-bot/
# DOC = "https://python-telegram-bot.readthedocs.io"
# https://maps.googleapis.com/maps/api/geocode/json?address=CrossfitDozen&key=AIzaSyDY9JokHXZsH5yanc-lWUsiexVtuCls27k