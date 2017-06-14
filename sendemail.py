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

    try:
        print("encode", message.text.encode('utf-8'), message.from_user.first_name.encode('utf-8'))
    except:
        print("decode", message.text.decode('utf-8'), message.from_user.first_name.decode('utf-8'))

    # print(message.from_user.first_name, message.from_user.last_name, message.from_user.username,
    #      message.text.decode('unicode-escape'))
    text = 'First name: {}\nLast name: {}\nUsername: {}\n\n{}'.format(message.from_user.first_name,
                                                                      message.from_user.last_name,
                                                                      message.from_user.username,
                                                                      message.text.decode('unicode-escape'))
    msg = MIMEText(text)
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
