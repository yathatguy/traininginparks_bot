# -*- coding: utf-8 -*-

from __future__ import unicode_literals, division, print_function

import smtplib
from email.mime.text import MIMEText


def send_email(text):
    # Create message

    me = 'traininginparks@mail.ru'
    you = 'thatguy@yandex.ru'
    smtp_server = 'smtp.mail.ru'
    msg = MIMEText('Message e-mail')
    msg["Subject"] = "TrainingInParks Bot Feedback"
    msg['From'] = me
    msg['To'] = you
    s = smtplib.SMTP(smtp_server)
    s.sendmail(me, [you], msg.as_string())
    server = smtplib.SMTP("localhost")
    server.sendmail(msg["From"], msg["To"], msg["Text"])
    server.quit()

    # Send the message via our own SMTP server, but don't include the envelope header.

    server = smtplib.SMTP("localhost")
    server.sendmail(me, [you], msg.as_string())
    server.quit()


def main():
    """
    Main function
    :return: N/A
    """

    pass


if __name__ == '__main__':
    main()
