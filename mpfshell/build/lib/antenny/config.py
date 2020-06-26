# src/config.py

# import json as ujson # Uncomment this line for local testing
import ujson
import os


#####################################
# Global variables and default values
#####################################

CONFIG_FILENAME = "config.json"
_config = None
_defaults = {
                # Elevation/azimuth servo defaults
                "elevation_servo_index": 0,
                "azimuth_servo_index": 1,
                "elevation_max_rate": 0.1,
                "azimuth_max_rate": 0.1,

                # Telemetry settings
                "telem_destaddr": "224.11.11.11",
                "telem_destport": "31337",

                # Pins
                "gps_uart_tx": 33,
                "gps_uart_rx": 27,
                "i2c_servo_scl": 21,
                "i2c_servo_sda": 22,
                "i2c_bno_scl": 19,
                "i2c_bno_sda": 23,
                "i2c_screen_scl": 25,
                "i2c_screen_sda": 26,

                # Not necessary if antenny isn't a tank
                "tank_left": [1,2],
                "tank_right": [0,3],
                "tank_motors": [0,1,2,3],
            }


####################
# Internal functions
####################


def _save():
    global _config

    with open(CONFIG_FILENAME, "w") as f:
        ujson.dump(_config, f)



####################
# Inteface functions
####################

def reload():
    global _config

    try:
        with open(CONFIG_FILENAME, "r") as f:
            _config = ujson.load(f)
    except OSError:
        _config = {}


def get(key):
    global _config
    global _defaults

    if _config is None or _defaults is None:
        reload()

    if key not in _config:
        return _defaults[key]
    else:
        return _config[key]


def set(key, value):
    global _config

    if _config is None:
        reload()

    _config[key] = value

    _save()


def print_values():
    global _config
    global _defaults

    if _config:
        print("Config values:")
        for key, val in _config.items():
            print("%s: %s" % (key, ujson.dumps(val)))
        print()
    else:
        print("No non-default configuration values set!")

    print("Default values:")
    for key, val in _defaults.items():
        print("%s: %s" % (key, ujson.dumps(val)))
    print()


def clear(backup=True):
    try:
        if backup:
            os.rename(CONFIG_FILENAME, "%s.bak" % CONFIG_FILENAME)
        else:
            os.remove(CONFIG_FILENAME)
    except OSError:
        pass

    reload()


def revert():
    try:
        os.rename("%s.bak" % CONFIG_FILENAME, CONFIG_FILENAME)
        reload()
    except OSError:
        pass


def remove_backup():
    try:
        os.remove("%s.bak" % CONFIG_FILENAME)
    except OSError:
        pass


###################################
# Main function -- loaded on import
###################################

reload()
