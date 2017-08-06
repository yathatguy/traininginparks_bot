# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function

import json
import logging
import os
from time import time, sleep

import pymongo
import telegram
from bson import json_util
from telegram.ext import CommandHandler, ConversationHandler, RegexHandler, CallbackQueryHandler
from telegram.ext import Updater

from clients import log_client
from google_calendar import dump_calendar_event, dump_calendar, dump_mongodb
from maps_api import get_coordinates
from mongodata import get_things, get_thing
from wod import wod, wod_info, wod_by_mode, wod_by_modality, wod_amrap, wod_emom, wod_rt, wod_strength, wod_time, \
    wod_modality

# Set up Updater and Dispatcher

updater = Updater(token=os.environ['TOKEN'])
updater.stop()
dispatcher = updater.dispatcher

step = 5


def start(bot, update):
    if update.message.chat.type in ["group", "supergroup", "channel"]:
        bot.sendMessage(text="Не-не, в группах я отказываюсь работать, я стеснительный. Пиши мне только тет-а-тет 😉",
                        chat_id=update.message.chat.id)
        return

    if update.message.chat.username == "":
        kb = []
        button = telegram.InlineKeyboardButton(text="Инструкции", callback_data="000")
        kb.append([button])
        kb_markup = telegram.InlineKeyboardMarkup(kb)
        kb_start = [[telegram.KeyboardButton('/start')]]
        kb_markup_start = telegram.ReplyKeyboardMarkup(kb_start, resize_keyboard=False)
        bot.sendMessage(
            text="Привет!\n\nК сожалению Вы не установили username для своего telegram-аккаунта, и поэтому бот не сможет корректно для Вас работать.",
            chat_id=update.message.chat.id,
            reply_markup=kb_markup_start)
        bot.sendMessage(text="Хочешь посмотреть на инструкции, как это быстро и легко сделать?",
                        chat_id=update.message.chat.id, reply_markup=kb_markup)
    else:
        kb_markup = keyboard()
        bot.send_message(chat_id=update.message.chat.id,
                         text="Добро пожаловать, @{}!".format(update.message.chat.username),
                         reply_markup=kb_markup)
        log_client(bot, update)


def keyboard():
    kb = [[telegram.KeyboardButton('🏃 Треня'), telegram.KeyboardButton('🏅 Мероприятия')],
          [telegram.KeyboardButton('🙏 Участники'), telegram.KeyboardButton('💪 Мои тренировки')],
          [telegram.KeyboardButton('🏋 WOD'), telegram.KeyboardButton('🏁 Соревнования')]]
    kb_markup = telegram.ReplyKeyboardMarkup(kb, resize_keyboard=True)

    return kb_markup


def get_trains(bot, update):
    if update.message.chat.type in ["group", "supergroup", "channel"]:
        bot.sendMessage(text="Не-не, в группах я отказываюсь работать, я стеснительный. Пиши мне только тет-а-тет 😉",
                        chat_id=update.message.chat.id)
        return

    trains_list = get_things("trains")
    kb = []
    if trains_list:
        iter = 0
        next = iter + step
        for train in trains_list[iter:next]:
            button = telegram.InlineKeyboardButton(text=train["start"]["date"] + ":\t" + train["summary"],
                                                   callback_data="100;" + train["id"])
            kb.append([button])
            iter += 1
        kb_markup = telegram.InlineKeyboardMarkup(kb)
        bot.sendMessage(text="Расписание следующих тренировок:", chat_id=update.message.chat.id, reply_markup=kb_markup)
    else:
        bot.sendMessage(text="Пока тренировки не запланированы. Восстанавливаемся!", chat_id=update.message.chat.id,
                        reply_markup=keyboard())


def get_events(bot, update):
    if update.message.chat.type in ["group", "supergroup", "channel"]:
        bot.sendMessage(text="Не-не, в группах я отказываюсь работать, я стеснительный. Пиши мне только тет-а-тет 😉",
                        chat_id=update.message.chat.id)
        return
    db_name = "events"
    events_list = get_things(db_name)
    if events_list:
        iter = 0
        step = 5
        next = iter + step
        thing_list(bot, update, db_name, iter, next)
    else:
        bot.sendMessage(text="Пока тренировки не запланированы. Восстанавливаемся!", chat_id=update.message.chat.id,
                        reply_markup=keyboard())


