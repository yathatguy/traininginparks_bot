# -*- coding: utf-8 -*-

from __future__ import unicode_literals, division, print_function

import smtplib


def send_email(text):
    # Create message

    msg = dict()
    msg["Subject"] = "TrainingInParks Bot Feedback"
    msg["From"] = "traininginparks_bot"
    msg["To"] = "thatguy@yandex.ru"
    msg["Text"] = text

    # Send the message via our own SMTP server, but don't include the envelope header.

    server = smtplib.SMTP("localhost")
    server.sendmail(msg["From"], msg["To"], msg["Text"])
    server.quit()


def main():
    """
    Main function
    :return: N/A
    """

    pass


if __name__ == '__main__':
    main()
