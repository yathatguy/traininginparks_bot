# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function

import inspect
import logging
import os
import signal
import time

import pymongo
import telegram
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, ConversationHandler, RegexHandler
from telegram.ext import Updater, Filters

from clients import log_client
from google_calendar import dump_calendar, dump_mongodb, get_events, dump_calendar_event
from maps_api import get_coordinates
from wod import wod, wod_info, wod_by_mode, wod_by_modality, wod_amrap, wod_emom, wod_rt, wod_strength, wod_time, \
    wod_modality

# Set up Updater and Dispatcher

# updater = Updater(token=os.environ['TOKEN'])
updater = Updater('370932219:AAGXeZFMAuY9vJYSt5qns274i1von1cvY4I')
updater.stop()
dispatcher = updater.dispatcher

# Add logging

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.WARNING)

TIME, NOTIME = range(2)


def event_button(bot, update, user_data):
    """
    Get a User selected event from call back, add User to attendees list for the event
    and gives User info about selected event (date, time, location)
    :param bot: telegram API object
    :param update: telegram API state
    :return: N/A
    """
    logging.critical("event_button")
    logging.critical(user_data)
    query = update.callback_query
    connection = pymongo.MongoClient(os.environ['MONGODB_URI'])
    db = connection["heroku_r261ww1k"]
    action = query.data.split(";")[0]
    if action[0] == "0":
        event_id = query.data.split(";")[1]
        event = db.trains.find_one({"id": event_id})
        if action == "001":
            if "attendee" not in event.keys() or query.message.chat.username not in event["attendee"]:
                db.trains.update({"id": event_id}, {"$push": {"attendee": query.message.chat.username}}, upsert=True)
                bot.sendMessage(text="Отлично, записались!", chat_id=query.message.chat_id)
                if event["start"]["dateTime"].split("T")[1][:5] != "00:00":
                    bot.sendMessage(text="Ждем тебя {} в {}".format(event["start"]["dateTime"].split("T")[0],
                                                                    event["start"]["dateTime"].split("T")[1][:5]),
                                    chat_id=query.message.chat_id)
                else:
                    bot.sendMessage(text="Ждем тебя {}".format(event["start"]["dateTime"].split("T")[0]),
                                    chat_id=query.message.chat_id)
            else:
                bot.sendMessage(
                    text="Ты уже записан на тренировку. Или ты хочешь выполнять в 2 раза больше повторений!? Скажи тренеру об этом перед началом 😉",
                    chat_id=query.message.chat_id)
        elif action == "002":
            event_loc(bot, query, event)
        elif action == "003":
            text = event_info(bot, update, event)
            bot.sendMessage(text=text, chat_id=query.message.chat_id)
        elif action == "004":
            try:
                event["attendee"].remove(query.message.chat.username)
                db.trains.update({"id": event_id}, {"$set": {"attendee": event["attendee"]}})
                bot.sendMessage(text="Жаль. Посмотри на другие тренировки. Возможно, что то подойтет тебе.",
                                chat_id=query.message.chat_id)
            except Exception as exc:
                logging.exception(exc)
        else:
            pass
    elif action[0] == "1":
        event_id = query.data.split(";")[1]
        event = db.events.find_one({"id": event_id})
        if action == "101":
            if "attendee" not in event.keys() or query.message.chat.username not in event["attendee"]:
                db.events.update({"id": event_id}, {"$push": {"attendee": query.message.chat.username}}, upsert=True)
                bot.sendMessage(text="Отлично, записались!", chat_id=query.message.chat_id)
                if event["start"]["dateTime"].split("T")[1][:5] != "00:00":
                    bot.sendMessage(text="Ждем тебя {} в {}".format(event["start"]["dateTime"].split("T")[0],
                                                                    event["start"]["dateTime"].split("T")[1][:5]),
                                    chat_id=query.message.chat_id)
                else:
                    bot.sendMessage(text="Ждем тебя {}".format(event["start"]["dateTime"].split("T")[0]),
                                    chat_id=query.message.chat_id)
            else:
                bot.sendMessage(
                    text="Ты уже записан на это мероприятие.", chat_id=query.message.chat_id)
        elif action == "102":
            event_loc(bot, query, event)
        elif action == "103":
            text = event_info(bot, update, event)
            bot.sendMessage(text=text, chat_id=query.message.chat_id)
        elif action == "104":
            try:
                event["attendee"].remove(query.message.chat.username)
                db.events.update({"id": event_id}, {"$set": {"attendee": event["attendee"]}})
                bot.sendMessage(text="Жаль. Посмотри на другие мероприятия. Возможно, что то подойтет тебе.",
                                chat_id=query.message.chat_id)
            except Exception as exc:
                logging.exception(exc)
        else:
            pass
    elif action[0] == "2":
        events = list()
        if action == "201":
            for train in db.trains.find({}):
                if "attendee" in train.keys() and query.message.chat.username in train["attendee"]:
                    events.append(train["id"])
            if len(events) > 0:
                bot.sendMessage(text="Список твоих тренировок:", chat_id=query.message.chat_id)
                for train_id in events:
                    train = db.trains.find_one({"id": train_id})
                    if train["start"]["dateTime"].split("T")[1][:5] == "00:00":
                        bot.sendMessage(
                            text="{}: {}".format(train["start"]["dateTime"].split("T")[0], train["summary"]),
                            chat_id=query.message.chat_id)
                    else:
                        bot.sendMessage(
                            text="{}: {} с {} до {}".format(train["start"]["dateTime"].split("T")[0], train["summary"],
                                                            train["start"]["dateTime"].split("T")[1][:5],
                                                            train["end"]["dateTime"].split("T")[1][:5]),
                            chat_id=query.message.chat_id)
            else:
                bot.sendMessage(text="Ты никуда не записался(лась)", chat_id=query.message.chat_id)
        elif action == "202":
            for event in db.events.find({}):
                if "attendee" in event.keys() and query.message.chat.username in event["attendee"]:
                    events.append(event["id"])
            if len(events) > 0:
                bot.sendMessage(text="Список твоих мероприятий:", chat_id=query.message.chat_id)
                for event_id in events:
                    event = db.events.find_one({"id": event_id})
                    if event["start"]["dateTime"].split("T")[1][:5] == "00:00":
                        bot.sendMessage(
                            text="{}: {}".format(event["start"]["dateTime"].split("T")[0], event["summary"]),
                            chat_id=query.message.chat_id)
                    else:
                        bot.sendMessage(
                            text="{}: {} с {} до {}".format(event["start"]["dateTime"].split("T")[0], event["summary"],
                                                            event["start"]["dateTime"].split("T")[1][:5],
                                                            event["end"]["dateTime"].split("T")[1][:5]),
                            chat_id=query.message.chat_id)
            else:
                bot.sendMessage(text="Ты никуда не записался(лась)", chat_id=query.message.chat_id)
        else:
            pass
    elif action[0] == "3":
        if action == "301":
            wod_by_mode(bot, update)
        elif action == "303":
            wod_info(bot, update)
        elif action == "311":
            wod_emom(bot, update)
        elif action == "321":
            wod_amrap(bot, update)
        elif action == "331":
            wod_rt(bot, update)
        elif action == "341":
            wod_time(bot, update)
        elif action == "351":
            wod_strength(bot, update)
        elif action == "302":
            wod_by_modality(bot, update)
        elif action == "312":
            modality_str = query.data.split(";")[1]
            modality = modality_str.split(", ")
            wod_modality(bot, update, modality)
        else:
            pass
    elif action == "401":
        bot.sendMessage(text="Открываем приложение.", chat_id=query.message.chat_id)
        bot.sendMessage(text="Выбираем [Настройки].", chat_id=query.message.chat_id)
        bot.sendPhoto(
            photo="http://telegram-online.ru/wp-content/uploads/2015/11/kak-ustanovit-ili-pomenyat-imya-v-telegram-1-576x1024.jpg",
            chat_id=query.message.chat_id)
        bot.sendMessage(text="Кликаем на надпись 'Не задано'.", chat_id=query.message.chat_id)
        bot.sendPhoto(
            photo="http://telegram-online.ru/wp-content/uploads/2015/11/kak-ustanovit-ili-pomenyat-imya-v-telegram-2-576x1024.jpg",
            chat_id=query.message.chat_id)
        bot.sendMessage(text="Пишем подходящий ник и жмем галочку в правом верхнем углу.",
                        chat_id=query.message.chat_id)
        bot.sendPhoto(
            photo="http://telegram-online.ru/wp-content/uploads/2015/11/kak-ustanovit-ili-pomenyat-imya-v-telegram-3.jpg",
            chat_id=query.message.chat_id)
    elif action == "wod_emom":
        wod_emom(bot, update)
    elif action == "wod_amrap":
        wod_amrap(bot, update)
    elif action == "wod_rt":
        wod_rt(bot, update)
    elif action == "wod_time":
        wod_time(bot, update)
    elif action == "wod_strength":
        wod_strength(bot, update)
    elif action == "wod_modality":
        wod_modality(bot, update, query.data.split(";")[1].split(", "))
    elif action == "501":
        whiteboard_results(bot, update, query.data.split(";")[1])
    else:
        pass
    connection.close()


