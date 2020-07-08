from mp.mpfexp import MpFileExplorer, MpFileExplorerCaching
from mp.pyboard import PyboardError
from nyan_pyboard import NyanPyboard


class NyanExplorer(MpFileExplorer, NyanPyboard):
    """Wrapper for MpFileExplorer that includes the new NyanPyboard functionality."""

    EL_SERVO_INDEX = "elevation_servo_index"
    AZ_SERVO_INDEX = "azimuth_servo_index"

    def is_antenna_initialized(self):
        """Test if there is an AntKontrol object on the board"""
        try:
            self.exec_("isinstance(a, AntKontrol")
            return True
        except PyboardError:
            return False

    def which_config(self):
        """Get the name of the currently used config file."""
        return self.eval_string_expr("config.current_file()")

    def config_get(self, key):
        """Get the value of an individual config parameter.

        Arguments:
        key -- name of config parameter.
        """
        command = "config.get(\"{}\")".format(key)
        return self.eval_string_expr(command)

    def config_set(self, key, val):
        """Set an individual parameter in the config file.

        Arguments:
        key -- name of config parameter. Tab complete to see choices.
        val -- value of paramter
        """
        if isinstance(val, int) or isinstance(val, float):
            self.exec_("config.set(\"%s\", %d)" % (key, val))
        elif isinstance(val, str):
            self.exec_("config.set(\"%s\", %s)" % (key, val))

    def config_get_default(self, key):
        """Get the default value of a config parameter.

        Arguments:
        key -- name of config parameter.
        """
        return self.eval_string_expr("config.get_default(\"{}\")".format(key))

    def config_new(self, name):
        """Create a new config file on the ESP32.

        Arguments:
        name -- name of new config file.
        """
        self.exec_("config.new(\"{}\")".format(name))

    def config_switch(self, name):
        """Switch to using a different config file.

        Arguments:
        name -- name of config file.
        """
        self.exec_("config.switch(\"{}\")".format(name))

    def imu_calibration_status(self):
        """Get IMU calibration status."""
        return self.eval_string_expr("a.imu.calibration_status()")

    def imu_save_calibration_profile(self):
        """Save the current IMU calibration as 'calibration.json'."""
        return self.eval_string_expr("a.imu.save_calibration_profile('calibration.json')")

    def imu_upload_calibration_profile(self):
        """Upload 'calibration.json' to the IMU."""
        return self.eval_string_expr("a.imu.upload_calibration_profile('calibration.json')")

    def motor_test(self, index, pos):
        """Run a motor accuracy test, for testing the disparity between the motor and IMU.

        Arguments:
        index -- index of motor on the PWM driver.
        pos -- desired angle.
        """
        return self.eval_string_expr("a.motor_test({}, {})".format(index, pos))

    def set_elevation_degree(self, el_angle):
        """Set the elevation angle.

        Arguments:
        el_angle -- desired elevation angle.
        """
        return self.eval_string_expr("a.set_el_deg({})".format(el_angle))

    def set_azimuth_degree(self, az_angle):
        """Set the azimuth angle.

        Arguments:
        az_angle -- desired azimuth angle.
        """
        return self.eval_string_expr("a.set_az_deg({})".format(az_angle))

    def create_antkontrol(self):
        """Create an antkontrol object on the ESP32."""
        try:
            ret = self.exec_("import antenny")
            ret = self.exec_("a = antenny.AntKontrol()")
            self.antenna_initialized = True
            return ret.decode()
        except PyboardError:
            raise PyboardError("Could not create antkontrol object")


class NyanExplorerCaching(NyanExplorer, MpFileExplorerCaching):
    """Wrapper for MpFileExplorerCaching that includes the new NyanPyboard/NyanExplorer functionality."""
    pass

