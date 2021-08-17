import time

import machine

from config.config import Config
from controller.controller import PlatformController
from controller.mock_controller import MockPlatformController
from controller.pid_controller import PIDPlatformController
from exceptions import AntennyIMUException, AntennyMotorException, AntennyTelemetryException, AntennyScreenException
from gps.gps import GPSController
from gps.gps_basic import BasicGPSController
from gps.mock_gps_controller import MockGPSController
from imu.imu import ImuController
from imu.imu_bno055 import Bno055ImuController
from imu.imu_bno08x_i2c import Bno08xImuController
from imu.imu_bno08x_rvc import Bno08xUARTImuController
from imu.mock_imu import MockImuController
from motor.mock_motor import MockPWMController
from motor.motor import PWMController, ServoController
from motor.motor_pca9685 import Pca9685ServoController, Pca9685Controller
from screen.mock_screen import MockScreenController
from screen.screen import ScreenController
from screen.screen_ssd1306 import Ssd1306ScreenController
from antenny_threading import Queue
from sender.sender import TelemetrySender
from sender.sender_udp import UDPTelemetrySender
from sender.mock_sender import MockTelemetrySender


_DEFAULT_MOTOR_POSITION = 90.
_DEFAULT_MOTION_DELAY = 0.75


class AntennyAPI:
    """
    Interface for interacting with the antenny board.
    """

    def __init__(self):
        self.antenny_config: Config = Config("antenny")
        self.imu_config: Config = Config("imu")
        self.servo_config: Config = Config("servo")
        self.pid_config: Config = Config("pid")
        self.safe_mode: bool = True
        self.imu: ImuController = ImuController()
        self.pwm_controller: PWMController = PWMController()
        self.screen: ScreenController = ScreenController()
        self.telemetry: TelemetrySender = TelemetrySender()
        self.gps: GPSController = GPSController()
        self.elevation_servo: ServoController = ServoController()
        self.azimuth_servo: ServoController = ServoController()
        self.platform: PlatformController = PlatformController()
        self.i2c_bno: machine.I2C = self.i2c_init(0, 0, 0)
        self.i2c_pwm_controller: machine.I2C = self.i2c_init(0, 0, 0)
        self.i2c_screen: machine.I2C = self.i2c_init(0, 0, 0)

