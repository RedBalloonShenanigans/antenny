# Client middle layer
import ast
import asyncio
import getpass
import json
import logging
import threading

from time import sleep
from dataclasses import dataclass
from typing import List

from nyansat.host.shell.terminal_printer import TerminalPrinter
from nyansat.host.shell.command_invoker import CommandInvoker
from nyansat.host.shell.errors import *

from mp.pyboard import PyboardError
from mp.mpfexp import MpFileExplorer
from nyansat.host.shell.nyan_pyboard import NyanPyboard

from nyansat.host.satellite_observer import SatelliteObserver, parse_tle_file


import nyansat.host.satdata_client as SatelliteScraper


class AntennyClient(object):

    def __init__(self, caching):
        self.caching = caching
        self.fe = None
        self.invoker = None
        self.tracking = None
        self.prompts = {
            "antenny_board_version": ("Antenny Board Version (integer, -1 for DIY)", int),
            "gps_uart_tx": ("GPS UART TX pin#", int),
            "gps_uart_rx": ("GPS UART RX pin#", int),
            "use_gps": ("Use GPS (True or False)", bool),
            "latitude": ("Current position latitude (ignore if using GPS)", float),
            "longitude": ("Current position longitude (ignore if using GPS)", float),
            "i2c_servo_scl": ("Servo SCL pin#", int),
            "i2c_servo_sda": ("Servo SDA pin#", int),
            "i2c_servo_address": ("Servo address (in decimal)", int),
            "i2c_bno_scl": ("BNO055 SCL pin#", int),
            "i2c_bno_sda": ("BNO055 SDA pin#", int),
            "i2c_bno_address": ("BNO055 address (in decimal)", int),
            "use_imu": ("Use IMU (True or False)", bool),
            "i2c_screen_scl": ("Screen SCL pin#", int),
            "i2c_screen_sda": ("Screen SDA pin#", int),
            "i2c_screen_address": ("Screen address (in decimal)", int),
            "use_screen": ("Use Screen (True or False)", bool),
            "elevation_servo_index": ("Servo default elevation index", float),
            "azimuth_servo_index": ("Servo default azimuth index", float),
            "elevation_max_rate": ("Servo elevation max rate", float),
            "azimuth_max_rate": ("Servo azimuth max rate", float),
            "use_webrepl": ("Use WebREPL", bool),
            "use_telemetry": ("Use Telemetry", bool),
            "enable_demo": ("Enable movement demo (short pin#15 to ground)", bool)
        }

    def initialize(self, fe: MpFileExplorer):
        if fe:
            self.fe = fe
            self.invoker = CommandInvoker(fe.con)

    def safemode_guard(self):
        """Warns user if AntKontrol is in SAFE MODE while using motor-class commands"""
        if self.invoker.is_safemode():
            raise SafeModeWarning

    def guard_open(self):
        if self.fe is None or self.invoker is None:
            raise DeviceNotOpenError

    def guard_init(self):
        if not self.invoker.is_antenna_initialized():
            raise NoAntKontrolError

    def guard_config_status(self):
        if not self.invoker.config_status():
            raise ConfigStatusError

    @exception_handler
    def startmotion(self, az, el):
        self.guard_open()
        self.guard_init()
        self.safemode_guard()
        self.invoker.start_motion(az, el)

    @exception_handler
    def elevation(self, el):
        self.guard_open()
        self.guard_init()
        self.safemode_guard()
        self.invoker.set_elevation_degree(el)

    @exception_handler
    def azimuth(self, az):
        self.guard_open()
        self.guard_init()
        self.safemode_guard()
        self.invoker.set_azimuth_degree(az)

    @exception_handler
    def antkontrol(self, mode):
        self.guard_open()
        if mode == 'start':
            if self.invoker.is_antenna_initialized():
                self.invoker.delete_antkontrol()

            # TODO: raise BNO055UploadError in nyan_explorer
            ret = self.invoker.create_antkontrol()
            self.safemode_guard()
            if self.invoker.is_antenna_initialized():
                print("AntKontrol initialized")
            else:
                raise AntKontrolInitError
        elif mode == 'status':
            self.guard_init()
            if self.invoker.is_safemode():
                print("AntKontrol is running in SAFE MODE")
            else:
                print("AntKontrol appears to be initialized properly")

    @exception_handler
    def track(self, sat_name):
        self.guard_open()
        self.guard_init()
        imu_enabled = self.invoker.config_get("use_imu")
        if imu_enabled == 'False':
            TerminalPrinter.print_track_warning()
        self.invoker.set_tracking(True)
        latitude = float(self.invoker.config_get("latitude"))
        longitude = float(self.invoker.config_get("longitude"))
        asyncio.run(self._start_track(sat_name, (latitude, longitude)))

    @exception_handler
    def cancel(self):
        # TODO: Same as for track
        self.guard_open()
        self.guard_init()
        if self.invoker.is_tracking():
            self._cancel()
        else:
            raise NotTrackingError

    @exception_handler
    def upload_calibration(self):
        self.guard_open()
        self.guard_init()

        # TODO: raise BNO055UploadError in nyan_explorer
        status = self.invoker.imu_upload_calibration_profile()
        if not status:
            raise BNO055UploadError

    @exception_handler
    def save_calibration(self):
        self.guard_open()
        self.guard_init()

        # TODO: raise BNO055UploadError in nyan_explorer
        status = self.invoker.imu_save_calibration_profile()
        if not status:
            raise BNO055RegistersError

    @exception_handler
    def calibrate(self):
        self.guard_open()
        print("Detecting calibration status ...")
        data = self.invoker.imu_calibration_status()
        data = (data['system'], data['gyroscope'], data['accelerometer'], data['magnetometer'])
        if not data:
            TerminalPrinter.print_error("Error connecting to BNO055.")
            return

        system_level, gyro_level, accel_level, magnet_level = data
        system_calibrated = system_level > 0
        gyro_calibrated = gyro_level > 0
        accel_calibrated = accel_level > 0
        magnet_calibrated = magnet_level > 0
        components_calibrated = (system_calibrated, gyro_calibrated, accel_calibrated, magnet_calibrated)
        TerminalPrinter.display_initial_calibration_status(components_calibrated)

        waiting_dot_count = 4
        dot_counter = 0
        sleep(1)
        while not (magnet_calibrated and accel_calibrated and gyro_calibrated):
            sleep(0.5)
            old_calibration_status = (system_calibrated, gyro_calibrated, accel_calibrated, magnet_calibrated)
            system_calibrated, gyro_calibrated, accel_calibrated, magnet_calibrated = TerminalPrinter.display_loop_calibration_status(
                data,
                old_calibration_status,
                waiting_dot_count,
                dot_counter
            )

            # Re-fetch calibration data
            data = self.invoker.imu_calibration_status()
            data = (data['system'], data['gyroscope'], data['accelerometer'], data['magnetometer'])
            if not data:
                TerminalPrinter.print_error("Error connecting to BNO055.")
                return

            dot_counter = (dot_counter + 1) % waiting_dot_count

        print(f"System calibration complete: {TerminalPrinter.YES_DISPLAY_STRING}")
        print("Saving calibration data ...")
        # self.do_save_calibration(None)
        self.save_calibration()
        print("Calibration data is now saved to config.")

    @exception_handler
    def i2ctest(self):
        self.guard_open()
        print("Input the SDA pin and SCL for the I2C bus to check")

        try:
            sda = int(input("SDA Pin#: "))
            scl = int(input("SCL Pin#: "))
        except ValueError:
            raise PinInputError

        # TODO: raise appropriate error in nyan_explorer
        addresses = self.invoker.i2c_scan(sda, scl)
        addresses_list = addresses.strip('] [').strip(', ')
        if not addresses_list:
            raise I2CNoAddressesError
        else:
            print("Found the following device addresses: {}".format(addresses_list))
        print("If you had a running AntKontrol instance, be sure to restart it")

    @exception_handler
    def motor_test(self, motor, pos):
        self.guard_open()
        self.guard_init()
        self.safemode_guard()
        if motor == 'EL':
            index = self.invoker.config_get(self.invoker.EL_SERVO_INDEX)
        elif motor == "AZ":
            index = self.invoker.config_get(self.invoker.AZ_SERVO_INDEX)
        else:
            # Shouldn't happen
            raise ValueError
        data = self.invoker.motor_test(index, pos)
        real_pos, x_angle, y_angle, z_angle = data

        print("real imu angles: %d", real_pos)
        print("expected position: %d", real_pos)

    @exception_handler
    def setup(self, name):
        self.guard_open()
        current = self.invoker.which_config()
        self.invoker.config_new(name)
        print("Welcome to Antenny!")
        print("Please enter the following information about your hardware\n")

        for k, info in self.prompts.items():
            prompt_text_bare, typ = info
            default_val = self.invoker.config_get_default(k)
            prompt_text = prompt_text_bare + " (Default value is {}): ".format(default_val)
            try:
                if typ == bool:
                    literal_input = input(prompt_text)
                    if literal_input == "False" or literal_input == "0":
                        new_val = False
                    elif literal_input == "True" or literal_input == "1":
                        new_val = True
                    else:
                        raise ValueError
                else:
                    new_val = typ(input(prompt_text))

            except ValueError:
                new_val = self.invoker.config_get_default(k)
                print("Invalid type, setting to default value \"{}\".\nUse \"set\" to "
                      "change the parameter".format(new_val))

            self.invoker.config_set(k, new_val)

        # TODO: figure this out, do we need this (make caching by default?)
        if self.caching:
            self.fe.cache = {}

        print("\nConfiguration set for \"{}\"!\n".format(name) +
              "You can use \"set\" to change individual parameters\n"
              "or \"edit\" to change the config file "
              "directly")

    @exception_handler
    def set(self, key, new_val):
        self.guard_open()

        # TODO: raise appropriate NoSuchConfig error in nyan_explorer
        old_val = self.invoker.config_get(key)
        _, typ = self.prompts[key]
        new_val = typ(new_val)

        self.invoker.config_set(key, new_val)
        print("Changed " + "\"" + key + "\" from " + str(old_val) + " --> " + str(new_val))

    @exception_handler
    def configs(self):
        # TODO: Something with ConfigUnknownError
        self.guard_open()
        print("-Config parameters-\n" +
              "Using \"{}\"".format(self.invoker.which_config()))
        for key in self.prompts.keys():
            print(key + ": " + self.invoker.config_get(key))

    @exception_handler
    def switch(self, name):
        self.guard_open()
        self.guard_config_status()

        files = self.fe.ls()
        if name not in files:
            raise NoSuchConfigFileError
        current = self.invoker.which_config()
        self.invoker.config_switch(name)
        print("Switched from \"{}\"".format(current) +
              " to \"{}\"".format(name))

    @exception_handler
    def _track_update(self, observer):
        """Update the antenna position every 2 seconds"""
        print(f"Tracking {observer.sat_name} ...")
        while self.invoker.is_tracking():
            elevation, azimuth, distance = observer.get_current_stats()
            self.invoker.set_elevation_degree(elevation)
            self.invoker.set_azimuth_degree(azimuth)
            sleep(2)

    async def _start_track(self, sat_name, coords):
        """Track a satellite across the sky"""
        tle_data_encoded = await SatelliteScraper.load_tle()
        tle_data = parse_tle_file(tle_data_encoded)
        observer = SatelliteObserver.parse_tle(coords, sat_name, tle_data)

        if not observer.get_visible():
            self._cancel()
            raise NotVisibleError
        t = threading.Thread(target=self._track_update, args=(observer,))
        t.start()

    def _cancel(self):
        """Cancel tracking mode"""
        self.invoker.set_tracking(False)

    @exception_handler
    def wifi_setup(self):
        self.guard_open()
        wifi_config_path = 'wifi_config.json'
        try:
            wifi_config = {
                'ssid': input("WiFi SSID: "),
                'key': getpass.getpass("WiFi password: "),
            }
            with open(wifi_config_path, 'w') as f:
                json.dump(wifi_config, f)
            self.fe.put(wifi_config_path)
            print("SSID/Password successfully changed")
        except KeyboardInterrupt:
            print("WiFi setup canceled, using previous settings")

    @exception_handler
    def bno_test(self):
        self.guard_open()   # No need to guard for antenna initialization when doing diagnostics

        print("Input the SDA pin and SCL of the BNO device to test")
        try:
            sda = int(input("SDA Pin#: "))
            scl = int(input("SCL Pin#: "))
        except ValueError:
            TerminalPrinter.print_error("Invalid type for pin number. Try again using only decimal numbers")
            return

        bno_test_diagnostics = self.invoker.bno_diagnostics(sda, scl)
        print("---")
        print("I2C bus usable?", bno_test_diagnostics.i2c_bus_scannable)
        if len(bno_test_diagnostics.i2c_addresses) == 0:
            print("I2C address detected? False")
        else:
            print("I2C address detected? True, addresses =", bno_test_diagnostics.i2c_addresses)
        print("BNO connection established?", bno_test_diagnostics.bno_object_created)
        print("BNO calibrated?", bno_test_diagnostics.bno_object_calibrated)

    @exception_handler
    def pwm_test(self):
        self.guard_open()   # No need to guard for antenna initialization when doing diagnostics

        print("Input the SDA pin and SCL of the PWM driver to test")
        try:
            sda = int(input("SDA Pin#: "))
            scl = int(input("SCL Pin#: "))
        except ValueError:
            TerminalPrinter.print_error("Invalid type for pin number. Try again using only decimal numbers")
            return

        pwm_test_diagnostics = self.invoker.pwm_diagnostics(sda, scl)
        print("---")
        print("I2C bus usable?", pwm_test_diagnostics.i2c_bus_scannable)
        if len(pwm_test_diagnostics.i2c_addresses) == 0:
            print("I2C address detected? False")
        else:
            print("I2C address detected? True, addresses =", pwm_test_diagnostics.i2c_addresses)
        print("PWM connection established?", pwm_test_diagnostics.pca_object_created)
