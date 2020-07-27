import ast
import asyncio
import json
import threading

from time import sleep

from mp.mpfexp import MpFileExplorer, MpFileExplorerCaching
from mp.pyboard import PyboardError
from nyansat.host.shell.nyan_pyboard import NyanPyboard

from nyansat.host.satellite_observer import SatelliteObserver, parse_tle_file, NotVisibleError

import nyansat.host.satdata_client as SatelliteScraper


class NyanExplorer(MpFileExplorer, NyanPyboard):
    """Wrapper for MpFileExplorer that includes the new NyanPyboard functionality."""

    EL_SERVO_INDEX = "elevation_servo_index"
    AZ_SERVO_INDEX = "azimuth_servo_index"

    def __init__(self, *args):
        self.tracking = None
        super().__init__(*args)

    def is_antenna_initialized(self):
        """Test if there is an AntKontrol object on the board"""
        try:
            self.exec_("isinstance(api, antenny.AntennyAPI)")
            return True
        except PyboardError:
            return False

    def which_config(self):
        """Get the name of the currently used config file."""
        return self.eval_string_expr("api.config.current_file()")

    def config_get(self, key):
        """Get the value of an individual config parameter.

        Arguments:
        key -- name of config parameter.
        """
        command = "api.config.get(\"{}\")".format(key)
        return self.eval_string_expr(command)

    def config_set(self, key, val):
        """Set an individual parameter in the config file.

        Arguments:
        key -- name of config parameter. Tab complete to see choices.
        val -- value of paramter
        """
        if isinstance(val, int) or isinstance(val, float):
            self.exec_("api.config.set(\"%s\", %d)" % (key, val))
        elif isinstance(val, str):
            self.exec_("api.config.set(\"%s\", %s)" % (key, val))

    def config_get_default(self, key):
        """Get the default value of a config parameter.

        Arguments:
        key -- name of config parameter.
        """
        return self.eval_string_expr("api.config.get_default(\"{}\")".format(key))

    def config_new(self, name):
        """Create a new config file on the ESP32.

        Arguments:
        name -- name of new config file.
        """
        self.exec_("api.config.new(\"{}\")".format(name))

    def config_switch(self, name):
        """Switch to using a different config file.

        Arguments:
        name -- name of config file.
        """
        self.exec_("api.config.switch(\"{}\")".format(name))

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
        return json.loads(self.eval_string_expr("api.imu.get_calibration_status()"))

    def imu_save_calibration_profile(self):
        """Save the current IMU calibration as 'calibration.json'."""
        return self.eval_string_expr("api.imu.save_calibration_profile('calibration.json')")

    def imu_upload_calibration_profile(self):
        """Upload 'calibration.json' to the IMU."""
        return self.eval_string_expr("api.imu.upload_calibration_profile('calibration.json')")

    def motor_test(self, index, pos):
        """Run a motor accuracy test, for testing the disparity between the motor and IMU.

        Arguments:
        index -- index of motor on the PWM driver.
        pos -- desired angle.
        """
        return ast.literal_eval(self.eval_string_expr("api.antenna.motor_test({}, {})".format(index, pos)))

    def set_elevation_degree(self, el_angle):
        """Set the elevation angle.

        Arguments:
        el_angle -- desired elevation angle.
        """
        self.eval_string_expr("api.antenna.set_elevation({})".format(el_angle))

    def set_azimuth_degree(self, az_angle):
        """Set the azimuth angle.

        Arguments:
        az_angle -- desired azimuth angle.
        """
        self.eval_string_expr("api.antenna.set_azimuth({})".format(az_angle))

    def create_antkontrol(self):
        """Create an antkontrol object on the ESP32."""
        try:
            ret = self.exec_("import antenny")
            ret = self.exec_("api = antenny.esp32_antenna_api_factory()")
            self.antenna_initialized = True
            return ret.decode()
        except PyboardError:
            raise PyboardError("Could not create antkontrol object")

    def delete_antkontrol(self):
        """Delete the existing antkontrol object on the ESP32."""
        try:
            ret = self.exec_("del(api)")
            self.antenna_initialized = False
            return ret.decode()
        except PyboardError:
            raise PyboardError("Could not create antkontrol object")

    def is_tracking(self):
        return self.tracking

    def _track_update(self, observer):
        """Update the antenna position every 2 seconds"""
        print(f"Tracking {observer.sat_name} ...")
        while self.tracking:
            elevation, azimuth, distance = observer.get_current_stats()
            self.set_elevation_degree(elevation)
            self.set_azimuth_degree(azimuth)
            sleep(2)

    async def track(self, sat_name):
        """Track a satellite across the sky"""
        coords = (40.0, -73.0)
        tle_data_encoded = await SatelliteScraper.load_tle()
        tle_data = parse_tle_file(tle_data_encoded)
        observer = SatelliteObserver.parse_tle(coords, sat_name, tle_data)

        if not observer.get_visible():
            self.cancel()
            raise NotVisibleError
        t = threading.Thread(target=self._track_update, args=(observer,))
        t.start()

    def wrap_track(self, sat_name):
        """Entry point for tracking mode"""
        self.tracking = True
        asyncio.run(self.track(sat_name))

    def cancel(self):
        """Cancel tracking mode"""
        self.tracking = False


class NyanExplorerCaching(NyanExplorer, MpFileExplorerCaching):
    """Wrapper for MpFileExplorerCaching that includes the new NyanPyboard/NyanExplorer functionality."""
    pass
