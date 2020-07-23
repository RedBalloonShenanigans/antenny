import _thread
import logging
import time

import machine
from machine import Pin

from config.config import ConfigRepository
from gps.gps_basic import BasicGPSController
from imu.imu import ImuController
from imu.imu_bno055 import Bno055ImuController
from motor.motor_pca9685 import Pca9685Controller
from screen.screen_ssd1306 import Ssd1306ScreenController
from sender import UDPTelemetrySender


class AntennaController:
    """
    Control antenna related servos & IMU.
    """

    def __init__(
            self,
            imu: ImuController,
            motor_controller,
    ):
        self.antenna_imu = imu
        self.imu_lock = _thread.allocate_lock()
        self.motor_controller = motor_controller
        self.cfg = ConfigRepository()

        self._el_moving = False
        self._az_moving = False
        self._pinned_mode = False

        # TODO: these all need to be split into their respective heading control class
        self._elevation_servo_idx = self.cfg.get("elevation_servo_index")
        self._azimuth_servo_idx = self.cfg.get("azimuth_servo_index")
        self.get_heading()
        self._elevation_target = self._el_last = self._heading.elevation
        self._azimuth_target = self._az_last = self._heading.azimuth
        self._actual_elevation = 90.0
        self._actual_azimuth = 90.0
        self.do_imu_calibration()

        self._el_max_rate = self.cfg.get("elevation_max_rate")
        self._az_max_rate = self.cfg.get("azimuth_max_rate")

        self._calibrated_elevation_offset = None
        self._calibrated_azimuth_offset = None

        self._heading = None
        self._pinned_heading = None
        self._pinned_servo_pos = None

        self._orientation_updates = True
        self._motion_control = True
        self._orientation_thread = _thread.start_new_thread(self.update_orientation, ())
        self._move_thread = _thread.start_new_thread(self.move_loop, ())

        time.sleep(6)
        self.motor_controller.set_position(self._elevation_servo_idx, 90)
        time.sleep(0.1)
        self.motor_controller.set_position(self._azimuth_servo_idx, 90)
        time.sleep(0.1)

    def close(self):
        self._orientation_updates = False
        self._motion_control = False

    def do_imu_calibration(self):
        heading = self.antenna_imu.heading()
        self._elevation_target = heading.elevation
        self._azimuth_target = heading.azimuth

        self._calibrated_elevation_offset = heading.elevation - self._actual_elevation
        self._calibrated_azimuth_offset = heading.azimuth - self._actual_azimuth

    def get_heading(self):
        with self.imu_lock:
            self._heading = self.antenna_imu.heading()

    def pin(self):
        """
        Pin the antenna in place.
        """
        self._pinned_heading = self._heading
        self._pinned_servo_pos = [self._el_last, self._az_last]
        self._pinned_mode = True

    def unpin(self):
        """
        Unpin the antenna from it's heading
        """
        self._pinned_heading = None
        self._pinned_servo_pos = None
        self._pinned_mode = False

    def do_move_mode(self):
        """
        Perform a smooth move to the target elevation & azimuth.
        """
        self.motor_controller.smooth_move(self._elevation_servo_idx, self._elevation_target, 10)
        self._el_moving = False
        self.motor_controller.smooth_move(self._azimuth_servo_idx, self._azimuth_target, 10)
        self._az_moving = False

    def do_pin_mode(self):
        """
        Pin the antenna heading in place, moving for any deltas sensed by the IMU
        """
        delta_x = self._pinned_heading.elevation - self._heading.elevation
        delta_y = self._pinned_heading.azimuth - self._heading.azimuth
        logging.info("d-x {}, d-y {}".format(delta_x, delta_y))
        self._elevation_target = self._el_last + delta_x * -1
        self._azimuth_target = self._az_last + delta_y
        self.do_move_mode()

    def update_orientation(self):
        """
        Acquire a lock on the IMU, update the current heading.
        """
        while self._orientation_updates:
            try:
                with self.imu_lock:
                    self._heading = self.antenna_imu.heading()
            except Exception as e:
                logging.info("Error in orientation update: {}".format(e))

    def move_loop(self):
        """
        Handle motion control, in both fixed heading (pin mode) and single target (move mode).
        """
        while self._motion_control:
            while self._az_moving or self._el_moving or self._pinned_mode:
                try:
                    if self._pinned_heading:
                        self.do_pin_mode()
                    else:
                        self.do_move_mode()
                    time.sleep(0.1)
                except Exception as e:
                    logging.info(e)
            time.sleep(0.1)

    def imu_status(self) -> str:
        return self.antenna_imu.get_status().to_string()

    def set_elevation_degrees(self, deg):
        """
        Perform a move by setting the target elevation in degrees.
        """
        self._el_moving = True
        self._elevation_target = deg

    def set_azimuth_degrees(self, deg):
        """
        Perform a move by setting the target azimuth in degrees.
        """
        self._az_moving = True
        self._azimuth_target = deg

    @property
    def azimuth(self):
        return self._actual_azimuth

    @azimuth.setter
    def azimuth(self, deg):
        self.set_azimuth_degrees(deg)

    @property
    def current_azimuth(self):
        return self._az_last + self._calibrated_azimuth_offset

    @current_azimuth.setter
    def current_azimuth(self, deg):
        self.set_azimuth_degrees(deg + self._calibrated_azimuth_offset)

    @property
    def current_elevation(self):
        return self._el_last + self._calibrated_elevation_offset

    @current_elevation.setter
    def current_elevation(self, deg):
        self.set_elevation_degrees(deg + self._calibrated_elevation_offset)

    @property
    def elevation(self):
        return self._el_last

    @elevation.setter
    def elevation(self, deg):
        self.set_elevation_degrees(deg)

    def motor_test(self, index, position):
        pos = self.motor_controller.smooth_move(index, position, 10)
        x_angle, y_angle, z_angle = self.antenna_imu.euler()
        return pos, x_angle, y_angle, z_angle

    def _measure_az(self, min_angle, max_angle):
        with self.imu_lock:
            self.motor_controller.set_position(self._azimuth_servo_idx, min_angle)
            time.sleep(0.3)
            a1 = self.antenna_imu.heading().azimuth
            time.sleep(1)
            self.motor_controller.set_position(self._azimuth_servo_idx, max_angle)
            time.sleep(0.3)
            a2 = self.antenna_imu.heading().azimuth
            time.sleep(1)
            return a1, a2

    def test_az_axis(self):
        # measure servo pwm parameters
        self.current_azimuth = 90
        time.sleep(1)
        self.get_heading()
        self.current_azimuth = 80
        time.sleep(2)
        self.get_heading()
        a1 = self._heading.azimuth
        self.current_azimuth = 100
        time.sleep(2)
        self.get_heading()
        a2 = self._heading.azimuth

        # should be 20 degrees. what did we get
        observed_angle = abs(a1) + a2
        angle_factor = observed_angle / 20.0
        self.motor_controller._set_degrees(1, self.motor_controller.degrees(1) * angle_factor)
        print("Observed angle: {} factor: {}".format(observed_angle, angle_factor))

    def test_el_axis(self):
        # measure servo pwm parameters
        self.current_azimuth = 90.0
        time.sleep(1)
        self.motor_controller.set_position(0, 90)
        time.sleep(1)
        self.get_heading()
        self.motor_controller.set_position(0, 70)
        time.sleep(2)
        a1 = self._heading.elevation
        self.motor_controller.set_position(0, 110)
        time.sleep(2)
        self.get_heading()
        a2 = self._heading.elevation

        # should be 20 degrees. what did we get
        observed_angle = a1 - a2
        angle_factor = observed_angle / 4.0
        self.motor_controller._set_degrees(0, self.motor_controller.degrees(0) * angle_factor)
        print("Observed angle: {} factor: {}".format(observed_angle, angle_factor))

    def auto_zero_az(self):
        # automatically find azimuth offset
        self.motor_controller.set_position(self._azimuth_servo_idx, 90)
        self.motor_controller.set_position(self._elevation_servo_idx, 90)
        time.sleep(1)
        a1 = 60
        a2 = 120
        p_center = 100
        while abs(p_center) > 0.1:
            p1, p2 = self._measure_az(a1, a2)
            p_center = (p1 + p2) / 2
            print("a1: {},{} a2: {},{} a-center: {}".format(a1, p1, a2, p2, p_center))
            if p_center > 0:
                a2 = a2 - abs(p_center)
            else:
                a1 = a1 + abs(p_center)

        min_y = 100
        min_angle = None
        cur_angle = avg_angle = (a1 + a2) / 2 - 1.5
        while cur_angle < avg_angle + 1.5:
            self.motor_controller.set_position(self._azimuth_servo_idx, cur_angle)
            time.sleep(0.2)
            cur_y = abs(self.antenna_imu.heading().azimuth)
            if cur_y < min_y:
                min_y = cur_y
                min_angle = cur_angle
            cur_angle += 0.1

        time.sleep(1)
        a_center = min_angle
        self.motor_controller.set_position(self._azimuth_servo_idx, a_center)
        print("a-center: {}".format(a_center))
        self.get_heading()
        self._calibrated_azimuth_offset = a_center - 90.0

    def pwm_calibration(self, error=0.1):
        # Azimuth calibration first
        # Move motor to neutral
        base_degree = 90
        self.motor_controller.set_position(self._azimuth_servo_idx, degrees=base_degree)
        time.sleep(2)
        base_duty = self.motor_controller.duty(self._azimuth_servo_idx)
        base_heading, base_roll, base_pitch = self.antenna_imu.euler()

        if base_heading < 1.0:
            base_degree = 100
            self.motor_controller.set_position(self._azimuth_servo_idx, degrees=base_degree)
            time.sleep(2)
            base_duty = self.motor_controller.duty(self._azimuth_servo_idx)
            base_heading, base_roll, base_pitch = self.antenna_imu.euler()

        # Move "1" degree
        self.motor_controller.set_position(self._azimuth_servo_idx, degrees=base_degree+1)
        time.sleep(2)
        end_duty = self.motor_controller.duty(self._azimuth_servo_idx)
        end_heading, end_roll, end_pitch = self.antenna_imu.euler()

        diff_heading = end_heading - base_heading
        print("{} {} {}".format(diff_heading, end_heading, base_heading))

        while abs(diff_heading - 1) > error:
            if (diff_heading - 1) > 0:
                end_duty = end_duty + 1
            else:
                end_duty = end_duty - 1
            self.motor_controller.set_position(self._azimuth_servo_idx, duty=end_duty)
            time.sleep(2)
            end_heading, end_roll, end_pitch = self.antenna_imu.euler()
            diff_heading = end_heading - base_heading
            print("{} {} {}".format(diff_heading, end_heading, base_heading))

        calibrated_az_duty = abs(base_duty - end_duty)

        print("Calibrated Azimuth Duty Cycle: {}".format(calibrated_az_duty))

        # TODO Same procedure with elevation
        # TODO Save calibrated data to some place and actually make use of it
        return calibrated_az_duty

    def auto_calibration(self):
        # read from BNO055 sensor, move antenna
        # soft home, etc
        self.motor_controller.set_position(self._azimuth_servo_idx, 90)
        self.motor_controller.set_position(self._elevation_servo_idx, 90)
        time.sleep(1)

        self.motor_controller.set_position(self._elevation_servo_idx, 180)
        time.sleep(1)
        self.motor_controller.set_position(self._elevation_servo_idx, 0)
        time.sleep(1)
        self.motor_controller.set_position(self._elevation_servo_idx, 180)
        time.sleep(1)
        self.motor_controller.set_position(self._elevation_servo_idx, 0)
        time.sleep(1)

        self.motor_controller.set_position(self._azimuth_servo_idx, 180)
        time.sleep(1)
        self.motor_controller.set_position(self._azimuth_servo_idx, 0)
        time.sleep(1)
        self.motor_controller.set_position(self._azimuth_servo_idx, 180)
        time.sleep(1)
        self.motor_controller.set_position(self._azimuth_servo_idx, 0)
        time.sleep(1)

        self.motor_controller.set_position(self._azimuth_servo_idx, 90)
        self.motor_controller.set_position(self._elevation_servo_idx, 90)
        time.sleep(1)

        self.motor_controller.set_position(self._elevation_servo_idx, 0)
        self.get_heading()
        x1 = self._heading.elevation
        time.sleep(1)
        self.motor_controller.set_position(self._elevation_servo_idx, 180)
        self.get_heading()
        x2 = self._heading.elevation
        time.sleep(1)
        self.motor_controller.set_position(self._azimuth_servo_idx, 0)
        self.get_heading()
        y1 = self._heading.azimuth
        time.sleep(1)
        self.motor_controller.set_position(self._azimuth_servo_idx, 180)
        self.get_heading()
        y2 = self._heading.azimuth

        return "[{}] - [{}] [{}] - [{}]".format(x1, x2, y1, y2)


