import logging
import machine
import _thread

from config.config import ConfigRepository
from gps.gps_basic import BasicGPSController
from gps.mock_gps_controller import MockGPSController
from imu.imu import ImuController

from imu.mock_imu import MockImuController
from motor.mock_motor import MockMotorController
from motor.motor import MotorController
from screen.mock_screen import MockScreenController
from screen.screen import ScreenController
from antenny_threading import Queue
from sender.sender_udp import UDPTelemetrySender
from sender.mock_sender import MockTelemetrySender

_DEFAULT_MOTOR_POSITION = 90.
_DEFAULT_MOTION_DELAY = 0.75

LOG = logging.getLogger('antenny')


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
        LOG.info("Setting azimuth to '{}'".format(desired_heading))
        self.azimuth.set_motor_position(desired_heading)
        return self.get_azimuth()

    def get_azimuth(self):
        if not self._motion_started:
            raise RuntimeError("Please start motion before querying the azimuth position")
        return self.azimuth.get_motor_position()

    def set_elevation(self, desired_heading: float):
        if not self._motion_started:
            raise RuntimeError("Please start motion before moving the antenna")
        LOG.info("Setting elevation to '{}'".format(desired_heading))
        self.elevation.set_motor_position(desired_heading)
        return self.get_elevation()

    def get_elevation(self):
        if not self._motion_started:
            raise RuntimeError("Please start motion before querying the elevation position")
        return self.elevation.get_motor_position()

    def pin_motion_test(self, p):
        p.irq(trigger=0, handler=self.pin_motion_test)
        interrupt_pin = machine.Pin(15, machine.Pin.IN, machine.Pin.PULL_DOWN)
        LOG.info("Pin 4 has been pulled down")
        LOG.info("Entering Motor Demo State")
        LOG.info("To exit this state, reboot the device")
        _thread.start_new_thread(self.move_thread, ())

    def move_thread(self):
        import time
        LOG.info("Entering move thread, starting while loop")
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

    def __init__(
            self,
            antenna: AntennaController,
            imu: ImuController,
            config: ConfigRepository,
            screen,  # type: Optional[ScreenController]
            telemetry,  # type: Optional[TelemetrySender]
            safe_mode: bool,
    ):
        self.antenna = antenna
        self.imu = imu
        self.config = config
        self._screen = screen
        self._telemetry = telemetry
        self.safe_mode = safe_mode

    def start(self):
        if self._screen is not None:
            self._screen.start()
        if self._telemetry is not None:
            self._telemetry.start()

    def stop(self):
        if self._screen is not None:
            self._screen.stop()
        if self._telemetry is not None:
            self._telemetry.stop()

    def is_safemode(self):
        return self.safe_mode

    def imu_is_calibrated(self) -> bool:
        LOG.info("Checking the IMU calibration status")
        return self.imu.get_calibration_status().is_calibrated()

    def save_imu__calibration_profile(self, path: str):
        LOG.info("Saving IMU calibration from '{}'".format(path))

    def load_imu_calibration_profile(self, path: str):
        LOG.info("Loading IMU calibration from '{}'".format(path))

    def set_config_value(self, config_name: str, config_value):
        LOG.info("Setting config entry '{}' to value '{}'".format(config_name, config_value))
        self.config.set(config_name, config_value)

    def get_config_value(self, config_name: str):
        return self.config.get(config_name)

    def print_to_display(self, data):
        LOG.debug("Outputting '{}' to the screen.".format(data))
        if self._screen is None:
            raise ValueError("Please enable the 'use_screen' option in the config")
        self._screen.display(data)

    def update_telemetry(self, data: dict):
        LOG.debug("Outputting '{}' to telemetry.".format(data))
        if self._telemetry is None:
            raise ValueError("Please enable the 'use_telemetry' option in the config")
        self._telemetry.update(data)

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
        # type: (...) -> Tuple[int, float, float, float]
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


def mock_antenna_api_factory(
        use_screen: bool = False,
        use_telemetry: bool = False,
):
    """
    Create a new MOCK AntennyAPI object. Useful for local debugging in a desktop python environment.
    """
    config = ConfigRepository()
    imu = MockImuController()
    motor = MockMotorController()
    antenna_controller = AntennaController(
        AxisController(
            1,
            imu,
            motor,
        ),
        AxisController(
            0,
            imu,
            motor,
        ),
    )
    if use_screen and not config.get("use_screen"):
        config.set("use_screen", True)
    screen = None
    if config.get("use_screen"):
        screen = MockScreenController(
            Queue()
        )
    if use_telemetry and not config.get("use_telemetry"):
        config.set("use_telemetry", True)
    telemetry_sender = None
    if use_telemetry:
        telemetry_sender = MockTelemetrySender('127.0.0.1', 1337)
    api = AntennyAPI(
        antenna_controller,
        imu,
        config,
        screen,
        telemetry_sender,
        True,
    )
    api.start()
    return api


