class ImuStatus(object):
    def to_string(self) -> str:
        raise NotImplementedError()


class ImuCalibrationStatus(object):
    def is_calibrated(self) -> bool:
        raise NotImplementedError()

    def __str__(self) -> str:
        """Return JSON string representation of a string -> int mapping
        between names of constituent sensors and integers representing
        levels of calibration for those sensors.

        For example, a BNO055 orientation sensor has three constituent
        sensors: accelerometer, magnetometer, gyroscope, as well an "overall
        system" calibration level, so its calibration_status might look like
            {'magnetometer': 0,
             'gyroscope': 1,
             'accelerometer': 2,
             'system': 1}
        The string used in this return value will be used in the shell's
        calibration routine.
        """
        raise NotImplementedError()

class ImuHeading(object):
    def __init__(
            self,
            elevation: float,
            azimuth: float,
    ):
        self.elevation = elevation
        self.azimuth = azimuth


class ImuController(object):
    """Interface for a generic IMU controller for use in antenny."""

    def euler(self) -> tuple:
        """Return Euler angles in degrees: (heading, roll, pitch)."""
        raise NotImplementedError()

    def heading(self) -> ImuHeading:
        raise NotImplementedError()

    def get_status(self) -> ImuStatus:
        raise NotImplementedError()

    def get_calibration_status(self) -> ImuCalibrationStatus:
        raise NotImplementedError()

    def save_calibration_profile(self, filename: str) -> None:
        """Save the device's current calibration profile to the specified file,
        creating the file if it does not exist and overwriting it if it does.
        The format that the calibration profile is saved in should be readable
        by upload_calibration_profile.
        """
        raise NotImplementedError()

    def upload_calibration_profile(self, filename: str) -> None:
        """Upload a calibration profile from the specified file to the device.
        The format that the calibration profile is saved in should be the same
        as that used by save_calibration_profile.
        """
        raise NotImplementedError()
