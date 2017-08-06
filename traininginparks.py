# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function

import logging

import telegram
from telegram.ext import CommandHandler, ConversationHandler, RegexHandler, CallbackQueryHandler
from telegram.ext import Updater

from clients import log_client
from mongodata import get_things

# Set up Updater and Dispatcher

# updater = Updater(token=os.environ['TOKEN'])
updater = Updater('370932219:AAGXeZFMAuY9vJYSt5qns274i1von1cvY4I')
updater.stop()
dispatcher = updater.dispatcher

TRAIN, EVENT = range(2)
step = 5


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

    return TRAIN


def keyboard():
    """
    Create keyboard markup object with buttons
    :return: keyboard markup object
    """

    kb = [[telegram.KeyboardButton('🏃 Треня'), telegram.KeyboardButton('/attendees')],
          [telegram.KeyboardButton('🏅 Мероприятия')],
          [telegram.KeyboardButton('/wod'), telegram.KeyboardButton('/whiteboard')]]
    kb_markup = telegram.ReplyKeyboardMarkup(kb, resize_keyboard=True)

    return kb_markup


def trains(bot, update):

    logging.critical("train")
    if update.message.chat.type in ["group", "supergroup", "channel"]:
        bot.sendMessage(text="Не-не, в группах я отказываюсь работать, я стеснительный. Пиши мне только тет-а-тет 😉",
                        chat_id=update.message.chat.id)
        return

    trains = get_things("trains")
    kb = []
    if trains:
        iter = 0
        next = iter + step
        for train in trains[iter:next]:
            button = telegram.InlineKeyboardButton(text=train["start"]["date"] + ":\t" + train["summary"],
                                                   callback_data="100;" + train["id"])
            kb.append([button])
            iter += 1
        kb_markup = telegram.InlineKeyboardMarkup(kb)
        bot.sendMessage(text="Расписание следующих тренировок:", chat_id=update.message.chat.id, reply_markup=kb_markup)
        logging.critical("request for train")
    else:
        bot.sendMessage(bot, update, text="Пока тренировки не запланированы. Восстанавливаемся!",
                        chat_id=update.message.chat.id)
        logging.critical("no trains")
        kb = []
        bot.sendMessage(text="Пока тренировки не запланированы. Восстанавливаемся!", chat_id=update.message.chat.id,
                        reply_markup=keyboard())


def events(bot, update):
    logging.critical("train")
    if update.message.chat.type in ["group", "supergroup", "channel"]:
        bot.sendMessage(text="Не-не, в группах я отказываюсь работать, я стеснительный. Пиши мне только тет-а-тет 😉",
                        chat_id=update.message.chat.id)
        return
    db_name = "events"
    events = get_things(db_name)
    if events:
        iter = 0
        step = 5
        next = iter + step
        thing_list(bot, update, db_name, iter, next)
    else:
        logging.critical("no events")
        kb = []
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
        button = telegram.InlineKeyboardButton(text=thing["start"]["date"] + ":\t" + thing["summary"],
                                               callback_data="200;" + thing["id"])
        kb.append([button])
        iter += 1
    kb.append(pager(bot, update, db_name, iter, step, next))
    kb_markup = telegram.InlineKeyboardMarkup(kb)
    bot.sendMessage(text="Расписание следующих мероприятий:", chat_id=chat_id, reply_markup=kb_markup)
    logging.critical("request for event")
    return thing_list


def pager(bot, update, db_name, iter, step, next):
    logging.critical("pager")
    logging.critical((iter - step) == 0)
    if iter - step == 0:
        logging.critical("next button")
        button_next = telegram.InlineKeyboardButton(text=">", callback_data="302;" + str(next) + ";" + db_name)
        buttons = []
        buttons.append(button_next)
    elif len(get_things(db_name)) > next:
        logging.critical("prev and next buttons")
        button_prev = telegram.InlineKeyboardButton(text="<", callback_data="301;" + str(next - step) + ";" + db_name)
        button_next = telegram.InlineKeyboardButton(text=">", callback_data="302;" + str(next) + ";" + db_name)
        buttons = []
        buttons.append(button_prev)
        buttons.append(button_next)
    else:
        logging.critical("prev button")
        button_prev = telegram.InlineKeyboardButton(text="<", callback_data="301;" + str(next - step) + ";" + db_name)
        buttons = []
        buttons.append(button_prev)
    return buttons


def train_details(bot, update):
    logging.critical("train_details")
    logging.critical(update.message.text)


def event_details(bot, update):
    logging.critical("event_details")
    logging.critical(update.message.text)


def text_processing(bot, update):
    # 000 - username instructions
    # 100 - trains
    # 200 - events
    # 301 - pager: next
    # 302 - pager: prev

    logging.critical("text_processing")
    text = update.callback_query.data
    logging.critical(text)
    action = text.split(";")[0]
    details = text.split(";")[1]
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
    elif action == "301":
        db_name = text.split(";")[2]
        details = int(details)
        thing_list(bot, update, db_name, details - step, details)
    elif action == "302":
        logging.critical(text)
        db_name = text.split(";")[2]
        details = int(details)
        thing_list(bot, update, db_name, details, details + step)
    else:
        logging.critical(update.callback_query)


def cancel(bot, update):
    logging.critical("cancel")
    bot.sendMessage(text="Что то ты не то ввел...", chat_id=update.message.chat.id)
    return ConversationHandler.END


def main():
    logging.critical('start trainigninparks bot script')

    # Set up handlers

    start_handler = CommandHandler("start", start)
    dispatcher.add_handler(start_handler)

    train_handler = RegexHandler("^(🏃 Треня)$", trains)
    dispatcher.add_handler(train_handler)

    event_handler = RegexHandler("^(🏅 Мероприятия)$", events)
    dispatcher.add_handler(event_handler)

    message_handler = CallbackQueryHandler(text_processing)
    dispatcher.add_handler(message_handler)

    # Poll user actions

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
