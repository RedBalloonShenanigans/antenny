class ImuController(object):
    """Interface for a generic IMU controller for use in antenny."""
    def get_elevation(self):
        """
        Gets the reported elevation
        :return:
        """
        raise NotImplementedError()

    def get_azimuth(self):
        """
        Gets the reported azimuth
        :return:
        """
        raise NotImplementedError()

    def mode(self, mode):
        """
        Changes the device mode
        :param mode:
        :return:
        """
        raise NotImplementedError()

    def get_euler(self) -> tuple:
        """
        Return Euler angles in degrees: (heading, roll, pitch).
        :return:
        """
        raise NotImplementedError()

    def get_accelerometer_status(self):
        """
        Gets the calibration status of the accelerometer
        :return:
        """
        raise NotImplementedError()

    def get_magnetometer_status(self):
        """
        Gets the calibration status of the magnetometer
        :return:
        """
        raise NotImplementedError()

    def get_gyro_status(self):
        """
        Gets the calibration status of the gyroscope
        :return:
        """
        raise NotImplementedError()

    def prepare_calibration(self):
        """
        Prepares the IMU for calibration
        :return:
        """
        raise NotImplementedError()

    def is_calibrated(self):
        """
        Returns true if the imu is calibrated fully
        :return:
        """
        raise NotImplementedError()

    def set_accelerometer_calibration(self, calibration):
        """
        Sets the accelerometer calibration values to what is on the device
        :return:
        """
        raise NotImplementedError()

    def get_accelerometer_calibration(self):
        """
        Gets the current calibration registers
        :return:
        """
        raise NotImplementedError()

    def save_accelerometer_calibration(self):
        """
        Downloads the calibration registers from the device
        :return:
        """
        raise NotImplementedError()

    def set_magnetometer_calibration(self, calibration):
        """
        Sets the magnetometer calibration values to what is on the device
        :return:
        """
        raise NotImplementedError()

    def get_magnetometer_calibration(self):
        """
        Gets the current magnetometer calibration registers
        :return:
        """
        raise NotImplementedError()

    def save_magnetometer_calibration(self):
        """
        Downloads the calibration registers from the device
        :return:
        """
        raise NotImplementedError()

    def set_gyroscope_calibration(self, calibration):
        """
        Sets the gyroscope config calibration values to what is on the device
        :return:
        """
        raise NotImplementedError()

    def get_gyroscope_calibration(self):
        """
        Gets the current gyroscope calibration registers
        :return:
        """
        raise NotImplementedError()

    def save_gyroscope_calibration(self):
        """
        Downloads the calibration registers from the device
        :return:
        """
        raise NotImplementedError()

    def calibrate_accelerometer(self):
        """
        Manually calibrate the accelerometer
        :return:
        """
        raise NotImplementedError()

    def calibrate_magnetometer(self):
        """
        Manually calibrate the magnetometer
        :return:
        """
        raise NotImplementedError()

    def calibrate_gyroscope(self):
        """
        Manually calibrate the gyroscope
        :return:
        """
        raise NotImplementedError()

    def reset_calibration(self):
        """
        Resets the IMU's calibration
        :return:
        """
        raise NotImplementedError()

    def upload_calibration_profile(self) -> None:
        """
        Uploads the current calibration profile to the device
        :return:
        """
        raise NotImplementedError()
