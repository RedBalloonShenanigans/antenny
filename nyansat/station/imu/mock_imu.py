from imu.imu import ImuController


class MockImuController(ImuController):
    """Interface for a generic IMU controller for use in antenny."""

    def mode(self, mode):
        raise NotImplementedError()

    def get_euler(self) -> tuple:
        """Return Euler angles in degrees: (heading, roll, pitch)."""
        return (0, 0, 0)

    def get_gyro_status(self):
        """
        Gets the calibration status of the gyroscope
        :return:
        """
        return 0

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

    def set_accelerometer_calibration(self):
        """
        Sets the accelerometer config calibration values to what is on the device
        :return:
        """
        return tuple()

    def set_magnetometer_calibration(self):
        """
        Sets the magnetometer config calibration values to what is on the device
        :return:
        """
        return tuple()

    def set_gyroscope_calibration(self):
        """
        Sets the gyroscope config calibration values to what is on the device
        :return:
        """
        return tuple()

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

    def reset_calibration(self):
        """
        Resets the IMU's calibration
        :return:
        """
        pass

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

    def save_calibration_profile(self) -> None:
        """
        Saves the imu calibration status to the internal config class
        :return:
        """
        pass

    def save_calibration_profile_as(self, name):
        """
        Save the current calibration as a new config profile
        :param name:
        :return:
        """
        pass

    def save_calibration_profile_as_default(self):
        """
        Make the current calibration profile present at imu init
        :return:
        """
        pass

    def reload_calibration_profile(self):
        """
        Reload the calibration profile from the saved config
        :return:
        """
        pass

    def load_default_calibration(self):
        """
        Load the calibration profile present on startup
        :return:
        """
        pass

    def load_calibration_profile(self, name):
        """
        Loads a new imu calibration status from a config
        :param name:
        :return:
        """
        pass

    def upload_calibration_profile(self) -> None:
        """Upload a calibration profile from the specified file to the device.
        The format that the calibration profile is saved in should be the same
        as that used by save_calibration_profile.
        """
        pass
