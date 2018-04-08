# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function

import json
import logging
import os

import pymongo
import telegram
from bson import json_util
from telegram.ext import CommandHandler, RegexHandler, CallbackQueryHandler, MessageHandler
from telegram.ext import Updater, Filters
from time import time, sleep

from clients import log_client, check_username
from decorators import only_private
from google_calendar import dump_calendar_event, dump_calendar, dump_mongodb
from keyboard import keyboard
from maps_api import get_coordinates
from mongodata import get_things, get_thing
from wod import wod, wod_info, wod_by_mode, wod_by_modality, wod_amrap, wod_emom, wod_rt, wod_strength, wod_time, \
    wod_modality
import activities

# Set up Updater and Dispatcher

updater = Updater(token=os.environ['TOKEN'])
# updater = Updater(token="370932219:AAGXeZFMAuY9vJYSt5qns274i1von1cvY4I")
updater.stop()
dispatcher = updater.dispatcher

step = 5


@only_private
def start(bot, update):
    query = get_query(bot, update)
    if check_username(bot, update) == False:
        return
    kb_markup = keyboard()
    bot.send_message(chat_id=query.message.chat.id,
                     text="Добро пожаловать, @{}!".format(query.message.chat.username),
                     reply_markup=kb_markup)
    log_client(bot, update)


def get_query(bot, update):
    if update.callback_query:
        query = update.callback_query
    else:
        query = update
    return query


@only_private
def get_trains_activities(bot, update, *args, **kwargs):
    query = get_query(bot, update)
    db_name = "trains"
    kb_markup = activities.keyboard(db_name)
    bot.sendMessage(text="Какая категоря тренировок тебя интересует?", chat_id=query.message.chat.id, reply_markup=kb_markup)


def get_trains(bot, update, *args, **kwargs):
    user = kwargs.get("user", None)
    activity = kwargs.get("activities", None)
    query = get_query(bot, update)
    db_name = "trains"
    if user:
        trains_list = get_things(db_name, user=user, activities=activity)
    else:
        trains_list = get_things(db_name, activities=activity)
    if trains_list:
        iter = 0
        next = iter + step
        if user:
            if len(trains_list) <= next:
                thing_list(bot, update, db_name, iter, next, skip_pager=True, user=user, activities=activity)
            elif len(trains_list) > next:
                thing_list(bot, update, db_name, iter, next, user=user, activities=activity)
        else:
            if len(trains_list) <= next:
                thing_list(bot, update, db_name, iter, next, skip_pager=True, activities=activity)
            elif len(trains_list) > next:
                thing_list(bot, update, db_name, iter, next, activities=activity)
    else:
        bot.sendMessage(text="Пока тренировки не запланированы. Восстанавливаемся!", chat_id=query.message.chat.id,
                        reply_markup=keyboard())


@only_private
def get_events_activities(bot, update, *args, **kwargs):
    query = get_query(bot, update)
    db_name = "events"
    kb_markup = activities.keyboard(db_name)
    bot.sendMessage(text="Какая категория соревнований тебя интересует?", chat_id=query.message.chat.id, reply_markup=kb_markup)


def get_events(bot, update, *args, **kwargs):
    user = kwargs.get("user", None)
    activity = kwargs.get("activities", None)
    query = get_query(bot, update)
    db_name = "events"
    if user:
        events_list = get_things(db_name, user=user, activities=activity)
    else:
        events_list = get_things(db_name, activities=activity)
    if events_list:
        iter = 0
        next = iter + step
        if user:
            if len(events_list) <= next:
                thing_list(bot, update, db_name, iter, next, skip_pager=True, user=user, activities=activity)
            else:
                thing_list(bot, update, db_name, iter, next, user=user, activities=activity)
        else:
            if len(events_list) <= next:
                thing_list(bot, update, db_name, iter, next, skip_pager=True, activities=activity)
            else:
                thing_list(bot, update, db_name, iter, next, activities=activity)
    else:
        bot.sendMessage(text="Пока мероприятия не запланированы. Восстанавливаемся!", chat_id=query.message.chat.id,
                        reply_markup=keyboard())


