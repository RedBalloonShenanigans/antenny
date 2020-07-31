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
from websocket import WebSocketConnectionClosedException

import colorama
import serial
from mp import mpfshell
from mp.mpfexp import MpFileExplorer, MpFileExplorerCaching
from mp.mpfshell import MpFileShell
from mp.conbase import ConError
from mp.pyboard import PyboardError
from mp.tokenizer import Tokenizer

from nyansat.host.shell.cli_arg_parser import CLIArgumentProperty, parse_cli_args
from nyansat.host.shell.terminal_printer import TerminalPrinter
from nyansat.host.shell.antenny_client import AntennyClient

from nyansat.host.shell.errors import cli_handler


def arg_exception_handler(func):
    """
    Decorator for catching improper arguments to the do_something commands.
    """
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except ValueError as e:
            logging.error(e)
        except RuntimeError as e:
            logging.error(e)

    return wrapper


class NyanShell(mpfshell.MpFileShell):
    """Extension of MPFShell that adds NyanSat-specific features"""

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
        self.client = None
        # self.printer = TerminalPrinter()


        self.repl = None
        self.tokenizer = Tokenizer()
        self._intro()
        self._set_prompt_path()

        self.emptyline = lambda: None

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

    def _connect(self, port):
        """
        Creates FileExplorers. Also creates a AntennyClient (which creates an invoker) using
        FileExplorer's self.con object.
        """
        super()._MpFileShell__connect(port)
        self.client = AntennyClient(self.fe)

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

    @cli_handler
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
        name, = parsed_args
        self.client.setup(name)

    @cli_handler
    def do_set(self, args):
        """set <CONFIG_PARAM> <NEW_VAL>
        Set a parameter in the configuration file to a new value."""
        arg_properties = [
            CLIArgumentProperty(
                str,
                None
            )
        ]
        parsed_args = parse_cli_args(args, 'set', 1, arg_properties)
        key, new_val = parsed_args
        self.client.set(key, new_val)

    def complete_set(self, *args):
        """Tab completion for 'set' command."""
        if self._is_open():
            return [key for key in self.client.prompts.keys() if key.startswith(args[0])]
        else:
            return []

    def do_configs(self, args):
        """configs
        Print a list of all configuration parameters."""
        self.client.configs()

    @cli_handler
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
        name, = parsed_args
        self.client.switch(name)

    def do_i2ctest(self, args):
        """i2ctest
        Scan an i2c bus for i2c device addresses
        """
        self.client.i2ctest()

    # TODO: refactor
    def do_bnotest(self, args):
        """bnotest
        Return some diagnostic data that may be helpful in connecting a BNO055 device.
        """
        if not self._is_open():
            return

        print("Input the SDA pin and SCL of the BNO device to test")
        try:
            sda = int(input("SDA Pin#: "))
            scl = int(input("SCL Pin#: "))
        except ValueError:
            self._error("Invalid type for pin number. Try again using only decimal numbers")
            return

        bno_test_diagnostics = self.client.bno_test(sda, scl)
        print("---")
        print("I2C bus usable?", bno_test_diagnostics.i2c_bus_scannable)
        if len(bno_test_diagnostics.i2c_addresses) == 0:
            print("I2C address detected? False")
        else:
            print("I2C address detected? True, addresses =", bno_test_diagnostics.i2c_addresses)
        print("BNO connection established?", bno_test_diagnostics.bno_object_created)
        print("BNO calibrated?", bno_test_diagnostics.bno_object_calibrated)

    # TODO: refactor
    def do_pwmtest(self, args):
        """pwmtest
        Return some diagnostic data that may be helpful in connecting a PCA9685 device.
        """
        if not self._is_open():
            return

        print("Input the SDA pin and SCL of the PWM driver to test")
        try:
            sda = int(input("SDA Pin#: "))
            scl = int(input("SCL Pin#: "))
        except ValueError:
            self._error("Invalid type for pin number. Try again using only decimal numbers")
            return

        pwm_test_diagnostics = self.client.pwm_test(sda, scl)
        print("---")
        print("I2C bus usable?", pwm_test_diagnostics.i2c_bus_scannable)
        if len(pwm_test_diagnostics.i2c_addresses) == 0:
            print("I2C address detected? False")
        else:
            print("I2C address detected? True, addresses =", pwm_test_diagnostics.i2c_addresses)
        print("PWM connection established?", pwm_test_diagnostics.pca_object_created)

    def do_calibrate(self, args):
        """calibrate
        Detect IMU calibration status and provide instructions on how to
        calibrate if necessary. If calibration is necessary, wait for the user
        to calibrate the device and cease waiting once all sensors are
        calibrated. Regardless of whether calibration is necessary or not, save
        the calibration profile to the config at the end.
        """
        arg_properties = []
        parsed_args = parse_cli_args(args, 'calibrate', 0, arg_properties)
        self.client.calibrate()

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

    def do_save_calibration(self, args):
        """save_calibration
        Save current IMU calibration data to the current configuration.
        """
        self.client.save_calibration()

    def do_upload_calibration(self, args):
        """upload_calibration
        Upload the currently stored calibration data to the connected IMU.
        """
        self.client.upload_calibration()

    @cli_handler
    def do_motortest(self, args):
        """motortest <EL | AZ> <ANGLE>
        Test the motors to plot their accuracy against the measured IMU values.
        """
        arg_properties = [
            CLIArgumentProperty(
                str,
                {
                    'EL', 'AZ'
                }
            ),
            CLIArgumentProperty(
                float,
                None
            )
        ]
        parsed_args = parse_cli_args(args, 'motortest', 2, arg_properties)
        motor, pos = parsed_args
        self.client.motor_test(motor, pos)

    @cli_handler
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

    @cli_handler
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
        self.client.azimuth(az)

    @cli_handler
    def do_antkontrol(self, args):
        """antkontrol <start | status>
        Create a new global AntKontrol instance or query the status of an existing one
        """
        arg_properties = [
            CLIArgumentProperty(
                str,
                {
                    'start', 'status'
                }
            )
        ]
        parsed_args = parse_cli_args(args, 'antkontrol', 1, arg_properties)
        mode, = parsed_args
        self.client.antkontrol(mode)

    @cli_handler
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
        self.client.track(sat_name)

    def do_cancel(self, args):
        """cancel
        Cancel tracking mode.
        """
        self.client.track()


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
