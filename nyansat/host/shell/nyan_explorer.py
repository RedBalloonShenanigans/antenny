import ast
import asyncio
from dataclasses import dataclass
import json
import threading
from typing import List

from time import sleep

from mp.mpfexp import MpFileExplorer, MpFileExplorerCaching
from mp.pyboard import PyboardError
from nyansat.host.shell.nyan_pyboard import NyanPyboard

from nyansat.host.satellite_observer import SatelliteObserver, parse_tle_file
from nyansat.host.shell.errors import NotVisibleError

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
        return self.eval_string_expr(command)

    def config_set(self, key, val):
        """Set an individual parameter in the config file.

        Arguments:
        key -- name of config parameter. Tab complete to see choices.
        val -- value of paramter
        """
        if isinstance(val, int) or isinstance(val, float):
            self.exec_("config.set(\"%s\", %d)" % (key, val))
        elif isinstance(val, str):
            self.exec_("config.set(\"%s\", %s)" % (key, val))

    def config_get_default(self, key):
        """Get the default value of a config parameter.

        Arguments:
        key -- name of config parameter.
        """
        return self.eval_string_expr("config.get_default(\"{}\")".format(key))

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
        self.exec_("config.switch(\"{}\")".format(name))

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

    
    def bno_test(self, sda, scl):
        """
        Create a BNO controller object for the given I2C sda/scl configuration. Uses the default
        value of 40 for the BNO055 I2C address.
        :param sda: Pin number for sda
        :param scl: Pin number for scl
        :return: A BnoTestDiagnostics object containing relevant T/F information about the setup
        """
        i2c_bus_scannable = False
        i2c_addresses = []
        bno_object_created = False
        bno_object_calibrated = False

        # Test scanning I2C bus
        try:
            addresses = self.i2c_scan(sda, scl)
        except PyboardError:
            return BnoTestDiagnostics(
                i2c_bus_scannable,
                i2c_addresses,
                bno_object_created,
                bno_object_calibrated
            )
        i2c_bus_scannable = True

        # Test what's on the I2C bus and their addresses
        try:
            i2c_addresses = [int(n) for n in addresses.strip('] [').split(', ')]
            if not i2c_addresses:
                return BnoTestDiagnostics(
                    i2c_bus_scannable,
                    i2c_addresses,
                    bno_object_created,
                    bno_object_calibrated
                )
        except ValueError:
            return BnoTestDiagnostics(
                i2c_bus_scannable,
                i2c_addresses,
                bno_object_created,
                bno_object_calibrated
            )

        # Test creating BNO object
        try:
            self.exec_("from imu.imu_bno055 import Bno055ImuController")
            self.exec_("bno = Bno055ImuController(i2c)")
        except PyboardError:
            return BnoTestDiagnostics(
                i2c_bus_scannable,
                i2c_addresses,
                bno_object_created,
                bno_object_calibrated
            )
        bno_object_created = True

        # Test calibration status of BNO object
        try:
            calibration_status = json.loads(self.eval_string_expr("bno.get_calibration_status()"))
            bno_object_calibrated = calibration_status['system'] > 0
        except PyboardError:
            bno_object_calibrated = False

        return BnoTestDiagnostics(
            i2c_bus_scannable,
            i2c_addresses,
            bno_object_created,
            bno_object_calibrated
        )

    def pwm_test(self, sda, scl):
        """
        Create a PCA9685 controller object for the given I2C sda/scl configuration. Uses the default
        value of 40 for the controller's address.
        :param sda: Pin number for sda
        :param scl: Pin number for scl
        :return: A PwmTestDiagnostics object containing relevant T/F information about the setup
        """
        i2c_bus_scannable = False
        i2c_addresses = []
        pca_object_created = False

        # Test scanning I2C bus
        try:
            addresses = self.i2c_scan(sda, scl)
        except PyboardError:
            return PwmTestDiagnostics(
                i2c_bus_scannable,
                i2c_addresses,
                pca_object_created
            )
        i2c_bus_scannable = True

        # Test what's on the I2C bus and their addresses
        try:
            i2c_addresses = [int(n) for n in addresses.strip('] [').split(', ')]
            if not i2c_addresses:
                return PwmTestDiagnostics(
                    i2c_bus_scannable,
                    i2c_addresses,
                    pca_object_created
                )
        except ValueError:
            return PwmTestDiagnostics(
                i2c_bus_scannable,
                i2c_addresses,
                pca_object_created
            )

        # Test creating BNO object
        try:
            self.exec_("from motor.motor_pca9685 import Pca9685Controller")
            self.exec_("pca = Pca9685Controller(i2c)")
            pca_object_created = True
        except PyboardError:
            pca_object_created = False

        return PwmTestDiagnostics(
            i2c_bus_scannable,
            i2c_addresses,
            pca_object_created
        )

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
        index -- index of motor on the PWM driver (defaults: 0 == elevation, 1 == azimuth).
        pos -- desired angle.
        """
        return ast.literal_eval(self.eval_string_expr("api.motor_test({}, {})".format(index, pos)))

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
            ret = self.exec_("del(config)")
            ret = self.exec_("config = api.config")
            self.antenna_initialized = True
            return ret.decode()
        except PyboardError as e:
            self.exec_("from config.config import ConfigRepository")
            self.exec_("config = ConfigRepository")
            # This is ugly as SHIT. Needs to be fixed with PROPER error handling
            return e

    def delete_antkontrol(self):
        """Delete the existing antkontrol object on the ESP32."""
        try:
            ret = self.exec_("del(api)")
            self.antenna_initialized = False

            def __init__(self):
                super().__init__()
            return ret.decode()
        except PyboardError:
            pass

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
            pass

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


class NyanExplorerError(Exception):
    pass


@dataclass
class BnoTestDiagnostics:
    """Store diagnostic T/F values for BNO test. Used in the handling for 'bnotest' command."""
    i2c_bus_scannable: bool
    i2c_addresses: List[int]
    bno_object_created: bool
    bno_object_calibrated: bool

@dataclass
class PwmTestDiagnostics:
    """Store diagnostic T/F values for PWM test. Used in the handling for 'pwmtest' command."""
    i2c_bus_scannable: bool
    i2c_addresses: List[int]
    pca_object_created: bool
