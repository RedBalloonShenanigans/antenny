
from bno055 import BNO055, CONFIG_MODE
import machine
import ujson

from .imu_controller import ImuController

class Bno055Controller(ImuController):
    """Controller for the Bosch BNO055 orientation sensor for antenny. This
    sensor actually provides more information than strictly needed, e.g.
    accelerometer, magnetometer, and temperature data.
    """

    # Registers 0x55 through 0x6A are used for storing calibration data, which
    # includes sensor and offset data for each sensor. Address reference can be
    # found in BNO055 datasheet, section 4.3 "Register Description"
    CALIBRATION_REGISTERS = {
        "acc_offset_x_lsb": 0x55,
        "acc_offset_x_msb": 0x56,
        "acc_offset_y_lsb": 0x57,
        "acc_offset_y_msb": 0x58,
        "acc_offset_z_lsb": 0x59,
        "acc_offset_z_msb": 0x5A,
        "mag_offset_x_lsb": 0x5B,
        "mag_offset_x_msb": 0x5C,
        "mag_offset_y_lsb": 0x5D,
        "mag_offset_y_msb": 0x5E,
        "mag_offset_z_lsb": 0x5F,
        "mag_offset_z_msb": 0x60,
        "gyr_offset_x_lsb": 0x61,
        "gyr_offset_x_msb": 0x62,
        "gyr_offset_y_lsb": 0x63,
        "gyr_offset_y_msb": 0x64,
        "gyr_offset_z_lsb": 0x65,
        "gyr_offset_z_msb": 0x66,
        "acc_radius_lsb": 0x67,
        "acc_radius_msb": 0x68,
        "mag_radius_lsb": 0x69,
        "mag_radius_msb": 0x6A
    }

    def __init__(self, i2c: machine.I2C, sign: tuple = (0, 0, 0)):
        """Initialize the BNO055 from a given micropython machine.I2C connection
        object and an orientation sign integer 3-tuple.
        """
        self.bno = BNO055(i2c, sign=(0, 0, 0))

    def euler(self) -> tuple:
        """Return Euler angles in degrees: (heading, roll, pitch)."""
        return self.bno.euler()

    def is_calibrated(self) -> bool:
        """Return true if the BNO055 is currently calibrated, i.e. all
        four calibration levels are above zero.

        (The BNO055 stores four calibration levels: one each for the
        gyroscope, accelerometer, magnetometer, and the system as a whole. Each
        level can take on integer values from 0 through 3, with zero indicating
        completely uncalibrated, 1 and 2 indicating partially calbrated, and 3
        indicating fully calibrated.)
        """
        system_level, gyro_level, accel_level, magnet_level = self.bno.cal_status()
        return all((system_level, gyro_level, accel_level, magnet_level))

    def save_calibration_profile(self, filename: str) -> None:
        """Save the BNO's current calibration profile to the given file using
        a JSON representation, creating the file if it does not exist and over-
        writing it if it does.

        The format that this controller saves BNO calibration profile data in
        is as a str -> int dictionary, using as keys the descriptors found in
        the BNO055 manual section 4.3 "Register description". They are also the
        keys in CALIBRATION_REGISTERS.
        """
        calibration_profile = self._get_calibration_profile()
        with open(filename, 'w') as f:
            ujson.dump(calibration_profile, f)

    def upload_calibration_profile(self, filename: str) -> None:
        """Upload to the BNO a previously saved calibration profile, previously
        saved to the given file using a JSON representation. Assumes the same
        format as that used by save_calibration_profile.
        """
        with open(filename, 'r') as f:
            calibration_profile = ujson.load(f)
        self._set_calibration_profile(calibration_profile)

    def _get_calibration_profile(self) -> dict:
        # In order to read or write to the calibration registers, we have to
        # switch into the BNO's config mode, read/write, then switch out
        old_mode = self.bno.mode(CONFIG_MODE)
        profile = {register_name: self.bno._read(register_address)
                   for register_name, register_address in self.CALIBRATION_REGISTERS.items()}
        self.bno.mode(old_mode)
        return profile

    def _set_calibration_profile(self, calibration_profile: dict) -> None:
        old_mode = self.bno.mode(CONFIG_MODE)
        for register_name, register_address in self.CALIBRATION_REGISTERS:
            self.bno._write(register_address, calibration_profile[register_name])
        self.bno.mode(old_mode)