def thing_list(bot, update, db_name, iter, next, *args, **kwargs):
    query = get_query(bot, update)
    chat_id = query.message.chat.id
    user = kwargs.get("user", None)
    activity = kwargs.get("activities", None)
    if user:
        things = get_things(db_name, user=user, activities=activity)
    else:
        things = get_things(db_name, activities=activity)
    thing_list = things[iter:next]
    kb = []
    for thing in thing_list:
        if db_name == "trains":
            button = telegram.InlineKeyboardButton(
                text=thing["start"]["date"] + " " + thing["start"]["dateTime"].split("T")[1][:5] + ": " + thing[
                    "summary"], callback_data="100;" + thing["id"])
        elif db_name == "events":
            button = telegram.InlineKeyboardButton(text=thing["start"]["date"] + ":\t" + thing["summary"],
                                                   callback_data="200;" + thing["id"])
        else:
            return []
        kb.append([button])
        iter += 1
    skip_pager = kwargs.get("skip_pager", False)
    if not skip_pager:
        kb.append(pager(bot, update, db_name, iter, step, next))
    kb_markup = telegram.InlineKeyboardMarkup(kb)
    if db_name == "trains":
        bot.sendMessage(text="Расписание следующих тренировок:", chat_id=chat_id, reply_markup=kb_markup)
    elif db_name == "events":
        bot.sendMessage(text="Расписание следующих мероприятий:", chat_id=chat_id, reply_markup=kb_markup)
    else:
        logging.critical(u"thing_list: db error: " + db_name)
    return thing_list


def pager(bot, update, db_name, iter, step, next, *args, **kwargs):
    user = kwargs.get("user", None)
    activity = kwargs.get("activities", None)
    if iter - step == 0:
        button_next = telegram.InlineKeyboardButton(text=">", callback_data="302;" + str(next) + ";" + db_name)
        buttons = []
        buttons.append(button_next)
    elif user and len(get_things(db_name, user=user, activities=activity)) > next:
        button_prev = telegram.InlineKeyboardButton(text="<", callback_data="301;" + str(next - step) + ";" + db_name)
        button_next = telegram.InlineKeyboardButton(text=">", callback_data="302;" + str(next) + ";" + db_name)
        buttons = []
        buttons.append(button_prev)
        buttons.append(button_next)
    elif len(get_things(db_name, activities=activity)) > next:
        button_prev = telegram.InlineKeyboardButton(text="<", callback_data="301;" + str(next - step) + ";" + db_name)
        button_next = telegram.InlineKeyboardButton(text=">", callback_data="302;" + str(next) + ";" + db_name)
        buttons = []
        buttons.append(button_prev)
        buttons.append(button_next)
    else:
        button_prev = telegram.InlineKeyboardButton(text="<", callback_data="301;" + str(next - step) + ";" + db_name)
        buttons = []
        buttons.append(button_prev)
    return buttons


def train_details(bot, update, train):
    if check_username(bot, update) == False:
        return
    query = get_query(bot, update)
    kb = []
    try:
        if "attendee" in train.keys() and query.message.chat.username in train["attendee"]:
            text_sign = "❌ Не смогу прийти"
            signup = telegram.InlineKeyboardButton(text=text_sign, callback_data="101;" + str(train["id"]))
        else:
            text_sign = "✅ Записаться"
            signup = telegram.InlineKeyboardButton(text=text_sign, callback_data="102;" + str(train["id"]))
    except Exception as exc:
        logging.exception(exc)
    text_attendees = "🙏 Участники"
    attendees = telegram.InlineKeyboardButton(text=text_attendees, callback_data="105;{};".format(str(train["id"])))
    kb.append([signup, attendees])
    text_loc = "🗺 Где это?"
    location = telegram.InlineKeyboardButton(text=text_loc, callback_data="103;" + str(train["id"]))
    #    text_cal = "🗓 Добавить"
    #    cal = telegram.InlineKeyboardButton(text=text_cal, url=train["htmlLink"] +
    #        "&action=TEMPLATE" +
    #        "&text=" + train["summary"] +
    #        "&dates=" + train["start"]["dateTime"] + "/" + train["end"]["dateTime"] + # Проблема с конвертацией даты
    #        "&trp=false" +
    #        "&sprop=" +
    #        "&sprop=name:" +
    #        "&pprop=HowCreated:QUICKADD&scp=ONE")
    #    logging.critical(cal)
    #    kb.append([location, cal])
    kb.append([location])
    kb_markup = telegram.InlineKeyboardMarkup(kb)
    bot.sendMessage(text="Детали по событию: {} - {}".format(train["start"]["date"], train["summary"]),
                    chat_id=query.message.chat.id, reply_markup=kb_markup)


