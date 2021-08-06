import machine
import pca9685 as pca9685
from motor.motor import ServoController, PWMController


class Pca9685Controller(PWMController):
    """Controller for the PCA9685 servomotor PWM mux driver for antenny."""
    def __init__(self, i2c: machine.I2C):
        self.pca9685 = pca9685.PCA9685(i2c)

    def reset(self):
        """
        Resets the device
        :return:
        """
        return self.pca9685.reset()

    def freq(self, freq=None):
        """
        Sets the output pwm frequency for all channels in Hz
        :param freq:
        :return:
        """
        return self.pca9685.freq(freq=freq)

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
    def __init__(self, pwm_controller: pca9685.PCA9685, index: int):
        self.pwm_controller = pwm_controller
        self.index = index
        self.min_duty = 0
        self.max_duty = 4095

    def set_min_position(self, min_duty):
        """
        Sets the minimum duty cycle that will move the servo
        :param min_duty:
        :return:
        """
        self.min_duty = min_duty

    def get_min_position(self):
        """
        Gets the minimum duty cycle that will move the servo
        :return:
        """
        return self.min_duty

    def set_max_position(self, max_duty):
        """
        Sets the maximum duty cycle that will move the servo
        :param max_duty:
        :return:
        """
        self.max_duty = max_duty

    def get_max_position(self):
        """
        Gets the maximum duty cycle that will move the servo
        :return:
        """
        return self.max_duty

    def set_position(self, position):
        """
        Sets the position of the servo
        :param position:
        :return:
        """
        if self.min_duty is None or self.max_duty is None:
            print("Servo motor must be initialized!")
            raise Exception("Servo motor must be initialized!")
        if position < self.min_duty:
            self.pwm_controller.duty(self.index, self.min_duty)
            return False
        elif position > self.max_duty:
            self.pwm_controller.duty(self.index, self.max_duty)
            return False
        self.pwm_controller.duty(self.index, position)
        return True

    def get_position(self):
        """
        Gets the position of the servo
        :return:
        """
        return self.pwm_controller.duty(self.index)

    def step(self, d=1):
        """
        Steps by a given unit d
        :param d:
        :return:
        """
        current = self.get_position()
        return self.set_position(current + d)
