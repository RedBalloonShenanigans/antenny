from motor.motor import ServoController


class MockPWMController(object):
    """Mock interface for a pwm controller object"""
    def _write(self, address, value):
        pass

    def _read(self, address):
        return 0

    def reset(self):
        pass

    def freq(self, freq=None):
        pass

    def pwm(self, index, on=None, off=None):
        pass

    def duty(self, index, value=None, invert=False):
        return 0


class MockServoController(ServoController):
    def set_min_duty(self, min_duty):
        pass

    def get_min_duty(self):
        pass

    def set_max_duty(self, max_duty):
        pass

    def get_max_duty(self):
        pass

    def set_position(self, position):
        pass

    def get_position(self):
        return 0

    def step(self, d=1):
        pass
