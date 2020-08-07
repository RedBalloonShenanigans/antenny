import logging

from nyansat.host.shell.terminal_printer import TerminalPrinter
from mp.pyboard import PyboardError


def exception_handler(func):
    """
    Decorator for printing various errors from the ESP32 (see errors.py)
    """
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except AntennyException as e:
            TerminalPrinter.print_error(e.msg + '\n')
            print_board_error(e)

    return wrapper


def cli_handler(func):
    """
    Decorator for handling argument parsing errors (see cli_arg_parser.py)
    """

    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except CLIException as e:
            print(e)

    wrapper.__doc__ = func.__doc__
    return wrapper


def print_board_error(e: 'AntennyException'):
    """
    Print the error string returned from the ESP32
    """
    def parse_board_error(error: 'AntennyException'):
        error_list = str(error).strip('()').split(", b'")
        error_list[0] = error_list[0][1:]
        ret = []
        for err in error_list:
            ret.append(bytes(err[0:-1], 'utf-8').decode('unicode-escape'))
        return ret
    try:
        print(parse_board_error(e)[2])
    except:
        pass


class AntennyException(Exception):
    # Abstract Class
    # TODO: some decorator needed here? Not sure how to properly do abstract
    msg = ""


class CLIException(Exception):
    # Abstract Class
    # TODO: some decorator needed here? Not sure how to properly do abstract
    msg = ""


class NoAntKontrolError(AntennyException):
    msg = "Please run 'antkontrol start' to initialize the antenna."


class AntKontrolInitError(AntennyException):
    msg = "Error creating AntKontrol object. Please check your physical setup and configuration match up"


class NotRespondingError(AntennyException):
    msg = "The AntKontrol object is not responding. Restart it with 'antkontrol start'"

class StartMotionError(AntennyException):
    msg = "Either motion is not started or AntKontrol object is not responding. Try 'startmotion' or 'antkontrol start'"

class NotVisibleError(AntennyException):
    msg = "The satellite is not visible from your position"


class DeviceNotOpenError(AntennyException):
    msg = "Not connected to device. Use 'open' first."


class SafeModeWarning(AntennyException):
    msg = "AntKontrol is in SAFE MODE. Attached motors will not move\n"\
          "If you did not intend to be in SAFE MODE, check your configuration and run "\
          "'antkontrol start'"


class BNO055RegistersError(AntennyException):
    msg = "Error: BNO055 not detected or error in writing calibration registers.\n" \
          "You can try to check your configuration file to see if IMU is enabled"


class BNO055UploadError(AntennyException):
    msg = "The AntKontrol object is either not responding or your current configuration does not support IMU"\
          "calibration\n" \
          "You can try to restart AntKontrol by running 'antkontrol start'\n" \
          "If you believe your configuration is incorrect, run 'configs' to check your configuration and " \
          "'setup <CONFIG_FILE>' to create a new one\n"


class PinInputError(AntennyException):
    msg = "Invalid type for pin number. Try again using only decimal numbers"


class I2CNoAddressesError(AntennyException):
    msg = "Did not find any I2C devices"


class ConfigStatusError(AntennyException):
    msg = "Could not access existing configuration object or create one."


class NoSuchConfigError(AntennyException):
    msg = "No such configuration parameter."


class ConfigUnknownError(AntennyException):
    msg = "Command faulted while trying to access or set configuration"


class NoSuchConfigFileError(AntennyException):
    msg = "No such config file"


class NotTrackingError(AntennyException):
    msg = "The antenna is not currently tracking any satellite"


class AntennaAPIFactoryError(AntennyException):
    msg = "Could not initalize Antenny API"


class AntennyImportError(AntennyException):
    msg = "Could not import a module"


class ParameterError(AntennyException, CLIException):
    msg = "Incorrect parameter type"


class NumArgsError(CLIException):
    pass


class CalibrationStatusError(AntennyException):
    msg = "Accessing calibration status failed; verify 'use_imu=True' in config\nIf you are using a BNO055, " \
          "you can check if your device is responsive using the 'bnotest' command "


if __name__ == '__main__':
    class W(Warning):
        print("Warning....")
        pass

    try:
        raise W
    except:
        print("asdfasdf")
