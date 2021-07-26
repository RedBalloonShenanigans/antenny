import random
import time

import machine
import PID

from imu.imu import ImuController
from motor.motor import ServoController


class PIDAntennaController:
    """
    Control the antenna motion device of the antenny.
    """

    def __init__(
            self,
            azimuth: ServoController,
            elevation: ServoController,
            imu: ImuController
    ):
        self.azimuth = azimuth
        self.elevation = elevation
        self.imu = imu
        self._motion_started = False
        self.pin_interrupt = True
        self.elevation_pid = PID.PID(5, .01, .1, setpoint=self.imu.get_elevation(), output_limits=(-100, 100))
        self.azimuth_pid = PID.PID(5, .01, .1, setpoint=self.imu.get_azimuth(), output_limits=(-100, 100))
        self.elevation_pid_loop_timer = machine.Timer(0)
        self.azimuth_pid_loop_timer = machine.Timer(1)
        self.new_elevation = imu.get_elevation()
        self.new_azimuth = imu.get_azimuth()

    def set_azimuth(self, azimuth):
        self.new_azimuth = azimuth

    def get_azimuth(self):
        return self.azimuth.get_position()

    def set_elevation(self, elevation):
        self.new_elevation = elevation

    def get_elevation(self):
        return self.elevation.get_position()

    # def pin_motion_test(self, p):
    #     p.irq(trigger=0, handler=self.pin_motion_test)
    #     interrupt_pin = machine.Pin(15, machine.Pin.IN, machine.Pin.PULL_DOWN)
    #     print("Pin 4 has been pulled down")
    #     print("Entering Motor Demo State")
    #     print("To exit this state, reboot the device")
    #     _thread.start_new_thread(self.move_thread, ())

    def __elevation_pid_loop(self, timer):
        try:
            self.elevation_pid.set_point = self.new_elevation
            speed = int(self.elevation_pid(self.imu.get_elevation()))
            if speed != 0:
                print("moving elevation axis {}".format(speed))
            self.elevation.step(d=speed)
        except Exception as e:
            print(e)
            print("ERROR: De-initializing PID loop")
            timer.deinit()

    def auto_calibrate_gyroscope(self):
        old_mode = self.imu.prepare_calibration()
        gyro_level = self.imu.get_gyro_status()
        prev_gyro_level = gyro_level
        print("Calibrating gyroscope")
        print("Configuration level: {}".format(gyro_level))
        while gyro_level < 3:
            gyro_level = self.imu.get_gyro_status()
            if gyro_level != prev_gyro_level:
                print("Configuration level: {}".format(gyro_level))
                prev_gyro_level = gyro_level
        print("Gyr calibration done!")
        self.imu.mode(old_mode)
        gyro_calibration = self.imu.set_gyroscope_calibration()
        return gyro_calibration

    def auto_calibrate_accelerometer(self):
        old_mode = self.imu.prepare_calibration()
        accel_level = self.imu.get_accelerometer_status()
        prev_accel_level = accel_level
        print("Calibrating accelerometer")
        print("Configuration level: {}".format(accel_level))
        start = time.time()
        while accel_level < 3:
            if time.time() - start > 2:
                self.elevation.set_position(random.randint(self.elevation.get_min_duty(), self.elevation.get_max_duty()))
                self.azimuth.set_position(random.randint(self.azimuth.get_min_duty(), self.azimuth.get_max_duty()))
                start = time.time()
            accel_level = self.imu.get_accelerometer_status()
            if accel_level != prev_accel_level:
                print("Configuration level: {}".format(accel_level))
                prev_accel_level = accel_level
        print("Accelerometer calibration done!")
        self.imu.mode(old_mode)
        accel_calibration = self.imu.set_accelerometer_calibration()
        return accel_calibration

    def auto_calibrate_magnetometer(self):
        old_mode = self.imu.prepare_calibration()
        magnet_level = self.imu.get_magnetometer_status()
        prev_magnet_level = magnet_level
        print("Calibrating magnetometer")
        print("Configuration level: {}".format(magnet_level))
        start = time.time()
        count = 0
        count_2 = 0
        self.elevation.set_position(self.elevation.get_min_duty())
        while magnet_level < 3:
            if time.time() - start > 2:
                self.azimuth.set_position(self.azimuth.get_min_duty() + count)
                count += int((self.azimuth.get_max_duty() - self.azimuth.get_min_duty()) / 8)
                if count + self.azimuth.get_min_duty() > self.azimuth.get_max_duty():
                    count_2 += int((self.elevation.get_max_duty() - self.elevation.get_min_duty()) / 8)
                    if count_2 + self.elevation.get_min_duty() > self.elevation.get_max_duty():
                        count_2 = 0
                    self.elevation.set_position(self.elevation.get_min_duty() + count_2)
                    count = 0
                start = time.time()
            magnet_level = self.imu.get_magnetometer_status()
            if magnet_level != prev_magnet_level:
                print("Configuration level: {}".format(magnet_level))
                prev_magnet_level = magnet_level
        print("Magnetometer calibration done!")
        self.imu.mode(old_mode)
        magnet_calibration = self.imu.set_magnetometer_calibration()
        return magnet_calibration

    @staticmethod
    def get_delta(current, prev):
        d = abs(current - prev)
        if d > 180:
            d = 360 - d
        return d

    def get_elevation_min_max(self, duty=25, d=.5):
        moving = False
        first_move = False
        self.elevation.set_min_duty(0)
        self.elevation.set_max_duty(4095)
        self.elevation.set_position(int((self.azimuth.get_max_duty() - self.azimuth.get_min_duty()) / 2))
        prev_elevation = self.imu.get_elevation()
        for i in range(self.elevation.get_min_duty(), self.elevation.get_max_duty(), duty):
            self.elevation.set_position(i)
            current = self.imu.get_elevation()
            delta = self.get_delta(current, prev_elevation)
            print("{}: {}".format(i, delta))
            if (delta > d) and not first_move:
                first_move = True
                print("First movement detected at {}".format(i))
                print("Waiting again")
                print("Previous: {}".format(prev_elevation))
                print("Current: {}".format(current))
                print("Delta: {}".format(delta))
            elif (delta > d) and first_move and not moving:
                moving = True
                print("Movement detected at {}".format(i))
                print("Previous: {}".format(prev_elevation))
                print("Current: {}".format(current))
                print("Delta: {}".format(delta))
                self.elevation.min_duty = i
            elif (delta < d) and moving:
                self.elevation.set_position(i+100)
                try_again_delta = self.get_delta(self.imu.get_elevation(), current)
                if try_again_delta > d:
                    continue
                print("No movement detected at {}".format(i))
                print("Previous: {}".format(prev_elevation))
                print("Current: {}".format(current))
                print("Delta: {}".format(delta))
                self.elevation.max_duty = i
                return
            prev_elevation = current

    def get_azimuth_min_max(self, duty=25, d=.5):
        moving = False
        first_move = False
        self.azimuth.set_min_duty(0)
        self.azimuth.set_max_duty(4095)
        self.elevation.set_position(int((self.azimuth.get_max_duty() - self.azimuth.get_min_duty()) / 2))
        self.imu.get_elevation()
        self.azimuth.set_position(int((self.azimuth.get_max_duty() - self.azimuth.get_min_duty()) / 2))
        prev_azimuth= self.imu.get_azimuth()
        for i in range(self.azimuth.get_min_duty(), self.azimuth.get_max_duty(), duty):
            self.azimuth.set_position(i)
            current = self.imu.get_azimuth()
            delta = self.get_delta(current, prev_azimuth)
            print("{}: {}".format(i, delta))
            if (delta > d) and not first_move:
                first_move = True
                print("First movement detected at {}".format(i))
                print("Waiting again")
                print("Previous: {}".format(prev_azimuth))
                print("Current: {}".format(current))
                print("Delta: {}".format(delta))
            elif (delta > d) and first_move and not moving:
                moving = True
                print("Movement detected at {}".format(i))
                print("Previous: {}".format(prev_azimuth))
                print("Current: {}".format(current))
                print("Delta: {}".format(delta))
                self.azimuth.min_duty = i
            elif (delta < d) and moving:
                self.azimuth.set_position(i+100)
                try_again_delta = self.get_delta(self.imu.get_azimuth(), current)
                if try_again_delta > d:
                    continue
                print("No movement detected at {}".format(i))
                print("Previous: {}".format(prev_azimuth))
                print("Current: {}".format(current))
                print("Delta: {}".format(delta))
                self.azimuth.max_duty = i
                return
            prev_azimuth = current
