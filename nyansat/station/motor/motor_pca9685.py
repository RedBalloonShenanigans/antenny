import math

import machine
import pca9685
import time

from imu.imu import ImuController
from motor.motor import ServoController, PWMController


class Pca9685Controller(PWMController):
    """Controller for the PCA9685 servomotor PWM mux driver for antenny."""
    def __init__(self, i2c: machine.I2C):
        self.pca9685 = pca9685.PCA9685(i2c)

    def _write(self, address, value):
        return self.pca9685._write(address, value)

    def _read(self, address):
        return self.pca9685._read(address)

    def reset(self):
        return self.pca9685.reset()

    def freq(self, freq=None):
        return self.pca9685.freq(freq=333)

    def pwm(self, index, on=None, off=None):
        return self.pca9685.pwm(index, on=on, off=off)

    def duty(self, index, value=None, invert=False):
        return self.pca9685.duty(index, value=value, invert=invert)


class Pca9685ServoController(ServoController):
    def __init__(self, pwm_controller: pca9685.PCA9685, index: int):
        self.pwm_controller = pwm_controller
        self.index = index
        self.min_duty = 0
        self.max_duty = 4095

    def set_min_duty(self, min_duty):
        self.min_duty = min_duty

    def get_min_duty(self):
        return self.min_duty

    def set_max_duty(self, max_duty):
        self.max_duty = max_duty

    def get_max_duty(self):
        return  self.max_duty

    def set_position(self, position):
        if self.min_duty is None or self.max_duty is None:
            print("Servo motor must be initialized!")
            raise Exception("Servo motor must be initialized!")
        if position < self.min_duty or position > self.max_duty:
            print("Servo already at its limit, please move in the other direction")
            return False
        self.pwm_controller.duty(self.index, position)

    def get_position(self):
        return self.pwm_controller.duty()

    def step(self, d=1):
        current = self.get_position()
        return self.set_position(current + d)

