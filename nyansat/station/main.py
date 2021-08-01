"""
Antenny main entry point, runs after boot.py.
"""
import webrepl
import machine

import antenny_threading
from api.api import AntennyAPI
from config.config import Config


def start():
    api = AntennyAPI()
    print("Antenny API initialized, current config is {}".format(api.antenny_config.print_values()))
    print("Please edit config to your hardware and run \"api.init_components()\"")
    return api

api = start()
