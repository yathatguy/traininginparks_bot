# -*- coding: utf-8 -*-

from __future__ import unicode_literals, division, print_function

import os

import requests

BASE_URL = "https://maps.googleapis.com/maps/api/geocode/json"


def get_coordinates(address):
    params = {"address": address, "key": os.environ["MAPS_API"]}
    raw_coordinates = requests.get(BASE_URL, params).json()
    if raw_coordinates["status"] == "OK":
        coordinates = raw_coordinates["results"][0]["geometry"]["location"]

    return coordinates


def main():
    pass


if __name__ == '__main__':
    main()
