# -*- coding: utf-8 -*-

from __future__ import unicode_literals, division, print_function

import os

import requests

BASE_URL = "https://maps.googleapis.com/maps/api/geocode/json"


def get_coordinates(address):
    """
    GEt address and check Google Maps Geocoding API for latitude and longitude
    :param address: address to chec
    :return: dict with coordinates - {"lat": float, "lng": float}
    """

    params = {"address": address, "key": os.environ["MAPS_API"]}
    raw_coordinates = requests.get(BASE_URL, params).json()
    if raw_coordinates["status"] == "OK":
        coordinates = raw_coordinates["results"][0]["geometry"]["location"]
    else:
        coordinates = dict()

    return coordinates


def main():
    """
    Main function
    :return: N/A
    """
    pass


if __name__ == '__main__':
    main()
