import machine
import _thread

from config.config import Config
from exceptions import AntennyIMUException, AntennyMotorException, AntennyGPSException, AntennyTelemetryException, \
    AntennyControllerException, AntennyConfigException, AntennyScreenException
from gps.gps_basic import BasicGPSController
from gps.mock_gps_controller import MockGPSController
from imu.imu import ImuController
from imu.imu_bno055 import Bno055ImuController
from imu.mock_imu import MockImuController
from motor.mock_motor import MockMotorController
from motor.motor import MotorController
from motor.motor_pca9685 import Pca9685Controller
from screen.mock_screen import MockScreenController
from screen.screen_ssd1306 import Ssd1306ScreenController
from antenny_threading import Queue
from sender.sender_udp import UDPTelemetrySender
from sender.mock_sender import MockTelemetrySender

_DEFAULT_MOTOR_POSITION = 90.
_DEFAULT_MOTION_DELAY = 0.75


class AxisController:
    """
    Control a single axis of motion - azimuth / elevation.
    """

    def __init__(
            self,
            motor_idx: int,
            imu: ImuController,
            motor: MotorController,
    ):
        self.motor_idx = motor_idx
        self.imu = imu
        self.motor = motor
        self._current_motor_position = self.get_motor_position()

    def get_motor_position(self) -> float:
        self._current_motor_position = self.motor.get_position(self.motor_idx)
        return self._current_motor_position

    def set_motor_position(self, desired_heading: float):
        self._current_motor_position = desired_heading
        self.motor.smooth_move(self.motor_idx, desired_heading, 50)

    def get_duty(self):
        return self.motor.duty(self.motor_idx)

    def set_duty(self, duty):
        self.motor.set_position(self.motor_idx, duty=duty)


class AntennaController:
    """
    Control the antenna motion device of the antenny.
    """

    def __init__(
            self,
            azimuth: AxisController,
            elevation: AxisController,
    ):
        self.azimuth = azimuth
        self.elevation = elevation
        self._motion_started = False
        self.pin_interrupt = True

    def start_motion(self, azimuth: int, elevation: int):
        """
        Mark motion
        """
        self._motion_started = True
        self.set_azimuth(azimuth)
        self.set_elevation(elevation)

    def stop_motion(self):
        self._motion_started = False

    def set_azimuth(self, desired_heading: float):
        if not self._motion_started:
            raise RuntimeError("Please start motion before moving the antenna")
        print("Setting azimuth to '{}'".format(desired_heading))
        self.azimuth.set_motor_position(desired_heading)
        return self.get_azimuth()

    def get_azimuth(self):
        if not self._motion_started:
            raise RuntimeError("Please start motion before querying the azimuth position")
        return self.azimuth.get_motor_position()

    def set_elevation(self, desired_heading: float):
        if not self._motion_started:
            raise RuntimeError("Please start motion before moving the antenna")
        print("Setting elevation to '{}'".format(desired_heading))
        self.elevation.set_motor_position(desired_heading)
        return self.get_elevation()

    def get_elevation(self):
        if not self._motion_started:
            raise RuntimeError("Please start motion before querying the elevation position")
        return self.elevation.get_motor_position()

    def pin_motion_test(self, p):
        p.irq(trigger=0, handler=self.pin_motion_test)
        interrupt_pin = machine.Pin(15, machine.Pin.IN, machine.Pin.PULL_DOWN)
        print("Pin 4 has been pulled down")
        print("Entering Motor Demo State")
        print("To exit this state, reboot the device")
        _thread.start_new_thread(self.move_thread, ())

    def move_thread(self):
        import time
        print("Entering move thread, starting while loop")
        self.elevation.set_motor_position(45)
        time.sleep(5)
        self.azimuth.set_motor_position(45)
        time.sleep(10)
        while True:
            self.elevation.set_motor_position(20)
            time.sleep(1)
            self.azimuth.set_motor_position(20)
            time.sleep(15)
            self.elevation.set_motor_position(70)
            time.sleep(1)
            self.azimuth.set_motor_position(70)
            time.sleep(15)


