# Client middle layer
import logging

from nyansat.host.shell.terminal_printer import TerminalPrinter
from nyansat.host.shell.nyan_explorer import NyanExplorer
from nyansat.host.shell.errors import *


# TODO: Move error messages into the errors.py as a self.message attribute
def exception_handler(func):

    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except NoAntKontrolError as e:
            print("Please run 'antkontrol start' to initialize the antenna.")
            logging.error(e)
        except DeviceNotOpenError as e:
            print("Not connected to device. Use 'open' first.")
            logging.error(e)
        except PyboardError as e:
            print("The AntKontrol object is not responding. Restart it with 'antkontrol start'")
            logging.error(e)
        except AntKontrolInitError as e:
            logging.error(e)
            print("Error creating AntKontrol object. Please check your physical setup and configuration match up")
        except SafeModeWarning as e:
            logging.warning(e)
            print("AntKontrol is in SAFE MODE. Attached motors will not move")
            print("If you did not intend to be in SAFE MODE, check your configuration and run "
                  "'antkontrol start'")
        except NotVisibleError:
            print("The satellite is not visible from your position")
        except BNO055RegistersError as e:
            logging.error(e)
            print("Error: BNO055 not detected or error in writing calibration registers.")
        except BNO055UploadError as e:
            logging.error(e)
            print("The AntKontrol object is either not responding or your current configuration does not support IMU "
                  "calibration.")
            print("You can try to restart AntKontrol by running 'antkontrol start'")
            print("If you believe your configuration is incorrect, run 'configs' to check your configuration and "
                  "'setup <CONFIG_FILE>' to create a new one\n")
        except PinInputError as e:
            logging.error(e)
            print("Invalid type for pin number. Try again using only decimal numbers")
        except I2CNoAddressesError as e:
            logging.error(e)
            print("Did not find any I2C devices")

    return wrapper


class AntennyClient(object):

    def __init__(self, fe: NyanExplorer, printer: TerminalPrinter):
        self.fe = fe
        self.printer = printer

    def safemode_guard(self):
        """Warns user if AntKontrol is in SAFE MODE while using motor-class commands"""
        if self.fe.is_safemode():
            raise SafeModeWarning

    def guard_open(self):
        if self.fe is None:
            raise DeviceNotOpenError
        else:
            return True

    def guard_init(self):
        if not self.fe.is_antenna_initialized():
            raise NoAntKontrolError
        else:
            return True

    def check_open_and_init(self):
        self.guard_open()
        self.guard_init()

    @exception_handler
    def elevation(self, el):
        self.check_open_and_init()
        self.safemode_guard()
        self.fe.set_elevation_degree(el)

    @exception_handler
    def azimuth(self, az):
        self.check_open_and_init()
        self.safemode_guard()
        self.fe.set_elevation_degree(az)

    @exception_handler
    def antkontrol(self, mode):
        self.guard_open()
        if mode == 'start':
            if self.fe.is_antenna_initialized():
                self.fe.delete_antkontrol()

            # TODO: raise BNO055UploadError in nyan_explorer
            ret = self.fe.create_antkontrol()
            self.safemode_guard()
            if self.fe.is_antenna_initialized():
                print("AntKontrol initialized")
            else:
                raise AntKontrolInitError
        elif mode == 'status':
            self.guard_init()
            if self.fe.is_safemode():
                print("AntKontrol is running in SAFE MODE")
            else:
                print("AntKontrol appears to be initialized properly")

    @exception_handler
    def track(self):
        self.guard_open()
        self.guard_init()
        # TODO: Get back to this, this one has a bunch of logic inside NyanExplorer
        pass

    @exception_handler
    def cancel(self):
        # TODO: Same as for track
        pass

    @exception_handler
    def upload_calibration(self):
        self.guard_open()
        self.guard_init()

        # TODO: raise BNO055UploadError in nyan_explorer
        status = self.fe.imu_upload_calibration_profile()
        if not status:
            raise BNO055RegistersError

    @exception_handler
    def save_calibration(self):
        self.guard_open()
        self.guard_init()

        # TODO: raise BNO055UploadError in nyan_explorer
        status = self.fe.imu_save_calibration_profile()
        if not status:
            raise BNO055RegistersError

    # TODO: This one is huge, needs to be broken up
    @exception_handler
    def calibrate(self):
        pass

    @exception_handler
    def i2ctest(self):
        print("Input the SDA pin and SCL for the I2C bus to check")

        try:
            sda = int(input("SDA Pin#: "))
            scl = int(input("SCL Pin#: "))
        except ValueError:
            raise PinInputError

        # TODO: raise appropriate error in nyan_explorer
        addresses = self.fe.i2c_scan(sda, scl)
        addresses_list = addresses.strip('] [').strip(', ')
        if not addresses_list:
            raise I2CNoAddressesError
        else:
            print("Found the following device addresses: {}".format(addresses_list))
        print("If you had a running AntKontrol instance, be sure to restart it")

    @exception_handler
    def motor_test(self):
        self.guard_open()
        self.guard_init()
        self.safemode_guard()
        pass
