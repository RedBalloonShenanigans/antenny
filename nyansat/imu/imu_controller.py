
class ImuController():
    """Interface for a generic IMU controller for use in antenny."""

    def euler(self) -> tuple:
        """Return Euler angles in degrees: (heading, roll, pitch)."""
        return

    def is_calibrated(self) -> bool:
        """Return true if the IMU is currently calibrated."""
        return

    def calibration_status(self) -> dict:
        """Return a Dict[str, bool] mapping between names of constituent
        sensors and a boolean representing whether or not that sensor is
        currently calibrated.

        For example, a BNO055 orientation sensor has three constituent
        sensors: accelerometer, magnetometer, gyroscope, as well an "overall
        system" calibration level, so its calibration_status might look like
            {'magnetometer': 0,
             'gyroscope': 1,
             'accelerometer': 2,
             'system': 1}
        The strings used in this return value will be used in the shell's
        calibration routine.
        """
    
    def save_calibration_profile(self, filename: str) -> None:
        """Save the device's current calibration profile to the specified file,
        creating the file if it does not exist and overwriting it if it does.
        The format that the calibration profile is saved in should be readable
        by upload_calibration_profile.
        """
        return

    def upload_calibration_profile(self, filename: str) -> None:
        """Upload a calibration profile from the specified file to the device.
        The format that the calibration profile is saved in should be the same
        as that used by save_calibration_profile.
        """
        return