class AntennyAPI:
    """
    Interface for interacting with the antenny board.
    """

    def __init__(self, config: Config):
        self.config = config
        self.safe_mode = True
        self.antenna = None
        self.imu = None
        self.motor = None
        self.screen = None
        self.telemetry = None
        self.gps = None
        self.i2c_bno = None
        self.i2c_servo = None
        self.i2c_screen = None

    @staticmethod
    def init_i2c(id_, scl, sda, freq=400000):
        return machine.I2C(id_,
                           scl=machine.Pin(scl, machine.Pin.OUT, machine.Pin.PULL_DOWN),
                           sda=machine.Pin(sda, machine.Pin.OUT, machine.Pin.PULL_DOWN),
                           freq=freq
                           )

    def init_imu(self, chain: machine.I2C = None):
        if self.config.get("use_imu"):
            print("use_imu found in config: {}".format(self.config.get_name()))
            try:
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
            except Exception as e:
                print("Failed to initialize IMU I2C ")
                raise AntennyIMUException(e)
        else:
            imu = MockImuController()
            print("According to your config, ou do not have an IMU connected")
        self.imu = imu
        return imu

    def init_motor(self, chain: machine.I2C = None):
        if self.config.get("use_motor"):
            print("use_motor found in config: {}".format(self.config.get_name()))
            try:
                if chain is None:
                    i2c_servo_scl = self.config.get("i2c_servo_scl")
                    i2c_servo_sda = self.config.get("i2c_servo_sda")
                    self.i2c_servo = self.init_i2c(0, i2c_servo_scl, i2c_servo_sda)
                else:
                    self.i2c_servo = chain
                motor = Pca9685Controller(
                    self.i2c_servo,
                    address=self.config.get("i2c_servo_address"),
                    min_us=500,
                    max_us=2500,
                    degrees=180
                )
                print("Motor connected")
                safe_mode = False
            except Exception as e:
                print("Failed to initialize motor")
                raise AntennyMotorException("Failed to initialize motor")
        else:
            motor = MockMotorController()
            print("According to your config, you do not have a motor connected, entering Safe Mode")
            safe_mode = True
        self.motor = motor
        self.safe_mode = safe_mode
        return motor, safe_mode

    def init_screen(self, chain: machine.I2C = None):
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
        if self.config.get("use_gps"):
            print("use_gps found in config: {}".format(self.config.get_name()))
            try:
                gps = BasicGPSController(self.config.get("gps_uart_tx"), self.config.get("gps_uart_rx"))
            except Exception as e:
                print("Failed to initialize GPS")
                raise AntennyGPSException(e)
        else:
            gps = MockGPSController()
            print("According to your config, you do not have a GPS connected")
        self.gps = gps
        return gps

    def init_telemetry(self, port=31337):
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
            try:
                telemetry_sender = UDPTelemetrySender(port, self.gps, self.imu)
            except Exception as e:
                print("Failed to initialize telemetry sender")
                raise AntennyTelemetryException(e)
        else:
            telemetry_sender = MockTelemetrySender("localhost", 31337)
            print("According to your config, you do not have a telemetry enabled")
        self.telemetry = telemetry_sender
        return telemetry_sender

    def init_controller(self):
        if self.imu is None:
            print("Cannot initialize antenna controller without IMU")
            print("Attempting to initialize IMU from Antenna Controller initialization")
            try:
                self.init_imu()
            except Exception as e:
                print("Failed to initialize IMU from Antenna Controller initialization")
                raise AntennyControllerException(e)
        if self.motor is None:
            print("Cannot initialize antenna controller without Motor")
            print("Attempting to initialize Motor from Antenna Controller initialization")
            try:
                self.init_motor()
            except Exception as e:
                print("Failed to initialize Motor from Antenna Controller initialization")
                raise AntennyControllerException(e)
        try:
            if isinstance(self.imu, MockImuController) or isinstance(self.motor, MockMotorController):
                print("WARNING: Initializing Antenna Controller with mock components, please check your config")
            print("Initializing AntennaController class")
            antenna = AntennaController(
                AxisController(
                    self.config.get("azimuth_servo_index"),
                    self.imu,
                    self.motor,
                ),
                AxisController(
                    self.config.get("elevation_servo_index"),
                    self.imu,
                    self.motor,
                ),
            )
        except Exception as e:
            print("Failed to initialize AntennaController class")
            raise AntennyControllerException(e)
        self.antenna = antenna
        return antenna

    def init_components(self):
        if self.config is None:
            print("Please load a config before initializing components")
        if not self.config.check():
            print("Config {} is not valid, failed to initialize".format(self.config.get_name()))
            print("If you believe this is an error, or you have modified the base components of the antenny board, "
                  "please check Config class as well as the default configs for more details.")

        self.init_imu()
        self.init_motor()
        self.init_screen()
        self.init_gps()
        self.init_telemetry()
        self.init_controller()

    def scan_imu(self):
        if self.i2c_bno is None:
            print("No I2C bus set for the IMU")
            raise AntennyIMUException("No I2C bus set for the IMU")
        return self.i2c_bno.scan()

    def scan_motor(self):
        if self.i2c_servo is None:
            print("No I2C bus set for the Motor")
            raise AntennyMotorException("No I2C bus set for the Motor")
        return self.i2c_servo.scan()

    def scan_screen(self):
        if self.i2c_bno is None:
            print("No I2C bus set for the Screen")
            raise AntennyScreenException("No I2C bus set for the Screen")
        return self.i2c_screen.scan()

    def start(self):
        if self.screen is not None:
            self.screen.start()
        if self.telemetry is not None:
            self.telemetry.start()

    def stop(self):
        if self.screen is not None:
            self.screen.stop()
        if self.telemetry is not None:
            self.telemetry.stop()

    def which_config(self):
        return self.config.get_name()

    def config_get(self, key):
        return self.config.get(key)

    def config_set(self, key, val):
        return self.config.set(key, val)

    def config_save(self):
        return self.config.save()

    def config_save_as(self, config_name, force=False):
        return self.config.save_as(config_name, force=force)

    def config_load(self, config_name):
        return self.config.load(config_name)

    def config_print_values(self):
        return self.config.print_values()

    def config_load_default(self):
        return self.config.load_default_config()

    def config_save_as_default(self):
        return self.config.save_as_default_config()

    def config_new(self, config_name):
        return self.config.new_config(config_name)

    def config_help(self):
        return self.config.get_help_info()

    def config_reset(self):
        return self.config.reset_default_config()

    def list_configs(self):
        return self.config.list_configs()

    def is_safemode(self):
        return self.safe_mode

    def imu_is_calibrated(self) -> bool:
        print("Checking the IMU calibration status")
        return self.imu.is_calibrated()

    def imu_calibrate_accelerometer(self):
        return self.imu.calibrate_accelerometer()

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

    def imu_calibrate(self):
        self.imu_reset_calibration()
        self.imu_calibrate_magnetometer()
        self.imu_calibrate_gyroscope()
        self.imu_calibrate_accelerometer()
        self.imu_upload_calibration()

    def imu_save_calibration_profile(self, path: str):
        print("Saving IMU calibration from '{}'".format(path))


    def load_imu_calibration_profile(self, path: str):
        print("Loading IMU calibration from '{}'".format(path))

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
        print("Outputting '{}' to telemetry.".format(data))
        if self.telemetry is None:
            raise ValueError("Please enable the 'use_telemetry' option in the config")
        self.telemetry.update(data)

    def pwm_calibration(self, error=0.1):
        """
        Calibrates Azimuth and Elevation to within specified error
        :param error: Acceptable target error
        :return: Duty cycle to get 1 degree movement with acceptable error for azimuth & elevation
        """
        # TODO Save calibrated data to some place and actually make use of it
        self.antenna.start_motion(90, 90)
        calibrated_az_duty = self.pwm_calibrate_axis(self.antenna.azimuth, 0, 1, error=error)
        calibrated_el_duty = self.pwm_calibrate_axis(self.antenna.elevation, 2, 1, error=error)
        print("Calibrated Az Duty: {}\nCalibrated El Duty: {}".format(calibrated_az_duty, calibrated_el_duty))
        return calibrated_az_duty, calibrated_el_duty

    def pwm_calibrate_axis(self, index, euler_axis, multiplier, error=0.1):
        """
        Calibrates the target axis with given measurement axis
        :param index: Target axis motor object
        :param euler_axis: Target measurement axis from Euler measurement
        :param multiplier: Calibration step multiplier
        :param error: Acceptable target error
        :return: Duty cycle to get 1 degree movement with acceptable error
        """
        # Move axis to "neutral"
        base_degree = 90
        import time
        index.set_motor_position(base_degree)
        time.sleep(2)
        base_duty = index.get_duty()
        base_euler = self.imu.euler()[euler_axis]

        if base_euler < 3.0 or base_euler > 357.0:
            base_degree = 100
            index.set_motor_position(base_degree)
            time.sleep(2)
            base_duty = index.get_duty()
            base_euler = self.imu.euler()[euler_axis]

        # Move "1" degree
        index.set_motor_position(base_degree + 1)
        time.sleep(2)
        end_duty = index.get_duty()
        end_euler = self.imu.euler()[euler_axis]

        diff_euler = end_euler - base_euler
        print("Initial Reading\nDifference: {} End: {} Base: {}".format(diff_euler, end_euler, base_euler))

        # Try to "edge" duty cycle to acceptable error
        while abs(diff_euler - 1) > error:
            if (diff_euler - 1) > 0:
                end_duty = end_duty + multiplier
            else:
                end_duty = end_duty - multiplier
            index.set_duty(end_duty)
            time.sleep(2)
            end_euler = self.imu.euler()[euler_axis]
            diff_euler = end_euler - base_euler
            print("Difference: {} End: {} Base: {}".format(diff_euler, end_euler, base_euler))

        calibrated_duty = abs(base_duty - end_duty)

        return calibrated_duty

    def motor_test(self, index: int, positon: int):
        """
        Legacy motor test, chose an index to move (0 == elevation, 1 == azimuth) and return
            the IMU values.
        """
        if index == 0:
            self.antenna.elevation.set_motor_position(positon)
        elif index == 1:
            self.antenna.azimuth.set_motor_position(positon)
        x, y, z = self.imu.euler()
        return positon, x, y, z

