# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals

import json
import logging
import os
import requests
import pymongo

BASE = "https://api.typeform.com/"
TYPEFORM_KEY = os.environ["TYPEFORM_KEY"]
FORMS = ["aocZvF", "LzjVO3"]


FORMAT = "%(funcName)s  %(lineno)d   %(message)s"
logging.basicConfig(format=FORMAT, level=logging.INFO)


def get_responses(form_id):
    payload = {"key": TYPEFORM_KEY}
    try:
        r = requests.get(BASE + "v1/forms/" + form_id + "/responses", params = payload)
        logging.debug(r)
        return r.json()
    except Exception as e:
        logging.critical(e)
        logging.debug(r.json())
        return None


def get_run_results(responses):
    run_results = list()
    logging.debug(responses)
    for response in responses["items"]:
        if response["answers"] != None:
            user_response = dict()
            hours, minutes, seconds = None, None, None
            for answer in response["answers"]:
                logging.debug(answer)
                if answer["field"]["id"] == "f55UNmjGgd2y":
                    user_response["category"] = answer["text"]
                if answer["field"]["id"] == "qmdG4QvqnoPR":
                    user_response["date"] = answer["date"].split("T")[0]
                if answer["field"]["id"] == "XX8owCm9G88k":
                    if answer["url"] == "http://":
                        user_response["media"] = None
                    else:
                        user_response["media"] = answer["url"]
                if answer["field"]["id"] == "Nq1mrP1EZyCH":
                    user_response["user"] = answer["text"].strip("@")
                if answer["field"]["id"] == "GoJk4PUJAVQa":
                    hours = answer["number"]
                if answer["field"]["id"] == "xJUGyXwKnU6n":
                    minutes = answer["number"]
                if answer["field"]["id"] == "DGnjz8jMwMfD":
                    seconds = answer["number"]
            if hours != None and minutes != None and seconds != None:
                user_response["result"] = "{} hours {} minutes {} seconds".format(hours, minutes, seconds)
            run_results.append(user_response)
    logging.debug(user_response)
    logging.debug(run_results)
    return run_results


def get_weight_results(responses):
    weight_results = list()
    logging.debug(responses)
    for response in responses["items"]:
        if response["answers"] != None:
            user_response = dict()
            kg, g = None, None
            for answer in response["answers"]:
                logging.debug(answer)
                if answer["field"]["id"] == "HcIAZuaaeVjk":
                    user_response["category"] = answer["text"]
                if answer["field"]["id"] == "ZW6yHCU1S0E1":
                    user_response["date"] = answer["date"].split("T")[0]
                if answer["field"]["id"] == "ljyCJ4BGGtPz":
                    if answer["url"] == "http://":
                        user_response["media"] = None
                    else:
                        user_response["media"] = answer["url"]
                if answer["field"]["id"] == "gOnQHjRMiuoV":
                    user_response["user"] = answer["text"].strip("@")
                if answer["field"]["id"] == "hgIGgaaVimc6":
                    kg = answer["number"]
                if answer["field"]["id"] == "UomzONn87aM0":
                    g = answer["number"]
            if kg != None and g != None:
                user_response["result"] = "{} kg {} g".format(kg, g)
            weight_results.append(user_response)
    logging.debug(user_response)
    logging.debug(weight_results)
    return weight_results


def join_results(run_results, weight_results):
    if run_results and weight_results:
        return run_results + weight_results
    elif run_results:
        return run_results
    else:
        return weight_results


def create_db(results):
    category_list = create_category_list(results)
    db_records = create_db_records(results, category_list)
    logging.debug(db_records)
    update_db(db_records)


def update_db(db_records):
    connection = pymongo.MongoClient(os.environ['MONGODB_URI'])
    db = connection["heroku_20w2cn6z"]
    db["results"].remove()
    db["results"].insert_many(db_records)
    connection.close()


def create_category_list(results):
    category_list = list()
    for result in results:
        if result["category"] not in category_list:
            category_list.append(result["category"])
    logging.debug(category_list)
    dump_category(category_list)
    return category_list


def dump_category(category_list):
    connection = pymongo.MongoClient(os.environ['MONGODB_URI'])
    db = connection["heroku_20w2cn6z"]
    db["results_category"].remove()
    db["results_category"].insert_many([{"categories": category_list}])
    connection.close()


def create_db_records(results, categoty_list):
    db_records = list()
    for category in categoty_list:
        db_record = dict()
        db_record["category"] = category
        db_record["results"] = list()
        for result in results:
            if "category" in  result and result["category"] == db_record["category"]:
                del result["category"]
                db_record["results"].append(result)
        db_records.append(db_record)
    logging.debug(db_records)
    return db_records


def main():
    for form in FORMS:
        responses = get_responses(form)
        logging.debug(responses)
        if form == "aocZvF":
            run_results = get_run_results(responses)
            logging.debug(run_results)
        elif form == "LzjVO3":
            weight_results = get_weight_results(responses)
            logging.debug(weight_results)
        else:
            logging.critical(form, responses)
    results = join_results(run_results, weight_results)
    logging.debug(results)
    create_db(results)


if __name__ == "__main__":
    main()
