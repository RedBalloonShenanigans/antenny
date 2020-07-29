from imu.imu import ImuCalibrationStatus, ImuController, ImuHeading, ImuStatus


class MockImuController(ImuController):
    """Interface for a generic IMU controller for use in antenny."""

    def euler(self) -> tuple:
        """Return Euler angles in degrees: (heading, roll, pitch)."""
        return (
            0.,
            0.,
            0.,
        )

    def heading(self) -> ImuHeading:
        return ImuHeading(0., 0., )

    def get_status(self) -> ImuStatus:
        return ImuStatus()

    def get_calibration_status(self) -> ImuCalibrationStatus:
        return ImuCalibrationStatus()

    def save_calibration_profile(self, filename: str) -> None:
        """Save the device's current calibration profile to the specified file,
        creating the file if it does not exist and overwriting it if it does.
        The format that the calibration profile is saved in should be readable
        by upload_calibration_profile.
        """
        pass

    def upload_calibration_profile(self, filename: str) -> None:
        """Upload a calibration profile from the specified file to the device.
        The format that the calibration profile is saved in should be the same
        as that used by save_calibration_profile.
        """
        pass
