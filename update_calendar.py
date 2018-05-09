# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function

import os
import logging
from google_calendar import dump_calendar, dump_mongodb


def main():
    # Dump events from Google Calendar and update MongoDB

    train_calendar = os.environ['TRAIN_CALENDAR_ID']
    trains = dump_calendar(train_calendar, 10)
    dump_mongodb("trains", trains)

    # Dump events from Google Calendar and update MongoDB

    events_calendar = os.environ['EVENTS_CALENDAR_ID']
    events = dump_calendar(events_calendar, 50)
    dump_mongodb("events", events)


if __name__ == '__main__':
    main()
