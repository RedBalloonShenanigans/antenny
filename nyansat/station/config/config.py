# src/config.py

try:
    import ujson as json
except ImportError:
    import json
try:
    import logging
except ImportError:
    pass
import os


############
# Main class
############

class ConfigRepository:
    """Used for getting, setting, loading, and storing configuration file
    values.
    """

    DEFAULT_CONFIG = {
        # Default configuration file to load
        "last_loaded": "config.json",
        # Disable optional hardware features
        "use_gps": False,
        "use_screen": False,
        "use_telemetry": False,
        "use_imu": False,
        "use_webrepl": False,
        "enable_demo": True,
        # Elevation/azimuth servo defaults
        "elevation_servo_index": 0,
        "azimuth_servo_index": 1,
        "elevation_max_rate": 0.1,
        "azimuth_max_rate": 0.1,
        # Antenny board layout
        "antenny_board_version": 2,
        # Pins
        "gps_uart_tx": 33,
        "gps_uart_rx": 27,
        "i2c_servo_scl": 21,
        "i2c_servo_sda": 22,
        "i2c_servo_address": 64,
        "i2c_bno_scl": 18,
        "i2c_bno_sda": 19,
        "i2c_bno_address": 40,
        "i2c_screen_scl": 25,
        "i2c_screen_sda": 26,
        "i2c_screen_address": 0,
        # Position coordinates
        "latitude": 40.0,
        "longitude": -73.0,
        # IMU calibration - cf. section 3.6.4 "Sensor calibration data" in
        # Bosch BNO055 datasheet. Default values are all zero
        "acc_offset_x_lsb": 0,
        "acc_offset_x_msb": 0,
        "acc_offset_y_lsb": 0,
        "acc_offset_y_msb": 0,
        "acc_offset_z_lsb": 0,
        "acc_offset_z_msb": 0,
        "mag_offset_x_lsb": 0,
        "mag_offset_x_msb": 0,
        "mag_offset_y_lsb": 0,
        "mag_offset_y_msb": 0,
        "mag_offset_z_lsb": 0,
        "mag_offset_z_msb": 0,
        "gyr_offset_x_lsb": 0,
        "gyr_offset_x_msb": 0,
        "gyr_offset_y_lsb": 0,
        "gyr_offset_y_msb": 0,
        "gyr_offset_z_lsb": 0,
        "gyr_offset_z_msb": 0,
        "acc_radius_lsb": 0,
        "acc_radius_msb": 0,
        "mag_radius_lsb": 0,
        "mag_radius_msb": 0,
    }

    def __init__(self, config_filename: str = "") -> None:
        self._config = {}
        self._config_filename = config_filename
        self.reload()

    def _save(self) -> None:
        """Dump in-memory configuration values to a file on the board."""
        with open(self._config_filename, "w") as f:
            json.dump(self._config, f)

    def reload(self) -> None:
        """Reload the in-memory configuration key-value store from the config
        file. Use a default filename if one is not set. The default file may
        point to a different default config file.

        Note: it is possible to enter an infinite loop if configs have
        "last_loaded" values that point to one another.
        """
        default_config = ConfigRepository.DEFAULT_CONFIG.get("last_loaded")
        last_loaded = default_config

        try:
            if self._config_filename:
                with open(self._config_filename, "r") as f:
                    self._config = json.load(f)
            else:
                loaded = set()
                while self._config_filename != last_loaded:
                    # Set config filename to the default value
                    self._config_filename = last_loaded
                    with open(self._config_filename, "r") as f:
                        self._config = json.load(f)
                    last_loaded = self._config.get("last_loaded",
                                                   self._config_filename)
                    if (last_loaded in loaded
                            and last_loaded != self._config_filename):
                        try:
                            logging.error("Cyclic config files! Using default: "
                                          + default_config)
                        except (NameError, AttributeError):
                            pass
                        self._config_filename = default_config
                        self.reload()
                        self._config["last_loaded"] = self._config_filename
                    else:
                        loaded.add(last_loaded)
        except OSError:
            self._config = dict(ConfigRepository.DEFAULT_CONFIG)
            self._config["last_loaded"] = self._config_filename

    def new(self, name: str) -> None:
        """Create a new configuration file and ensure each call to "reload" uses
        the correct file. Does not overwrite if the file already exists.
        """
        self.set("last_loaded", name)
        self._config_filename = name
        self.reload()

    def switch(self, name: str) -> None:
        """Switch the configuration file being used."""
        self.new(name)

    def get(self, key: str, call_reload: bool = True):
        """Get a value from the in-memory key-value store loaded from the
        configuration file. If no value exists for the key, try and get it from
        the dictionary of default values. If "call_reload" is true, it will try
        and reload the config file from storage before checking for the value.
        """
        if call_reload and self._config is None:
            self.reload()

        if key not in self._config:
            return self.get_default(key, call_reload=call_reload)
        else:
            return self._config[key]

    def get_default(self, key: str, call_reload: bool = True):
        """Get the default value for a given key. Reload the config file if
        the flag is set and it is not already loaded in memory.
        """
        if call_reload and self._config is None:
            self.reload()
        return ConfigRepository.DEFAULT_CONFIG[key]

    def set(self, key: str, value) -> None:
        """Set the value for a key in-memory and save it to the file system."""
        if self._config is None:
            self.reload()

        self._config[key] = value
        self._save()
        self.reload()

    def print_values(self) -> None:
        """Print the value of all user-set and default keys."""
        print("Using configuration file %s" % self._config_filename)
        print()

        if self._config:
            print("Config values:")
            for key, val in self._config.items():
                print("%s: %s" % (key, json.dumps(val)))
            print()
        else:
            print("No non-default configuration values set!")

        print("Default values:")
        for key, val in ConfigRepository.DEFAULT_CONFIG.items():
            print("%s: %s" % (key, json.dumps(val)))
        print()

    def clear(self, backup: bool = True) -> None:
        """Erase all user-set keys and back up the configuration file to a .bak
        file by default.
        """
        try:
            if backup:
                os.rename(self._config_filename,
                          "%s.bak" % self._config_filename)
            else:
                os.remove(self._config_filename)
        except OSError:
            pass
        self.reload()

    def revert(self) -> None:
        """Revert the current configuration from a backup."""
        try:
            os.rename("%s.bak" % self._config_filename, self._config_filename)
            self.reload()
        except OSError:
            pass

    def remove_backup(self) -> None:
        """Delete a stored backup, if one exists."""
        try:
            os.remove("%s.bak" % self._config_filename)
        except OSError:
            pass

    def current_file(self) -> None:
        """Return the current config filename being used."""
        return self._config_filename
