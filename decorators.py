# coding=utf-8
from functools import wraps

from keyboard import keyboard


def only_private(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        bot = kwargs.get('bot') if kwargs.get('bot') else args[0]
        update = kwargs.get('update') if kwargs.get('update') else args[1]
        if update.message.chat.type in ["group", "supergroup", "channel"]:
            kb_markup = keyboard()
            bot.sendMessage(
                text="Не-не, в группах я отказываюсь работать, я стеснительный. Пиши мне только тет-а-тет 😉",
                chat_id=update.message.from_user.id,
                reply_markup=kb_markup)
            return
        return f(*args, **kwargs)

    return wrapped