def whiteboard(bot, update):
    logging.critical("whiteboard")
    if update.message.chat.type in ["group", "supergroup", "channel"]:
        bot.sendMessage(text="Не-не, в группах я отказываюсь работать, я стеснительный. Пиши мне только тет-а-тет 😉",
                        chat_id=update.message.chat.id)
        return

    connection = pymongo.MongoClient(os.environ['MONGODB_URI'])
    db = connection["heroku_r261ww1k"]

    if db.benchmarks.find({}).count() == 0:
        bot.sendMessage(text="На данный момент у нас нет комплексов для оценки", chat_id=update.message.chat_id)
        return

    benchmarks = db.benchmarks.find({})
    kb = []
    for benchmark in benchmarks:
        button = telegram.InlineKeyboardButton(text=benchmark["name"], callback_data="501;" + benchmark["name"])
        kb.append([button])
    kb_markup = telegram.InlineKeyboardMarkup(kb)
    update.message.reply_text(text="Выбирай комплекс:", reply_markup=kb_markup)
    connection.close()


def whiteboard_results(bot, update, benchmark_name):
    logging.critical("whiteboard_results")
    connection = pymongo.MongoClient(os.environ['MONGODB_URI'])
    db = connection["heroku_r261ww1k"]
    benchmark = db.benchmarks.find_one({"name": benchmark_name})
    bot.sendMessage(text=benchmark["name"], chat_id=update.callback_query.message.chat.id)
    bot.sendMessage(text=benchmark["description"], chat_id=update.callback_query.message.chat.id)
    if len(benchmark["results"]) == 0:
        bot.sendMessage(text="Еще никто не записал свой результат. Ты можешь быть первым!",
                        chat_id=update.callback_query.message.chat.id)
    else:
        for man in benchmark["results"]:
            bot.sendMessage(text="@" + man["name"] + ":\t" + man["result"],
                            chat_id=update.callback_query.message.chat.id)
    connection.close()
    bot.sendMessage(text="Хочешь добавить свое время?", chat_id=update.callback_query.message.chat.id)
    return TIME