#  Antenny Generic Functions

    @staticmethod
    def i2c_init(id_, scl, sda, freq=400000):
        """
        Initialize a new I2C channel
        :param id_: a unique ID for the i2c channel (0 and -1 reserved for imu and motor
        :param scl: the SCL pin on the antenny board
        :param sda: the SDA pin on the antenny board
        :param freq: the I2C comm frequency
        :return: machine.I2C class
        """
        return machine.I2C(id_,
                           scl=machine.Pin(
                               scl,
                               machine.Pin.OUT,
                               machine.Pin.PULL_DOWN
                           ),
                           sda=machine.Pin(
                               sda,
                               machine.Pin.OUT,
                               machine.Pin.PULL_DOWN
                           ),
                           freq=freq
                           )

    def uart_init(self, id, rx, tx, baud=9600):
        return machine.UART(id, baudrate=baud, rx=rx, tx=tx)

    def antenny_config_check(self):
        """
        Checks if the current config is valid
        :return:
        """
        return self.antenny_config.check()

    def antenny_which_config(self):
        """
        Show the current config
        :return: config name
        """
        return self.antenny_config.get_name()

    def antenny_config_get(self, key):
        """
        Get a key from the config
        :param key: the config key
        :return: the config value
        """
        return self.antenny_config.get(key)

    def antenny_config_set(self, key, val):
        """
        Set a key from the config
        :param key: the config key
        :param val: the config  value
        :return: bool
        """
        return self.antenny_config.set(key, val)

    def antenny_config_save(self, name: str = None, force: bool = False):
        """
        Save the current config
        :return: None
        """
        return self.antenny_config.save(name, force=force)

    def antenny_config_load(self, name: str = None):
        """
        Load an existin config
        :param name:
        :return: None
        """
        return self.antenny_config.load(name)

    def antenny_config_print_values(self):
        """
        Print the current config values
        :return: None
        """
        return self.antenny_config.print_values()

    def antenny_config_load_default(self):
        """
        Reloads the config that was present on startup
        :return: None
        """
        return self.antenny_config.load_default_config()

    def antenny_config_make_default(self):
        """
        Will now load the current config on startup
        :return: None
        """
        return self.antenny_config.save_as_default_config()

    def antenny_config_help(self):
        """
        Gives you help and type info for each config key in json format.
        :return: help json dictionary
        """
        return self.antenny_config.get_help_info()

    def antenny_config_reset(self):
        """
        Resets the config back to "default"
        :return: None
        """
        return self.antenny_config.reset_default_config()

    def antenny_list_configs(self):
        """
        Lists all of the configs available on the device.
        :return:
        """
        return self.antenny_config.list_configs()

    def antenny_is_safemode(self):
        """
        Checks if the device is in safemode
        :return:
        """
        return self.safe_mode

    def antenny_init_components(self):
        """
        Initialize all antenny system components
        :return: None
        """
        if self.antenny_config is None:
            print("Please load a config before initializing components")
        if not self.antenny_config.check():
            print("Config {} is not valid, failed to initialize".format(self.antenny_config.get_name()))
            print("If you believe this is an error, or you have modified the base components of the antenny board, "
                  "please check Config class as well as the default configs for more details.")

        self.imu_init()
        self.pwm_controller_init()
        self.elevation_servo_init()
        self.azimuth_servo_init()
        self.screen_init()
        self.gps_init()
        self.telemetry_init()
        self.platform_init()

    def antenny_save(self, name: str = None):
        """
        Will save all current configs to be started on device startup
        :param name: A new name for the config, if not specified, will overwrite the current
        :return:
        """
        self.antenny_config.save(name)
        self.antenny_config.save_as_default_config()
        self.imu_save(name)
        self.imu_config.save_as_default_config()
        self.azimuth_servo_save(name)
        self.elevation_servo_save(name)
        self.servo_config.save_as_default_config()

    def antenny_calibrate(self, name: str = None):
        """
        Initializes all components, auto-calibrates the platform, then saves all as default
        Should be used after assembling a new antenny or after wiping your previous configs
        :param name:
        :return:
        """
        if self.antenny_config.get("use_bno08x_rvc"):
            t = .25
            d = .5
            us = 50
        else:
            t = .1
            d = .5
            us = 100
        self.platform.auto_calibrate_elevation_servo(us=us, t=t, d=d)
        self.platform.auto_calibrate_azimuth_servo(us=us, t=t, d=d)
        if self.antenny_config.get("use_bno055"):
            self.platform.auto_calibrate_magnetometer()
            self.platform.auto_calibrate_gyroscope()
            self.platform.auto_calibrate_accelerometer()

    def antenny_manual_setup(self):
        """
        Manually input calibration and configuration fields
        :return:
        """
        print(
            """
            Welcome to the Antenny Manual Setup Menu!
            Would you like to:
                A) Set up the Antenny hardware and pin configuration
                B) Manually input your servo limits (in us)
                C) Set your longitude and latitude
                D) Tune your PID loop
                Z) All of the above
            """
        )
        choice = input("(A, B, C, D, Z): ").strip().lower()
        if choice == "a" or choice == "z":
            if choice == "a":
                print("You have chosen <Set up the Antenny pin configuration>, a fine choice!")
            if choice == "d":
                print("You have chosen <All of the above>, one of my favorite choices.")
            keep_name = input("The config is currently \"{}\", would you like to name it something else? (Y/n)".format(
                self.antenny_config.get_name())).strip( ).lower() == "n"
            if not keep_name:
                name = input("Select a new name: ")
                self.antenny_config.save(name)
                self.servo_config.save(name)
                self.imu_config.save(name)
            print("First, lets see what hardware you are using.")
            print("Beware, some (or all) functionality might be disabled if you are missing hardware.")
            imu = input("Are you using an IMU (y, N)").strip().lower() == "y"
            if not imu:
                print("It appears you are not using an IMU. Beware, core functionality will be disabled")
            else:
                print("You are using an IMU! I'M proud of U...")
                print("But which one are you using?")
                bno055 = input("Is it the BNO055? (y/N)").strip().lower() == "y"
                if not bno055:
                    print("Ah, so it must be the BNO080!")
                    print("But do you have it hooked up for Robotic Vacuum Cleaner mode?")
                    print("This is the suggested mode, otherwise conversion from quaternion is required, "
                          "check the Antenny manual and BNO080 datasheet for more details.")
                    bno08x_rvc = input("BNO080 in UART RVC mode? (y/N)").strip().lower() == "y"
                    if not bno08x_rvc:
                        print("So it's I2C then...")
                        print("Beware, this is not well supported by the Antenny ground station at this time.")
                        bno08x_i2c = True

                    else:
                        bno08x_i2c = False
                        use_ps_pins = input("Have you soldered the proper jumpers on the back of the IMU? ("
                                            "y/N)").strip().lower() == "y"
                        if not use_ps_pins:
                            print("That's fine, you just have to let me know which ESP32 pins you wired to PS0 and PS1 "
                                  "on the IMU")
                            try:
                                ps0 = int(input("PS0: ").strip())
                                ps1 = int(input("PS1: ").strip())
                            except ValueError as e:
                                print("I need a number!")
                                ps0 = int(input("PS0: ").strip())
                                ps1 = int(input("PS1: ").strip())
                            self.antenny_config.set("bno_ps0", ps0)
                            self.antenny_config.set("bno_ps1", ps1)

                    print("Alright, now that we figured that out, which ESP32 pins are you using for the IMU "
                          "communication? ")
                    print("If you are confused, it should be printed on the back of your Antenny PCB.")
                    print("And in the case of Robotic Vacuum Cleaner mode, I can do the I2C->UART translation for you.")
                    try:
                        bno_scl = int(input("SCL: "))
                        bno_sda = int(input("SDA: "))
                        bno_rst = int(input("RESET: "))
                    except ValueError as e:
                        print("I need a number!")
                        bno_scl = int(input("SCL: "))
                        bno_sda = int(input("SDA: "))
                        bno_rst = int(input("RESET: "))
                    self.antenny_config.set("use_bno055", bno055)
                    self.antenny_config.set("use_bno08x_i2c", bno08x_i2c)
                    self.antenny_config.set("use_bno08x_rvc", bno08x_rvc)
                    self.antenny_config.set("i2c_bno_scl", bno_scl)
                    self.antenny_config.set("i2c_bno_sda", bno_sda)
                    self.antenny_config.set("bno_rst", bno_rst)

            pwm_controller = input("Are you using a motor/servo assembly? (y/N)").strip().lower()
            if not pwm_controller:
                print("It appears you are not using a motor assembly. Beware, core functionality will be disabled.")
            else:
                print("So you are using a motor. Let's get movin'!")
                print("Which pins are you using for the PWM controller communication? If you are unsure it should be "
                      "printed on the back of your board.")
                try:
                    pwm_scl = int(input("SCL: ").strip())
                    pwm_sda = int(input("SDA: ").strip())
                except ValueError as e:
                    print("I need a number!")
                    pwm_scl = int(input("SCL: ").strip())
                    pwm_sda = int(input("SDA: ").strip())

                print("Great!, Now which PWM indexes are your servos/motors plugged into? The indexes should be "
                      "printed on the board.")
                try:
                    elevation_index = int(input("Elevation index: ").strip())
                    azimuth_index = int(input("Azimuth index: ").strip())
                except ValueError as e:
                    print("I need a number!")
                    elevation_index = int(input("Elevation index: ").strip())
                    azimuth_index = int(input("Azimuth index: ").strip())
                self.antenny_config.set("i2c_pwm_controller_scl", pwm_scl)
                self.antenny_config.set("i2c_pwm_controller_sda", pwm_sda)
                self.antenny_config.set("elevation_servo_index", elevation_index)
                self.antenny_config.set("azimuth_servo_index", azimuth_index)

        if choice == "b" or choice == "z":
            if choice == "b":
                print("You have chosen <Manually input your servo limits (in us)>. I hope it exists!")
            print("What are the max and minimum values we can pump into your servos? Please give the values in "
                  "microseconds")
            print("If you are unsure you can play around with your antenny, or you can skip this setup and use the "
                  "api.antenny_calibrate() to find something close enough.")
            try:
                elevation_min = int(input("Elevation minimum (us): ").strip())
                elevation_max = int(input("Elevation maximum (us): ").strip())
                azimuth_min = int(input("Azimuth minimum (us): ").strip())
                azimuth_max = int(input("Azimuth maximum (us): ").strip())
            except ValueError as e:
                print("I need a number!")
                elevation_min = int(input("Elevation minimum (us): ").strip())
                elevation_max = int(input("Elevation maximum (us): ").strip())
                azimuth_min = int(input("Azimuth minimum (us): ").strip())
                azimuth_max = int(input("Azimuth maximum (us): ").strip())
            self.servo_config.set("elevation", {"min": elevation_min, "max": elevation_max})
            self.servo_config.set("azimuth", {"min": azimuth_min, "max": azimuth_max})

        if choice == "c" or choice == "z":
            if choice == "c":
                print("You have chosen <Set your longitude and latitude>. I hope it's somewhere warm.")
            print("I hope I'm not being too forward but where are you?")
            try:
                longitude = int(input("Longitude: ").strip())
                latitude = int(input("Latitude: ").strip())
            except ValueError as e:
                print("I need a number!")
                longitude = int(input("Longitude: ").strip())
                latitude = int(input("Latitude: ").strip())
            self.antenny_config.set("latitude", latitude)
            self.antenny_config.set("longitude", longitude)

        if choice == "d" or choice == "z":
            if choice == "d":
                print("You have chosen <Tune your PID loop>. I hope you brought your tuning fork.")
            print("These values are mostly experimental, but there are plent of online resources for PID tuning best "
                  "practices.")
            try:
                print("What should the minimum output value be?")
                min_limit = float(input("Min Output: ").strip())
                print("What should the maximum output be?")
                max_limit = float(input("Max Output: ").strip())
                print("What should be the period of each PID iteration?")
                period = int(input("Period (ms): ").strip())
            except ValueError as e:
                print("I need a number!")
                print("What should the minimum output value be?")
                min_limit = float(input("Min Output: ").strip())
                print("What should the maximum output be?")
                max_limit = float(input("Max Output: ").strip())
                print("What should be the period of each PID iteration?")
                period = int(input("Period (ms): ").strip())
            self.pid_config.set("output_limits", [min_limit, max_limit])
            self.pid_config.set("period", period)
            print("And now the PID constants, it is recommended leaving them default in the begining.")
            try:
                p = float(input("P (Default is 1.0): ").strip())
                self.pid_config.set("p", p)
            except ValueError as e:
                self.pid_config.set("p", 1.0)
            try:
                i = float(input("I (Default is 0.0): ").strip())
                self.pid_config.set("i", i)
            except ValueError as e:
                self.pid_config.set("i", 0.0)
            try:
                d = float(input("D (Default is 0.0): ").strip())
                self.pid_config.set("d", d)
            except ValueError as e:
                self.pid_config.set("d", 0.0)

        print("You have completed the Antenny manual setup! Please remember to save your config as the default with "
              "api.antenny_save() once you're happy with it.")

    #  PWM Controller Functions

    def pwm_controller_init(self, chain: machine.I2C = None, freq: int = 333):
        """
        Initialize the antenny system PWM controller
        :param freq: pwm frequency
        :param chain: provide your own I2C channel
        :return: Pca9865Controller class
        """
        if self.antenny_config.get("use_motor"):
            print("use_motor found in config: {}".format(self.antenny_config.get_name()))
            if chain is None:
                i2c_pwm_controller_scl = self.antenny_config.get("i2c_pwm_controller_scl")
                i2c_pwm_controller_sda = self.antenny_config.get("i2c_pwm_controller_sda")
                self.i2c_pwm_controller = self.i2c_init(
                    0,
                    i2c_pwm_controller_scl,
                    i2c_pwm_controller_sda
                )
            else:
                self.i2c_pwm_controller = chain
            pwm_controller = Pca9685Controller(self.i2c_pwm_controller, freq=freq)
            print("Motor connected")
            safe_mode = False
        else:
            pwm_controller = MockPWMController()
            print("According to your config, you do not have a motor connected, entering Safe Mode")
            safe_mode = True
        self.pwm_controller = pwm_controller
        self.safe_mode = safe_mode
        return pwm_controller, safe_mode

    def pwm_controller_scan(self):
        """
        Scan the Motor I2C chain
        :return: List of I2C addresses
        """
        if self.i2c_pwm_controller is None:
            print("No I2C bus set for the Motor")
            raise AntennyMotorException("No I2C bus set for the Motor")
        return self.i2c_pwm_controller.scan()

