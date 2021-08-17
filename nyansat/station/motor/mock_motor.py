from motor.motor import ServoController


class MockPWMController(object):
    """Mock interface for a pwm controller object"""
    def reset(self):
        """
        Resets the device
        :return:
        """
        pass

    def freq(self, freq=None):
        """
        Sets the output pwm frequency for all channels in Hz
        :param freq:
        :return:
        """
        pass

    def pwm(self, index, on=None, off=None):
        """
        Sets the pwm output for a given pwm pin
        :param index:
        :param on:
        :param off:
        :return:
        """
        pass

    def duty(self, index, value=None, invert=False):
        """
        Sets the duty cycle for a given pwm pin
        :param index:
        :param value:
        :param invert:
        :return:
        """
        pass


class MockServoController(ServoController):
    def set_min_position(self, min_us):
        """
        Sets the minimum duty cycle that will move the servo
        :param min_us:
        :return:
        """
        pass

    def get_min_position(self):
        """
        Gets the minimum duty cycle that will move the servo
        :return:
        """
        pass

    def set_max_position(self, max_us):
        """
        Sets the maximum duty cycle that will move the servo
        :param max_us:
        :return:
        """
        pass

    def get_max_position(self):
        """
        Gets the maximum duty cycle that will move the servo
        :return:
        """
        pass

    def set_position(self, position):
        """
        Sets the position of the servo
        :param position:
        :return:
        """
        pass

    def get_position(self):
        """
        Gets the position of the servo
        :return:
        """
        return 0

    def step(self, d=1):
        """
        Steps by a given unit d
        :param d:
        :return:
        """
        pass