def whiteboard_add(bot, update, benchmark_name, user_data):
    logging.critical("whiteboard_add")
    logging.critical(TIME, NOTIME)
    logging.critical(update.message.text)
    logging.critical(user_data)
    connection = pymongo.MongoClient(os.environ['MONGODB_URI'])
    db = connection["heroku_r261ww1k"]
    benchmark = db.benchmarks.find_one({"name": benchmark_name})
    db.benchmarks.update({"name": benchmark["name"]},
                         {"$pull": {"results": {"name": update.callback_query.message.chat.username}}})
    db.benchmarks.update({"name": benchmark["name"]}, {"$push": {
        "results": {"$each": [{"name": update.callback_query.message.chat.username, "result": "0:00"}], "$sort": 1}}})
    connection.close()


def cancel(bot, update):
    logging.critical("cancel")
    bot.sendMessage(text="Это не время, а что то еще...", chat_id=update.message.chat.id)

    return ConversationHandler.END


def graceful(signum, frame):
    """
    Graceful exit
    :param signum: Signal number
    :param frame: Frame
    :return: N/A
    """

    print("Got CTRL+C")
    exit(0)


def error(bot, update, error):
    logging.critical('Update "%s" caused error "%s"' % (update, error))


def main():
    """
    Main function
    :return: N/A
    """

    # Graceful exit

    signal.signal(signal.SIGINT, graceful)

    # Set up handlers and buttons

#    start_handler = CommandHandler("start", start)
#    dispatcher.add_handler(start_handler)

#    train_handler = CommandHandler("train", train)
#    dispatcher.add_handler(train_handler)

#    train_handler = CommandHandler("attendees", attendees)
#    dispatcher.add_handler(train_handler)

#    wod_handler = CommandHandler("wod", wod)
#    dispatcher.add_handler(wod_handler)

#    whiteboard_handler = CommandHandler("whiteboard", whiteboard)
#    dispatcher.add_handler(whiteboard_handler, group=0)

#    calendar_handler = CommandHandler("calendar", calendar)
#    dispatcher.add_handler(calendar_handler)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("whiteboard", whiteboard)],
        states={
            TIME: [RegexHandler('^[0-9]+:[0-5][0-9]$', whiteboard_add, pass_user_data=True)],
            NOTIME: [MessageHandler(Filters.text, whiteboard_add, pass_user_data=True)],
        },

        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    )
    dispatcher.add_handler(conv_handler, group=0)

    updater.dispatcher.add_handler(CallbackQueryHandler(event_button, pass_user_data=True))

    # log all errors
#    updater.dispatcher.add_error_handler(error)

    # Poll user actions

    updater.start_polling()
    updater.idle()

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
    # DOC: https://core.telegram.org/bots/api
    main()
