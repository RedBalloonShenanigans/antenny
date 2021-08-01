import time

from bno055 import BNO055, CONFIG_MODE, NDOF_MODE
import machine
from imu.imu import ImuController


class Bno055ImuController(ImuController):
    """Controller for the Bosch BNO055 orientation sensor for antenny. This
    sensor actually provides more information than strictly needed, e.g.
    accelerometer, magnetometer, and temperature data.
    """

    # Registers 0x55 through 0x6A are used for storing calibration data, which
    # includes sensor and offset data for each sensor. Address reference can be
    # found in BNO055 datasheet, section 4.3 "Register Description"
    ACCELEROMETER_CALIBRATION_REGISTERS = {
        "acc_offset_x_lsb": 0x55,
        "acc_offset_x_msb": 0x56,
        "acc_offset_y_lsb": 0x57,
        "acc_offset_y_msb": 0x58,
        "acc_offset_z_lsb": 0x59,
        "acc_offset_z_msb": 0x5A,
        "acc_radius_lsb": 0x67,
        "acc_radius_msb": 0x68,
    }
    MAGNETOMETER_CALIBRATION_REGISTERS = {
        "mag_offset_x_lsb": 0x5B,
        "mag_offset_x_msb": 0x5C,
        "mag_offset_y_lsb": 0x5D,
        "mag_offset_y_msb": 0x5E,
        "mag_offset_z_lsb": 0x5F,
        "mag_offset_z_msb": 0x60,
        "mag_radius_lsb": 0x69,
        "mag_radius_msb": 0x6A,
    }
    GYROSCOPE_CALIBRATION_REGISTERS = {
        "gyr_offset_x_lsb": 0x61,
        "gyr_offset_x_msb": 0x62,
        "gyr_offset_y_lsb": 0x63,
        "gyr_offset_y_msb": 0x64,
        "gyr_offset_z_lsb": 0x65,
        "gyr_offset_z_msb": 0x66,
    }

    def __init__(self, i2c: machine.I2C, address: int = 40, crystal=True, sign: tuple = (0, 0, 0)):
        """Initialize the BNO055 from a given micropython machine.I2C connection
        object, I2C device address, and an orientation sign integer 3-tuple.
        """
        self.bno = BNO055(i2c, address=address, crystal=crystal, sign=sign)
        self.accel_calibration: dict = {}
        self.magnet_calibration: dict = {}
        self.gyro_calibration:dict = {}

    def get_elevation(self):
        """
        Gets the reported elevation
        :return:
        """
        elevation = self.bno.euler()[2]
        new_elevation = self.bno.euler()[2]
        while new_elevation != elevation:
            elevation = self.bno.euler()[2]
            new_elevation = self.bno.euler()[2]
        return elevation % 90

    def get_azimuth(self):
        """
        Gets the reported azimuth
        :return:
        """
        azimuth = self.bno.euler()[0]
        new_azimuth = self.bno.euler()[0]
        while new_azimuth != azimuth:
            azimuth = self.bno.euler()[0]
            new_azimuth = self.bno.euler()[0]
        return azimuth % 360

    def mode(self, mode):
        """
        Changes the device mode
        :param mode:
        :return:
        """
        return self.bno.mode(mode)

    def get_euler(self):
        """
        Return Euler angles in degrees: (heading, roll, pitch).
        :return:
        """
        return self.bno.euler()

    def get_accelerometer_status(self):
        """
        Gets the calibration status of the accelerometer
        :return:
        """
        _, _, accel_level, _ = tuple(self.bno.cal_status())
        return accel_level

    def get_magnetometer_status(self):
        """
        Gets the calibration status of the magnetometer
        :return:
        """
        _, _, _, magnet_level = tuple(self.bno.cal_status())
        return magnet_level

    def get_gyro_status(self):
        """
        Gets the calibration status of the gyroscope
        :return:
        """
        _, gyro_level, _, _ = tuple(self.bno.cal_status())
        return gyro_level

    def prepare_calibration(self):
        """
        Prepares the IMU for calibration
        :return:
        """
        return self.mode(NDOF_MODE)

    def is_calibrated(self):
        """
        Returns true if the imu is calibrated fully
        :return:
        """
        return self.bno.calibrated()

    def set_accelerometer_calibration(self, calibration):
        """
        Sets the accelerometer calibration values to what is on the device
        :return:
        """
        self.accel_calibration = calibration

    def get_accelerometer_calibration(self):
        """
        Gets the current calibration registers
        :return:
        """
        return self.accel_calibration

    def download_accelerometer_calibration(self):
        """
        Downloads the calibration registers from the device
        :return:
        """
        self.accel_calibration = self.get_calibration_profile(self.ACCELEROMETER_CALIBRATION_REGISTERS)
        return self.accel_calibration

    def set_magnetometer_calibration(self, calibration):
        """
        Sets the magnetometer calibration values to what is on the device
        :return:
        """
        self.magnet_calibration = calibration

    def get_magnetometer_calibration(self):
        """
        Gets the current magnetometer calibration registers
        :return:
        """
        return self.magnet_calibration

    def download_magnetometer_calibration(self):
        """
        Downloads the calibration registers from the device
        :return:
        """
        self.magnet_calibration = self.get_calibration_profile(self.MAGNETOMETER_CALIBRATION_REGISTERS)
        return self.magnet_calibration

    def set_gyroscope_calibration(self, calibration):
        """
        Sets the gyroscope config calibration values to what is on the device
        :return:
        """
        self.gyro_calibration = calibration

    def get_gyroscope_calibration(self):
        """
        Gets the current gyroscope calibration registers
        :return:
        """
        return self.gyro_calibration

    def download_gyroscope_calibration(self):
        """
        Downloads the calibration registers from the device
        :return:
        """
        self.gyro_calibration = self.get_calibration_profile(self.GYROSCOPE_CALIBRATION_REGISTERS)
        return self.gyro_calibration

    def calibrate_accelerometer(self):
        """
        Manually calibrate the accelerometer
        :return:
        """
        old_mode = self.prepare_calibration()
        _, _, accel_level, _ = tuple(self.bno.cal_status())
        prev_accel_level = accel_level
        print("Calibrating accelerometer")
        print("Rotate the IMU smoothly to different 3D orientations, waiting 2 seconds in between.")
        print("It helps to keep one edge rested on a table to keep the IMU steady.")
        print("This one takes a while but bear with it!")
        print("Configuration level: {}".format(accel_level))
        while accel_level < 3:
            _, _, accel_level, _ = tuple(self.bno.cal_status())
            if accel_level != prev_accel_level:
                print("Configuration level: {}".format(accel_level))
                prev_accel_level = accel_level
        print("Acceleromete    calibration done!")
        self.bno.mode(old_mode)
        return self.download_accelerometer_calibration()

    def calibrate_magnetometer(self):
        """
        Manually calibrate the magnetometer
        :return:
        """
        old_mode = self.prepare_calibration()
        _, _, _, magnet_level = tuple(self.bno.cal_status())
        prev_magnet_level = magnet_level
        print("Calibrating magnetometer")
        print("Spin the IMU in 45 degree increments in a circle on the table!")
        print("Configuration level: {}".format(magnet_level))
        while magnet_level < 3:
            _, _, _, magnet_level = tuple(self.bno.cal_status())
            if magnet_level != prev_magnet_level:
                print("Configuration level: {}".format(magnet_level))
                prev_magnet_level = magnet_level
        print("Magnetometer calibration done!")
        self.bno.mode(old_mode)
        return self.download_magnetometer_calibration()

    def calibrate_gyroscope(self):
        """
        Manually calibrate the gyroscope
        :return:
        """
        old_mode = self.prepare_calibration()
        _, gyro_level, _, _ = tuple(self.bno.cal_status())
        prev_gyro_level = gyro_level
        print("Calibrating gyroscope")
        print("Lay the IMU on a flat surface!")
        print("Configuration level: {}".format(gyro_level))
        while gyro_level < 3:
            _, gyro_level, _, _ = tuple(self.bno.cal_status())
            if gyro_level != prev_gyro_level:
                print("Configuration level: {}".format(gyro_level))
                prev_gyro_level = gyro_level
        print("Gyr calibration done!")
        self.bno.mode(old_mode)
        return self.download_gyroscope_calibration()

    def reset_calibration(self):
        """
        Resets the IMU's calibration
        :return:
        """
        old_mode = self.bno.mode(NDOF_MODE)
        self.bno.reset()  # reset will put the system into NDOF mode at the end
        self.bno.mode(old_mode)

    def upload_calibration_profile(self) -> None:
        """
        Uploads the current calibration profile to the device
        :return:
        """
        self._set_calibration_profile(
            self.accel_calibration,
            self.ACCELEROMETER_CALIBRATION_REGISTERS
        )
        self._set_calibration_profile(
            self.gyro_calibration,
            self.GYROSCOPE_CALIBRATION_REGISTERS
        )
        self._set_calibration_profile(
            self.magnet_calibration,
            self.MAGNETOMETER_CALIBRATION_REGISTERS
        )

    def get_calibration_profile(self, registers):
        """
        Receives the calibration registers from the device
        :param registers:
        :return:
        """
        # In order to read or write to the calibration registers, we have to
        # switch into the BNO's config mode, read/write, then switch out
        previous_mode = self.bno.mode(CONFIG_MODE)
        result = {
            register_name: self.bno._read(register_address)
            for register_name, register_address in registers.items()
        }
        self.bno.mode(previous_mode)
        return result

    def _set_calibration_profile(self, register_results, registers) -> None:
        """
        Sets the calibration registers on the device
        :param register_results:
        :param registers:
        :return:
        """
        old_mode = self.bno.mode(CONFIG_MODE)
        for register_name, register_address in registers.items():
            self.bno._write(register_address, register_results[register_name])
        self.bno.mode(old_mode)
