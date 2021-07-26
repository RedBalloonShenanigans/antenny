import machine
import pca9685

from config.config import Config
from controller.controller import AntennaController
from controller.mock_controller import MockAntennaController
from controller.pid_controller import PIDAntennaController
from exceptions import AntennyIMUException, AntennyMotorException, AntennyTelemetryException, AntennyScreenException
from gps.gps import GPSController
from gps.gps_basic import BasicGPSController
from gps.mock_gps_controller import MockGPSController
from imu.imu import ImuController
from imu.imu_bno055 import Bno055ImuController
from imu.mock_imu import MockImuController
from motor.mock_motor import MockPWMController
from motor.motor import PWMController, ServoController
from motor.motor_pca9685 import Pca9685ServoController
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

    def __init__(self, config: Config):
        self.config: Config = config
        self.safe_mode: bool = True
        self.imu: ImuController = ImuController()
        self.pwm_controller: PWMController = PWMController()
        self.screen: ScreenController = ScreenController()
        self.telemetry: TelemetrySender = TelemetrySender()
        self.gps: GPSController = GPSController()
        self.elevation_servo: ServoController = ServoController()
        self.azimuth_servo: ServoController = ServoController()
        self.antenna: AntennaController = AntennaController(
            self.azimuth_servo,
            self.elevation_servo,
            self.imu)
        self.i2c_bno: machine.I2C = self.init_i2c(0, 0, 0)
        self.i2c_pwm_controller: machine.I2C = self.init_i2c(0, 0, 0)
        self.i2c_screen: machine.I2C = self.init_i2c(0, 0, 0)

    @staticmethod
    def init_i2c(id_, scl, sda, freq=400000):
        """
        Initialize a new I2C channel
        :param id_: a unique ID for the i2c channel (0 and -1 reserved for imu and motor
        :param scl: the SCL pin on the antenny board
        :param sda: the SDA pin on the antenny board
        :param freq: the I2C comm frequency
        :return: machine.I2C class
        """
        return machine.I2C(id_,
                           scl=machine.Pin(scl, machine.Pin.OUT, machine.Pin.PULL_DOWN),
                           sda=machine.Pin(sda, machine.Pin.OUT, machine.Pin.PULL_DOWN),
                           freq=freq
                           )

    def init_imu(self, chain: machine.I2C = None):
        """
        Initialize the antenny system IMU
        :param chain: provide your own I2C channel
        :return: Bno055ImuController class
        """
        if self.config.get("use_imu"):
            print("use_imu found in config: {}".format(self.config.get_name()))
            if chain is None:
                i2c_bno_scl = self.config.get("i2c_bno_scl")
                i2c_bno_sda = self.config.get("i2c_bno_sda")
                self.i2c_bno = self.init_i2c(-1, i2c_bno_scl, i2c_bno_sda, freq=1000)
            else:
                self.i2c_bno = chain
            imu = Bno055ImuController(
                self.i2c_bno,
                crystal=False,
                address=self.config.get("i2c_bno_address"),
                sign=(0, 0, 0)
            )
            print("IMU connected")
        else:
            imu = MockImuController()
            print("According to your config, ou do not have an IMU connected")
        self.imu = imu
        return imu

    def init_pwm_controller(self, chain: machine.I2C = None, freq: int = 333):
        """
        Initialize the antenny system PWM controller
        :param freq: pwm frequency
        :param chain: provide your own I2C channel
        :return: Pca9865Controller class
        """
        if self.config.get("use_motor"):
            print("use_motor found in config: {}".format(self.config.get_name()))
            if chain is None:
                i2c_pwm_controller_scl = self.config.get("i2c_pwm_controller_scl")
                i2c_pwm_controller_sda = self.config.get("i2c_pwm_controller_sda")
                self.i2c_pwm_controller = self.init_i2c(0, i2c_pwm_controller_scl, i2c_pwm_controller_sda)
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

    def init_elevation_servo(self):
        if self.pwm_controller is None:
            print("You must initialize the PWM controller before the servo")
            raise AntennyMotorException
        elevation_servo = Pca9685ServoController(self.pwm_controller, self.config_get("elevation_servo_index"))
        self.elevation_servo = elevation_servo
        return self.elevation_servo

    def init_azimuth_servo(self):
        if self.pwm_controller is None:
            print("You must initialize the PWM controller before the servo")
            raise AntennyMotorException
        azimuth_servo = Pca9685ServoController(self.pwm_controller, self.config_get("azimuth_servo_index"))
        self.azimuth_servo = azimuth_servo
        return self.azimuth_servo

    def init_screen(self, chain: machine.I2C = None):
        """
        Initialize the antenny I2C screen
        :param chain: provide your own I2C channel
        :return: Ssd13065ScreenController class
        """
        if self.config.get("use_screen"):
            if chain is None:
                i2c_screen_scl = self.config.get("i2c_screen_scl")
                i2c_screen_sda = self.config.get("i2c_screen_sda")
                self.i2c_screen = machine.I2C(
                    0,
                    scl=machine.Pin(i2c_screen_scl, machine.Pin.OUT, machine.Pin.PULL_DOWN),
                    sda=machine.Pin(i2c_screen_sda, machine.Pin.OUT, machine.Pin.PULL_DOWN),
                )
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

    def init_gps(self):
        """
        Initialize the antenny system GPS
        :return: BasicGPSController class
        """
        if self.config.get("use_gps"):
            print("use_gps found in config: {}".format(self.config.get_name()))
            gps = BasicGPSController(self.config.get("gps_uart_tx"), self.config.get("gps_uart_rx"))
        else:
            gps = MockGPSController()
            print("According to your config, you do not have a GPS connected")
        self.gps = gps
        return gps

    def init_telemetry(self, port=31337):
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

        if self.config.get("use_telemetry"):
            print("use_telemetry found in config")
            telemetry_sender = UDPTelemetrySender(port, self.gps, self.imu)
        else:
            telemetry_sender = MockTelemetrySender("localhost", 31337)
            print("According to your config, you do not have a telemetry enabled")
        self.telemetry = telemetry_sender
        return telemetry_sender

    def init_controller(self):
        """
        Initialize the antenny axis control system
        :return: AntennaController
        """
        if isinstance(self.imu, MockImuController) or isinstance(self.pwm_controller, MockPWMController):
            print("Mock components detected, creating mock antenna controller")
            antenna = MockAntennaController()
        else:
            print("Initializing PIDAntennaController class")
            antenna = PIDAntennaController(
                self.azimuth_servo,
                self.elevation_servo,
                self.imu
            )
        self.antenna = antenna
        return antenna

    def init_components(self):
        """
        Initialize all antenny system components
        :return: None
        """
        if self.config is None:
            print("Please load a config before initializing components")
        if not self.config.check():
            print("Config {} is not valid, failed to initialize".format(self.config.get_name()))
            print("If you believe this is an error, or you have modified the base components of the antenny board, "
                  "please check Config class as well as the default configs for more details.")

        self.init_imu()
        self.init_pwm_controller()
        self.init_elevation_servo()
        self.init_azimuth_servo()
        self.init_screen()
        self.init_gps()
        self.init_telemetry()
        self.init_controller()

    def scan_imu(self):
        """
        Scan the IMU I2C chain
        :return: List of I2C addresses
        """
        if self.i2c_bno is None:
            print("No I2C bus set for the IMU")
            raise AntennyIMUException("No I2C bus set for the IMU")
        return self.i2c_bno.scan()

    def scan_motor(self):
        """
        Scan the Motor I2C chain
        :return: List of I2C addresses
        """
        if self.i2c_pwm_controller is None:
            print("No I2C bus set for the Motor")
            raise AntennyMotorException("No I2C bus set for the Motor")
        return self.i2c_pwm_controller.scan()

    def scan_screen(self):
        """
        Scan the screen I2C chain
        :return: List of I2C addresses
        """
        if self.i2c_bno is None:
            print("No I2C bus set for the Screen")
            raise AntennyScreenException("No I2C bus set for the Screen")
        return self.i2c_screen.scan()

    def which_config(self):
        """
        Show the current config
        :return: config name
        """
        return self.config.get_name()

    def config_get(self, key):
        """
        Get a key from the config
        :param key: the config key
        :return: the config value
        """
        return self.config.get(key)

    def config_set(self, key, val):
        """
        Set a key from the config
        :param key: the config key
        :param val: the config  value
        :return: bool
        """
        return self.config.set(key, val)

    def config_save(self):
        """
        Save the current config
        :return: None
        """
        return self.config.save()

    def config_save_as(self, config_name, force=False):
        """
        Save the current config under a new name
        :param config_name: the new name
        :param force: overwrite if the config currently exists
        :return: None
        """
        return self.config.save_as(config_name, force=force)

    def config_load(self, config_name):
        """
        Load an existin config
        :param config_name: the config to load
        :return: None
        """
        return self.config.load(config_name)

    def config_print_values(self):
        """
        Print the current config values
        :return: None
        """
        return self.config.print_values()

    def config_load_default(self):
        """
        Reloads the config that was present on startup
        :return: None
        """
        return self.config.load_default_config()

    def config_save_as_default(self):
        """
        Will now load the current config on startup
        :return: None
        """
        return self.config.save_as_default_config()

    def config_new(self, config_name):
        """
        Create a new config without saving it
        :param config_name:
        :return: None
        """
        return self.config.new_config(config_name)

    def config_help(self):
        """
        Gives you help and type info for each config key in json format.
        :return: help json dictionary
        """
        return self.config.get_help_info()

    def config_reset(self):
        """
        Resets the config back to "default"
        :return: None
        """
        return self.config.reset_default_config()

    def list_configs(self):
        """
        Lists all of the configs available on the device.
        :return:
        """
        return self.config.list_configs()

    def is_safemode(self):
        """
        Checks if the device is in safemode
        :return:
        """
        return self.safe_mode

    def imu_is_calibrated(self) -> bool:
        """
        Checks if the IMU is calibrated
        :return: bool
        """
        return self.imu.is_calibrated()

    def imu_calibrate_accelerometer(self):
        """
        Starts the accelerometer calibration routine.
        :return: calibration results
        """
        return self.imu.calibrate_accelerometer()

    def auto_calibrate_check(self):
        if isinstance(self.pwm_controller, MockPWMController):
            raise AntennyMotorException("Can not auto calibrate without a motor")
        if isinstance(self.imu, MockImuController):
            raise AntennyIMUException("Can not auto calibrate without an imu")

    def imu_auto_calibrate_accelerometer(self):
        self.auto_calibrate_check()
        return self.antenna.auto_calibrate_accelerometer()

    def imu_auto_calibrate_magnetometer(self):
        self.auto_calibrate_check()
        return self.antenna.auto_calibrate_magnetometer()

    def imu_auto_calibrate_gyroscope(self):
        self.auto_calibrate_check()
        return self.antenna.auto_calibrate_gyroscope()

    def imu_calibrate_magnetometer(self):
        return self.imu.calibrate_magnetometer()

    def imu_calibrate_gyroscope(self):
        return self.imu.calibrate_gyroscope()

    def imu_save_calibration(self):
        return self.imu.save_calibration_profile()

    def imu_save_calibration_as(self, name):
        return self.imu.save_calibration_profile_as(name)

    def imu_make_default(self):
        return self.imu.save_calibration_profile_as_default()

    def imu_load_calibration(self, name):
        return self.imu.load_calibration_profile(name)

    def imu_reload_calibration(self):
        return self.imu.reload_calibration_profile()

    def imu_load_default(self):
        return self.imu.load_default_calibration()

    def imu_reset_calibration(self):
        return self.imu.reset_calibration()

    def imu_upload_calibration(self):
        self.imu.upload_calibration_profile()

    def imu_calibrate(self, name=None):
        self.imu_reset_calibration()
        self.imu_calibrate_magnetometer()
        self.imu_calibrate_gyroscope()
        self.imu_calibrate_accelerometer()
        if name is not None:
            self.imu_save_calibration_as(name)
        else:
            self.imu_save_calibration()
        self.imu_upload_calibration()

    def imu_auto_calibrate(self, name=None):
        self.imu_reset_calibration()
        self.imu_auto_calibrate_magnetometer()
        self.imu_auto_calibrate_gyroscope()
        self.imu_auto_calibrate_accelerometer()
        if name is not None:
            self.imu_save_calibration_as(name)
        else:
            self.imu_save_calibration()
        self.imu_upload_calibration()

    def motor_auto_find_min_max(self):
        self.auto_calibrate_check()
        self.antenna.get_elevation_min_max()
        self.antenna.get_azimuth_min_max()

    def auto_calibrate(self):
        self.motor_auto_find_min_max()
        self.imu_auto_calibrate()

    def set_config_value(self, config_name: str, config_value):
        print("Setting config entry '{}' to value '{}'".format(config_name, config_value))
        self.config.set(config_name, config_value)

    def get_config_value(self, config_name: str):
        return self.config.get(config_name)

    def print_to_display(self, data):
        print("Outputting '{}' to the screen.".format(data))
        if self.screen is None:
            raise ValueError("Please enable the 'use_screen' option in the config")
        self.screen.display(data)

    def update_telemetry(self, data: dict):
        #  TODO: The implimentation that was here does not work, make one that does or remove
        raise NotImplementedError()

    # def pwm_calibration(self, error=0.1):
    #     """
    #     Calibrates Azimuth and Elevation to within specified error
    #     :param error: Acceptable target error
    #     :return: Duty cycle to get 1 degree movement with acceptable error for azimuth & elevation
    #     """
    #     # TODO Save calibrated data to some place and actually make use of it
    #     self.antenna.start_motion(90, 90)
    #     calibrated_az_duty = self.pwm_calibrate_axis(self.antenna.azimuth, 0, 1, error=error)
    #     calibrated_el_duty = self.pwm_calibrate_axis(self.antenna.elevation, 2, 1, error=error)
    #     print("Calibrated Az Duty: {}\nCalibrated El Duty: {}".format(calibrated_az_duty, calibrated_el_duty))
    #     return calibrated_az_duty, calibrated_el_duty
    #
    # def pwm_calibrate_axis(self, index, euler_axis, multiplier, error=0.1):
    #     """
    #     Calibrates the target axis with given measurement axis
    #     :param index: Target axis motor object
    #     :param euler_axis: Target measurement axis from Euler measurement
    #     :param multiplier: Calibration step multiplier
    #     :param error: Acceptable target error
    #     :return: Duty cycle to get 1 degree movement with acceptable error
    #     """
    #     # Move axis to "neutral"
    #     base_degree = 90
    #     import time
    #     index.set_motor_position(base_degree)
    #     time.sleep(2)
    #     base_duty = index.get_duty()
    #     base_euler = self.imu.euler()[euler_axis]
    #
    #     if base_euler < 3.0 or base_euler > 357.0:
    #         base_degree = 100
    #         index.set_motor_position(base_degree)
    #         time.sleep(2)
    #         base_duty = index.get_duty()
    #         base_euler = self.imu.euler()[euler_axis]
    #
    #     # Move "1" degree
    #     index.set_motor_position(base_degree + 1)
    #     time.sleep(2)
    #     end_duty = index.get_duty()
    #     end_euler = self.imu.euler()[euler_axis]
    #
    #     diff_euler = end_euler - base_euler
    #     print("Initial Reading\nDifference: {} End: {} Base: {}".format(diff_euler, end_euler, base_euler))
    #
    #     # Try to "edge" duty cycle to acceptable error
    #     while abs(diff_euler - 1) > error:
    #         if (diff_euler - 1) > 0:
    #             end_duty = end_duty + multiplier
    #         else:
    #             end_duty = end_duty - multiplier
    #         index.set_duty(end_duty)
    #         time.sleep(2)
    #         end_euler = self.imu.euler()[euler_axis]
    #         diff_euler = end_euler - base_euler
    #         print("Difference: {} End: {} Base: {}".format(diff_euler, end_euler, base_euler))
    #
    #     calibrated_duty = abs(base_duty - end_duty)
    #
    #     return calibrated_duty
    #
    # def motor_test(self, index: int, positon: int):
    #     """
    #     Legacy motor test, chose an index to move (0 == elevation, 1 == azimuth) and return
    #         the IMU values.
    #     """
    #     if index == 0:
    #         self.antenna.elevation.set_motor_position(positon)
    #     elif index == 1:
    #         self.antenna.azimuth.set_motor_position(positon)
    #     x, y, z = self.imu.euler()
    #     return positon, x, y, z

