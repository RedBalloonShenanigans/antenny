# src/config.py

# import json as ujson # Uncomment this line for local testing
import ujson
import os


#####################################
# Global variables and default values
#####################################

_config_filename = ""
_config = None
_defaults = {
                # Default configuration file to load
                "last_loaded": "config.json",

                # Disable optional hardware features
                "use_gps": False,
                "use_screen": False,

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
                "i2c_bno_scl": 18,
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

    with open(_config_filename, "w") as f:
        ujson.dump(_config, f)



####################
# Inteface functions
####################

def reload():
    """Reload the in-memory configuration key-value store from the config file.
    Use a default filename if one is not set. The default file may point to a
    different default config file.

    Note: it is possible to enter an infinite loop if configs have
    "last_loaded" values that point to one another.
    """
    global _config
    global _config_filename
    last_loaded = _defaults["last_loaded"]

    try:
        if _config_filename:
            with open(_config_filename, "r") as f:
                _config = ujson.load(f)
        else:
            while _config_filename != last_loaded:
                # Set config filename to the default value
                _config_filename = last_loaded
                with open(_config_filename, "r") as f:
                    _config = ujson.load(f)
                last_loaded = _config.get("last_loaded", _config_filename)
    except OSError:
        # print("Config file %s not found while reloading. Creating a new one." %
        #         _config_filename)
        _config = {}


def new(name):
    """Create a new configuration file and ensure each call to "reload" uses
    the correct file. Does not overwrite if the file already exists.
    """
    global _config_filename
    global _defaults

    if _config_filename == _defaults["last_loaded"]:
        set("last_loaded", name)
    _config_filename = name
    reload()


def switch(name):
    """Switch the configuration file being used."""
    new(name)


def get(key, call_reload=True):
    """Get a value from the in-memory key-value store loaded from the
    configuration file. If no value exists for the key, try and get it from the
    dictionary of default values. If "call_reload" is true, it will try and
    reload the config file from storage before checking for the value.
    """
    global _config

    if call_reload and _config is None:
        reload()

    if key not in _config:
        return get_default(key, call_reload=call_reload)
    else:
        return _config[key]


def get_default(key, call_reload=True):
    """Get the default value for a given key."""
    global _defaults

    if call_reload and _defaults is None:
        reload()

    return _defaults[key]


def set(key, value):
    """Set the value for a key in-memory and save it to the file system."""
    global _config

    if _config is None:
        reload()

    _config[key] = value
    _save()
    reload()


def print_values():
    """Print the value of all user-set and default keys."""
    global _config
    global _defaults

    print("Using configuration file %s" % _config_filename)
    print()

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
    """Erase all user-set keys and back up the configuration file to a .bak
    file by default.
    """
    try:
        if backup:
            os.rename(_config_filename, "%s.bak" % _config_filename)
        else:
            os.remove(_config_filename)
    except OSError:
        pass
    reload()


def revert():
    """Revert the current configuration from a backup."""
    try:
        os.rename("%s.bak" % _config_filename, _config_filename)
        reload()
    except OSError:
        pass


def remove_backup():
    """Delete a stored backup, if one exists."""
    try:
        os.remove("%s.bak" % _config_filename)
    except OSError:
        pass


def current_file():
    """Return the current config filename being used."""
    return _config_filename



###################################
# Main function -- loaded on import
###################################

reload()