class AntKontrol:
    """Controller for Nyansat setup: integrated servo controls, IMU usage

    Default components:
    - BNO055 Absolute orientation sensor
    - 16-channel pwm breakout servo controller
    """

    def __init__(self):
        self.cfg = ConfigRepository()
        self._gps = BasicGPSController()
        self.imu = Bno055ImuController(
            machine.I2C(
                1,
                scl=machine.Pin(self.cfg.get("i2c_bno_scl"), Pin.OUT, Pin.PULL_DOWN),
                sda=machine.Pin(self.cfg.get("i2c_bno_sda"), Pin.OUT, Pin.PULL_DOWN),
            ),
            sign=(0, 0, 0)
        )
        self._sender = UDPTelemetrySender(
                self._gps,
                self.imu
        )
        self.antenna = AntennaController(
                self.imu,
                Pca9685Controller(
                    machine.I2C(
                        0,
                        scl=Pin(self.cfg.get("i2c_servo_scl"), Pin.OUT, Pin.PULL_DOWN),
                        sda=Pin(self.cfg.get("i2c_servo_sda"), Pin.OUT, Pin.PULL_DOWN),
                    ),
                    address=self.cfg.get("i2c_servo_address"),
                    min_us=500,
                    max_us=2500,
                    degrees=180
                )
        )

        try:
            self._i2c_screen = machine.I2C(
                    -1,
                    scl=machine.Pin(self.cfg.get("i2c_screen_scl"), Pin.OUT, Pin.PULL_DOWN),
                    sda=machine.Pin(self.cfg.get("i2c_screen_sda"), Pin.OUT, Pin.PULL_DOWN),
            )  # on [60] ssd1306
            self._screen = Ssd1306ScreenController(self._i2c_screen, width=128, height=32)
            self._screen_thread = _thread.start_new_thread(self.display_status, ())
        except:
            self._screen = None
            self._screen_thread = None

        self._sender.start()
        self._gps_thread = _thread.start_new_thread(self._gps.run, ())

    def display_status(self):
        while self._screen is not None:
            try:
                self._screen.display(self.imu.euler())
                pass
            except Exception as e:
                logging.info("Status display error: {}".format(str(e)))
            time.sleep(0.2)

    def close(self):
        self.antenna.close()
