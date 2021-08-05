# Client middle layer
import ast
import asyncio
import getpass
import json
import logging
import threading
from pydoc import locate

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

LOG = logging.getLogger("antenny_client")

class AntennyClient(object):

    def __init__(self):
        self.initialized = False
        self.fe: MpFileExplorer = None
        self.invoker: CommandInvoker = None

    @exception_handler
    def reboot(self):
        if self.fe:
            self.fe.con.serial.setDTR(False)
            self.fe.con.serial.setDTR(True)

    @exception_handler
    def initialize_client(self, fe: MpFileExplorer):
        if fe:
            self.fe = fe
            self.invoker = CommandInvoker(fe.con)
            self.initialized = True

    @exception_handler
    def safemode_guard(self):
        if self.invoker.antenny_is_safemode():
            raise SafeModeWarning

    @exception_handler
    def guard_open(self):
        if self.fe is None or self.invoker is None:
            raise DeviceNotOpenError

    @exception_handler
    def guard_init(self):
        if not self.initialized:
            raise NoAntKontrolError

    @exception_handler
    def initialize_components(self):
        self.invoker.imu_init()
        self.invoker.pwm_controller_init()
        self.invoker.elevation_servo_init()
        self.invoker.azimuth_servo_init()
        self.invoker.screen_init()
        self.invoker.gps_init()
        self.invoker.telemetry_init()
        self.invoker.platform_init()

    @exception_handler
    def save_all(self, name: str = None, force: bool = False):
        self.invoker.antenny_config_save(name=name, force=force)
        self.invoker.antenny_config_make_default()
        self.invoker.elevation_servo_save(name=name, force=force)
        self.invoker.azimuth_servo_save(name=name, force=force)
        self.invoker.servo_make_default()
        self.invoker.imu_save(name=name, force=force)

    @exception_handler
    def auto_calibrate(self):
        self.invoker.platform_auto_calibrate_azimuth_servo()
        self.invoker.platform_auto_calibrate_elevation_servo()
        self.invoker.platform_auto_calibrate_magnetometer()
        self.invoker.platform_auto_calibrate_gyroscope()
        self.invoker.platform_auto_calibrate_accelerometer()

    @exception_handler
    def set_azimuth(self, azimuth):
        self.invoker.platform_set_azimuth(azimuth)

    @exception_handler
    def set_elevation(self, elevation):
        self.invoker.platform_set_elevation(elevation)

    @exception_handler
    def set_coordinates(self, azimuth, elevation):
        self.invoker.platform_set_coordinates(azimuth, elevation)
