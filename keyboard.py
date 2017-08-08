# coding=utf-8
import telegram


def keyboard():
    kb = [[telegram.KeyboardButton('🏃 Треня'), telegram.KeyboardButton('🏅 Мероприятия')],
          [telegram.KeyboardButton('🙏 Участники'), telegram.KeyboardButton('💪 Мои тренировки')],
          [telegram.KeyboardButton('🏋 WOD'), telegram.KeyboardButton('🏁 Соревнования')]]
    kb_markup = telegram.ReplyKeyboardMarkup(kb, resize_keyboard=True)

    return kb_markup