def event_details(bot, update, event):
    if check_username(bot, update) == False:
        return
    query = get_query(bot, update)
    kb = []
    try:
        if "attendee" in event.keys() and query.message.chat.username in event["attendee"]:
            text_sign = "❌ Не смогу прийти"
            signup = telegram.InlineKeyboardButton(text=text_sign, callback_data="201;" + str(event["id"]))
        else:
            text_sign = "✅ Записаться"
            signup = telegram.InlineKeyboardButton(text=text_sign, callback_data="202;" + str(event["id"]))
    except Exception as exc:
        logging.exception(exc)
    text_attendees = "🙏 Участники"
    attendees = telegram.InlineKeyboardButton(text=text_attendees, callback_data="205;{};".format(str(event["id"])))
    kb.append([signup, attendees])
    text_loc = "🗺 Где это?"
    location = telegram.InlineKeyboardButton(text=text_loc, callback_data="203;" + str(event["id"]))
    text_info = "📋 Информация"
    info = telegram.InlineKeyboardButton(text=text_info, callback_data="204;" + str(event["id"]))
    kb.append([info, location])
    kb_markup = telegram.InlineKeyboardMarkup(kb)
    bot.sendMessage(text="Детали по событию: {} - {}".format(event["start"]["date"], event["summary"]),
                    chat_id=query.message.chat.id, reply_markup=kb_markup)


def sign_out(bot, update, db_name, thing_id):
    if check_username(bot, update) == False:
        return
    query = get_query(bot, update)
    thing = get_thing(db_name, thing_id)
    connection = pymongo.MongoClient(os.environ['MONGODB_URI'])
    db = connection["heroku_r261ww1k"]
    try:
        thing["attendee"].remove(query.message.chat.username)
        db[db_name].update({"id": thing_id}, {"$set": {"attendee": thing["attendee"]}})
        bot.sendMessage(text="Жаль. Посмотри на другие мероприятия. Возможно, что то подойтет тебе.",
                        chat_id=query.message.chat_id)
    except Exception as exc:
        logging.exception(exc)
    connection.close()


def sign_in(bot, update, db_name, thing_id):
    if check_username(bot, update) == False:
        return
    query = get_query(bot, update)
    try:
        thing = get_thing(db_name, thing_id)
    except Exception as exp:
        logging.critical(exp)
    connection = pymongo.MongoClient(os.environ['MONGODB_URI'])
    db = connection["heroku_r261ww1k"]
    try:
        if "attendee" not in thing.keys() or query.message.chat.username not in thing["attendee"]:
            db[db_name].update({"id": thing_id}, {"$push": {"attendee": query.message.chat.username}},
                               upsert=True)
            bot.sendMessage(text="Отлично, записались!", chat_id=query.message.chat_id)
            if thing["start"]["dateTime"].split("T")[1][:5] != "00:00":
                bot.sendMessage(text="Ждем тебя {} в {}".format(thing["start"]["dateTime"].split("T")[0],
                                                                thing["start"]["dateTime"].split("T")[1][:5]),
                                chat_id=query.message.chat_id)
            else:
                bot.sendMessage(text="Ждем тебя {}".format(thing["start"]["dateTime"].split("T")[0]),
                                chat_id=query.message.chat_id)
        else:
            bot.sendMessage(
                text="Ты уже записан на тренировку. Или ты хочешь выполнять в 2 раза больше повторений!? Скажи тренеру об этом перед началом 😉",
                chat_id=query.message.chat_id)
    except Exception as exc:
        logging.exception(exc)
    connection.close()


@only_private
def attendees(bot, update):
    query = get_query(bot, update)
    kb = []
    train_att = telegram.InlineKeyboardButton(text="Кто записан на тренировки?", callback_data="501")
    event_att = telegram.InlineKeyboardButton(text="Кто записан на мероприятия?", callback_data="502")
    kb.append([train_att])
    kb.append([event_att])
    kb_markup = telegram.InlineKeyboardMarkup(kb)
    bot.sendMessage(text="Давай посмотрим", chat_id=query.message.chat.id, reply_markup=kb_markup)