def thing_list(bot, update, db_name, iter, next):
    try:
        chat_id = update.message.chat.id
    except:
        chat_id = update.callback_query.message.chat.id
    things = get_things(db_name)
    thing_list = things[iter:next]
    kb = []
    for thing in thing_list:
        if db_name == "trains":
            button = telegram.InlineKeyboardButton(text=thing["start"]["date"] + ":\t" + thing["summary"],
                                                   callback_data="200;" + thing["id"])
        elif db_name == "events":
            button = telegram.InlineKeyboardButton(text=thing["start"]["date"] + ":\t" + thing["summary"],
                                                   callback_data="300;" + thing["id"])
        else:
            return []
        kb.append([button])
        iter += 1
    kb.append(pager(bot, update, db_name, iter, step, next))
    kb_markup = telegram.InlineKeyboardMarkup(kb)
    bot.sendMessage(text="Расписание следующих мероприятий:", chat_id=chat_id, reply_markup=kb_markup)
    return thing_list


def pager(bot, update, db_name, iter, step, next):
    if iter - step == 0:
        button_next = telegram.InlineKeyboardButton(text=">", callback_data="302;" + str(next) + ";" + db_name)
        buttons = []
        buttons.append(button_next)
    elif len(get_things(db_name)) > next:
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
    query = update.callback_query.message
    kb = []
    if "attendee" in train.keys() and query.chat.username in train["attendee"]:
        text_sign = "✖️ Не смогу прийти"
        signup = telegram.InlineKeyboardButton(text=text_sign, callback_data="101;" + str(train["id"]))
    else:
        text_sign = "✔️ Записаться"
        signup = telegram.InlineKeyboardButton(text=text_sign, callback_data="102;" + str(train["id"]))
    text_loc = "Где это?"
    location = telegram.InlineKeyboardButton(text=text_loc, callback_data="103;" + str(train["id"]))
    kb.append([signup, location])
    kb_markup = telegram.InlineKeyboardMarkup(kb)
    bot.sendMessage(text="Детали по событию: {} - {}".format(train["start"]["date"], train["summary"]),
                    chat_id=query.chat.id, reply_markup=kb_markup)


def event_details(bot, update, event):
    query = update.callback_query.message
    kb = []
    if "attendee" in event.keys() and query.chat.username in event["attendee"]:
        text_sign = "✖️ Не смогу прийти"
        signup = telegram.InlineKeyboardButton(text=text_sign, callback_data="201;" + str(event["id"]))
    else:
        text_sign = "✔️ Записаться"
        signup = telegram.InlineKeyboardButton(text=text_sign, callback_data="202;" + str(event["id"]))
    text_loc = "Где это?"
    location = telegram.InlineKeyboardButton(text=text_loc, callback_data="203;" + str(event["id"]))
    kb.append([signup, location])
    text_info = "Информация"
    info = telegram.InlineKeyboardButton(text=text_info, callback_data="204;" + str(event["id"]))
    kb.append([info])
    kb_markup = telegram.InlineKeyboardMarkup(kb)
    bot.sendMessage(text="Детали по событию: {} - {}".format(event["start"]["date"], event["summary"]),
                    chat_id=query.chat.id, reply_markup=kb_markup)


def sign_out(bot, update, db_name, thing_id):
    thing = get_thing(db_name, thing_id)
    connection = pymongo.MongoClient(os.environ['MONGODB_URI'])
    db = connection["heroku_r261ww1k"]
    try:
        thing["attendee"].remove(update.callback_query.message.chat.username)
        db.events.update({"id": thing_id}, {"$set": {"attendee": thing["attendee"]}})
        bot.sendMessage(text="Жаль. Посмотри на другие мероприятия. Возможно, что то подойтет тебе.",
                        chat_id=update.callback_query.message.chat_id)
    except Exception as exc:
        logging.exception(exc)
    connection.close()


