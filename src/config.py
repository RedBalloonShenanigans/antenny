# src/config.py

import ujson


#####################################
# Global variables and default values
#####################################

_config = None
_defaults = {
                "elevation_servo_index": 0,
                "azimuth_servo_index": 1,
            }



####################
# Internal functions
####################

def _init():
    global _config

    try:
        with open("config.json", "r") as f:
            _config = ujson.load(f)
    except:
        _config = {}


def _save():
    global _config

    with open("config.json", "w") as f:
        ujon.dump(_config)



####################
# Inteface functions
####################

def get(key):
    global _config
    global _defaults

    if _config is None or _defaults is None:
        _init()

    if key not in _config:
        return _defaults[key]
    else:
        return _config[key]


def set(key, value):
    global _config

    if _config is None or _defaults is None:
        _init()

    _save()
