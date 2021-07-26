class AntennaController:
    """
    Control the antenna motion device of the antenny.
    """

    def set_azimuth(self, azimuth):
        raise NotImplementedError()

    def get_azimuth(self):
        raise NotImplementedError()

    def set_elevation(self, elevation):
        raise NotImplementedError()

    def get_elevation(self):
        raise NotImplementedError()

    def auto_calibrate_gyroscope(self):
        raise NotImplementedError

    def auto_calibrate_accelerometer(self):
        raise NotImplementedError()

    def auto_calibrate_magnetometer(self):
        raise NotImplementedError()

    def get_elevation_min_max(self):
        raise NotImplementedError()

    def get_azimuth_min_max(self):
        raise NotImplementedError()