def sign_in(bot, update, db_name, thing_id):
    thing = get_thing(db_name, thing_id)
    connection = pymongo.MongoClient(os.environ['MONGODB_URI'])
    db = connection["heroku_r261ww1k"]
    if "attendee" not in thing.keys() or update.callback_query.message.chat.username not in thing["attendee"]:
        db[db_name].update({"id": thing_id}, {"$push": {"attendee": update.callback_query.message.chat.username}},
                           upsert=True)
        bot.sendMessage(text="Отлично, записались!", chat_id=update.callback_query.message.chat_id)
        if thing["start"]["dateTime"].split("T")[1][:5] != "00:00":
            bot.sendMessage(text="Ждем тебя {} в {}".format(thing["start"]["dateTime"].split("T")[0],
                                                            thing["start"]["dateTime"].split("T")[1][:5]),
                            chat_id=update.callback_query.message.chat_id)
        else:
            bot.sendMessage(text="Ждем тебя {}".format(thing["start"]["dateTime"].split("T")[0]),
                            chat_id=update.callback_query.message.chat_id)
    else:
        bot.sendMessage(
            text="Ты уже записан на тренировку. Или ты хочешь выполнять в 2 раза больше повторений!? Скажи тренеру об этом перед началом 😉",
            chat_id=update.callback_query.message.chat_id)
    connection.close()


def attendees(bot, update):
    if update.message.chat.type in ["group", "supergroup", "channel"]:
        bot.sendMessage(text="Не-не, в группах я отказываюсь работать, я стеснительный. Пиши мне только тет-а-тет 😉",
                        chat_id=update.message.chat.id)
        return

    kb = []
    train_att = telegram.InlineKeyboardButton(text="Кто записан на тренировки?", callback_data="501")
    event_att = telegram.InlineKeyboardButton(text="Кто записан на мероприятия?", callback_data="502")
    kb.append([train_att])
    kb.append([event_att])
    kb_markup = telegram.InlineKeyboardMarkup(kb)
    bot.sendMessage(text="Давай посмотрим", chat_id=update.message.chat.id, reply_markup=kb_markup)


def get_train_attendees(bot, update):
    trains_list = get_things("trains")
    if trains_list:
        bot.sendMessage(chat_id=update.callback_query.message.chat.id,
                        text="Список людей, записавшихся на предстоящие тренировки:")
        for train in trains_list:
            if "attendee" in train.keys() and len(train["attendee"]) > 0:
                attendees_list = ''
                for attendee in train["attendee"]:
                    attendees_list = attendees_list + ' @' + attendee
                bot.sendMessage(chat_id=update.callback_query.message.chat.id,
                                text="{}: {} ({}) - {}".format(train["start"]["dateTime"].split("T")[0],
                                                               train["summary"],
                                                               len(train["attendee"]), attendees_list))
            else:
                bot.sendMessage(chat_id=update.callback_query.message.chat.id,
                                text="{}: {} ({}) - {}".format(train["start"]["dateTime"].split("T")[0],
                                                               train["summary"],
                                                               0, 'пока никто не записался'))
    else:
        bot.sendMessage(chat_id=update.callback_query.message.chat.id, text="Нет трениировок, нет и записавшихся.")


def get_event_attendees(bot, update):
    events_list = get_things("events")
    if events_list:
        bot.sendMessage(chat_id=update.callback_query.message.chat.id,
                        text="Список людей, записавшихся на предстоящие мероприятия:")
        for event in events_list:
            if "attendee" in event.keys() and len(event["attendee"]) > 0:
                attendees_list = ''
                for attendee in event["attendee"]:
                    attendees_list = attendees_list + ' @' + attendee
                bot.sendMessage(chat_id=update.callback_query.message.chat.id,
                                text="{}: {} ({}) - {}".format(event["start"]["dateTime"].split("T")[0],
                                                               event["summary"],
                                                               len(event["attendee"]), attendees_list))
            else:
                bot.sendMessage(chat_id=update.callback_query.message.chat.id,
                                text="{}: {} ({}) - {}".format(event["start"]["dateTime"].split("T")[0],
                                                               event["summary"],
                                                               0, 'пока никто не записался'))
    else:
        bot.sendMessage(chat_id=update.callback_query.message.chat.id, text="Нет мероприятий, нет и записавшихся.")


