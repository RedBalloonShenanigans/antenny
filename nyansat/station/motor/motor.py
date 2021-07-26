class PWMController(object):
    def _write(self, address, value):
        raise NotImplementedError()

    def _read(self, address):
        raise NotImplementedError()

    def reset(self):
        raise NotImplementedError()

    def freq(self, freq=None):
        raise NotImplementedError()

    def pwm(self, index, on=None, off=None):
        raise NotImplementedError()

    def duty(self, index, value=None, invert=False):
        raise NotImplementedError()


class ServoController(object):
    def set_min_duty(self, min_duty):
        raise NotImplementedError()

    def get_min_duty(self):
        raise NotImplementedError()

    def set_max_duty(self, max_duty):
        raise NotImplementedError()

    def get_max_duty(self):
        raise NotImplementedError()

    def set_position(self, position):
        raise NotImplementedError()

    def get_position(self):
        raise NotImplementedError()

    def step(self, d=1):
        raise NotImplementedError()
