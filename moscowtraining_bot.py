# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function

import inspect
import logging
import os
import signal
import time

import pymongo
import telegram
from telegram.contrib.botan import Botan
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler
from telegram.ext import Updater, Filters

from google_calendar import dump_calendar, dump_mongodb, get_events, dump_calendar_event
from maps_api import get_coordinates
from sendemail import send_email
from wod import wod, wod_info, wod_by_mode, wod_by_modality, wod_amrap, wod_emom, wod_rt, wod_strength, wod_time, \
    wod_modality

# Set up Updater and Dispatcher

updater = Updater(token=os.environ['TOKEN'])
updater.stop()
dispatcher = updater.dispatcher

# Set up Botan

botan = Botan(os.environ['BOTAN_API_KEY'])

# Add logging

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.WARNING)


def botan_track(message, update):
    """
    Call Bot API and send info
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

    if update.message.chat.username == "":
        kb = []
        button = telegram.InlineKeyboardButton(text="Инструкции", callback_data="401")
        kb.append([button])
        kb_markup = telegram.inlinekeyboardmarkup.InlineKeyboardMarkup(kb)
        kb_start = [[telegram.KeyboardButton('/start')]]
        kb_markup_start = telegram.ReplyKeyboardMarkup(kb_start, resize_keyboard=False)
        update.message.reply_text(
            text="Привет!\n\nК сожалению Вы не установили username для своего telegram-аккаунта, и поэтому бот не сможет корректно для Вас работать.",
            reply_markup=kb_markup_start)
        update.message.reply_text(text="Хочешь посмотреть на инструкции, как это быстро и легко сделать?",
                                  reply_markup=kb_markup)
    else:
        kb_markup = keyboard()
        bot.send_message(chat_id=update.message.chat.id,
                         text="Добро пожаловать, @{}!".format(update.message.chat.username),
                         reply_markup=kb_markup)


def keyboard():
    """
    Create keyboard markup object with buttons
    :return: keyboard markup object
    """

    kb = [[telegram.KeyboardButton('/train'), telegram.KeyboardButton('/attendees')],
          [telegram.KeyboardButton('/calendar')],
          [telegram.KeyboardButton('/wod'), telegram.KeyboardButton('/exercise')],
          [telegram.KeyboardButton('/feedback')]]
    kb_markup = telegram.ReplyKeyboardMarkup(kb, resize_keyboard=True)

    return kb_markup


def attendees(bot, update):
    """
    Count number of attendees for each planned event and share with User
    :param bot: telegram API object
    :param update: telegram API state
    :return: N/A
    """

    events = get_events("trains", 5)
    if events:
        bot.sendMessage(chat_id=update.message.chat.id,
                        text="Список людей, записавшихся на предстоящие тренировки:")
        for event in events:
            if "attendee" in event.keys() and len(event["attendee"]) > 0:
                attendees_list = ''
                for attendee in event["attendee"]:
                    attendees_list = attendees_list + ' @' + attendee
                bot.sendMessage(chat_id=update.message.chat.id,
                                text="{}: {} ({}) - {}".format(event["start"]["dateTime"].split("T")[0],
                                                               event["summary"],
                                                               len(event["attendee"]), attendees_list))
            else:
                bot.sendMessage(chat_id=update.message.chat.id,
                                text="{}: {} ({}) - {}".format(event["start"]["dateTime"].split("T")[0],
                                                               event["summary"],
                                                               0, 'пока никто не записался'))
        botan_track(update.message, update)
    else:
        bot.sendMessage(chat_id=update.message.chat.id, text="Нет трениировок, нет и записавшихся.")


def reply(bot, update, text):
    """
    Reply to User and calls Botan API
    :param bot: telegram API object
    :param update: telegram API state
    :param text: message that was send to User
    :return: N/A
    """

    bot.send_message(chat_id=update.message.chat.id, text=text)
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
            kb_markup = event_keyboard(bot, update, event)
            update.message.reply_text(
                text="{}: {} с {} до {}".format(event["start"]["dateTime"].split("T")[0], event["summary"],
                                                event["start"]["dateTime"].split("T")[1][:5],
                                                event["end"]["dateTime"].split("T")[1][:5]), reply_markup=kb_markup)
            botan_track(update.message, update)
        all_events(bot, update)
    else:
        reply(bot, update, text="Пока тренировки не запланированы. Восстанавливаемся!")
        botan_track(update.message, update)


def event_keyboard(bot, update, event):
    """
    Create keyboard with inline buttons for trains and events
    :param bot: telegram API object
    :param update: telegram API state 
    :param event: Event from MongoDB (train or event)
    :return: inline keyboard markup
    """

    # 001 - signup for train
    # 002 - location for train
    # 003 - info for train
    # 004 - signout for train
    # 101 - signup for event
    # 102 - location for event
    # 103 - info for event
    # 104 - signout for event

    # 201 - all trains
    # 202 - all events

    # 301 - wod by mode
    # 302 - wod by modality
    # 311 - wod mode: EMOM
    # 321 - wod mode: AMRAP
    # 331 - wod mode: For reps and time
    # 341 - wod mode: For time
    # 351 - wod mode: strength
    # 312 - wod modality: selection

    # 401 - username instruction

    if inspect.stack()[1][3] == 'train':
        kb = []
        if "attendee" in event.keys() and update.message.from_user.username in event["attendee"]:
            text_sign = "Не пойду!"
            signup = telegram.InlineKeyboardButton(text=text_sign, callback_data="004;" + str(event["id"]))
        else:
            text_sign = "Пойду!"
            signup = telegram.InlineKeyboardButton(text=text_sign, callback_data="001;" + str(event["id"]))
        text_loc = "Где это?"
        location = telegram.InlineKeyboardButton(text=text_loc, callback_data="002;" + str(event["id"]))
        kb.append([signup, location])
        kb_markup = telegram.inlinekeyboardmarkup.InlineKeyboardMarkup(kb)
    elif inspect.stack()[1][3] == 'calendar':
        kb = []

        if "attendee" in event.keys() and update.message.from_user.username in event["attendee"]:
            text_sign = "Не пойду!"
            signup = telegram.InlineKeyboardButton(text=text_sign, callback_data="104;" + str(event["id"]))
        else:
            text_sign = "Пойду!"
            signup = telegram.InlineKeyboardButton(text=text_sign, callback_data="101;" + str(event["id"]))
        text_loc = "Где это?"
        location = telegram.InlineKeyboardButton(text=text_loc, callback_data="102;" + str(event["id"]))
        text_info = "Инфо"
        info = telegram.InlineKeyboardButton(text=text_info, callback_data="103;" + str(event["id"]))
        kb.append([signup])
        kb.append([location, info])
        kb_markup = telegram.inlinekeyboardmarkup.InlineKeyboardMarkup(kb)
    else:
        kb_markup = keyboard()
    return kb_markup


def event_button(bot, update):
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
                    text="Ты уже записан на тренировку. Или ты хочешь выполнять в 2 раза больше повторений!? Скажи тренеру об этом перед начало 😉",
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
                bot.sendMessage(text="Жаль. Посмотри на другие тренировки. Возможно, что то подойтет тебе.",
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
    else:
        pass
    connection.close()


def calendar(bot, update):
    """
    Get upcoming events and list to User
    :param bot: telegram API object
    :param update: telegram API state
    :return: N/A
    """

    events = get_events("events", 20)
    if events:
        reply(bot, update, text="Список предстоящих событий:")
        botan_track(update.message, update)
        for event in events:
            kb_markup = event_keyboard(bot, update, event)
            if "date" in event["end"].keys():
                update.message.reply_text(
                    text="{}: {}".format(event["start"]["dateTime"].split("T")[0], event["summary"]),
                    reply_markup=kb_markup)
            else:
                update.message.reply_text(
                    text="{}: {} с {} до {}".format(event["start"]["dateTime"].split("T")[0], event["summary"],
                                                    event["start"]["dateTime"].split("T")[1][:5],
                                                    event["end"]["dateTime"].split("T")[1][:5]), reply_markup=kb_markup)
            botan_track(update.message, update)
        all_events(bot, update)
    else:
        bot.sendMessage(text="В календаре пока нет запланированных событий.")
        botan_track(update.message, update)


def event_loc(bot, update, event):
    """
    Send location information to User about signed event
    :param bot: telegram API object
    :param update: telegram API state
    :param event: event from MongoDB
    :return: N/A
    """

    cal_event = dump_calendar_event(event["organizer"]["email"], event)

    if "location" in cal_event.keys():
        coordinates = get_coordinates(cal_event["location"])
        if bool(coordinates):
            bot.send_venue(chat_id=update.message.chat.id, latitude=coordinates["lat"], longitude=coordinates["lng"],
                           title=cal_event["summary"], address=cal_event["location"])
        else:
            reply(bot, update, text="Местоположение задано некорректно. Свяжитесь с организаторами мероприятия.")
    else:
        reply(bot, update, text="Местоположение не задано")


def event_info(bot, update, event):
    """

    :param bot: telegram API object
    :param update: telegram API state
    :param event: event from MongoDB
    :return: event description from Google Calendar
    """

    cal_event = dump_calendar_event(event["organizer"]["email"], event)
    attendee_list = str()

    if "attendee" in event.keys() and len(event["attendee"]) > 0:
        for attendee in event["attendee"]:
            attendee_list = attendee_list + " @" + attendee
    if "description" in cal_event.keys() and attendee_list != "":
        text = "На мероприятие собираются:" + attendee_list + "\n\nОписание события:\n\n" + cal_event["description"]
    elif "description" in cal_event.keys() and attendee_list == "":
        text = "На мероприятие пока никто не записался." + "\n\nОписание события:\n\n" + cal_event["description"]
    else:
        text = "Описание не задано."

    return text


def all_events(bot, update):
    """
    Inline button to list all events for a User
    :param bot: telegram API object
    :param update: telegram API state 
    :return: N/A 
    """

    if inspect.stack()[1][3] == 'train':
        kb = list()
        message = telegram.InlineKeyboardButton(text="куда уже ты записан(а)", callback_data="201")
        kb.append([message])
        kb_markup = telegram.inlinekeyboardmarkup.InlineKeyboardMarkup(kb)
    elif inspect.stack()[1][3] == 'calendar':
        kb = list()
        message = telegram.InlineKeyboardButton(text="куда уже ты записан(а)", callback_data="202")
        kb.append([message])
        kb_markup = telegram.inlinekeyboardmarkup.InlineKeyboardMarkup(kb)
    else:
        pass
    update.message.reply_text(text="Давай посмотрим", reply_markup=kb_markup)


def feedback(bot, update):
    """
    Handle 'feedback' command and calls message handler
    :param bot: telegram API object
    :param update:  telegram API state
    :return: N/A 
    """

    global old_message
    old_message = update.message
    bot.send_message(chat_id=update.message.chat.id,
                     text="Оставьте свой отзыв о работе бота. Вместе мы сделаем его лучше!",
                     reply_markup=telegram.ReplyKeyboardRemove())


def handle_message(bot, update):
    """
    Parse message and/or update and do actions. Use 'global old_message' to handle different messages.
    :param bot: telegram API object
    :param update:  telegram API state
    :return: N/A 
    """

    global old_message
    if ('old_message' in vars() or 'old_message' in globals()) \
            and "/feedback" in old_message.parse_entities(types="bot_command").values():
        send_email(update.message)
        kb_markup = keyboard()
        bot.send_message(chat_id=update.message.chat.id, text="Ваш отзыв принят, спасибо.", reply_markup=kb_markup)
    old_message = update.message


def exercise(bot, update):
    bot.send_message(chat_id=update.message.chat.id, text="Тут будет описание упражений.")


def graceful(signum, frame):
    """
    Graceful exit
    :param signum: Signal number
    :param frame: Frame
    :return: N/A
    """

    print("Got CTRL+C")
    exit(0)


def main():
    """
    Main function
    :return: N/A
    """

    # Graceful exit

    signal.signal(signal.SIGINT, graceful)

    # Set up handlers and buttons

    start_handler = CommandHandler("start", start)
    dispatcher.add_handler(start_handler)

    train_handler = CommandHandler("train", train)
    dispatcher.add_handler(train_handler)

    train_handler = CommandHandler("attendees", attendees)
    dispatcher.add_handler(train_handler)

    wod_handler = CommandHandler("wod", wod)
    dispatcher.add_handler(wod_handler)

    exercise_handler = CommandHandler("exercise", exercise)
    dispatcher.add_handler(exercise_handler)

    calendar_handler = CommandHandler("calendar", calendar)
    dispatcher.add_handler(calendar_handler)

    feedback_handler = CommandHandler("feedback", feedback)
    dispatcher.add_handler(feedback_handler)

    updater.dispatcher.add_handler(CallbackQueryHandler(event_button))

    updater.dispatcher.add_handler(MessageHandler(filters=Filters.text, callback=handle_message))

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
    # DOC: https://core.telegram.org/bots/api
    main()
