# -*- coding: utf-8 -*-

from __future__ import unicode_literals, division, print_function

import os

import pymongo
import telegram

connection = pymongo.MongoClient(os.environ['MONGODB_URI'])
db = connection["heroku_r261ww1k"]

if "clients" not in db.collection_names() or db.clients.count() == 0:
    db.clients.insert({"username": "", "name": "", "surname": ""})


def log_client(bot, update):
    client = {"username": update.message.chat.username}
    client_db = db.clients.find_one({"username": client["username"]})
    if client_db is None:
        if update.message.chat.first_name:
            client["name"] = update.message.chat.first_name
        else:
            client["name"] = None
        if update.message.chat.last_name:
            client["surname"] = update.message.chat.last_name
        else:
            update.message.chat.last_name = None
        if update.message.chat.id:
            client["chat_id"] = update.message.chat.id
        else:
            client["chat_id"] = None
        db.clients.insert(client)


def check_username(bot, update):
    query = get_query(bot, update)
    if not query.message.chat.username or query.message.chat.username == "":
        kb = []
        button = telegram.InlineKeyboardButton(text="Инструкции", callback_data="000")
        kb.append([button])
        kb_markup = telegram.InlineKeyboardMarkup(kb)
        kb_start = [[telegram.KeyboardButton('/start')]]
        kb_markup_start = telegram.ReplyKeyboardMarkup(kb_start, resize_keyboard=False)
        bot.sendMessage(
            text="Привет!\n\nК сожалению Вы не установили username для своего telegram-аккаунта, и поэтому бот не сможет корректно для Вас работать.",
            chat_id=query.message.chat.id,
            reply_markup=kb_markup_start)
        bot.sendMessage(text="Хочешь посмотреть на инструкции, как это быстро и легко сделать?",
                        chat_id=query.message.chat.id, reply_markup=kb_markup)
        return False
    else:
        return True


def get_query(bot, update):
    if update.callback_query:
        query = update.callback_query
    else:
        query = update
    return query


def main():
    pass


if __name__ == '__main__':
    main()