def thing_loc(bot, update, db_name, thing_id):
    thing = get_thing(db_name, thing_id)
    cal_event = dump_calendar_event(thing["organizer"]["email"], thing)
    if "location" in cal_event.keys():
        coordinates = get_coordinates(cal_event["location"])
        if bool(coordinates):
            bot.send_venue(chat_id=update.callback_query.message.chat.id, latitude=coordinates["lat"],
                           longitude=coordinates["lng"],
                           title=cal_event["summary"], address=cal_event["location"])
        else:
            bot.sendMessage(text="Местоположение задано некорректно. Свяжитесь с организаторами мероприятия.",
                            chat_id=update.callback_query.message.chat.id)
    else:
        bot.sendMessage(text="Местоположение не задано", chat_id=update.callback_query.message.chat.id)


def event_info(bot, update, event_id):
    event = get_thing("events", event_id)
    cal_event = dump_calendar_event(event["organizer"]["email"], event)
    if "description" in cal_event.keys():
        text = cal_event["description"]
        bot.sendMessage(text=text, chat_id=update.callback_query.message.chat.id)
    else:
        bot.sendMessage(text="Описание не задано", chat_id=update.callback_query.message.chat.id)


def attendee(bot, update):
    if update.message.chat.type in ["group", "supergroup", "channel"]:
        bot.sendMessage(text="Не-не, в группах я отказываюсь работать, я стеснительный. Пиши мне только тет-а-тет 😉",
                        chat_id=update.message.chat.id)
        return
    bot.sendMessage(text="Твои тренировки:", chat_id=update.message.chat.id)
    trains = get_things("trains")
    if trains:
        count = 0
        for train in trains:
            if "attendee" in train.keys() and update.message.chat.username in train["attendee"]:
                bot.sendMessage(text=train["start"]["date"] + ":\t" + train["summary"],
                                chat_id=update.message.chat.id,
                                reply_markup=keyboard())
                count = + 1
            else:
                pass
        if count == 0:
            bot.sendMessage(text="Ты не записан(а) ни на одну из тренировок.", chat_id=update.message.chat.id)
    else:
        bot.sendMessage(text="Пока тренировки не запланированы. Восстанавливаемся!", chat_id=update.message.chat.id,
                        reply_markup=keyboard())
    bot.sendMessage(text="Твои мероприятия:", chat_id=update.message.chat.id)
    events = get_things("events")
    if events:
        count = 0
        for event in events:
            if "attendee" in event.keys() and update.message.chat.username in event["attendee"]:
                bot.sendMessage(text=event["start"]["date"] + ":\t" + event["summary"],
                                chat_id=update.message.chat.id,
                                reply_markup=keyboard())
                count = + 1
            else:
                pass
        if count == 0:
            bot.sendMessage(text="Ты не записан(а) ни на одно из мероприятий.", chat_id=update.message.chat.id)
    else:
        bot.sendMessage(text="Пока тренировки не запланированы. Восстанавливаемся!", chat_id=update.message.chat.id,
                        reply_markup=keyboard())


def whiteboard(bot, update):
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
        button = telegram.InlineKeyboardButton(text=benchmark["name"], callback_data="601;" + benchmark["name"])
        kb.append([button])
    kb_markup = telegram.InlineKeyboardMarkup(kb)
    bot.sendMessage(text="Выбирай комплекс:", chat_id=update.message.chat_id, reply_markup=kb_markup)
    connection.close()


def whiteboard_results(bot, update, benchmark_name):
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


def on_user_joins(bot, update):
    if len(update.message.new_chat_members) > 0 and update.message.chat.type in ["group", "supergroup"]:
        log_client(bot, update)
        bot.sendMessage(text="Ммм... Свежее мясо!", chat_id=update.message.chat.id)
        bot.sendVideo(chat_id=update.message.chat.id, video="https://media.giphy.com/media/mDKCXYwoaoM5G/giphy.mp4")


