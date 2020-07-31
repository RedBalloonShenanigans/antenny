import logging
from mp.pyboard import PyboardError


# TODO: Move error messages into the errors.py as a self.message attribute
def exception_handler(func):

    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except AntennyException as e:
            logging.error(e)
            print(e.msg)

    return wrapper


def cli_handler(func):

    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except CLIException as e:
            print(e)

    return wrapper

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


class NotVisibleError(AntennyException):
    msg = "The satellite is not visible from your position"


class DeviceNotOpenError(AntennyException):
    msg = "Not connected to device. Use 'open' first."


class SafeModeWarning(Warning):
    msg = "AntKontrol is in SAFE MODE. Attached motors will not move\n"\
          "If you did not intend to be in SAFE MODE, check your configuration and run "\
          "'antkontrol start'"


class BNO055RegistersError(AntennyException):
    msg = "Error: BNO055 not detected or error in writing calibration registers."


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


class ParameterError(AntennyException, CLIException):
    msg = "Incorrect parameter type"


class NumArgsError(CLIException):
    pass


class CalibrationStatusError(AntennyException):
    msg = "Accessing calibration status failed"


if __name__ == '__main__':
    class W(Warning):
        print("Warning....")
        pass

    try:
        raise W
    except:
        print("asdfasdf")
