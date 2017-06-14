# -*- coding: utf-8 -*-

from __future__ import unicode_literals, division, print_function

import os
import smtplib
from email.mime.text import MIMEText


def send_email(message):
    # Create message

    me = "traininginparks@yandex.ru"
    you = "thatguy@yandex.ru"
    # "ilazdorenko@gmail.com"

    text = message.from_user.first_name.encode('utf-8') + message.from_user.last_name.encode(
        'utf-8') + message.from_user.username.encode('utf-8') + message.text

    print(type(text), text)

    try:
        print(type(message.from_user.first_name),
              type(message.from_user.last_name),
              type(message.from_user.username),
              type(message.text))
    except:
        print(type(message.from_user.first_name.encode('utf-8')),
              type(message.from_user.last_name.encode('utf-8')),
              type(message.from_user.username.encode('utf-8')),
              type(message.text))

    msg = MIMEText(text, 'plain')
    msg["Subject"] = "TrainingInParks Bot Feedback"
    msg["From"] = me
    msg["To"] = you

    # Send the message via our own SMTP server, but don't include the envelope header.

    server = smtplib.SMTP_SSL("smtp.yandex.ru", 465)
    server.connect("smtp.yandex.ru", 465)
    server.ehlo()
    server.login(me, os.environ["YANDEX_PASSWORD"])
    server.sendmail(me, you, msg.as_string())
    server.quit()


def main():
    """
    Main function
    :return: N/A
    """

    pass


if __name__ == '__main__':
    main()
