# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function
from oauth2client.service_account import ServiceAccountCredentials
from httplib2 import Http
from googleapiclient.discovery import build
import datetime
import os
import pymongo
import json


def get_events(num):
    scope_list = []
    scope_list.append(os.environ['SCOPES'])
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(os.environ['GOOGLE_CREDENTIALS']), scope_list)
    http_auth = credentials.authorize(Http())
    service = build(serviceName='calendar', version='v3', http=http_auth)
    now = datetime.datetime.utcnow().isoformat() + '+03:00'
    eventsResult = service.events().list(calendarId=os.environ['CALENDAR_ID'], timeMin=now, maxResults=10, singleEvents=True, orderBy='startTime').execute()
    events = eventsResult.get('items', [])
    google_events = []
    if events:
        for event in events:
            google_event = service.events().get(calendarId=os.environ['CALENDAR_ID'], eventId=event["id"]).execute()
            google_events.append(google_event)
            dump_mongo(google_event)
    return google_events

# TODO: разнести обновение календаря и базы в разные вызовы.


def dump_mongo(event):
    connection = pymongo.MongoClient(os.environ['MONGODB_URI'])
    db = connection["heroku_r261ww1k"]
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
                                                    "creator": event["creator"],
                                                    "attendee": ''
                                                    }}, upsert=True)
    connection.close()


def main():
    pass


if __name__ == '__main__':
    main()


# https://www.googleapis.com/calendar/v3/calendars/kaf5qkq0jeas32k56fop5k0ci0%40group.calendar.google.com/events?maxResults=5&orderBy=startTime&singleEvents=true&key={YOUR_API_KEY}
# DOC: https://developers.google.com/api-client-library/python/auth/service-accounts
# DOC: https://developers.google.com/resources/api-libraries/documentation/calendar/v3/python/latest/index.html



