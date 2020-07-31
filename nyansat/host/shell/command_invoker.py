
import ast
import asyncio
import json
import threading

from time import sleep

from mp.pyboard import PyboardError
from nyansat.host.shell.nyan_pyboard import NyanPyboard

from nyansat.host.satellite_observer import SatelliteObserver, parse_tle_file
from nyansat.host.shell.errors import *

import nyansat.host.satdata_client as SatelliteScraper

from typing import List
from dataclasses import dataclass


class CommandInvoker(NyanPyboard):
    """
    Replacement for nyan_explorer. Antenny-specific functionality only.
    """
    def __init__(self, con):
        super().__init__(con)
        self.tracking = False

    EL_SERVO_INDEX = "elevation_servo_index"
    AZ_SERVO_INDEX = "azimuth_servo_index"

    def is_antenna_initialized(self):
        """Test if there is an AntKontrol object on the board"""
        try:
            self.exec_("isinstance(api, antenny.AntennyAPI)")
            return True
        except PyboardError:
            return False

    def is_tracking(self):
        return self.tracking

    def set_tracking(self, val: bool):
        self.tracking = val

    def config_status(self):
        """Test if there is a valid config object on the board; if not, try to create one"""
        try:
            self.exec_("isinstance(config, ConfigRepository")
            return True
        except PyboardError:
            self.exec_("config = ConfigRepository()")
            ret = self.eval_string_expr("isinstance(config, ConfigRepository)")
            if ret == "False":
                return False
            else:
                return True

    def which_config(self):
        """Get the name of the currently used config file."""
        return self.eval_string_expr("config.current_file()")

    def config_get(self, key):
        """Get the value of an individual config parameter.

        Arguments:
        key -- name of config parameter.
        """
        command = "config.get(\"{}\")".format(key)
        try:
            return self.eval_string_expr(command)
        except PyboardError:
            raise NoSuchConfigError

    def config_set(self, key, val):
        """Set an individual parameter in the config file.

        Arguments:
        key -- name of config parameter. Tab complete to see choices.
        val -- value of paramter
        """
        try:
            if isinstance(val, int) or isinstance(val, float):
                self.exec_("config.set(\"%s\", %d)" % (key, val))
            elif isinstance(val, str):
                self.exec_("config.set(\"%s\", %s)" % (key, val))
        except PyboardError:
            raise NoSuchConfigError

    def config_get_default(self, key):
        """Get the default value of a config parameter.

        Arguments:
        key -- name of config parameter.
        """
        try:
            return self.eval_string_expr("config.get_default(\"{}\")".format(key))
        except PyboardError:
            raise NoSuchConfigError

    def config_new(self, name):
        """Create a new config file on the ESP32.

        Arguments:
        name -- name of new config file.
        """
        self.exec_("config.new(\"{}\")".format(name))

    def config_switch(self, name):
        """Switch to using a different config file.

        Arguments:
        name -- name of config file.
        """
        try:
            self.exec_("config.switch(\"{}\")".format(name))
        except PyboardError:
            raise ConfigUnknownError

    def i2c_scan(self, sda, scl):
        """
        Create and scan an i2c bus for addresses; helpful for debugging
        :param sda: Pin number for sda
        :param scl: Pin number for scl
        :return: Addresses found on i2c bus
        """
        self.exec_("import machine")
        self.exec_("from machine import Pin")
        self.exec_(
            "i2c = machine.I2C(-1, sda=Pin({}, Pin.OUT, Pin.PULL_DOWN), scl=Pin({}, Pin.OUT, Pin.PULL_DOWN))".format(
                    sda,
                    scl
                )
            )
        return self.eval_string_expr("i2c.scan()")

    def imu_calibration_status(self):
        """Get IMU calibration status."""
        try:
            return json.loads(self.eval_string_expr("api.imu.get_calibration_status()"))
        except PyboardError:
            raise

    def imu_save_calibration_profile(self):
        """Save the current IMU calibration as 'calibration.json'."""
        return self.eval_string_expr("api.imu.save_calibration_profile('calibration.json')")

    def imu_upload_calibration_profile(self):
        """Upload 'calibration.json' to the IMU."""
        return self.eval_string_expr("api.imu.upload_calibration_profile('calibration.json')")

    def motor_test(self, index, pos):
        """Run a motor accuracy test, for testing the disparity between the motor and IMU.

        Arguments:
        index -- index of motor on the PWM driver (defaults: 0 == elevation, 1 == azimuth).
        pos -- desired angle.
        """
        try:
            return ast.literal_eval(self.eval_string_expr("api.motor_test({}, {})".format(index, pos)))
        except PyboardError:
            raise NotRespondingError

    def set_elevation_degree(self, el_angle):
        """Set the elevation angle.

        Arguments:
        el_angle -- desired elevation angle.
        """
        try:
            self.eval_string_expr("api.antenna.set_elevation({})".format(el_angle))
        except PyboardError:
            raise NotRespondingError

    def set_azimuth_degree(self, az_angle):
        """Set the azimuth angle.

        Arguments:
        az_angle -- desired azimuth angle.
        """
        try:
            self.eval_string_expr("api.antenna.set_azimuth({})".format(az_angle))
        except PyboardError:
            raise NotRespondingError

    def create_antkontrol(self):
        """Create an antkontrol object on the ESP32."""
        try:
            ret = self.exec_("import antenny")
            ret = self.exec_("api = antenny.esp32_antenna_api_factory()")
        except PyboardError:
            raise AntennaAPIFactoryError
        try:
            ret = self.exec_("del(config)")
            ret = self.exec_("config = api.config")
            # self.antenna_initialized = True
            return ret.decode()
        except PyboardError:
            self.exec_("from config.config import ConfigRepository")
            self.exec_("config = ConfigRepository")
            raise ConfigUnknownError

    def delete_antkontrol(self):
        """Delete the existing antkontrol object on the ESP32."""
        try:
            ret = self.exec_("del(api)")
            # self.antenna_initialized = False
            return ret.decode()
        except PyboardError:
            raise NotRespondingError

    def is_safemode(self):
        """Check if the API is in SAFE MODE"""
        try:
            ret = self.eval_string_expr("api.is_safemode()")
            # The following is inelegant, but a result of eval_string_expr's return
            if ret == 'False':
                ret = False
            else:
                ret = True
            return ret
        except PyboardError:
            raise NotRespondingError
