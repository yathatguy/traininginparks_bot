# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function

import logging
import os
import time

import pymongo
import telegram
from telegram.contrib.botan import Botan
from telegram.ext import CommandHandler, CallbackQueryHandler
from telegram.ext import Updater

from google_calendar import dump_calendar, dump_mongodb, get_events, dump_calendar_event
from maps_api import get_coordinates

# Set up Updater and Dispatcher

updater = Updater(token=os.environ['TOKEN'])
updater.stop()
dispatcher = updater.dispatcher

# Set up Botan

botan = Botan(os.environ['BOTAN_API_KEY'])

# Add logging

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)


def botan_track(message, update):
    """
    Call Bota API and send info
    :param message: message that was send to User
    :param update: telegram API state 
    :return: N/A
    """

    message_dict = message.to_dict()
    event_name = update.message.text
    botan.track(message_dict, event_name)


def start(bot, update):
    """
    Send welcome message to new users. 
    :return: N/A
    """

    # bot.sendMessage(chat_id=update.message.chat_id, text=os.environ['WELCOMETEXT'])

    botan_track(update.message, update)
    kb = [[telegram.KeyboardButton('/train')],
          [telegram.KeyboardButton('/attendees')],
          [telegram.KeyboardButton('/calendar')]]
    kb_markup = telegram.ReplyKeyboardMarkup(kb, resize_keyboard=True)
    bot.send_message(chat_id=update.message.chat_id,
                     text="Добро пожаловать, атлет!",
                     reply_markup=kb_markup,
                     resize_keyboard=True)


def attendees(bot, update):
    """
    Count number of attendees for each planned event and share with User
    :param bot: telegram API object
    :param update: telegram API state
    :return: N/A
    """

    bot.sendMessage(chat_id=update.message.chat_id,
                    text="Список людей, записавшихся на предстоящие тренировки:")
    events = get_events("trains", 5)
    if events:
        for event in events:
            if "attendee" in event.keys():
                attendees_list = ''
                for attendee in event["attendee"]:
                    attendees_list = attendees_list + ' @' + attendee
                bot.sendMessage(chat_id=update.message.chat_id,
                                text="{}: {} ({}) - {}".format(event["start"]["dateTime"].split("T")[0],
                                                               event["summary"],
                                                               len(event["attendee"]), attendees_list))
            else:
                bot.sendMessage(chat_id=update.message.chat_id,
                                text="{}: {} ({}) - {}".format(event["start"]["dateTime"].split("T")[0],
                                                               event["summary"],
                                                               0, 'пока никто не записался'))
        botan_track(update.message, update)
    else:
        bot.sendMessage(chat_id=update.message.chat_id, text="Нет трениировок, нет и записавшихся")


def reply(bot, update, text):
    """
    Reply to User and calls Botan API
    :param bot: telegram API object
    :param update: telegram API state
    :param text: message that was send to User
    :return: N/A
    """

    # TODO: не найден chat_id
    bot.sendMessage(chat_id=update.message.chat_id, text=text)
    botan_track(update.message, update)


def train(bot, update):
    """
    Get a NUM of upcoming trains and offer to attend any
    :param bot: telegram API object
    :param update: telegram API state
    :return: N/A
    """

    events = get_events("trains", 5)
    if events:
        reply(bot, update, text="Расписание следующих тренировок:")
        botan_track(update.message, update)
        for event in events:
            reply(bot, update,
                  text="{}: {} с {} до {}".format(event["start"]["dateTime"].split("T")[0], event["summary"],
                                                  event["start"]["dateTime"].split("T")[1][:5],
                                                  event["end"]["dateTime"].split("T")[1][:5]))
            botan_track(update.message, update)
        kb_markup = event_keyboard(bot, update, events)
        update.message.reply_text('Давай запишемся на одну из тренировок:', reply_markup=kb_markup)
    else:
        reply(bot, update, text="Пока тренировки не запланированы. Восстанавливаемся!")
        botan_track(update.message, update)


