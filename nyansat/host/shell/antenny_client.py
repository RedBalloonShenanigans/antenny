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
        except NotRespondingError as e:
            logging.error(e)
            print("The AntKontrol object is not responding. Restart it with 'antkontrol start'")
        except NoAntKontrolError as e:
            print("Please run 'antkontrol start' to initialize the antenna.")
            logging.error(e)
        except DeviceNotOpenError as e:
            print("Not connected to device. Use 'open' first.")
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
        except ConfigStatusError as e:
            logging.error(e)
            print("Could not access existing configuration object or create one.")
        except NoSuchConfigError as e:
            logging.error(e)
            print("No such configuration parameter.")
        except ConfigUnknownError as e:
            logging.error(e)
            print("Command faulted while trying to set configuration.")
        except ValueError as e:
            logging.error(e)
            print("Incorrect parameter type.")
        except NoSuchFileError as e:
            logging.error(e)
            print("No such file")

    return wrapper


class AntennyClient(object):

    def __init__(self, fe: NyanExplorer, printer: TerminalPrinter):
        self.fe = fe
        self.printer = printer
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

    def guard_config_status(self):
        if not self.fe.config_status():
            raise ConfigStatusError
        else:
            return True

    @exception_handler
    def elevation(self, el):
        self.guard_open()
        self.guard_init()
        self.safemode_guard()
        self.fe.set_elevation_degree(el)

    @exception_handler
    def azimuth(self, az):
        self.guard_open()
        self.guard_init()
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
    def motor_test(self, motor, pos):
        self.guard_open()
        self.guard_init()
        self.safemode_guard()
        if motor == 'EL':
            index = self.fe.config_get(self.fe.EL_SERVO_INDEX)
        elif motor == "AZ":
            index = self.fe.config_get(self.fe.AZ_SERVO_INDEX)

        data = self.fe.motor_test(index, pos)
        real_pos, x_angle, y_angle, z_angle = data

        print("real imu angles: %d", real_pos)
        print("expected position: %d", real_pos)

    @exception_handler
    def setup(self, name):
        self.guard_open()
        current = self.fe.which_config()
        print("Welcome to Antenny!")
        print("Please enter the following information about your hardware\n")

        for k, info in self.prompts.items():
            prompt_text, typ = info
            try:
                new_val = typ(input(prompt_text))
            except ValueError:
                new_val = self.fe.config_get_default(k)
                print("Invalid type, setting to default value \"{}\".\nUse \"set\" to "
                      "change the parameter".format(new_val))

            self.fe.config_set(k, new_val)

        # TODO: figure this out, do we need this (make caching by default?)
        # if self.caching:
            # self.fe.cache = {}

        print("\nConfiguration set for \"{}\"!\n".format(name) +
              "You can use \"set\" to change individual parameters\n"
              "or \"edit\" to change the config file "
              "directly")

    @exception_handler
    def set(self, key, new_val):
        self.guard_open()

        # TODO: raise appropriate NoSuchConfig error in nyan_explorer
        old_val = self.fe.config_get(key)
        _, typ = self.prompts[key]
        new_val = typ(new_val)

        self.fe.config_set(key, new_val)
        print("Changed " + "\"" + key + "\" from " + str(old_val) + " --> " + str(new_val))

    @exception_handler
    def configs(self):
        # TODO: Something with ConfigUnknownError
        self.guard_open()
        print("-Config parameters-\n" +
              "Using \"{}\"".format(self.fe.which_config()))
        for key in self.prompts.keys():
            print(key + ": " + self.fe.config_get(key))

    @exception_handler
    def switch(self, name):
        self.guard_open()
        self.guard_config_status()

        files = self.fe.ls()
        if name not in files:
            raise NoSuchFileError
        current = self.fe.which_config()
        self.fe.config_switch(name)
        print("Switched from \"{}\"".format(current) +
              " to \"{}\"".format(name))
