# -*- coding: utf-8 -*-

from __future__ import unicode_literals, division, print_function

import os
import smtplib
from email.mime.text import MIMEText


def send_email(text):
    # Create message

    me = "thatguy@yandex.ru"
    you = "thatguy@yandex.ru"
    msg = MIMEText(text)
    msg["Subject"] = "TrainingInParks Bot Feedback"
    msg["From"] = me
    msg["To"] = you

    # Send the message via our own SMTP server, but don't include the envelope header.

    server = smtplib.SMTP_SSL("smtp.yandex.ru")
    server.sendmail(me, [you], msg.as_string())
    server.login(me, os.environ["YANDEX_PASSWORD"])
    server.quit()


def main():
    """
    Main function
    :return: N/A
    """

    pass


if __name__ == '__main__':
    main()
