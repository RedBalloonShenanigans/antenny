import math

import machine
import pca9685 as pca9685
from motor.motor import ServoController, PWMController


class Pca9685Controller(PWMController):
    """Controller for the PCA9685 servomotor PWM mux driver for antenny."""
    def __init__(self, i2c: machine.I2C, freq: int = 333):
        self.pca9685 = pca9685.PCA9685(i2c)
        self.frequency = freq
        self.pca9685.freq(self.frequency)

    def reset(self):
        """
        Resets the device
        :return:
        """
        return self.pca9685.reset()

    def pwm(self, index, on=None, off=None):
        """
        Sets the pwm output for a given pwm pin
        :param index:
        :param on:
        :param off:
        :return:
        """
        return self.pca9685.pwm(index, on=on, off=off)

    def duty(self, index, value=None, invert=False):
        """
        Sets the duty cycle for a given pwm pin
        :param index:
        :param value:
        :param invert:
        :return:
        """
        return self.pca9685.duty(index, value=value, invert=invert)


class Pca9685ServoController(ServoController):
    def __init__(self, pwm_controller: Pca9685Controller, index: int):
        self.pwm_controller = pwm_controller
        self.index = index
        self.min_us = None
        self.max_us = None

    def _us2duty(self, us):
        return int(4095 * us / (1000000 / self.pwm_controller.frequency))

    def _duty2us(self, duty):
        return int(duty * (1000000 / self.pwm_controller.frequency) / 4095)

    def set_min_position(self, min_us):
        """
        Sets the minimum duty cycle that will move the servo
        :param min_us:
        :return:
        """
        self.min_us = min_us

    def get_min_position(self):
        """
        Gets the minimum duty cycle that will move the servo
        :return:
        """
        return self.min_us

    def set_max_position(self, max_us):
        """
        Sets the maximum duty cycle that will move the servo
        :param max_us:
        :return:
        """
        self.max_us = max_us

    def get_max_position(self):
        """
        Gets the maximum duty cycle that will move the servo
        :return:
        """
        return self.max_us

    def set_position(self, position):
        """
        Sets the position of the servo
        :param position:
        :return:
        """

        if self.min_us is None or self.max_us is None:
            print("Servo motor must be initialized!")
            raise Exception("Servo motor must be initialized!")

        position = self._us2duty(position)

        if position < self.min_us:
            self.pwm_controller.duty(self.index, self.min_us)
            return False
        elif position > self.max_us:
            self.pwm_controller.duty(self.index, self.max_us)
            return False
        self.pwm_controller.duty(self.index, position)

        return True

    def get_position(self):
        """
        Gets the position of the servo
        :return:
        """
        return self._duty2us(self.pwm_controller.duty(self.index))

    def step(self, d=1):
        """
        Steps by a given unit d
        :param d:
        :return:
        """
        current = self.get_position()
        return self.set_position(current + d)
