# -*- coding: utf-8 -*-

from __future__ import unicode_literals, division, print_function

import os

import pymongo
import telegram


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
        button = telegram.InlineKeyboardButton(text=benchmark["name"], callback_data="501;" + benchmark["name"])
        kb.append([button])
    kb_markup = telegram.InlineKeyboardMarkup(kb)
    update.message.reply_text(text="Выбирай комплекс:", reply_markup=kb_markup)
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
    kb = []
    button = telegram.InlineKeyboardButton(text="твой результат", callback_data="502;" + benchmark["name"])
    kb.append([button])
    kb_markup = telegram.InlineKeyboardMarkup(kb)

    update.callback_query.message.reply_text(text="Ну что ж, давай добавим твой результат. Пришли мне его.",
                                             reply_markup=kb_markup)


def whiteboard_add(bot, update, benchmark_name):
    connection = pymongo.MongoClient(os.environ['MONGODB_URI'])
    db = connection["heroku_r261ww1k"]
    benchmark = db.benchmarks.find_one({"name": benchmark_name})
    db.benchmarks.update({"name": benchmark["name"]},
                         {"$pull": {"results": {"name": update.callback_query.message.chat.username}}})
    db.benchmarks.update({"name": benchmark["name"]}, {"$push": {
        "results": {"$each": [{"name": update.callback_query.message.chat.username, "result": "0:00"}], "$sort": 1}}})
    return TIME