#  Servo Controller Functions

    def elevation_servo_init(self):
        """
        Initializes the elevation servo
        :return:
        """
        if self.pwm_controller is None:
            print("You must initialize the PWM controller before the servo")
            raise AntennyMotorException
        self.elevation_servo = Pca9685ServoController(
            self.pwm_controller,
            self.antenny_config.get("elevation_servo_index")
        )
        self.elevation_servo_load()
        return self.elevation_servo

    def elevation_servo_load(self, name: str = None):
        """
        Loads the servo's min and max duty cycle values from the config
        :param name:
        :return:
        """
        if name is not None:
            self.servo_config.load(name)
        self.elevation_servo.set_min_position(self.servo_config.get("elevation")["min"])
        self.elevation_servo.set_max_position(self.servo_config.get("elevation")["max"])

    def elevation_servo_save(self, name: str = None, force: bool = False):
        """
        Saves the servo's min and max duty cycle values to the config
        :param force:
        :param name:
        :return:
        """
        self.servo_config.set(
            "elevation",
            {
                "min": self.elevation_servo.get_min_position(),
                "max": self.elevation_servo.get_max_position()
             }
        )
        self.servo_config.save(name, force=force)

    def elevation_servo_set_position(self, position: int):
        """
        Sets the elveation servo position
        :param position:
        :return:
        """
        return self.elevation_servo.set_position(position)

    def elevation_servo_set_min_max(self, min: int, max: int):
        """
        Sets the min and max position for the servos.
        :param min:
        :param max:
        :return:
        """
        self.elevation_servo.set_min_position(min)
        self.elevation_servo.set_max_position(max)

    def azimuth_servo_init(self):
        """
        Initializes the azimuth servo
        :return:
        """
        if self.pwm_controller is None:
            print("You must initialize the PWM controller before the servo")
            raise AntennyMotorException
        self.azimuth_servo = Pca9685ServoController(
            self.pwm_controller,
            self.antenny_config.get("azimuth_servo_index")
        )
        self.azimuth_servo_load()
        return self.azimuth_servo

    def azimuth_servo_load(self, name: str = None):
        """
        Loads the servo's min and max duty cycle values from the config
        :param name:
        :return:
        """
        if name is not None:
            self.servo_config.load(name)
        self.azimuth_servo.set_min_position(self.servo_config.get("azimuth")["min"])
        self.azimuth_servo.set_max_position(self.servo_config.get("azimuth")["max"])

    def azimuth_servo_save(self, name: str = None, force: bool = False):
        """
        Saves the servo's min and max duty cycle values to the config
        :param force:
        :param name:
        :return:
        """
        self.servo_config.set(
            "azimuth",
            {
                "min": self.azimuth_servo.get_min_position(),
                "max": self.azimuth_servo.get_max_position()
            }
        )
        self.servo_config.save(name, force=force)

    def azimuth_servo_set_position(self, position: int):
        """
        Sets the azimuth servo position
        :param position:
        :return:
        """
        return self.azimuth_servo.set_position(position)

    def azimuth_servo_set_min_max(self, min: int, max: int):
        """
        Sets the min and max position for the servos.
        :param min:
        :param max:
        :return:
        """
        self.azimuth_servo.set_min_position(min)
        self.azimuth_servo.set_max_position(max)

    def servo_make_default(self):
        """
        Makes the current servo config the default
        :return:
        """
        self.servo_config.save_as_default_config()