def get_train_attendees(bot, update):
    query = get_query(bot, update)
    trains_list = get_things("trains")
    if trains_list:
        bot.sendMessage(chat_id=query.message.chat.id,
                        text="Список людей, записавшихся на предстоящие тренировки:")
        for train in trains_list:
            attendees_list = list_event_attendees(db_name="trains", event=train["id"])
            print_event_attendees(bot, update, train["start"]["dateTime"], train["summary"], attendees_list)
    else:
        bot.sendMessage(chat_id=query.message.chat.id, text="Нет трениировок, нет и записавшихся.")


def get_event_attendees(bot, update):
    query = get_query(bot, update)
    events_list = get_things("events")
    if events_list:
        bot.sendMessage(chat_id=query.message.chat.id,
                        text="Список людей, записавшихся на предстоящие мероприятия:")
        for event in events_list:
            attendees_list = list_event_attendees(db_name="events", event=event["id"])
            print_event_attendees(bot, update, event["start"]["dateTime"], event["summary"], attendees_list)
    else:
        bot.sendMessage(chat_id=query.message.chat.id, text="Нет мероприятий, нет и записавшихся.")


def list_event_attendees(db_name, event):
    one_event = get_thing(db_name, event)
    if "attendee" in one_event.keys() and len(one_event["attendee"]) > 0:
        attendees_list = ''
        for attendee in one_event["attendee"]:
            attendees_list = attendees_list + ' @' + attendee
        return attendees_list
    else:
        return None


def print_event_attendees(bot, update, event_start, event_summary, attendees_list):
    query = get_query(bot, update)
    if attendees_list:
        bot.sendMessage(chat_id=query.message.chat.id,
                        text="{}: {} ({}) - {}".format(event_start.split("T")[0],
                                                       event_summary,
                                                       len(attendees_list.split()), attendees_list))
    else:
        bot.sendMessage(chat_id=query.message.chat.id,
                        text="{}: {} ({}) - {}".format(event_start.split("T")[0],
                                                       event_summary,
                                                       0, 'пока никто не записался'))


def thing_loc(bot, update, db_name, thing_id):
    query = get_query(bot, update)
    thing = get_thing(db_name, thing_id)
    cal_event = dump_calendar_event(thing["organizer"]["email"], thing)
    if "location" in cal_event.keys():
        coordinates = get_coordinates(cal_event["location"])
        if bool(coordinates):
            bot.send_venue(chat_id=query.message.chat.id, latitude=coordinates["lat"],
                           longitude=coordinates["lng"],
                           title=cal_event["summary"], address=cal_event["location"])
        else:
            bot.sendMessage(text="Местоположение задано некорректно. Свяжитесь с организаторами мероприятия.",
                            chat_id=query.message.chat.id)
    else:
        bot.sendMessage(text="Местоположение не задано", chat_id=query.message.chat.id)


def event_info(bot, update, event_id):
    query = get_query(bot, update)
    event = get_thing("events", event_id)
    cal_event = dump_calendar_event(event["organizer"]["email"], event)
    if "description" in cal_event.keys():
        text = cal_event["description"]
        bot.sendMessage(text=text, chat_id=query.message.chat.id)
    else:
        bot.sendMessage(text="Описание не задано", chat_id=query.message.chat.id)


@only_private
def attendee(bot, update):
    query = get_query(bot, update)
    if check_username(bot, update) == False:
        return
    get_trains(bot, update, user=query.message.chat.username)
    get_events(bot, update, user=query.message.chat.username)


@only_private
def whiteboard(bot, update):
    query = get_query(bot, update)
    connection = pymongo.MongoClient(os.environ['MONGODB_URI'])
    db = connection["heroku_r261ww1k"]

    if db.benchmarks.find({}).count() == 0:
        bot.sendMessage(text="На данный момент у нас нет комплексов для оценки", chat_id=query.message.chat_id)
        return

    benchmarks = db.benchmarks.find({}).sort("date", pymongo.DESCENDING)
    kb = []
    for benchmark in benchmarks:
        button = telegram.InlineKeyboardButton(text=benchmark["name"], callback_data="601;" + benchmark["name"])
        kb.append([button])
    kb_markup = telegram.InlineKeyboardMarkup(kb)
    bot.sendMessage(text="Выбирай комплекс:", chat_id=query.message.chat_id, reply_markup=kb_markup)
    connection.close()


