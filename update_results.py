# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function

import json
import logging
import os

import requests


BASE = "https://api.typeform.com/"
TYPEFORM_KEY = os.environ["TYPEFORM_KEY"]
FORMS = ["aocZvF", "LzjVO3"]

FORMAT = "%(funcName)s  %(lineno)d   %(message)s"
logging.basicConfig(format=FORMAT, level=logging.DEBUG)


def get_responses(form_id):
    payload = {"key": TYPEFORM_KEY}
    try:
        r = requests.get(BASE + "v1/forms/" + form_id, params = payload)
        logging.debug(r)
        return r.json()
    except Exception as e:
        logging.critical(r.json())
        return None


def get_run_results(responses):
    run_results = list()
    for response in responses:
        if response["answers"]:
            user_response = dict()
            answers = response["answers"]
            for answer in answers:
                if answer["field"]["id"] == "HcIAZuaaeVjk":
                    user_response["category"] = answer["text"]
                if answer["field"]["id"] == "ZW6yHCU1S0E1":
                    user_response["date"] = answer["date"]
                if answer["field"]["id"] == "ljyCJ4BGGtPz":
                    user_response["media"] = answer["url"]
                if answer["field"]["id"] == "gOnQHjRMiuoV":
                    user_response["user"] = answer["text"]
                if answer["field"]["id"] == "hgIGgaaVimc6":
                    kg = user_response["number"]
                if answer["field"]["id"] == "UomzONn87aM0":
                    g = user_response["number"]
            if kg != None and g != None:
                user_response["result"] = "{} kg {} g".format(kg, g)
        run_results = run_results.append(user_response)
    else:
        logging.critical("No reslonse was provided: {}".format(response))
        



    return run_results


def get_weight_results(responses):
    pass
    return weight_results


def join_results(run_results, weight_results):
    pass
    return results


def create_db(results):
    pass


def main():
    for form in FORMS:
        responses = get_responses(form)
            if form == "aocZvF":
                run_results = get_run_results(responses)
            elif form == "LzjVO3":
                weight_results = get_weight_results(responses)
            else:
                logging.critical(form, response)
    results = join_results(run_results, weight_results)
    create_db(results)


if __name__ == "__main__":
    main()
