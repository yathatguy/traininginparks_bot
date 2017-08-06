# -*- coding: utf-8 -*-

from __future__ import unicode_literals, division, print_function

import itertools
import os
from random import randint

import pymongo
import telegram

connection = pymongo.MongoClient(os.environ['MONGODB_URI'])
db = connection["heroku_r261ww1k"]


# connection = pymongo.MongoClient()
# db = connection["wod"]

def wod(bot, update):
    if update.message.chat.type in ["group", "supergroup", "channel"]:
        bot.sendMessage(text="Не-не, в группах я отказываюсь работать, я стеснительный. Пиши мне только тет-а-тет 😉",
                        chat_id=update.message.chat.id)
        return

    bot.send_message(chat_id=update.message.chat.id, text="Давай подберем тебе териновку!")
    kb = []
    mode_button = telegram.InlineKeyboardButton(text="by mode", callback_data="401")
    modality_button = telegram.InlineKeyboardButton(text="by modailty", callback_data="402")
    info_button = telegram.InlineKeyboardButton(text="Информация", callback_data="403")
    kb.append([mode_button, modality_button])
    kb.append([info_button])
    kb_markup = telegram.InlineKeyboardMarkup(kb)
    update.message.reply_text(text="По какому принципу будем искать?",
                              reply_markup=kb_markup)


def wod_by_mode(bot, update):
    kb = []
    emom_button = telegram.InlineKeyboardButton(text="EMOM", callback_data="411")
    amrap_button = telegram.InlineKeyboardButton(text="AMRAP", callback_data="421")
    rt_button = telegram.InlineKeyboardButton(text="For reps and time", callback_data="431")
    time_button = telegram.InlineKeyboardButton(text="For time", callback_data="441")
    strength_button = telegram.InlineKeyboardButton(text="Strength", callback_data="451")
    kb.append([emom_button, amrap_button])
    kb.append([rt_button])
    kb.append([time_button, strength_button])
    kb_markup = telegram.InlineKeyboardMarkup(kb)
    bot.send_message(chat_id=update.callback_query.message.chat.id, text="Выбирай:", reply_markup=kb_markup)


def wod_by_modality(bot, update):
    trains = db.wod.find({})

    modality_list = list()
    for train in trains:
        train["modality"].sort(key=lambda s: (-len(s), s))
        modality_list.append(train["modality"])
    kb = []
    buttons = []
    for modality in itertools.groupby(sorted(modality_list)):
        modality_str = ", ".join(modality[0])
        button = telegram.InlineKeyboardButton(text=modality_str, callback_data="412;" + modality_str)
        if len(buttons) % 3 != 0:
            buttons.append(button)
        else:
            kb.append(buttons)
            buttons = []
            buttons.append(button)
    kb.append(buttons)
    kb_markup = telegram.InlineKeyboardMarkup(kb)
    bot.send_message(chat_id=update.callback_query.message.chat.id, text="Выбирай:", reply_markup=kb_markup)


def wod_info(bot, update):
    bot.send_message(chat_id=update.callback_query.message.chat.id, text="""mode - условия для выполнения комплекса.

    EMOM - Every Minute of the Minute – каждую минуту в начале минуты. Необходимо выполнять определенное количество заданных упражнений.

    For reps (AMRAP) - As Many Repetitions As Possible – выполнить как можно больше повторений/раундов за отведенное время.

    For reps and time - на количество повторений и время.

    For time - на время.

    strength - силовое выполнение.""")

    bot.send_message(chat_id=update.callback_query.message.chat.id, text="""modality - вид нагрузки.

    Исходя из этих задач тренировки делятся на три модальности:

    Модальность W
    К тяжелоатлетическим упражнениям относятся рывок и толчок штанги, всевозможные тяги: становая, румынская и прочие, все виды жимов: жим лежа, армейский жим и остальные и конечно же, все виды приседаний.

    Модальность G
    К гимнастике относятся различные упражнения, которые выполняются с собственным весом. К ним относятся как обычные отжимания, подтягивания и упражнения на пресс, так и высокотехничные упражнения в стойке на руках и упражненния на кольцах.

    Модальность M
    Кардио упражнения включают бег на стадионе и велодорожке, греблю на тренажере, велосипед и любой другой кардио тренажер.""")


def wod_text(bot, update, train, func):
    kb = []
    repeat_button = telegram.InlineKeyboardButton(text="Повторить поиск?", callback_data=func)
    kb.append([repeat_button])
    kb_markup = telegram.InlineKeyboardMarkup(kb)

    bot.send_message(chat_id=update.callback_query.message.chat.id, text="Название: " + train["name"])
    bot.send_message(chat_id=update.callback_query.message.chat.id, text="Условия: " + train["mode"])
    bot.send_message(chat_id=update.callback_query.message.chat.id,
                     text="Модальность: " + ", ".join(map(str, train["modality"])))
    bot.send_message(chat_id=update.callback_query.message.chat.id, text="Описание: " + train["description"])
    movements = str()
    for movement in train["exces"]:
        if type(movement["weights"]) is dict:
            movements = movements + movement["reps"] + "\t" + movement["movements"] + "\t" + movement["weights"][
                "men"] + "/" + movement["weights"]["women"] + "\n"
        else:
            movements = movements + movement["reps"] + "\t" + movement["movements"] + "\t" + movement[
                "weights"] + "\t" + "\n"
    if train["inventory"] == None:
        bot.send_message(chat_id=update.callback_query.message.chat.id, text="Движения:\n" + movements,
                         reply_markup=kb_markup)
    else:
        bot.send_message(chat_id=update.callback_query.message.chat.id, text="Движения:\n" + movements)
        bot.send_message(chat_id=update.callback_query.message.chat.id,
                         text="Вам потребуется: " + ", ".join(map(str, train["inventory"])), reply_markup=kb_markup)


def wod_emom(bot, update):
    trains = db.wod.find({"mode": "EMOM"})
    randint(0, trains.count())
    train = db.wod.find({"mode": "EMOM"}).limit(-1).skip(randint(0, trains.count())).next()
    wod_text(bot, update, train, "wod_emom")


def wod_amrap(bot, update):
    trains = db.wod.find({"mode": "For Reps (AMRAP)"})
    randint(0, trains.count())
    train = db.wod.find({"mode": "For Reps (AMRAP)"}).limit(-1).skip(randint(0, trains.count())).next()
    wod_text(bot, update, train, "wod_amrap")


def wod_rt(bot, update):
    trains = db.wod.find({"mode": "For Reps and Time"})
    randint(0, trains.count())
    train = db.wod.find({"mode": "For Reps and Time"}).limit(-1).skip(randint(0, trains.count())).next()
    wod_text(bot, update, train, "wod_rt")


def wod_time(bot, update):
    trains = db.wod.find({"mode": "For Time"})
    randint(0, trains.count())
    train = db.wod.find({"mode": "For Time"}).limit(-1).skip(randint(0, trains.count())).next()
    wod_text(bot, update, train, "wod_time")


def wod_strength(bot, update):
    trains = db.wod.find({"mode": "Strength"})
    randint(0, trains.count())
    train = db.wod.find({"mode": "Strength"}).limit(-1).skip(randint(0, trains.count())).next()
    wod_text(bot, update, train, "wod_strength")


def wod_modality(bot, update, modality):
    trains = db.wod.find({"modality": modality})
    randint(0, trains.count())
    train = db.wod.find({"modality": modality}).limit(-1).skip(randint(0, trains.count())).next()
    wod_text(bot, update, train, "wod_modality" + ";" + ", ".join(map(str, modality)))
