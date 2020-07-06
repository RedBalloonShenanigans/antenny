
class ImuController():
    """Interface for a generic IMU controller for use in antenny."""

    def euler(self) -> tuple:
        """Return Euler angles in degrees: (heading, roll, pitch)."""
        return

    def is_calibrated(self) -> bool:
        """Return true if the IMU is currently calibrated."""
        return
    
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

    # TODO: Do private methods get listed in the interface? Probably not. Take
    # out later.

    def _get_calibration_profile(self) -> dict:
        """Return a dictionary with keys and values corresponding to
        device-specific current calibration parameters. The key-value format of
        the dictionary should be the same as that used in
        set_calibration_profile; data obtained from this method can be passed in
        to set_calibration_profile to be written back to the IMU at a later
        time.
        """
        return

    def _set_calibration_profile(self, calibration_profile: dict) -> None:
        """Update the IMU's calibration profile with the given dictionary, which
        represents a device-specific calibration profile. The format of this
        dictionary should be the same as that used in get_calibration_profile.
        """
        return