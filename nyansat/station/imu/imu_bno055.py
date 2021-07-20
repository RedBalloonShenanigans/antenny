from bno055 import BNO055, CONFIG_MODE, NDOF_MODE, NDOF_FMC_OFF_MODE
import machine
import ujson

from config.config import Config
from exceptions import AntennyIMUException
from imu.imu import ImuController, ImuHeading, ImuStatus, ImuCalibrationStatus


class Bno055ImuStatus(ImuStatus):
    __slots__ = ['euler', 'temperature', 'magnetometer', 'gyroscope', 'accelerometer', 'linear_acccelerometer',
                 'gravity']

    def __init__(self, euler: tuple[float, float, float], temperature: float, magnetometer: tuple[float, float, float],
                 gyroscope: tuple[float, float, float], accelerometer: tuple[float, float, float],
                 linear_accelerometer: tuple[float, float, float], gravity: tuple[float, float, float]):
        self.euler = euler
        self.temperature = temperature
        self.magnetometer = magnetometer
        self.gyroscope = gyroscope
        self.accelerometer = accelerometer
        self.linear_accelerometer = linear_accelerometer
        self.gravity = gravity

    def to_string(self) -> str:
        lines = [
            "Temperature {}°C".format(self.temperature),
            "Mag        x {:5.0f}    y {:5.0f}     z {:5.0f}".format(*self.magnetometer),
            "Gyro       x {:5.0f}    y {:5.0f}     z {:5.0f}".format(*self.gyroscope),
            "Accel      x {:5.1f}    y {:5.1f}     z {:5.1f}".format(*self.accelerometer),
            "Lin accel  x {:5.1f}    y {:5.1f}     z {:5.1f}".format(*self.linear_accelerometer),
            "Gravity    x {:5.1f}    y {:5.1f}     z {:5.1f}".format(*self.gravity),
            "Heading    yaw {:4.0f} roll {:4.0f} pitch {:4.0f}".format(*self.euler),
        ]
        return "\n".join(lines)


class Bno055ImuCalibrationStatus(ImuCalibrationStatus):
    __slots__ = ['system', 'gyroscope', 'accelerometer', 'magnetometer']

    def __init__(self, system: bool, gyroscope: bool, accelerometer: bool, magnetometer: bool):
        self.system = system
        self.gyroscope = gyroscope
        self.accelerometer = accelerometer
        self.magnetometer = magnetometer

    def is_calibrated(self) -> bool:
        return self.system and self.gyroscope and self.accelerometer and self.magnetometer

    def __str__(self) -> str:
        """Return a JSON representation of str->int mapping between
        names of constituent sensors and integers representing levels of calibration
        for those sensors. For example, BNO055s will
        return {'magnetometer': <value>,
                'gyroscope': <value>,
                'accelerometer': <value>,
                'system': <value>}
        encoded in a string. The string used in this return value will be
        used in the shell's calibration routine.
        """
        calibration_levels = {
            'system': self.system,
            'gyroscope': self.gyroscope,
            'accelerometer': self.accelerometer,
            'magnetometer': self.magnetometer
        }
        return ujson.dumps(calibration_levels)


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
        self.config = Config("calibration")

    def euler(self) -> tuple:
        """Return Euler angles in degrees: (heading, roll, pitch)."""
        return self.bno.euler()

    def heading(self) -> ImuHeading:
        elevation, azimuth, _ = self.euler()
        return ImuHeading(elevation, azimuth)

    def get_status(self) -> Bno055ImuStatus:
        return Bno055ImuStatus(
            self.bno.euler(),
            self.bno.temperature(),
            self.bno.mag(),
            self.bno.gyro(),
            self.bno.accel(),
            self.bno.lin_acc(),
            self.bno.gravity(),
        )

    def is_calibrated(self):
        return self.bno.calibrated()

    def calibrate_accelerometer(self):
        old_mode = self.bno.mode(NDOF_MODE)
        _, _, accel_level, _ = tuple(self.bno.cal_status())
        prev_accel_level = accel_level
        print("Calibrating accelerometer")
        print("Rotate the IMU smoothly to different 3D orientations, waiting 2 seconds in between!")
        print("This one takes a while but bear with it!")
        print("Configuration level: {}".format(accel_level))
        while accel_level < 3:
            _, _, accel_level, _ = tuple(self.bno.cal_status())
            if accel_level != prev_accel_level:
                print("Configuration level: {}".format(accel_level))
                prev_accel_level = accel_level
        print("Accelerometer calibration done!")
        self.bno.mode(old_mode)
        accel_calibration = self._get_calibration_profile(self.ACCELEROMETER_CALIBRATION_REGISTERS)
        self.config.set("accelerometer", accel_calibration)
        return accel_calibration

    def calibrate_magnetometer(self):
        old_mode = self.bno.mode(NDOF_MODE)
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
        magnet_calibration = self._get_calibration_profile(self.MAGNETOMETER_CALIBRATION_REGISTERS)
        self.config.set("magnetometer", magnet_calibration)
        return magnet_calibration

    def calibrate_gyroscope(self):
        old_mode = self.bno.mode(NDOF_MODE)
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
        gyro_calibration = self._get_calibration_profile(self.GYROSCOPE_CALIBRATION_REGISTERS)
        self.config.set("gyroscope", gyro_calibration)
        return gyro_calibration

    def reset_calibration(self):
        old_mode = self.bno.mode(NDOF_MODE)
        self.bno.reset()  # reset will put the system into NDOF mode at the end
        self.bno.mode(old_mode)

    def _get_calibration_profile(self, registers):
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
        old_mode = self.bno.mode(CONFIG_MODE)
        for register_name, register_address in registers.items():
            self.bno._write(register_address, register_results[register_name])
        self.bno.mode(old_mode)

    def save_calibration_profile_as(self, name) -> None:
        """Save the BNO's current calibration profile to the given file using
        a JSON representation, creating the file if it does not exist and over-
        writing it if it does.

        The format that this controller saves BNO calibration profile data in
        is as a str -> int dictionary, using as keys the descriptors found in
        the BNO055 manual section 4.3 "Register description". They are also the
        keys in CALIBRATION_REGISTERS.
        """
        self.config.save_as(name)

    def save_calibration_profile(self):
        self.config.save()

    def load_calibration_profile(self, name):
        self.config.load(name)

    def reload_calibration_profile(self):
        self.load_calibration_profile(self.config._config_name)

    def save_calibration_as_default(self):
        self.config.save_as_default_config()

    def load_default_calibration(self):
        self.config.load_default_config()

    def upload_calibration_profile(self) -> None:
        """Upload to the BNO a previously saved calibration profile, previously
        saved to the given file using a JSON representation. Assumes the same
        format as that used by save_calibration_profile.
        """
        self._set_calibration_profile(
            self.config.get("accelerometer"),
            self.ACCELEROMETER_CALIBRATION_REGISTERS
        )
        self._set_calibration_profile(
            self.config.get("gyroscope"),
            self.GYROSCOPE_CALIBRATION_REGISTERS
        )
        self._set_calibration_profile(
            self.config.get("magnetometer"),
            self.MAGNETOMETER_CALIBRATION_REGISTERS
        )