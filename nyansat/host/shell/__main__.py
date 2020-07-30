import argparse
import cmd
import glob
import io
import logging
import os
import platform
import sys
import tempfile
import subprocess
import time
import shutil
from websocket import WebSocketConnectionClosedException

import colorama
import serial
from mp import mpfshell
from mp.mpfshell import MpFileShell
from mp.conbase import ConError
from mp.pyboard import PyboardError
from mp.tokenizer import Tokenizer

from nyansat.host.shell.nyan_explorer import NyanExplorerCaching, NyanExplorer, NotVisibleError
from nyansat.host.shell.cli_arg_parser import CLIArgumentProperty, parse_cli_args
from nyansat.host.shell.terminal_printer import TerminalPrinter
from nyansat.host.shell.antenny_client import AntennyClient


class NyanShell(mpfshell.MpFileShell):
    """Extension of MPFShell that adds NyanSat-specific features"""

    GYRO_CALIBRATION_MESSAGE = "To calibrate the gyroscope, let the sensor rest on a level surface for a few seconds."
    ACCEL_CALIBRATION_MESSAGE = "To calibrate the accelerometer, slowly move the sensor into >=6 distinct orientations,\nsome perpendicular to the xyz axes."
    MAGNET_CALIBRATION_MESSAGE = "To calibrate the magnetometer, move the sensor in figure-8 shapes through the air a few times."

    def __init__(self, color=False, caching=False, reset=False):
        """Creates Cmd-based shell object.

        Keyword arguments:
        color -- support colored text in the shell
        caching -- support caching the results of functions like 'ls'
        reset -- hard reset device via DTR. (serial connection only)
        """
        if color:
            colorama.init()
            cmd.Cmd.__init__(self, stdout=colorama.initialise.wrapped_stdout)
        else:
            cmd.Cmd.__init__(self)

        self.emptyline = lambda: None

        if platform.system() == "Windows":
            self.use_rawinput = False

        self.color = color
        self.caching = caching
        self.reset = reset

        self.fe = None
        self.repl = None
        self.tokenizer = Tokenizer()

        self.printer = TerminalPrinter()
        self.client = AntennyClient(self.fe, self.printer)
        self._intro()
        self._set_prompt_path()

        self.emptyline = lambda: None
        self.prompts = {
            "gps_uart_tx": ("GPS UART TX pin#: ", int),
            "gps_uart_rx": ("GPS UART RX pin#: ", int),
            "use_gps": ("Use GPS (true or false): ", bool),
            "i2c_servo_scl": ("Servo SCL pin#: ", int),
            "i2c_servo_sda": ("Servo SDA pin#: ", int),
            "i2c_servo_address": ("Servo address (in decimal): ", int),
            "i2c_bno_scl": ("BNO055 SCL pin#: ", int),
            "i2c_bno_sda": ("BNO055 SDA pin#: ", int),
            "i2c_bno_address": ("BNO055 address (in decimal): ", int),
            "use_imu": ("Use IMU (true or false): ", bool),
            "i2c_screen_scl": ("Screen SCL pin#: ", int),
            "i2c_screen_sda": ("Screen SDA pin#: ", int),
            "i2c_screen_address": ("Screen address (in decimal): ", int),
            "use_screen": ("Use Screen (true or false): ", bool),
            "elevation_servo_index": ("Servo default elevation index: ", float),
            "azimuth_servo_index": ("Servo default azimuth index: ", float),
            "elevation_max_rate": ("Servo elevation max rate: ", float),
            "azimuth_max_rate": ("Servo azimuth max rate: ", float),
            "use_webrepl": ("Use WebREPL: ", bool),
            "use_telemetry": ("Use Telemetry: ", bool)
        }

    def _intro(self):
        """Text that appears when shell is first launched."""
        self.intro = (
            "\n** Welcome to NyanSat File Shell **\n"
        )
        self.intro += "-- Running on Python %d.%d using PySerial %s --\n" % (
            sys.version_info[0],
            sys.version_info[1],
            serial.VERSION,
        )

    def _is_open(self):
        """Check if a connection has been established with an ESP32."""
        return super()._MpFileShell__is_open()

    def _disconnect(self):
        return super()._MpFileShell__disconnect()

    def _error(self, err):
        return super()._MpFileShell__error(err)

    def _parse_file_names(self, args):
        return super()._MpFileShell__parse_file_names(args)

    def _set_prompt_path(self):
        """Prompt that appears at the beginning of every line in the shell."""
        if self.fe is not None:
            pwd = self.fe.pwd()
        else:
            pwd = "/"
            self.prompt = "nyanshell [" + pwd + "]> "

    def parse_error(self, e):
        error_list = str(e).strip('()').split(", b'")
        error_list[0] = error_list[0][1:]
        ret = []
        for err in error_list:
            ret.append(bytes(err[0:-1], 'utf-8').decode('unicode-escape'))
        return ret

    def print_error_and_exception(self, error, exception):
        self.printer.print_error(error)
        error_list = self.parse_error(exception)
        try:
            print(error_list[2])
        except:
            pass

    def _connect(self, port):
        """Attempt to connect to the ESP32.

        Arguments:
        port -- (see do_open). Specify how to connect to the device.
        """
        try:
            self._disconnect()

            if self.reset:
                print("Hard resetting device ...")
            if self.caching:
                self.fe = NyanExplorerCaching(port, self.reset)
            else:
                self.fe = NyanExplorer(port, self.reset)
            print("Connected to %s" % self.fe.sysname)
            self._set_prompt_path()
        except PyboardError as e:
            logging.error(e)
            self.printer.print_error(str(e))
        except ConError as e:
            logging.error(e)
            self.printer.print_error("Failed to open: %s" % port)
        except AttributeError as e:
            logging.error(e)
            self.printer.print_error("Failed to open: %s" % port)
        return False

    def do_open(self, args):
        """open <TARGET>
        Open connection to device with given target. TARGET might be:
        - a serial port, e.g.       ttyUSB0, ser:/dev/ttyUSB0
        - a telnet host, e.g        tn:192.168.1.1 or tn:192.168.1.1,login,passwd
        - a websocket host, e.g.    ws:192.168.1.1 or ws:192.168.1.1,passwd
        """

        if not len(args):
            self.printer.print_error("Missing argument: <PORT>")
            return False

        if (
                not args.startswith("ser:/dev/")
                and not args.startswith("ser:COM")
                and not args.startswith("tn:")
                and not args.startswith("ws:")
        ):

            if platform.system() == "Windows":
                args = "ser:" + args
            else:
                args = "ser:/dev/" + args

        return self._connect(args)

    def do_repl(self, args):
        try:
            super().do_repl(args)
        except WebSocketConnectionClosedException as e:
            self.printer.print_error("Connection lost to repl")
            self._disconnect()

    def do_edit(self, args):
        """edit <REMOTE_FILE>
        Copies file over, opens it in your editor, copies back when done.
        """
        if not len(args):
            self.printer.print_error("Missing argument: <REMOTE_FILE>")

        elif self._is_open():
            rfile_name, = self._parse_file_names(args)
            local_name = "__board_" + rfile_name
            try:
                self.fe.get(rfile_name, local_name)
            except IOError as e:
                if "No such file" in str(e):
                    # make new file locally, then copy
                    pass
                else:
                    self.printer.print_error(str(e))
                    return

            if platform.system() == 'Windows':
                EDITOR = os.environ.get('EDITOR', 'notepad')
                subprocess.call([EDITOR, local_name], shell=True)
            else:
                EDITOR = os.environ.get('EDITOR', 'vim')
                subprocess.call([EDITOR, local_name])
            self.fe.put(local_name, rfile_name)

    complete_edit = MpFileShell.complete_get

    def parse_error(self, e):
        error_list = str(e).strip('()').split(", b'")
        error_list[0] = error_list[0][1:]
        ret = []
        for err in error_list:
            ret.append(bytes(err[0:-1], 'utf-8').decode('unicode-escape'))
        return ret

    def do_test(self, args):
        print(args)

    def do_setup(self, args):
        """setup <CONFIG_FILE>
        Interactive script to populate a config file.
        Switches to new config after finishing setup.
        To keep config persistent after reboots, name it "config.json"
        """
        arg_properties = [
            CLIArgumentProperty(
                str,
                None
            )
        ]
        parsed_args = parse_cli_args(args, 'setup', 1, arg_properties)
        if self._is_open():

            try:
                if self.fe.config_status():
                    name, = parsed_args
                    current = self.fe.which_config()

                    self.fe.config_new(name)

                    print(colorama.Fore.GREEN +
                          "Welcome to Antenny!" +
                          colorama.Fore.RESET)
                    print("Please enter the following information about your hardware\n")

                    for k, info in self.prompts.items():
                        prompt_text, typ = info
                        try:
                            new_val = typ(input(prompt_text))
                        except ValueError:
                            new_val = self.fe.config_get_default(k)
                            self.printer.print_error("Invalid type, setting to default value \"{}\".\nUse \"set\" to " \
                                        "change the parameter".format(new_val))

                        self.fe.config_set(k, new_val)

                    if self.caching:
                        self.fe.cache = {}

                    print(colorama.Fore.GREEN +
                          "\nConfiguration set for \"{}\"!\n".format(name) +
                          colorama.Fore.RESET +
                          "You can use \"set\" to change individual parameters\n" \
                          "or \"edit\" to change the config file " \
                          "directly")
                else:
                    self.printer.print_error("Could not access existing configuration object or create one.")

            except PyboardError as e:
                self.printer.print_error_and_exception("Command faulted while trying to set configuration", e)

    def do_set(self, args):
        """set <CONFIG_PARAM> <NEW_VAL>
        Set a parameter in the configuration file to a new value."""
        if self._is_open():
            arg_properties = [
                CLIArgumentProperty(
                    str,
                    None
                )
            ]
            parsed_args = parse_cli_args(args, 'set', 1, arg_properties)
            try:
                if self.fe.config_status():
                    key, new_val = parsed_args
                    try:
                        old_val = self.fe.config_get(key)
                    except:
                        self.printer.print_error("No such configuration parameter")
                        return

                    _, typ = self.prompts[key]
                    try:
                        new_val = typ(new_val)
                    except ValueError as e:
                        self.printer.print_error(str(e))
                        return

                    self.fe.config_set(key, new_val)
                    print("Changed " + "\"" + key + "\" from " + str(old_val) + " --> " + str(new_val))
                else:
                    self.printer.print_error("Could not access existing configuration object or create one.")
            except PyboardError as e:
                self.printer.print_error_and_exception("Command faulted while trying to set configuration", e)

    def complete_set(self, *args):
        """Tab completion for 'set' command."""
        if self._is_open():
            return [key for key in self.prompts.keys() if key.startswith(args[0])]
        else:
            return []

    def do_configs(self, args):
        """configs
        Print a list of all configuration parameters."""
        if self._is_open():
            try:
                if self.fe.config_status():
                    print("-Config parameters-\n" +
                          "Using \"{}\"".format(self.fe.which_config())
                          )
                    for key in self.prompts.keys():
                        print(key + ": " + self.fe.config_get(key))
                else:
                    self.printer.print_error("Could not access existing configuration object or create one.")
            except PyboardError as e:
                self.printer.print_error_and_exception("Command faulted while trying to access configuration", e)

    def do_switch(self, args):
        """switch <CONFIG_FILE>
        Switch to using a different config file."""
        arg_properties = [
            CLIArgumentProperty(
                str,
                None
            )
        ]
        parsed_args = parse_cli_args(args, 'switch', 1, arg_properties)
        if self._is_open():
            try:
                if self.fe.config_status():
                    name, = parsed_args
                    files = self.fe.ls()
                    if name not in files:
                        self.printer.print_error("No such file")
                        return
                    current = self.fe.which_config()
                    self.fe.config_switch(name)
                    print("Switched from \"{}\"".format(current) +
                          " to \"{}\"".format(name))
                else:
                    self.printer.print_error("Could not access existing configuration object or create one.")

            except PyboardError as e:
                self.printer.print_error_and_exception("Command faulted while trying to access or set new configuration", e)

    def do_i2ctest(self, args):
        """i2ctest
        Scan an i2c bus for i2c device addresses
        """
        try:
            print("Input the SDA pin and SCL for the I2C bus to check")

            try:
                sda = int(input("SDA Pin#: "))
                scl = int(input("SCL Pin#: "))
            except ValueError:
                self.printer.print_error("Invalid type for pin number. Try again using only decimal numbers")
                return
            addresses = self.fe.i2c_scan(sda, scl)
            addresses_list = addresses.strip('] [').strip(', ')
            if not addresses_list:
                print("Did not find any devices")
            else:
                print("Found the following device addresses: {}".format(addresses_list))
            print("If you had a running AntKontrol instance, be sure to restart it")
            return
        except PyboardError as e:
            self.printer.print_error_and_exception("Unable to scan the I2C bus", e)

    def complete_switch(self, *args):
        """Tab completion for switch command."""
        try:
            files = self.fe.ls(add_dirs=False)
        except Exception:
            files = []
        current = self.fe.which_config()
        return [f for f in files if f.startswith(args[0]) and f.endswith(".json")]

    def _calibration_wait_message(self, gyro_calibrated, accel_calibrated, magnet_calibrated, use_ellipsis=True):
        """
        generate a human-readable message that indicates which components remain
        to be calibrated, e.g. if all the arguments are true, then it should
        return the string "waiting for gyroscope, accelerometer and magnetometer
        to be calibrated...".
        """
        components = ((['gyroscope'] if not gyro_calibrated else []) +
                      (['accelerometer'] if not accel_calibrated else []) +
                      (['magnetometer'] if not magnet_calibrated else []))
        components_list_string = ', '.join(components[:-2] + [" and ".join(components[-2:])])
        if components:
            return ("waiting for " + components_list_string +
                    " to be calibrated" + ("..." if use_ellipsis else ""))
        else:
            return "all components calibrated!"

    def do_calibrate(self, args):
        """calibrate
        Detect IMU calibration status and provide instructions on how to
        calibrate if necessary. If calibration is necessary, wait for the user
        to calibrate the device and cease waiting once all sensors are
        calibrated. Regardless of whether calibration is necessary or not, save
        the calibration profile to the config at the end.
        """
        try:
            if args:
                self.printer.print_error("Usage: calibrate does not take arguments.")
                return

            if self._is_open() and self.fe.is_antenna_initialized():
                print("Detecting calibration status ...")
                data = self.fe.imu_calibration_status()
                data = (data['system'], data['gyroscope'], data['accelerometer'], data['magnetometer'])
                if not data:
                    self.printer.print_error("Error connecting to BNO055.")
                    return

                yes_display_string = colorama.Fore.GREEN + "YES" + colorama.Fore.RESET
                no_display_string = colorama.Fore.RED + "NO" + colorama.Fore.RESET

                system_level, gyro_level, accel_level, magnet_level = data
                system_calibrated = system_level > 0
                gyro_calibrated = gyro_level > 0
                accel_calibrated = accel_level > 0
                magnet_calibrated = magnet_level > 0

                print("System calibrated?",
                      f"{yes_display_string}" if system_calibrated else no_display_string)

                print("\n")
                if gyro_calibrated:
                    print(" - Gyroscope is calibrated.")
                else:
                    print(f" - {self.GYRO_CALIBRATION_MESSAGE}")

                if accel_calibrated:
                    print(" - Accelerometer is calibrated.")
                else:
                    print(f" - {self.ACCEL_CALIBRATION_MESSAGE}")

                if magnet_calibrated:
                    print(" - Magnetometer is calibrated.")
                else:
                    print(f" - {self.MAGNET_CALIBRATION_MESSAGE}")
                print("\n")

                overwrite_old_text = False
                waiting_dot_count = 4
                dot_counter = 0
                while not (magnet_calibrated and accel_calibrated and gyro_calibrated):
                    time.sleep(0.5)
                    if overwrite_old_text:
                        # This magic number 7 is linked to the number of lines
                        # printed out below in the calibration status panel.
                        # TODO: constant bad
                        for i in range(7):
                            print("\x1b[2A\x1b[2K")
                    else:
                        overwrite_old_text = True

                    system_level, gyro_level, accel_level, magnet_level = data
                    if not gyro_calibrated and gyro_level > 0:
                        gyro_calibrated = True
                    if not accel_calibrated and accel_level > 0:
                        accel_calibrated = True
                    if not magnet_calibrated and magnet_level > 0:
                        magnet_calibrated = True
                    if not system_calibrated and system_level > 0:
                        system_calibrated = True

                    # Print the calibration status panel: this is the section that
                    # automatically refereshes.
                    waiting_dots = ('.' * dot_counter) + '/' + ('.' * (waiting_dot_count - dot_counter - 1))
                    print("┌ CALIBRATION STATUS")
                    print("│")
                    print("│ * Gyroscope calibrated?",
                          f"{yes_display_string} (level {gyro_level}/3)" if gyro_calibrated else no_display_string)
                    print("│ * Accelerometer calibrated?",
                          f"{yes_display_string} (level {accel_level}/3)" if accel_calibrated else no_display_string)
                    print("│ * Magnetometer calibrated?",
                          f"{yes_display_string} (level {magnet_level}/3)" if magnet_calibrated else no_display_string)
                    print("│")
                    wait_message = self.printer.calibration_wait_message(gyro_calibrated, accel_calibrated, magnet_calibrated,
                                                                  use_ellipsis=False)
                    wait_message += (" " + waiting_dots if wait_message else "")

                    # Write the wait message with an appropriate amount of trailing whitespace in order
                    # to clear the line from previous longer writes
                    terminal_width, _ = shutil.get_terminal_size()
                    spacing_length = max(min(terminal_width - 3 - len(wait_message), 20), 0)
                    print(f"└ {wait_message}", " " * spacing_length)

                    # Re-fetch calibration data
                    data = self.fe.imu_calibration_status()
                    data = (data['system'], data['gyroscope'], data['accelerometer'], data['magnetometer'])
                    if not data:
                        self.printer.print_error("Error connecting to BNO055.")
                        return

                    dot_counter = (dot_counter + 1) % waiting_dot_count

                print(f"System calibration complete: {yes_display_string}")
                print("Saving calibration data ...")
                self.do_save_calibration(None)
                print("Calibration data is now saved to config.")
            else:
                self.printer.print_error("Please run 'antkontrol start' to initialize the antenna.")

        except PyboardError as e:
            self.printer.print_error_and_exception(
                "The AntKontrol object is either not responding or your current configuration does not support IMU "
                "calibration.",
                e
            )
            print("You can try to restart AntKontrol by running 'antkontrol start'")
            print("If you believe your configuration is incorrect, run 'configs' to check your configuration and "
                  "'setup <CONFIG_FILE>' to create a new one\n")

    def do_save_calibration(self, args):
        """save_calibration
        Save current IMU calibration data to the current configuration.
        """
        if self._is_open():
            try:
                if self.fe.is_antenna_initialized():
                    status = self.fe.imu_save_calibration_profile()

                    if not status:
                        self.printer.print_error("Error: BNO055 not detected or error in reading calibration registers.")
                else:
                    self.printer.print_error("Please run 'antkontrol start' to initialize the antenna.")
            except PyboardError as e:
                self.printer.print_error_and_exception(
                    "The AntKontrol object is either not responding or your current configuration does not support IMU "
                    "calibration.",
                    e
                )
                print("You can try to restart AntKontrol by running 'antkontrol start'")
                print("If you believe your configuration is incorrect, run 'configs' to check your configuration and "
                      "'setup <CONFIG_FILE>' to create a new one\n")

    def do_upload_calibration(self, args):
        """upload_calibration
        Upload the currently stored calibration data to the connected IMU.
        """
        if self._is_open():
            try:
                if self.fe.is_antenna_initialized():
                    status = self.fe.imu_upload_calibration_profile()

                    if not status:
                        self.printer.print_error("Error: BNO055 not detected or error in writing calibration registers.")
                else:
                    self.printer.print_error("Please run 'antkontrol start' to initialize the antenna.")
            except PyboardError as e:
                self.printer.print_error_and_exception(
                    "The AntKontrol object is either not responding or your current configuration does not support IMU "
                    "calibration.",
                    e
                )
                print("You can try to restart AntKontrol by running 'antkontrol start'")
                print("If you believe your configuration is incorrect, run 'configs' to check your configuration and "
                      "'setup <CONFIG_FILE>' to create a new one\n")

    def do_motortest(self, args):
        """motortest <EL | AZ> <ANGLE>
        Test the motors to plot their accuracy against the measured IMU values.
        """
        if self._is_open():
            arg_properties = [
                CLIArgumentProperty(
                    str,
                    {
                        'EL', 'AZ'
                    }
                ),
                CLIArgumentProperty(
                    float,
                    {
                        None
                    }
                )
            ]
            parsed_args = parse_cli_args(args, 'motortest', 2, arg_properties)
            error_str = "The first parameter must be EL or AZ. <ANGLE> must be an integer or float"
            try:
                if self.fe.is_antenna_initialized():
                    print("Running motor testing routine...")
                    self.client.safemode_guard()
                    try:
                        motor, pos = parsed_args
                        if motor == "EL":
                            index = self.fe.config_get(self.fe.EL_SERVO_INDEX)
                        elif motor == "AZ":
                            index = self.fe.config_get(self.fe.AZ_SERVO_INDEX)
                        else:
                            self.printer.print_error(error_str)
                            return
                        pos = float(pos)
                    except ValueError:
                        self.printer.print_error(error_str)
                        return
                    data = self.fe.motor_test(index, pos)
                    real_pos, x_angle, y_angle, z_angle = data

                    # Need to do math here
                    print("Real IMU angles: %d", real_pos)
                    print("Expected position: %d", real_pos)
                else:
                    self.printer.print_error("Please run 'antkontrol start' to initialize the antenna.")
            except PyboardError as e:
                self.printer.print_error_and_exception(
                    "The AntKontrol object is not responding. Restart it with 'antkontrol start'",
                    e
                )

    def do_elevation(self, args):
        """elevation <ELEVATION>
        Set the elevation to the level given in degrees by the first argument.
        """
        arg_properties = [
            CLIArgumentProperty(
                float,
                None
            )
        ]
        parsed_args = parse_cli_args(args, 'elevation', 1, arg_properties)
        el, = parsed_args
        self.client.elevation(el)
        if self._is_open():
            try:
                if self.fe.is_antenna_initialized():
                    self.client.safemode_guard()
                    self.fe.set_elevation_degree(el)
                else:
                    self.printer.print_error("Please run 'antkontrol start' to initialize the antenna.")
            except PyboardError as e:
                self.printer.print_error_and_exception(
                    "The AntKontrol object is not responding. Restart it with 'antkontrol start'",
                    e
                )

    def do_azimuth(self, args):
        """azimuth <AZIMUTH>
        Set the azimuth to the level given in degrees by the first argument.
        """
        # TODO: merge this function with do_elevation in one move command

        arg_properties = [
            CLIArgumentProperty(
                float,
                None
            )
        ]
        parsed_args = parse_cli_args(args, 'azimuth', 1, arg_properties)
        az, = parsed_args
        if self._is_open():
            try:
                if self.fe.is_antenna_initialized():
                    self.client.safemode_guard()
                    self.fe.set_azimuth_degree(az)
                else:
                    self.printer.print_error("Please run 'antkontrol start' to initialize the antenna.")
            except PyboardError as e:
                self.printer.print_error_and_exception(
                    "The AntKontrol object is not responding. Restart it with 'antkontrol start'",
                    e
                )

    def do_antkontrol(self, args):
        """antkontrol <start | status>
        Create a new global AntKontrol instance or query the status of an existing one
        """
        arg_properties = [
            CLIArgumentProperty(
                str,
                None
            )
        ]
        parsed_args = parse_cli_args(args, 'antkontrol', 1, arg_properties)
        if self._is_open():
            if parsed_args[0] == "start":
                self.start_antkontrol()
            elif parsed_args[0] == "status":
                self.status_antkontrol()
            else:
                print("Usage: antkontrol <start | status>")

    def start_antkontrol(self):
        if self.fe.is_antenna_initialized():
            self.fe.delete_antkontrol()
        try:
            ret = self.fe.create_antkontrol()
            if self.fe.is_safemode():
                self.printer.print_error("AntKontrol is running in SAFE MODE. If you did not intend to be in this mode, "
                            "check your setup and restart AntKontrol")
            else:
                if self.fe.is_antenna_initialized():
                    print("AntKontrol initialized")
                    return
                else:
                    self.printer.print_error_and_exception(
                        "Error creating AntKontrol object. Please check your physical setup and configuration match up",
                        ret
                    )

        except PyboardError as e:
            self.printer.print_error_and_exception(
                "Error creating AntKontrol object. Please check your physical setup and configuration match up",
                e
            )

    def status_antkontrol(self):
        if not self.fe.is_antenna_initialized():
            print("AntKontrol is not initialized. Run 'antkontrol start' to do so.")
        else:
            if self.fe.is_safemode():
                print("AntKontrol is running in SAFE MODE")
            else:
                print("AntKontrol appears to be initialized properly")

    def do_track(self, args):
        """track <SATELLITE_NAME>
        Tracks a satellite across the sky. Satellite data is taken from Active-Space-Stations file from Celestrak."""
        arg_properties = [
            CLIArgumentProperty(
                str,
                None
            )
        ]
        parsed_args = parse_cli_args(args, 'track', 1, arg_properties)
        sat_name, = parsed_args
        try:
            if self._is_open() and self.fe.is_antenna_initialized():
                try:
                    self.fe.wrap_track(sat_name)
                except NotVisibleError:
                    self.printer.print_error("The satellite is not visible from your position")
            else:
                self.printer.print_error("Please run 'antkontrol start' to initialize the antenna.")
        except PyboardError as e:
            self.printer.print_error_and_exception(
                "The AntKontrol object is not responding. Restart it with 'antkontrol start'",
                e
            )

    def do_cancel(self, args):
        """cancel
        Cancel tracking mode.
        """
        try:
            if self._is_open() and self.fe.is_antenna_initialized():
                if self.fe.is_tracking():
                    self.fe.cancel()
                else:
                    self.printer.print_error("The antenna is not currently tracking any satellite.")
            else:
                self.printer.print_error("Please run 'antkontrol start' to initialize the antenna.")
        except PyboardError as e:
            self.printer.print_error_and_exception(
                "The AntKontrol object is not responding. Restart it with 'antkontrol start'",
                e
            )


