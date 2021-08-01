class PlatformController:
    """
    Control the antenna motion device of the antenny.
    """
    def set_azimuth(self, azimuth):
        """
        Sets the platform to point at a specified azimuth
        :param azimuth:
        :return:
        """
        raise NotImplementedError()

    def get_azimuth(self):
        """
        Gets the current azimuth of the platform
        :return:
        """
        raise NotImplementedError()

    def set_elevation(self, elevation):
        """
        Sets the platform to point at a specified elevation
        :param elevation:
        :return:
        """
        raise NotImplementedError()

    def get_elevation(self):
        """
        Gets the current elevation of the platform
        :return:
        """
        raise NotImplementedError()

    def set_coordinates(self, azimuth, elevation):
        """
        Sets relative coordinates to point at
        :param azimuth:
        :param elevation:
        :return:
        """
        raise NotImplementedError()

    def auto_calibrate_accelerometer(self):
        """
        Uses the servos to calibrate the accelerometer
        :return:
        """
        raise NotImplementedError()

    def auto_calibrate_magnetometer(self):
        """
        Uses the servos to calibrate the magnetometer
        :return:
        """
        raise NotImplementedError()

    def auto_calibrate_gyroscope(self):
        """
        Uses the servos to calibrate the gyroscope
        :return:
        """
        raise NotImplementedError

    def auto_calibrate_elevation_servo(self, duty=25, d=.5):
        """
        Uses the IMU to calibrate the elevation servo
        :param duty:
        :param d:
        :return:
        """
        raise NotImplementedError()

    def auto_calibrate_azimuth_servo(self, duty=25, d=.5):
        """
        Uses the IMU to calibrate the azimuth servo
        :param duty:
        :param d:
        :return:
        """
        raise NotImplementedError()

    def orient(self):
        """
        Finds the current orientation. Saves and reports the servo azimuth deadzone.
        :return:
        """
        raise NotImplementedError()