def event_keyboard(bot, update, events):
    """
    Create keyboard markup that can be shown to User
    :param bot: telegram API object
    :param update: telegram API state
    :param events: list of events
    :return: keyboard markup that can be shown to User
    """

    kb = []
    for event in events:
        text = "{}: {}".format(event["summary"], event["start"]["dateTime"].split("T")[0])
        item = telegram.InlineKeyboardButton(text=text, callback_data=event["id"])
        kb.append([item])
    kb_markup = telegram.inlinekeyboardmarkup.InlineKeyboardMarkup(kb)
    return kb_markup


def train_button(bot, update):
    """
    Get a User selected event from call back, add User to attendees list for the event
    and gives User info about selected event (date, time, location)
    :param bot: telegram API object
    :param update: telegram API state
    :return: N/A
    """

    query = update.callback_query
    connection = pymongo.MongoClient(os.environ['MONGODB_URI'])
    db = connection["heroku_r261ww1k"]
    if db.events.find({"id": query.data, "attendee": query.message.chat.username}).count() == 0:
        event = db.events.find_one({"id": query.data})
        db.events.update({"id": query.data}, {"$push": {"attendee": query.message.chat.username}}, upsert=True)
        bot.sendMessage(text="Отлично, записались!", chat_id=query.message.chat_id, message_id=query.message.message_id)
        bot.sendMessage(text="Ждем тебя {} с {} по адресу:".format(event["start"]["dateTime"].split("T")[0],
                                                                   event["start"]["dateTime"].split("T")[1][:5]),
                        chat_id=query.message.chat_id, message_id=query.message.message_id)
        event_loc(bot, query, event)
    else:
        bot.sendMessage(text="Ты уже записан(а) на эту тренировку", chat_id=query.message.chat_id,
                        message_id=query.message.message_id)
    connection.close()


def calendar(bot, update):
    """
    Get upcomgin events and list to User
    :param bot: telegram API object
    :param update: telegram API state
    :return: N/A
    """

    events = get_events("events", 20)
    if events:
        reply(bot, update, text="Список предстоящих событий:")
        botan_track(update.message, update)
        for event in events:
            if "date" in event["end"].keys():
                reply(bot, update,
                      text="{}: {}".format(event["start"]["dateTime"].split("T")[0], event["summary"]))
            else:
                reply(bot, update,
                      text="{}: {} с {} до {}".format(event["start"]["dateTime"].split("T")[0], event["summary"],
                                                      event["start"]["dateTime"].split("T")[1][:5],
                                                      event["end"]["dateTime"].split("T")[1][:5]))
            botan_track(update.message, update)
    else:
        reply(bot, update, text="В календаре пока нет запланированных событий.")
        botan_track(update.message, update)


def event_loc(bot, update, event):
    """
    Send location information to User about signed event
    :param bot: telegram API object
    :param update:  telegram API state
    :param event: event from MongoDB
    :return: N/A
    """

    cal_event = dump_calendar_event(event["organizer"]["email"], event)
    coordinates = get_coordinates(cal_event["location"])
    bot.send_venue(chat_id=update.message.chat_id, latitude=coordinates["lat"],
                   longitude=coordinates["lng"], title=cal_event["summary"], address=cal_event["location"])


def main():
    """
    Main function
    :return: N/A
    """

    # Set up handlers and buttons

    start_handler = CommandHandler("start", start)
    dispatcher.add_handler(start_handler)

    train_handler = CommandHandler("train", train)
    dispatcher.add_handler(train_handler)

    train_handler = CommandHandler("attendees", attendees)
    dispatcher.add_handler(train_handler)

    calendar_handler = CommandHandler("calendar", calendar)
    dispatcher.add_handler(calendar_handler)

    updater.dispatcher.add_handler(CallbackQueryHandler(train_button))

    # Poll user actions

    updater.start_polling()

    # Update trains and events from calendar every 60 secs

    starttime = time.time()

    while True:
        # Dump events from Google Calendar and update MongoDB

        train_calendar = os.environ['TRAIN_CALENDAR_ID']
        trains = dump_calendar(train_calendar, 10)
        dump_mongodb("trains", trains)

        # Dump events from Google Calendar and update MongoDB

        events_calendar = os.environ['EVENTS_CALENDAR_ID']
        events = dump_calendar(events_calendar, 30)
        dump_mongodb("events", events)

        # Sleep to 60 secs

        time.sleep(60.0 - ((time.time() - starttime) % 60.0))


if __name__ == '__main__':
    main()
