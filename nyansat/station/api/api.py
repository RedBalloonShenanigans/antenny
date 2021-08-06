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
from imu.imu_bno08x import Bno08xImuController
from imu.mock_imu import MockImuController
from motor.mock_motor import MockPWMController
from motor.motor import PWMController, ServoController
from motor.motor_pca9685 import Pca9685ServoController, pca9685
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
        self.antenny_init_components()
        self.imu.reset_calibration()
        self.platform.auto_calibrate_elevation_servo()
        self.platform.auto_calibrate_azimuth_servo()
        self.platform.auto_calibrate_magnetometer()
        self.platform.auto_calibrate_gyroscope()
        self.platform.auto_calibrate_accelerometer()
        self.antenny_save(name)

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
            pwm_controller = pca9685.PCA9685(self.i2c_pwm_controller)
            pwm_controller.freq(freq)
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

    def servo_make_default(self):
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
        elif self.antenny_config.get("use_bno08x"):
            print("use_bno08x found in config: {}".format(self.antenny_config.get_name()))
            if chain is None:
                i2c_bno_scl = self.antenny_config.get("i2c_bno_scl")
                i2c_bno_sda = self.antenny_config.get("i2c_bno_sda")
                self.i2c_bno = self.i2c_init(1, i2c_bno_scl, i2c_bno_sda, freq=freq)
            else:
                self.i2c_bno = chain
            self.imu = Bno08xImuController(
                self.i2c_bno,
                debug=debug,
                reset=machine.Pin(
                               self.antenny_config.get("bno_rst"),
                               machine.Pin.OUT,
                               machine.Pin.PULL_DOWN
                           ),
            )
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
        if not self.antenny_config.get("use_bno08x"):
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
                self.imu
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
