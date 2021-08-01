from imu.imu import ImuController


class MockImuController(ImuController):
    """Interface for a generic IMU controller for use in antenny."""
    def get_elevation(self):
        """
        Gets the elevation of the imu in degrees
        :return:
        """
        return 0

    def get_azimuth(self):
        """
        Gets the azimuth of the imu in degrees
        :return:
        """
        return 0

    def mode(self, mode):
        """
        Changes the device mode
        :param mode:
        :return:
        """
        pass

    def get_euler(self) -> tuple:
        """Return Euler angles in degrees: (heading, roll, pitch)."""
        return 0, 0, 0

    def get_accelerometer_status(self):
        """
        Gets the calibration status of the accelerometer
        :return:
        """
        return 0

    def get_magnetometer_status(self):
        """
        Gets the calibration status of the magnetometer
        :return:
        """
        return 0

    def get_gyro_status(self):
        """
        Gets the calibration status of the gyroscope
        :return:
        """
        return 0

    def prepare_calibration(self):
        """
        Prepares the IMU for calibration
        :return:
        """
        pass

    def is_calibrated(self):
        """
        Returns true if the imu is calibrated fully
        :return:
        """
        return False

    def set_accelerometer_calibration(self, calibration):
        """
        Sets the accelerometer config calibration values to what is on the device
        :return:
        """
        pass

    def get_accelerometer_calibration(self):
        """
        Gets the current calibration registers
        :return:
        """
        pass

    def download_accelerometer_calibration(self):
        """
        Downloads the calibration registers from the device
        :return:
        """
        pass

    def set_magnetometer_calibration(self, calibration):
        """
        Sets the magnetometer config calibration values to what is on the device
        :return:
        """
        pass

    def get_magnetometer_calibration(self):
        """
        Gets the current magnetometer calibration registers
        :return:
        """
        pass

    def download_magnetometer_calibration(self):
        """
        Downloads the calibration registers from the device
        :return:
        """
        pass

    def set_gyroscope_calibration(self, calibration):
        """
        Sets the gyroscope config calibration values to what is on the device
        :return:
        """
        pass

    def get_gyroscope_calibration(self):
        """
        Gets the current gyroscope calibration registers
        :return:
        """
        pass

    def download_gyroscope_calibration(self):
        """
        Downloads the calibration registers from the device
        :return:
        """
        pass

    def calibrate_gyroscope(self):
        """
        Manually calibrate the gyroscope
        :return:
        """
        return tuple()

    def calibrate_accelerometer(self):
        """
        Manually calibrate the accelerometer
        :return:
        """
        return tuple()

    def calibrate_magnetometer(self):
        """
        Manually calibrate the magnetometer
        :return:
        """
        return tuple()

    def reset_calibration(self):
        """
        Resets the IMU's calibration
        :return:
        """
        pass

    def upload_calibration_profile(self) -> None:
        """Upload a calibration profile from the specified file to the device.
        The format that the calibration profile is saved in should be the same
        as that used by save_calibration_profile.
        """
        pass