def text_processing(bot, update):
    # 000 - username instructions
    # 100 - trains
    # 101 - event sign out
    # 102 - event sign in
    # 200 - events
    # 201 - event sign out
    # 202 - event sign in
    # 203 - event location
    # 204 - event info
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

    text = update.callback_query.data.split(";")
    action = text[0]
    if len(text) > 1:
        details = text[1]
    else:
        details = None
    if action == "000":
        bot.sendMessage(text="Открываем приложение.", chat_id=update.callback_query.message.chat_id)
        bot.sendMessage(text="Выбираем [Настройки].", chat_id=update.callback_query.message.chat_id)
        bot.sendPhoto(
            photo="http://telegram-online.ru/wp-content/uploads/2015/11/kak-ustanovit-ili-pomenyat-imya-v-telegram-1-576x1024.jpg",
            chat_id=update.callback_query.message.chat_id)
        bot.sendMessage(text="Кликаем на надпись 'Не задано'.", chat_id=update.callback_query.message.chat_id)
        bot.sendPhoto(
            photo="http://telegram-online.ru/wp-content/uploads/2015/11/kak-ustanovit-ili-pomenyat-imya-v-telegram-2-576x1024.jpg",
            chat_id=update.callback_query.message.chat_id)
        bot.sendMessage(text="Пишем подходящий ник и жмем галочку в правом верхнем углу.",
                        chat_id=update.callback_query.message.chat_id)
        bot.sendPhoto(
            photo="http://telegram-online.ru/wp-content/uploads/2015/11/kak-ustanovit-ili-pomenyat-imya-v-telegram-3.jpg",
            chat_id=update.callback_query.message.chat_id)
    elif action == "101":
        sign_out(bot, update, "trains", details)
    elif action == "102":
        sign_in(bot, update, "trains", details)
    elif action == "103":
        thing_loc(bot, update, "trains", details)
    elif action == "201":
        sign_out(bot, update, "events", details)
    elif action == "202":
        sign_in(bot, update, "events", details)
    elif action == "203":
        thing_loc(bot, update, "events", details)
    elif action == "204":
        event_info(bot, update, details)
    elif action == "200":
        train_details(bot, update, get_thing("trains", details))
    elif action == "300":
        event_details(bot, update, get_thing("events", details))
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
    else:
        logging.critical(update)


def sendall(bot, update):
    if update.message.chat.username in ["ya_thatguy"]:
        connection = pymongo.MongoClient(os.environ['MONGODB_URI'])
        db = connection["heroku_r261ww1k"]
        client_list = json.loads(json_util.dumps(db["clients"].find({})))
        for client in client_list:
            text = update.message.text[9:]
            bot.sendMessage(text=text, chat_id=client["chat_id"])
            sleep(1)
        connection.close()
    else:
        bot.sendMessage(text="Не хочешь выполнять ты команду эту... 👻", chat_id=update.message.chat.id)


def cancel(bot, update):
    bot.sendMessage(text="Что то ты не то ввел...", chat_id=update.message.chat.id)
    return ConversationHandler.END


def main():

    # Set up handlers

    start_handler = CommandHandler("start", start)
    dispatcher.add_handler(start_handler)

    train_handler = RegexHandler("^(🏃 Треня)$", get_trains)
    dispatcher.add_handler(train_handler)

    attendees_handler = RegexHandler("^(🙏 Участники)$", attendees)
    dispatcher.add_handler(attendees_handler)

    attendee_handler = RegexHandler("^(💪 Мои тренировки)$", attendee)
    dispatcher.add_handler(attendee_handler)

    event_handler = RegexHandler("^(🏅 Мероприятия)$", get_events)
    dispatcher.add_handler(event_handler)

    wod_handler = RegexHandler("^(🏋 WOD)$", wod)
    dispatcher.add_handler(wod_handler)

    whiteboard_handler = RegexHandler("^(🏁 Соревнования)$", whiteboard)
    dispatcher.add_handler(whiteboard_handler)

    message_handler = CallbackQueryHandler(text_processing)
    dispatcher.add_handler(message_handler)

    admin_handler = CommandHandler("sendall", sendall)
    dispatcher.add_handler(admin_handler)

    # Poll user actions

    updater.start_polling()
    updater.idle()

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

        # Sleep to 60 secs

        sleep(60.0 - ((time() - starttime) % 60.0))



if __name__ == '__main__':
    main()
