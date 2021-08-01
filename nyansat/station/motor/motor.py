class PWMController(object):
    """Controls the PWM controller over I2C"""
    def reset(self):
        """
        Resets the device
        :return:
        """
        raise NotImplementedError()

    def freq(self, freq=None):
        """
        Sets the output pwm frequency for all channels in Hz
        :param freq:
        :return:
        """
        raise NotImplementedError()

    def pwm(self, index, on=None, off=None):
        """
        Sets the pwm output for a given pwm pin
        :param index:
        :param on:
        :param off:
        :return:
        """
        raise NotImplementedError()

    def duty(self, index, value=None, invert=False):
        """
        Sets the duty cycle for a given pwm pin
        :param index:
        :param value:
        :param invert:
        :return:
        """
        raise NotImplementedError()


class ServoController(object):
    def set_min_position(self, min_duty):
        """
        Sets the minimum duty cycle that will move the servo
        :param min_duty:
        :return:
        """
        raise NotImplementedError()

    def get_min_position(self):
        """
        Gets the minimum duty cycle that will move the servo
        :return:
        """
        raise NotImplementedError()

    def set_max_position(self, max_duty):
        """
        Sets the maximum duty cycle that will move the servo
        :param max_duty:
        :return:
        """
        raise NotImplementedError()

    def get_max_position(self):
        """
        Gets the maximum duty cycle that will move the servo
        :return:
        """
        raise NotImplementedError()

    def set_position(self, position):
        """
        Sets the position of the servo
        :param position:
        :return:
        """
        raise NotImplementedError()

    def get_position(self):
        """
        Gets the position of the servo
        :return:
        """
        raise NotImplementedError()

    def step(self, d=1):
        """
        Steps by a given unit d
        :param d:
        :return:
        """
        raise NotImplementedError()
