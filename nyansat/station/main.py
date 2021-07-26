"""
Antenny main entry point, runs after boot.py.
"""
import webrepl
import machine

import antenny_threading
from api.api import AntennyAPI
from config.config import Config


def start():
    config = Config("antenny")

    if config.get('use_webrepl'):
        webrepl.start()

    api = AntennyAPI(config)
    if config.get("enable_demo"):
        interrupt_pin = machine.Pin(15, machine.Pin.IN, machine.Pin.PULL_UP)
        interrupt_pin.irq(trigger=machine.Pin.IRQ_FALLING, handler=api.antenna.pin_motion_test)
    print("Antenny API initialized, current config is {}".format(config.print_values()))
    print("Please edit config to your hardware and run \"api.init_components()\"")
    return api

api = start()