def esp32_antenna_api_factory():
    """
    Create a new AntennyAPI object.
    """
    import machine
    from machine import Pin

    from imu.imu_bno055 import Bno055ImuController
    from motor.motor_pca9685 import Pca9685Controller

    config = ConfigRepository()
    safe_mode = False

    i2c_bno_scl = config.get("i2c_bno_scl")
    i2c_bno_sda = config.get("i2c_bno_sda")
    i2c_servo_scl = config.get("i2c_servo_scl")
    i2c_servo_sda = config.get("i2c_servo_sda")
    i2c_ch0 = machine.I2C(
        0,
        scl=Pin(i2c_servo_scl, Pin.OUT, Pin.PULL_DOWN),
        sda=Pin(i2c_servo_sda, Pin.OUT, Pin.PULL_DOWN),
    )
    if (i2c_bno_scl == i2c_servo_scl) and (i2c_bno_sda == i2c_servo_sda):
        i2c_ch1 = i2c_ch0
        LOG.info("I2C Channel 0 is same as Channel 1; using chained bus")
    else:
        i2c_ch1 = machine.I2C(
            -1,
            scl=Pin(i2c_bno_scl, Pin.OUT, Pin.PULL_DOWN),
            sda=Pin(i2c_bno_sda, Pin.OUT, Pin.PULL_DOWN),
            freq=1000,
        )

    if config.get("use_imu"):
        try:
            imu = Bno055ImuController(
                i2c_ch1,
                crystal=False,
                address=config.get("i2c_bno_address"),
                sign=(0, 0, 0)
            )
        except OSError:
            LOG.warning("Unable to initialize IMU, check configuration")
            imu = MockImuController()
    else:
        LOG.warning("IMU disabled, please set use_imu=True in the settings and run `antkontrol`")
        imu = MockImuController()
    try:
        motor = Pca9685Controller(
            i2c_ch0,
            address=config.get("i2c_servo_address"),
            min_us=500,
            max_us=2500,
            degrees=180
        )
    except OSError:
        address = i2c_ch0.scan()
        if (i2c_ch1 != i2c_ch0) and (len(address) != 0):
            motor = Pca9685Controller(
                i2c_ch0,
                address=address[0],
                min_us=500,
                max_us=2500,
                degrees=180
            )
            LOG.info("Using auto address configuration for motor driver")
        else:
            LOG.warning("Unable to initialize motor driver, entering SAFE MODE OPERATION")
            LOG.warning("Your device may be improperly configured. Use the `setup` command to reconfigure and run "
                        "`antkontrol`")
            safe_mode = True
            motor = MockMotorController()

    try:
        azimuth_index = config.get("azimuth_servo_index")
        elevation_index = config.get("elevation_servo_index")
    except:
        LOG.warning("Unable to retrieve servo indices, using default values. Your motor movement may be incorrect")
        azimuth_index = 1
        elevation_index = 0

    antenna_controller = AntennaController(
        AxisController(
            azimuth_index,
            imu,
            motor,
        ),
        AxisController(
            elevation_index,
            imu,
            motor,
        ),
    )
    screen = None
    if config.get("use_screen"):
        screen = MockScreenController(
            Queue()
        )
    else:
        LOG.warning(
            "Screen disabled, please set use_screen=True in the settings and run `antkontrol`"
        )
    gps = None
    if config.get("use_gps"):
        gps = BasicGPSController()
    else:
        LOG.warning(
            "GPS disabled, please set use_gps=True in the settings and run `antkontrol`."
        )
        gps = MockGPSController()
    telemetry_sender = None
    if config.get("use_telemetry"):
        if not config.get("use_imu"):
            LOG.warning("Telemetry enabled, but IMU disabled in config! Please enable the IMU ("
                        "using the IMU mock)")
        if not config.get("use_gps"):
            LOG.warning("Telemetry enabled, but GPS disabled in config! Please enable the GPS ("
                        "using the GPS mock)")
        telemetry_sender = UDPTelemetrySender(31337, gps, imu)
    else:
        LOG.warning(
            "Telemetry disabled, please set use_screen=True in the settings and run `antkontrol`")
    api = AntennyAPI(
        antenna_controller,
        imu,
        config,
        screen,
        telemetry_sender,
        safe_mode,
    )
    if config.get("enable_demo"):
        interrupt_pin = machine.Pin(15, machine.Pin.IN, machine.Pin.PULL_UP)
        interrupt_pin.irq(trigger=machine.Pin.IRQ_FALLING, handler=api.antenna.pin_motion_test)

    api.start()
    return api