def whiteboard_results(bot, update, benchmark_name):
    query = get_query(bot, update)
    connection = pymongo.MongoClient(os.environ['MONGODB_URI'])
    db = connection["heroku_r261ww1k"]
    benchmark = db.benchmarks.find_one({"name": benchmark_name})
    bot.sendMessage(text=benchmark["name"], chat_id=query.message.chat.id)
    bot.sendMessage(text=benchmark["description"], chat_id=query.message.chat.id)
    if len(benchmark["results"]) == 0:
        bot.sendMessage(text="Еще никто не записал свой результат. Ты можешь быть первым!",
                        chat_id=query.message.chat.id)
    else:
        for man in sorted(sorted(benchmark["results"], key=lambda k: k["result"]), key=lambda m: m["mode"]):
            text = "@" + man["name"] + ":\t" + man["result"]
            if "mode" in man.keys():
                text = text + "\t(" + man["mode"] + ")"
            if "video" in man.keys():
                text = text + "\t" + man["video"]
            bot.sendMessage(text=text, chat_id=query.message.chat.id, disable_web_page_preview=True)
    connection.close()


def on_user_joins(bot, update):
    query = get_query(bot, update)
    if len(query.message.new_chat_members) > 0 and query.message.chat.type in ["group", "supergroup"]:
        user = query.message.chat.username
        log_client(bot, update)
        filedata = open("greeting.txt", "r")
        greeting = filedata.read()
        filedata.close()
        bot.sendMessage(text=greeting, chat_id=query.message.from_user.id, disable_web_page_preview=True)
        bot.sendMessage(text="Ммм... Свежее мясо!", chat_id=query.message.chat.id)
        bot.sendVideo(chat_id=query.message.chat.id, video="https://media.giphy.com/media/mDKCXYwoaoM5G/giphy.mp4")
        bot.sendMessage(
            text="@{}, рады приветстовать тебя! В нашем чате действуют правила: https://clck.ru/CVP7z".format(
                user), chat_id=query.message.chat.id)


def text_processing(bot, update):
    query = get_query(bot, update)

    # 000 - username instructions
    # 100 - trains
    # 101 - train sign out
    # 102 - train sign in
    # 105 - train attendees
    # 200 - events
    # 201 - event sign out
    # 202 - event sign in
    # 203 - event location
    # 204 - event info
    # 205 - event attendees
    # 301 - pager: next
    # 302 - pager: prev
    # 401 - wod by mode
    # 402 - wod by modality
    # 411 - wod mode: EMOM
    # 421 - wod mode: AMRAP
    # 431 - wod mode: For reps and time
    # 441 - wod mode: For time
    # 451 - wod mode: strength
    # 412 - wod modality: selection
    # 501 - attendees for trains
    # 502 - attendees for events
    # 601 - whiteboard results
    # 701 - trains activity choose
    # 702 - trains activity choose

    text = query.data.split(";")
    action = text[0]
    if len(text) > 1:
        details = text[1]
    else:
        details = None
    if action == "000":
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
    elif action == "100":
        train_details(bot, update, get_thing("trains", details))
    elif action == "101":
        sign_out(bot, update, "trains", details)
    elif action == "102":
        sign_in(bot, update, "trains", details)
    elif action == "103":
        thing_loc(bot, update, "trains", details)
    elif action == "105":
        print_event_attendees(bot, update, get_thing("trains", details)["start"]["dateTime"],
                              get_thing("trains", details)["summary"],
                              attendees_list=list_event_attendees("trains", details))
    elif action == "200":
        event_details(bot, update, get_thing("events", details))
    elif action == "201":
        sign_out(bot, update, "events", details)
    elif action == "202":
        sign_in(bot, update, "events", details)
    elif action == "203":
        thing_loc(bot, update, "events", details)
    elif action == "204":
        event_info(bot, update, details)
    elif action == "205":
        print_event_attendees(bot, update, get_thing("events", details)["start"]["dateTime"],
                              get_thing("events", details)["summary"],
                              attendees_list=list_event_attendees("events", details))
    elif action == "301":
        db_name = text[2]
        details = int(details)
        thing_list(bot, update, db_name, details - step, details)
    elif action == "302":
        db_name = text[2]
        details = int(details)
        thing_list(bot, update, db_name, details, details + step)
    elif action[0] == "4":
        if action == "401":
            wod_by_mode(bot, update)
        elif action == "403":
            wod_info(bot, update)
        elif action == "411":
            wod_emom(bot, update)
        elif action == "421":
            wod_amrap(bot, update)
        elif action == "431":
            wod_rt(bot, update)
        elif action == "441":
            wod_time(bot, update)
        elif action == "451":
            wod_strength(bot, update)
        elif action == "402":
            wod_by_modality(bot, update)
        elif action == "412":
            modality_str = details
            modality = modality_str.split(", ")
            wod_modality(bot, update, modality)
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
        wod_modality(bot, update, details)
    elif action == "501":
        get_train_attendees(bot, update)
    elif action == "502":
        get_event_attendees(bot, update)
    elif action == "601":
        whiteboard_results(bot, update, details)
    elif action == "701":
        get_trains(bot, update, activities=details)
    elif action == "702":
        get_events(bot, update, activities=details)
    else:
        logging.critical(update)


