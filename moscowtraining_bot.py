# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function

import datetime
import json
import logging
import os
import time

import pymongo
import telegram
from telegram.contrib.botan import Botan
from telegram.ext import CommandHandler, CallbackQueryHandler
from telegram.ext import Updater
from google_calendar import dump_calendar, dump_mongodb, get_events

# set up Updater and Dispatcher
updater = Updater(token=os.environ['TOKEN'])
updater.stop()
dispatcher = updater.dispatcher

# Set up Botan
botan = Botan(os.environ['BOTAN_API_KEY'])

# Add logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)


def botan_track(message, update):
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
          [telegram.KeyboardButton('/attendees')]]
    kb_markup = telegram.ReplyKeyboardMarkup(kb)
    bot.send_message(chat_id=update.message.chat_id,
                     text="Добро пожаловать, атлет!",
                     reply_markup=kb_markup,
                     resize_keyboard=True)


def attendees(bot, update):
    connection = pymongo.MongoClient(os.environ['MONGODB_URI'])
    db = connection["heroku_r261ww1k"]
    bot.sendMessage(chat_id=update.message.chat_id,
                    text="Список людей, записавшихся на предстоящие тренировки")
    for event in db.events.find({'start.dateTime': {
        '$gt': (datetime.datetime.utcnow() + datetime.timedelta(hours=3)).isoformat()[:19] + '+03:00'}}):
        if "attendee" in event.keys():
            attendees_list = ''
            for attendee in event["attendee"]:
                attendees_list = attendees_list + ' @' + attendee
            bot.sendMessage(chat_id=update.message.chat_id,
                            text="{}: {} ({}) - {}".format(event["start"]["dateTime"].split("T")[0], event["summary"],
                                                           len(event["attendee"]), attendees_list))
        else:
            bot.sendMessage(chat_id=update.message.chat_id,
                            text="{}: {} ({}) - {}".format(event["start"]["dateTime"].split("T")[0], event["summary"],
                                                           0, 'пока никто не записался'))
        botan_track(update.message, update)
    connection.close()


def reply(bot, update, text):
    # TODO: не найден chat_id
    print(update)
    print(update.message)
    print(update.message.chat_id)
    bot.sendMessage(chat_id=update.message.chat_id, text=text)
    botan_track(update.message, update)


def train(bot, update):
    events = get_events(3)
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
    kb = []
    for event in events:
        text = "{}: {}".format(event["summary"], event["start"]["dateTime"].split("T")[0])
        item = telegram.InlineKeyboardButton(text=text, callback_data=event["id"])
        kb.append([item])
    kb_markup = telegram.inlinekeyboardmarkup.InlineKeyboardMarkup(kb)
    return kb_markup


def train_button(bot, update):
    query = update.callback_query
    connection = pymongo.MongoClient(os.environ['MONGODB_URI'])
    db = connection["heroku_r261ww1k"]
    if db.events.find({"id": query.data, "attendee": query.message.chat.username}).count() == 0:
        event = db.events.find_one({"id": query.data})
        db.events.update({"id": query.data}, {"$push": {"attendee": query.message.chat.username}}, upsert=True)
        bot.sendMessage(text="Отлично, записались!", chat_id=query.message.chat_id, message_id=query.message.message_id)
        if "dozen" in event["summary"].lower():
            bot.sendMessage(text="Ждем тебя {} с {} по адресу:".format(event["start"]["dateTime"].split("T")[0],
                                                                       event["start"]["dateTime"].split("T")[1][:5]),
                            chat_id=query.message.chat_id, message_id=query.message.message_id)
            dozen_loc(bot, query)
        elif "нескучный" in event["summary"].lower():
            bot.sendMessage(text="Ждем тебя {} с {} по адресу:".format(event["start"]["dateTime"].split("T")[0],
                                                                       event["start"]["dateTime"].split("T")[1][:5]),
                            chat_id=query.message.chat_id, message_id=query.message.message_id)
            sad_loc(bot, query)
    else:
        bot.sendMessage(text="Ты уже записан(а) на эту тренировку", chat_id=query.message.chat_id,
                        message_id=query.message.message_id)
    connection.close()


def dozen_loc(bot, update):
    dozen = json.loads(os.environ['DOZEN'])
    bot.send_venue(chat_id=update.message.chat_id, latitude=dozen["latitude"],
                   longitude=dozen["longitude"], title=dozen["title"], address=dozen["address"])


def sad_loc(bot, update):
    sad = json.loads(os.environ['SAD'])
    bot.send_venue(chat_id=update.message.chat_id, latitude=sad["latitude"],
                   longitude=sad["longitude"], title=sad["title"], address=sad["address"])


def main():

    # Set up handlers and buttons

    start_handler = CommandHandler("start", start)
    dispatcher.add_handler(start_handler)

    train_handler = CommandHandler("train", train)
    dispatcher.add_handler(train_handler)

    train_handler = CommandHandler("attendees", attendees)
    dispatcher.add_handler(train_handler)

    updater.dispatcher.add_handler(CallbackQueryHandler(train_button))

    # Poll user actions

    updater.start_polling()

    # Update 10 events from calendar every 60 secs

    starttime = time.time()
    while True:
        events = dump_calendar(10)
        dump_mongodb(events)
        time.sleep(60.0 - ((time.time() - starttime) % 60.0))


if __name__ == '__main__':
    main()
