from controller.controller import PlatformController


class MockPlatformController(PlatformController):
    """
    Control the antenna motion device of the antenny.
    """
    def __init__(self, azimuth, elevation, imu):
        self.azimuth = azimuth
        self.elevation = elevation
        self.imu = imu

    def start(self):
        """
        Allows the antenna to move
        :return:
        """
        pass

    def stop(self):
        """
        Stops the antenna from moving
        :return:
        """
        pass

    def set_azimuth(self, azimuth):
        """
        Sets the platform to point at a specified azimuth
        :param azimuth:
        :return:
        """
        pass

    def get_azimuth(self):
        """
        Gets the current azimuth of the platform
        :return:
        """
        return 0

    def set_elevation(self, elevation):
        """
        Sets the platform to point at a specified elevation
        :param elevation:
        :return:
        """
        pass

    def get_elevation(self):
        """
        Gets the current elevation of the platform
        :return:
        """
        return 0

    def set_coordinates(self, azimuth, elevation):
        """
        Sets relative coordinates to point at
        :param azimuth:
        :param elevation:
        :return:
        """
        pass

    def auto_calibrate_accelerometer(self):
        """
        Uses the servos to calibrate the accelerometer
        :return:
        """
        pass

    def auto_calibrate_magnetometer(self):
        """
        Uses the servos to calibrate the magnetometer
        :return:
        """
        pass

    def auto_calibrate_gyroscope(self):
        """
        Uses the servos to calibrate the gyroscope
        :return:
        """
        pass

    def auto_calibrate_elevation_servo(self, duty=25, d=.5):
        """
        Uses the IMU to calibrate the elevation servo
        :param duty:
        :param d:
        :return:
        """
        pass

    def auto_calibrate_azimuth_servo(self, duty=25, d=.5):
        """
        Uses the IMU to calibrate the azimuth servo
        :param duty:
        :param d:
        :return:
        """
        pass

    def orient(self):
        """
        Finds the current orientation. Saves and reports the servo azimuth deadzone.
        :return:
        """
        pass