def main():
    """Entry point into the shell.
    Parse command line args and create a shell object.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "--command",
        help="execute given commands (separated by ;)",
        default=None,
        nargs="*",
    )
    parser.add_argument(
        "-s", "--script", help="execute commands from file", default=None
    )
    parser.add_argument(
        "-n",
        "--noninteractive",
        help="non interactive mode (don't enter shell)",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "--nocolor", help="disable color", action="store_true", default=False
    )
    parser.add_argument(
        "--nocache", help="disable cache", action="store_true", default=False
    )

    parser.add_argument("--logfile", help="write log to file", default=None)
    parser.add_argument(
        "--loglevel",
        help="loglevel (CRITICAL, ERROR, WARNING, INFO, DEBUG)",
        default="INFO",
    )

    parser.add_argument(
        "--reset",
        help="hard reset device via DTR (serial connection only)",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "-o",
        "--open",
        help="directly opens board",
        metavar="BOARD",
        action="store",
        default=None,
    )
    parser.add_argument(
        "board", help="directly opens board", nargs="?", action="store", default=None
    )

    args = parser.parse_args()

    format = "%(asctime)s\t%(levelname)s\t%(message)s"

    if args.logfile is not None:
        logging.basicConfig(format=format, filename=args.logfile, level=args.loglevel)
    else:
        logging.basicConfig(format=format, level=logging.CRITICAL)

    logging.info("Micropython File Shell started")
    logging.info(
        "Running on Python %d.%d using PySerial %s"
        % (sys.version_info[0], sys.version_info[1], serial.VERSION)
    )

    nyanshell = NyanShell(not args.nocolor, not args.nocache, args.reset)

    if args.open is not None:
        if args.board is None:
            if not nyanshell.do_open(args.open):
                return 1
        else:
            print(
                "Positional argument ({}) takes precedence over --open.".format(
                    args.board
                )
            )
    if args.board is not None:
        nyanshell.do_open(args.board)

    if args.command is not None:

        for acmd in " ".join(args.command).split(";"):
            scmd = acmd.strip()
            if len(scmd) > 0 and not scmd.startswith("#"):
                nyanshell.onecmd(scmd)

    elif args.script is not None:

        f = open(args.script, "r")
        script = ""

        for line in f:

            sline = line.strip()

            if len(sline) > 0 and not sline.startswith("#"):
                script += sline + "\n"

        if sys.version_info < (3, 0):
            sys.stdin = io.StringIO(script.decode("utf-8"))
        else:
            sys.stdin = io.StringIO(script)

        nyanshell.intro = ""
        nyanshell.prompt = ""

    if not args.noninteractive:

        try:
            nyanshell.cmdloop()
        except KeyboardInterrupt:
            print("")


if __name__ == "__main__":
    sys.exit(main())
