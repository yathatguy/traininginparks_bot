# -*- coding: utf-8 -*-

from __future__ import unicode_literals, division, print_function

import os

import requests

BASE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
KEY = os.environ['MAPS_API']


def get_coordinates(address):
    params = {"address": address, "key": KEY}
    raw_coordinates = requests.get(BASE_URL, params).json()
    if raw_coordinates["results"]["status"] == "OK":
        coordinates = raw_coordinates["results"]["geometry"]["location"]

    return coordinates


def main():
    pass


if __name__ == '__main__':
    main()
