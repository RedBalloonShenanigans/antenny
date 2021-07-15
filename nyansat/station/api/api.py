import machine
import _thread

from config.config import Config
from imu.imu import ImuController
from motor.motor import MotorController

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

    def __init__(
            self,
            antenna: AntennaController,
            imu: ImuController,
            config: Config,
            screen,
            telemetry,
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
        return self.imu.get_calibration_status().is_calibrated()

    def save_imu__calibration_profile(self, path: str):
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
        if self._screen is None:
            raise ValueError("Please enable the 'use_screen' option in the config")
        self._screen.display(data)

    def update_telemetry(self, data: dict):
        print("Outputting '{}' to telemetry.".format(data))
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

