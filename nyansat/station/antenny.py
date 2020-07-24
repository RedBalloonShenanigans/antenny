import logging

from config.config import ConfigRepository
from imu.imu import ImuController

from imu.mock_imu import MockImuController
from motor.mock_motor import MockMotorController
from motor.motor import MotorController
from screen.mock_screen import MockScreenController
from screen.screen import ScreenController
from antenny_threading import Queue
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
        self._current_motor_position = _DEFAULT_MOTOR_POSITION
        self.set_motor_position(_DEFAULT_MOTOR_POSITION)

    def get_motor_position(self) -> float:
        return self._current_motor_position

    def set_motor_position(self, desired_heading: float):
        self._current_motor_position = desired_heading
        self.motor.set_position(self.motor_idx, desired_heading)


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

    def set_azimuth(self, desired_heading: float):
        LOG.info("Setting azimuth to '{}'".format(desired_heading))
        self.azimuth.set_motor_position(desired_heading)
        return self.get_azimuth()

    def get_azimuth(self):
        return self.azimuth.get_motor_position()

    def set_elevation(self, desired_heading: float):
        LOG.info("Setting elevation to '{}'".format(desired_heading))
        self.elevation.set_motor_position(desired_heading)
        return self.get_elevation()

    def get_elevation(self):
        return self.elevation.get_motor_position()

    def motor_test(self):
        raise NotImplementedError


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
    ):
        self.antenna = antenna
        self.imu = imu
        self.config = config
        self._screen = screen
        self._telemetry = telemetry

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
    # if config.get("use_telemetry"):
    if use_telemetry:
        telemetry_sender = MockTelemetrySender('127.0.0.1', 1337)
    api = AntennyAPI(
            antenna_controller,
            imu,
            config,
            screen,
            telemetry_sender,
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

    if config.get("use_imu"):
        imu = Bno055ImuController(
                machine.I2C(
                        1,
                        scl=machine.Pin(config.get("i2c_bno_scl"), Pin.OUT, Pin.PULL_DOWN),
                        sda=machine.Pin(config.get("i2c_bno_sda"), Pin.OUT, Pin.PULL_DOWN),
                ),
                sign=(0, 0, 0)
        )
    else:
        LOG.warning("IMU disabled, please set use_imu=True in the settings and run `antkontrol`")
        imu = MockImuController()
    motor = Pca9685Controller(
            machine.I2C(
                    0,
                    scl=Pin(config.get("i2c_servo_scl"), Pin.OUT, Pin.PULL_DOWN),
                    sda=Pin(config.get("i2c_servo_sda"), Pin.OUT, Pin.PULL_DOWN),
            ),
            min_us=500,
            max_us=2500,
            degrees=180
    )
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
    screen = None
    if config.get("use_screen"):
        screen = MockScreenController(
                Queue()
        )
    else:
        LOG.warning(
                "Screen disabled, please set use_screen=True in the settings and run `antkontrol`"
        )
    telemetry_sender = None
    if config.get("use_telemetry"):
        telemetry_sender = MockTelemetrySender('127.0.0.1', 1337)
    else:
        LOG.warning(
            "Telemetry disabled, please set use_screen=True in the settings and run `antkontrol`")
    api = AntennyAPI(
            antenna_controller,
            imu,
            config,
            screen,
            telemetry_sender,
    )
    api.start()
    return api
