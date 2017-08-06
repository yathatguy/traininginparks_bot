# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function

import logging

import telegram
from telegram.ext import CommandHandler, ConversationHandler, RegexHandler
from telegram.ext import Updater

from clients import log_client
from mongodata import get_events

# Set up Updater and Dispatcher

# updater = Updater(token=os.environ['TOKEN'])
updater = Updater('370932219:AAGXeZFMAuY9vJYSt5qns274i1von1cvY4I')
updater.stop()
dispatcher = updater.dispatcher

TRAIN, EVENT = range(2)


def start(bot, update):
    """
    Send welcome message to new users. 
    :return: N/A
    """

    if update.message.chat.type in ["group", "supergroup", "channel"]:
        bot.sendMessage(text="Не-не, в группах я отказываюсь работать, я стеснительный. Пиши мне только тет-а-тет 😉",
                        chat_id=update.message.chat.id)
        return

    if update.message.chat.username == "":
        kb = []
        button = telegram.InlineKeyboardButton(text="Инструкции", callback_data="401")
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

    return TRAIN


def keyboard():
    """
    Create keyboard markup object with buttons
    :return: keyboard markup object
    """

    kb = [[telegram.KeyboardButton('/train'), telegram.KeyboardButton('/attendees')],
          [telegram.KeyboardButton('/calendar')],
          [telegram.KeyboardButton('/wod'), telegram.KeyboardButton('/whiteboard')]]
    kb_markup = telegram.ReplyKeyboardMarkup(kb, resize_keyboard=True)

    return kb_markup


def train(bot, update):
    """
    Get a NUM of upcoming trains and offer to attend any
    :param bot: telegram API object
    :param update: telegram API state
    :return: N/A
    """

    logging.critical("train")
    if update.message.chat.type in ["group", "supergroup", "channel"]:
        bot.sendMessage(text="Не-не, в группах я отказываюсь работать, я стеснительный. Пиши мне только тет-а-тет 😉",
                        chat_id=update.message.chat.id)
        return

    trains = get_events("trains")
    kb = []
    if trains:
        iter = 0
        step = 5
        next = iter + step
        for train in trains[iter:next]:
            button = text = train["start"]["date"] + ":\t" + train["summary"]
            kb.append([button])
            iter += 1
        kb_markup = telegram.ReplyKeyboardMarkup(kb, one_time_keyboard=True)
        bot.sendMessage(text="Расписание следующих тренировок:", chat_id=update.message.chat.id, reply_markup=kb_markup)
        logging.critical("request for train")
        return TRAIN
    else:
        bot.sendMessage(bot, update, text="Пока тренировки не запланированы. Восстанавливаемся!",
                        chat_id=update.message.chat.id)
        logging.critical("no trains")
        kb = []
        bot.sendMessage(text="Пока тренировки не запланированы. Восстанавливаемся!", chat_id=update.message.chat.id,
                        reply_markup=keyboard())
        return ConversationHandler.END


def train_details(bot, update):
    logging.critical("train_details")
    logging.critical(update.message)


def cancel(bot, update):
    logging.critical("cancel")
    bot.sendMessage(text="Что то ты не то ввел...", chat_id=update.message.chat.id)
    return ConversationHandler.END


def main():
    logging.info('start trainigninparks bot script')

    # Set up handlers

    start_handler = CommandHandler("start", start)
    dispatcher.add_handler(start_handler)

    train_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("train", train)],
        states={
            TRAIN: [RegexHandler("^2017", train_details), CommandHandler('cancel', cancel)],
            TRAIN: [RegexHandler("^2017", train_details), CommandHandler('cancel', cancel)]
        },

        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    )
    dispatcher.add_handler(train_conv_handler)

    # Poll user actions

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