#  Screen Functions

    def screen_init(self, chain: machine.I2C = None):
        """
        Initialize the antenny I2C screen
        :param chain: provide your own I2C channel
        :return: Ssd13065ScreenController class
        """
        if self.antenny_config.get("use_screen"):
            if chain is None:
                i2c_screen_scl = self.antenny_config.get("i2c_screen_scl")
                i2c_screen_sda = self.antenny_config.get("i2c_screen_sda")
                self.i2c_screen = self.i2c_init(0, i2c_screen_scl, i2c_screen_sda)
            else:
                self.i2c_screen = chain
            screen = Ssd1306ScreenController(
                self.i2c_screen,
            )
        else:
            screen = MockScreenController(Queue())
            print("According to your config, you do not have a screen connected")
        self.screen = screen
        return screen

    def screen_scan(self):
        """
        Scan the screen I2C chain
        :return: List of I2C addresses
        """
        if self.i2c_bno is None:
            print("No I2C bus set for the Screen")
            raise AntennyScreenException("No I2C bus set for the Screen")
        return self.i2c_screen.scan()

#  GPS Functions

    def gps_init(self):
        """
        Initialize the antenny system GPS
        :return: BasicGPSController class
        """
        if self.antenny_config.get("use_gps"):
            print("use_gps found in config: {}".format(self.antenny_config.get_name()))
            gps = BasicGPSController(self.antenny_config.get("gps_uart_tx"), self.antenny_config.get("gps_uart_rx"))
        else:
            gps = MockGPSController()
            print("According to your config, you do not have a GPS connected")
        self.gps = gps
        return gps

