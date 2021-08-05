import math

from bno08x import BNO08X_I2C
from bno08x_base import BNO_REPORT_GEOMAGNETIC_ROTATION_VECTOR
from imu.imu import ImuController

_BNO08X_DEFAULT_ADDRESS = 0x4B


class Bno08xImuController(ImuController):
    """Controller for the Bosch BNO055 orientation sensor for antenny. This
    sensor actually provides more information than strictly needed, e.g.
    accelerometer, magnetometer, and temperature data.
    """
    def __init__(self, i2c: machine.I2C, address=_BNO08X_DEFAULT_ADDRESS, reset=None, debug=False):
        """Initialize the BNO055 from a given micropython machine.I2C connection
        object, I2C device address, and an orientation sign integer 3-tuple.
        """
        self.bno = BNO08X_I2C(i2c, reset=reset, address=address, debug=debug)
        self._is_calibrated = False
        self.accel_calibration: dict = {}
        self.magnet_calibration: dict = {}
        self.gyro_calibration: dict = {}
        self.bno.enable_feature(BNO_REPORT_GEOMAGNETIC_ROTATION_VECTOR)

    def get_elevation(self):
        """
        Gets the reported elevation
        :return:
        """
        return self.get_euler()[2]

    def get_azimuth(self):
        """
        Gets the reported azimuth
        :return:
        """
        return self.get_euler()[0]

    def mode(self, mode):
        """
        Changes the device mode
        :param mode:
        :return:
        """
        print("BNO08x impl does not currently support mode switching")
        pass

    def get_euler(self) -> tuple:
        """
        Return Euler angles in degrees: (heading, roll, pitch).
        :return:
        """
        x, y, z, w = self.bno.geomagnetic_quaternion
        norm = math.sqrt(w * w + x * x + y * y + z * z)
        x = x / norm
        y = y / norm
        z = z / norm
        w = w / norm
        roll = math.atan2(2 * y * w - 2 * x * z, 1 - (2 * y * y - 2 * z * z))
        pitch = math.atan2(2 * x * w - 2 * y * z, 1 - (2 * x * x - 2 * z * z))
        yaw = math.atan2(2 * w * z + 2 * x * y, 1 - (2 * y * y + 2 * z * z))
        return math.degrees(yaw), math.degrees(roll), math.degrees(pitch)

    def get_accelerometer_status(self):
        """
        Gets the calibration status of the accelerometer
        :return:
        """
        return self.bno.get_accelerometer_calibration_status()

    def get_magnetometer_status(self):
        """
        Gets the calibration status of the magnetometer
        :return:
        """
        return self.bno.get_magnetometer_calibration_status()

    def get_gyro_status(self):
        """
        Gets the calibration status of the gyroscope
        :return:
        """
        return self.bno.get_gyroscope_calibration_status()

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
        return self._is_calibrated

    def set_accelerometer_calibration(self, calibration):
        """
        Sets the accelerometer calibration values to what is on the device
        :return:
        """
        pass

    def get_accelerometer_calibration(self):
        """
        Gets the current calibration registers
        :return:
        """
        pass

    def save_accelerometer_calibration(self):
        """
        Downloads the calibration registers from the device
        :return:
        """
        self.bno.save_calibration_data()

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
        self.bno.save_calibration_data()

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
        self.bno.save_calibration_data()

    def calibrate_accelerometer(self):
        """
        Manually calibrate the accelerometer
        :return:
        """
        accel_level = self.get_accelerometer_status()
        prev_accel_level = accel_level
        print("Calibrating accelerometer")
        print("Rotate the IMU smoothly to different 3D orientations, waiting 2 seconds in between.")
        print("It helps to keep one edge rested on a table to keep the IMU steady.")
        print("This one takes a while but bear with it!")
        print("Configuration level: {}".format(accel_level))
        while accel_level < 3:
            accel_level = self.get_accelerometer_status()
            if accel_level != prev_accel_level:
                print("Configuration level: {}".format(accel_level))
                prev_accel_level = accel_level
        print("Acceleromete    calibration done!")
        return self.save_accelerometer_calibration()

    def calibrate_magnetometer(self):
        """
        Manually calibrate the magnetometer
        :return:
        """
        magnet_level = self.get_magnetometer_status()
        prev_magnet_level = magnet_level
        print("Calibrating magnetometer")
        print("Spin the IMU in 45 degree increments in a circle on the table!")
        print("Configuration level: {}".format(magnet_level))
        while magnet_level < 3:
            magnet_level = self.get_magnetometer_status()
            if magnet_level != prev_magnet_level:
                print("Configuration level: {}".format(magnet_level))
                prev_magnet_level = magnet_level
        print("Magnetometer calibration done!")
        return self.save_magnetometer_calibration()

    def calibrate_gyroscope(self):
        """
        Manually calibrate the gyroscope
        :return:
        """
        gyro_level = self.get_gyro_status()
        prev_gyro_level = gyro_level
        print("Calibrating gyroscope")
        print("Lay the IMU on a flat surface!")
        print("Configuration level: {}".format(gyro_level))
        while gyro_level < 3:
            gyro_level = self.get_gyro_status()
            if gyro_level != prev_gyro_level:
                print("Configuration level: {}".format(gyro_level))
                prev_gyro_level = gyro_level
        print("Gyr calibration done!")
        return self.save_gyroscope_calibration()

    def reset_calibration(self):
        """
        Resets the IMU's calibration
        :return:
        """
        self.bno.soft_reset()

    def upload_calibration_profile(self) -> None:
        """
        Uploads the current calibration profile to the device
        :return:
        """
        pass