def sendall(bot, update):
    if check_username(bot, update) == False:
        return
    query = get_query(bot, update)
    if query.message.chat.username in ["ya_thatguy", "Ilyazdorenko", "Simple_kap"]:
        connection = pymongo.MongoClient(os.environ['MONGODB_URI'])
        db = connection["heroku_r261ww1k"]
        client_list = json.loads(json_util.dumps(db["clients"].find({})))
        for client in client_list:
            logging.info(client["username"])
            text = query.message.text[9:]
            try:
                bot.sendMessage(text=text, chat_id=client["chat_id"])
                logging.info("\tMessage sent")
            except Exception as exc:
                logging.critical(client["username"])
                logging.critical("\t@{}: message WAS NOT sent".format(client["username"]))
                logging.critical(exc)
            sleep(1)
        connection.close()
    else:
        bot.sendMessage(text="Не хочешь выполнять ты команду эту... 👻", chat_id=query.message.chat.id)


def main():
    logging.basicConfig(level=logging.WARN)

    # Set up handlers

    start_handler = CommandHandler("start", start)
    dispatcher.add_handler(start_handler)

    train_handler = RegexHandler("^(🏃 Треня)$", get_trains_activities)
    dispatcher.add_handler(train_handler)

    attendees_handler = RegexHandler("^(🙏 Участники)$", attendees)
    dispatcher.add_handler(attendees_handler)

    attendee_handler = RegexHandler("^(💪 Мои тренировки)$", attendee)
    dispatcher.add_handler(attendee_handler)

    event_handler = RegexHandler("^(🏅 Мероприятия)$", get_events_activities)
    dispatcher.add_handler(event_handler)

    wod_handler = RegexHandler("^(🏋 WOD)$", wod)
    dispatcher.add_handler(wod_handler)

    whiteboard_handler = RegexHandler("^(🏁 Соревнования)$", whiteboard)
    dispatcher.add_handler(whiteboard_handler)

    message_handler = CallbackQueryHandler(text_processing)
    dispatcher.add_handler(message_handler)

    admin_handler = CommandHandler("sendall", sendall)
    dispatcher.add_handler(admin_handler)

    text_handler = MessageHandler(Filters.all, on_user_joins)
    dispatcher.add_handler(text_handler)

    # Poll user actions

    updater.start_polling()

    starttime = time()

    while True:
        # Dump events from Google Calendar and update MongoDB

        train_calendar = os.environ['TRAIN_CALENDAR_ID']
        trains = dump_calendar(train_calendar, 10)
        dump_mongodb("trains", trains)

        # Dump events from Google Calendar and update MongoDB

        events_calendar = os.environ['EVENTS_CALENDAR_ID']
        events = dump_calendar(events_calendar, 30)
        dump_mongodb("events", events)

        # Update activities for trains / events

        activities.create_list()

        # Sleep to 60 secs

        sleep(60.0 - ((time() - starttime) % 60.0))

    updater.idle()

if __name__ == '__main__':
    main()