#  Telemetry Functions

    def telemetry_init(self, port=31337):
        """
        Initialize the antenny system Telemetry sender
        :param port: Communcation UDP port
        :return: UDPTelemetrySender
        """
        if self.imu is None:
            print("Cannot initialize telemetry without IMU")
            raise AntennyTelemetryException("Cannot initialize telemetry without IMU")
        if self.gps is None:
            print("Cannot initalize telemetry without GPS")
            raise AntennyTelemetryException("Cannot initalize telemetry without GPS")

        if isinstance(self.imu, MockImuController) or isinstance(self.gps, MockGPSController):
            print("WARNING: Initializing telemetry sender with mock components, please check your config")

        if self.antenny_config.get("use_telemetry"):
            print("use_telemetry found in config")
            telemetry_sender = UDPTelemetrySender(port, self.gps, self.imu)
        else:
            telemetry_sender = MockTelemetrySender("localhost", 31337)
            print("According to your config, you do not have a telemetry enabled")
        self.telemetry = telemetry_sender
        return telemetry_sender

#  IMU Functions

    def imu_init(self, chain: machine.I2C = None, freq=400000, debug=False):
        """
        Initialize the antenny system IMU
        :param debug:
        :param freq:
        :param chain: provide your own I2C channel
        :return: Bno055ImuController class
        """
        if self.antenny_config.get("use_bno055"):
            print("use_bno055 found in config: {}".format(self.antenny_config.get_name()))
            if chain is None:
                i2c_bno_scl = self.antenny_config.get("i2c_bno_scl")
                i2c_bno_sda = self.antenny_config.get("i2c_bno_sda")
                self.i2c_bno = self.i2c_init(1, i2c_bno_scl, i2c_bno_sda, freq=freq)
            else:
                self.i2c_bno = chain
            self.imu = Bno055ImuController(
                self.i2c_bno,
                crystal=False,
                address=self.antenny_config.get("i2c_bno_address"),
                sign=(0, 0, 0)
            )
            self.imu_load()
            self.imu.upload_calibration_profile()
            print("IMU connected")
        elif self.antenny_config.get("use_bno08x_i2c"):
            print("use_bno08x_i2c found in config: {}".format(self.antenny_config.get_name()))
            if chain is None:
                i2c_bno_scl = self.antenny_config.get("i2c_bno_scl")
                i2c_bno_sda = self.antenny_config.get("i2c_bno_sda")
                self.i2c_bno = self.i2c_init(1, i2c_bno_scl, i2c_bno_sda, freq=freq)
            else:
                self.i2c_bno = chain
            ps0 = machine.Pin(self.antenny_config.get("bno_ps0"), machine.Pin.OUT)
            ps1 = machine.Pin(self.antenny_config.get("bno_ps1"), machine.Pin.OUT)
            reset = machine.Pin(self.antenny_config.get("bno_rst"), machine.Pin.OUT)
            ps0.off()
            ps1.off()
            self.imu = Bno08xImuController(
                self.i2c_bno,
                debug=debug,
                reset=reset
            )
            self.imu.reset_calibration()
            print("IMU connected")
        elif self.antenny_config.get("use_bno08x_rvc"):
            print("use_bno08x_rvc found in config: {}".format(self.antenny_config.get_name()))
            tx = self.antenny_config.get("i2c_bno_scl")
            rx = self.antenny_config.get("i2c_bno_sda")
            ps0 = machine.Pin(self.antenny_config.get("bno_ps0"), machine.Pin.OUT)
            ps1 = machine.Pin(self.antenny_config.get("bno_ps1"), machine.Pin.OUT)
            reset = machine.Pin(self.antenny_config.get("bno_rst"), machine.Pin.OUT)
            ps0.on()
            ps1.off()
            uart_bno = self.uart_init(1, rx, tx, baud=115200)
            self.imu = Bno08xUARTImuController(
                uart_bno,
                reset=reset
            )
            self.imu.reset_calibration()
            time.sleep(.5)
            self.imu.start()
            print("IMU connected")
        else:
            self.imu = MockImuController()
            print("According to your config, ou do not have an IMU connected")
        return self.imu

    def imu_scan(self):
        """
        Scan the IMU I2C chain
        :return: List of I2C addresses
        """
        if self.i2c_bno is None:
            print("No I2C bus set for the IMU")
            raise AntennyIMUException("No I2C bus set for the IMU")
        return self.i2c_bno.scan()

    def imu_save(self, name: str = None, force: bool = False):
        """
        Saves the current calibration to the config
        :param name: A new config name, overwritten if not specified
        :param force:
        :return:
        """
        if self.antenny_config.get("use_bno055"):
            self.imu_config.set(
                "accelerometer",
                self.imu.get_accelerometer_calibration()
            )
            self.imu_config.set(
                "magnetometer",
                self.imu.get_magnetometer_calibration()
            )
            self.imu_config.set(
                "gyroscope",
                self.imu.get_gyroscope_calibration()
            )
            self.imu_config.save(name=name, force=force)

    def imu_load(self, name: str = None):
        """
        Reloads the calibration from the config
        :param name: A different config to be loaded if specified
        :return:
        """
        if not self.antenny_config.get("use_bno08x"):
            self.imu_config.load(name)
            self.imu.set_accelerometer_calibration(
                self.imu_config.get("accelerometer")
            )
            self.imu.set_magnetometer_calibration(
                self.imu_config.get("magnetometer")
            )
            self.imu.set_gyroscope_calibration(
                self.imu_config.get("gyroscope")
            )
            self.imu.upload_calibration_profile()

    def imu_make_default(self):
        """
        Makes the current IMU calibration config default
        :return:
        """
        return self.imu_config.save_as_default_config()

    def imu_load_default(self):
        """
        Loads the default calibration config
        :return:
        """
        return self.imu_config.load_default_config()

    def imu_get_azimuth(self):
        """
        Gets the azimuth as reported by the IMU
        :return:
        """
        return self.imu.get_azimuth()

    def imu_get_elevation(self):
        """
        Gets the elevation as reported by the IMU
        :return:
        """
        return self.imu.get_elevation()

    def imu_get_euler(self):
        """
        Gets the euler angles as reported by the IMU
        :return:
        """
        return self.imu.get_euler()

    def imu_calibrate(self):
        """
        Begin the manual calibration routine of the IMU
        :return:
        """
        self.imu.calibrate_accelerometer()
        self.imu.calibrate_gyroscope()
        self.imu.calibrate_magnetometer()

