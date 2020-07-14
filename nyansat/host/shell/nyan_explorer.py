import ast
import json

from mp.mpfexp import MpFileExplorer, MpFileExplorerCaching
from mp.pyboard import PyboardError
from nyansat.host.shell.nyan_pyboard import NyanPyboard


class NyanExplorer(MpFileExplorer, NyanPyboard):
    """Wrapper for MpFileExplorer that includes the new NyanPyboard functionality."""

    EL_SERVO_INDEX = "elevation_servo_index"
    AZ_SERVO_INDEX = "azimuth_servo_index"

    def is_antenna_initialized(self):
        """Test if there is an AntKontrol object on the board"""
        try:
            self.exec_("isinstance(a, antenny.AntKontrol)")
            return True
        except PyboardError:
            return False

    def which_config(self):
        """Get the name of the currently used config file."""
        return self.eval_string_expr("a.cfg.current_file()")

    def config_get(self, key):
        """Get the value of an individual config parameter.

        Arguments:
        key -- name of config parameter.
        """
        command = "a.cfg.get(\"{}\")".format(key)
        return self.eval_string_expr(command)

    def config_set(self, key, val):
        """Set an individual parameter in the config file.

        Arguments:
        key -- name of config parameter. Tab complete to see choices.
        val -- value of paramter
        """
        if isinstance(val, int) or isinstance(val, float):
            self.exec_("a.cfg.set(\"%s\", %d)" % (key, val))
        elif isinstance(val, str):
            self.exec_("a.cfg.set(\"%s\", %s)" % (key, val))

    def config_get_default(self, key):
        """Get the default value of a config parameter.

        Arguments:
        key -- name of config parameter.
        """
        return self.eval_string_expr("a.cfg.get_default(\"{}\")".format(key))

    def config_new(self, name):
        """Create a new config file on the ESP32.

        Arguments:
        name -- name of new config file.
        """
        self.exec_("a.cfg.new(\"{}\")".format(name))

    def config_switch(self, name):
        """Switch to using a different config file.

        Arguments:
        name -- name of config file.
        """
        self.exec_("a.cfg.switch(\"{}\")".format(name))

    def imu_calibration_status(self):
        """Get IMU calibration status."""
        return json.loads(self.eval_string_expr("a.imu.get_calibration_status()"))

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
        return ast.literal_eval(self.eval_string_expr("a.antenna.motor_test({}, {})".format(index, pos)))

    def set_elevation_degree(self, el_angle):
        """Set the elevation angle.

        Arguments:
        el_angle -- desired elevation angle.
        """
        return self.eval_string_expr("a.antenna.set_elevation_degrees({})".format(el_angle))

    def set_azimuth_degree(self, az_angle):
        """Set the azimuth angle.

        Arguments:
        az_angle -- desired azimuth angle.
        """
        return self.eval_string_expr("a.antenna.set_azimuth_degrees({})".format(az_angle))

    def create_antkontrol(self):
        """Create an antkontrol object on the ESP32."""
        try:
            ret = self.exec_("import antenny")
            ret = self.exec_("a = antenny.AntKontrol()")
            self.antenna_initialized = True
            return ret.decode()
        except PyboardError:
            raise PyboardError("Could not create antkontrol object")
    
    def track(self, sat_name):
        """Track a satellite across the sky"""
        # TODO: Call the get_tle/parse_tle functions
        # TODO: Create a timer that goes off every 2 seconds, updating the elevation/azimuth.
        pass

    def cancel(self):
        """Cancel tracking mode"""
        # TODO: Cancel the timer created in track.
        pass


class NyanExplorerCaching(NyanExplorer, MpFileExplorerCaching):
    """Wrapper for MpFileExplorerCaching that includes the new NyanPyboard/NyanExplorer functionality."""
    pass
