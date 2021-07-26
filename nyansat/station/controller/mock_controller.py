from controller.controller import AntennaController
from imu.mock_imu import MockImuController
from motor.mock_motor import MockServoController


class MockAntennaController(AntennaController):
    """
    Control the antenna motion device of the antenny.
    """

    def __init__(self, azimuth: MockServoController, elevation: MockServoController, imu: MockImuController):
        pass

    def set_azimuth(self, azimuth):
        pass

    def get_azimuth(self):
        return 0

    def set_elevation(self, elevation):
        pass

    def get_elevation(self):
        return 0

    def auto_calibrate_gyroscope(self):
        pass

    def auto_calibrate_accelerometer(self):
        pass

    def auto_calibrate_magnetometer(self):
        pass

    def get_elevation_min_max(self):
        return 0, 0

    def get_azimuth_min_max(self):
        return 0, 0