#  Platform Functions

    def platform_init(self):
        """
        Initialize the antenny axis control system
        :return: AntennaController
        """
        if isinstance(self.imu, MockImuController) or isinstance(self.pwm_controller, MockPWMController):
            print("Mock components detected, creating mock antenna controller")
            platform = MockPlatformController(self.azimuth_servo, self.elevation_servo, self.imu)
        else:
            print("Initializing PIDAntennaController class")
            platform = PIDPlatformController(
                self.azimuth_servo,
                self.elevation_servo,
                self.imu,
                pid_output_limits=self.pid_config.get("output_limits"),
                pid_frequency=self.pid_config.get("frequency"),
                p=self.pid_config.get("p"),
                i=self.pid_config.get("i"),
                d=self.pid_config.get("d")
            )
        self.platform = platform
        return platform

    def platform_auto_calibrate_accelerometer(self):
        """
        Uses the servos to perform the accelerometer routine
        :return:
        """
        self._platform_auto_calibrate_check()
        return self.platform.auto_calibrate_accelerometer()

    def platform_auto_calibrate_magnetometer(self):
        """
        Uses the servos to perform the magnetometer routine
        :return:
        """
        self._platform_auto_calibrate_check()
        return self.platform.auto_calibrate_magnetometer()

    def platform_auto_calibrate_gyroscope(self):
        """
        Uses the servos to perform the gyroscope routine
        :return:
        """
        self._platform_auto_calibrate_check()
        return self.platform.auto_calibrate_gyroscope()

    def platform_auto_calibrate_imu(self):
        """
        Uses the servos to automatically perform the IMU calibration
        :return:
        """
        self.imu.reset_calibration()
        self.platform.auto_calibrate_magnetometer()
        self.platform.auto_calibrate_gyroscope()
        self.platform.auto_calibrate_accelerometer()

    def platform_auto_calibrate_elevation_servo(self):
        """
        Uses the IMU to calibrate the elevation servo
        :return:
        """
        self._platform_auto_calibrate_check()
        self.platform.auto_calibrate_elevation_servo()

    def platform_auto_calibrate_azimuth_servo(self):
        """
        Uses the IMU to calibrate the azimuth servo
        :return:
        """
        self._platform_auto_calibrate_check()
        self.platform.auto_calibrate_azimuth_servo()

    def platform_auto_calibrate_servos(self):
        """
        Uses the IMU to automatically detect the min and max of the servos
        :return:
        """
        self.platform.auto_calibrate_elevation_servo()
        self.platform.auto_calibrate_azimuth_servo()

    def platform_auto_calibrate(self):
        """
        Uses the assembled platform construction to calibrate it's components
        :return:
        """
        self.platform_auto_calibrate_servos()
        self.platform_auto_calibrate_imu()

    def platform_set_azimuth(self, azimuth):
        """
        Sets the elevation of the antenna
        :param azimuth:
        :return:
        """
        self.platform.set_azimuth(azimuth)

    def platform_set_elevation(self, elevation):
        """
        Sets the elevation of the antenna
        :param elevation:
        :return:
        """
        self.platform.set_elevation(elevation)

    def platform_start(self):
        """
        Starts the platform movement
        :return:
        """
        self.platform.start()

    def platform_stop(self):
        """
        Stops the platform movement
        :return:
        """
        self.platform.stop()

    def platform_set_coordinates(self, azimuth, elevation):
        """
        Sets the coordinates of the antenna direction
        :param azimuth:
        :param elevation:
        :return:
        """
        return self.platform.set_coordinates(azimuth, elevation)

    def platform_orient(self):
        return self.platform.orient()

    def _platform_auto_calibrate_check(self):
        """
        Checks the antenny config for components before attempting to calibrate
        :return:
        """
        if isinstance(self.pwm_controller, MockPWMController):
            raise AntennyMotorException("Can not auto calibrate without a motor")
        if isinstance(self.imu, MockImuController):
            raise AntennyIMUException("Can not auto calibrate without an imu")
