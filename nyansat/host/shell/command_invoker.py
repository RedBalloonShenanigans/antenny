from nyansat.host.shell.nyan_pyboard import NyanPyboard
from nyansat.host.shell.errors import *


class CommandInvoker(NyanPyboard):
    """
    Invokes antenny API commands on the device
    """
    def __init__(self, con):
        super().__init__(con)
        self.tracking = False

#  Antenny Generic Functions

    def i2c_init(self, name: str, id_: int, scl: int, sda: int, freq=400000):
        """
        Initialize a new I2C channel
        :param name: the python interpreter variable to save the i2c channel as
        :param id_: a unique ID for the i2c channel (0 and -1 reserved for imu and motor
        :param scl: the SCL pin on the antenny board
        :param sda: the SDA pin on the antenny board
        :param freq: the I2C comm frequency
        :return: machine.I2C class
        """
        try:
            self.eval_string_expr("{} = api.i2c_init({}, {}, {}, freq={})".format(name, id_, scl, sda, freq))
            return name
        except PyboardError as e:
            raise AntennyException(e)

    def antenny_which_config(self):
        """
        Show the current config
        :return: config name
        """
        try:
            return self.eval_string_expr("api.antenny_which_config()")
        except PyboardError as e:
            raise AntennyException(e)

    def antenny_config_check(self):
        """
        Checks if the current config is valid
        :return:
        """
        try:
            return self.eval_string_expr("api.antenny_config_check()")
        except PyboardError as e:
            raise AntennyException(e)

    def antenny_config_get(self, key: str):
        """
        Get a key from the config
        :param key: the config key
        :return: the config value
        """
        try:
            return self.eval_string_expr("api.antenny_config_get(\"{}\")".format(key))
        except PyboardError as e:
            raise AntennyException(e)

    def antenny_config_set(self, key: str, val):
        """
        Set a key from the config
        :param key: the config key
        :param val: the config  value
        :return: bool
        """
        try:
            return self.eval_string_expr("api.antenny_config_set(\"{}\", \"{}\")".format(key, val))
        except PyboardError as e:
            raise AntennyException(e)

    def antenny_config_save(self, name: str = None, force: bool = False):
        """
        Save the current config
        :return: None
        """
        try:
            return self.eval_string_expr("api.antenny_config_save(name=\"{}\", force={})".format(name, force))
        except PyboardError as e:
            raise AntennyException(e)

    def antenny_config_load(self, name: str = None):
        """
        Load an existin config
        :param name:
        :return: None
        """
        try:
            return self.eval_string_expr("api.antenny_config_load(name=\"{}\")".format(name))
        except PyboardError as e:
            raise AntennyException(e)

    def antenny_config_print_values(self):
        """
        Print the current config values
        :return: None
        """
        try:
            return self.eval_string_expr("api.antenny_config_print_values()")
        except PyboardError as e:
            raise AntennyException(e)

    def antenny_config_load_default(self):
        """
        Reloads the config that was present on startup
        :return: None
        """
        try:
            return self.eval_string_expr("api.antenny_config_load_default()")
        except PyboardError as e:
            raise AntennyException(e)

    def antenny_config_make_default(self):
        """
        Will now load the current config on startup
        :return: None
        """
        try:
            return self.eval_string_expr("api.antenny_config_make_default()")
        except PyboardError as e:
            raise AntennyException(e)

    def antenny_config_help(self):
        """
        Gives you help and type info for each config key in json format.
        :return: help json dictionary
        """
        try:
            return self.eval_string_expr("api.antenny_config_help()")
        except PyboardError as e:
            raise AntennyException(e)

    def antenny_config_reset(self):
        """
        Resets the config back to "default"
        :return: None
        """
        try:
            return self.eval_string_expr("api.antenny_config_reset()")
        except PyboardError as e:
            raise AntennyException(e)

    def antenny_list_configs(self):
        """
        Lists all of the configs available on the device.
        :return:
        """
        try:
            return self.eval_string_expr("api.antenny_config_help()")
        except PyboardError as e:
            raise AntennyException(e)

    def antenny_is_safemode(self):
        """
        Checks if the device is in safemode
        :return:
        """
        try:
            return self.eval_string_expr("api.antenny_is_safemode()")
        except PyboardError as e:
            raise AntennyException(e)

    def antenny_init_components(self):
        """
        Initialize all antenny system components
        :return: None
        """
        try:
            return self.eval_string_expr("api.antenny_init_components()")
        except PyboardError as e:
            raise AntennyException(e)

    def antenny_save_all_configs_as_default(self, name: str = None):
        """
        Will save all current configs to be started on device startup
        :param name: A new name for the config, if not specified, will overwrite the current
        :return:
        """
        try:
            return self.eval_string_expr("api.antenny_save_all_configs_as_default(name=\"{}\")".format(name))
        except PyboardError as e:
            raise AntennyException(e)

    def antenny_start_calibrate_and_save_as_default(self, name: str = None):
        """
        Initializes all components, auto-calibrates the platform, then saves all as default
        Should be used after assembling a new antenny or after wiping your previous configs
        :param name:
        :return:
        """
        try:
            return self.eval_string_expr("api.antenny_start_calibrate_and_save_as_default(name=\"{}\")".format(name))
        except PyboardError as e:
            raise AntennyException(e)

#  PWM Controller Functions

    def pwm_controller_init(self, chain: str = None, freq: int = 333):
        """
        Initialize the antenny system PWM controller
        :param freq: pwm frequency
        :param chain: the name of a created i2c channel if chaining the bus
        :return: Pca9865Controller class
        """
        try:
            if chain is not None:
                chain = "\"{}\"".format(chain)
            return self.eval_string_expr("api.pwm_controller_init(chain={}, freq={})".format(chain, freq))
        except PyboardError as e:
            raise AntennyException(e)

    def pwm_controller_scan(self):
        """
        Scan the Motor I2C chain
        :return: List of I2C addresses
        """
        try:
            return self.eval_string_expr("api.pwm_controller_scan()")
        except PyboardError as e:
            raise AntennyException(e)

#  Servo Controller Functions

    def elevation_servo_init(self):
        """
        Initializes the elevation servo
        :return:
        """
        try:
            return self.eval_string_expr("api.elevation_servo_init()")
        except PyboardError as e:
            raise AntennyException(e)

    def elevation_servo_load(self, name: str = None):
        """
        Loads the servo's min and max duty cycle values from the config
        :param name:
        :return:
        """
        try:
            return self.eval_string_expr("api.elevation_servo_load(name=\"{}\")".format(name))
        except PyboardError as e:
            raise AntennyException(e)

    def elevation_servo_save(self, name: str = None, force: bool = False):
        """
        Saves the servo's min and max duty cycle values to the config
        :param force:
        :param name:
        :return:
        """
        try:
            return self.eval_string_expr("api.elevation_servo_save(name=\"{}\", force={})".format(name, force))
        except PyboardError as e:
            raise AntennyException(e)

    def azimuth_servo_init(self):
        """
        Initializes the azimuth servo
        :return:
        """
        try:
            return self.eval_string_expr("api.azimuth_servo_init()")
        except PyboardError as e:
            raise AntennyException(e)

    def azimuth_servo_load(self, name: str = None):
        """
        Loads the servo's min and max duty cycle values from the config
        :param name:
        :return:
        """
        try:
            return self.eval_string_expr("api.azimuth_servo_load(name=\"{}\")".format(name))
        except PyboardError as e:
            raise AntennyException(e)

    def azimuth_servo_save(self, name: str = None, force: bool = False):
        """
        Saves the servo's min and max duty cycle values to the config
        :param force:
        :param name:
        :return:
        """
        try:
            return self.eval_string_expr("api.azimuth_servo_save(name=\"{}\", force={})".format(name, force))
        except PyboardError as e:
            raise AntennyException(e)

    def servo_make_default(self):
        try:
            return self.eval_string_expr("api.servo_make_default()")
        except PyboardError as e:
            raise AntennyException(e)

#  Screen Functions

    def screen_init(self, chain: str = None):
        """
        Initialize the antenny I2C screen
        :param chain: provide your own I2C channel
        :return: Ssd13065ScreenController class
        """
        try:
            if chain is not None:
                chain = "\"{}\"".format(chain)
            return self.eval_string_expr("api.screen_init(chain={})".format(chain))
        except PyboardError as e:
            raise AntennyException(e)

    def screen_scan(self):
        """
        Scan the screen I2C chain
        :return: List of I2C addresses
        """
        try:
            return self.eval_string_expr("api.screen_scan()")
        except PyboardError as e:
            raise AntennyException(e)

#  GPS Functions

    def gps_init(self):
        """
        Initialize the antenny system GPS
        :return: BasicGPSController class
        """
        try:
            return self.eval_string_expr("api.gps_init()")
        except PyboardError as e:
            raise AntennyException(e)

#  Telemetry Functions

    def telemetry_init(self, port=31337):
        """
        Initialize the antenny system Telemetry sender
        :param port: Communcation UDP port
        :return: UDPTelemetrySender
        """
        try:
            return self.eval_string_expr("api.telemetry_init(port={})".format(port))
        except PyboardError as e:
            raise AntennyException(e)

#  IMU Functions

    def imu_init(self, chain: str = None):
        """
        Initialize the antenny system IMU
        :param chain: provide your own I2C channel
        :return: Bno055ImuController class
        """
        try:
            if chain is not None:
                chain = "\"{}\"".format(chain)
            return self.eval_string_expr("api.imu_init(chain={})".format(chain))
        except PyboardError as e:
            raise AntennyException(e)

    def imu_scan(self):
        """
        Scan the IMU I2C chain
        :return: List of I2C addresses
        """
        try:
            return self.eval_string_expr("api.imu_scan()")
        except PyboardError as e:
            raise AntennyException(e)

    def imu_is_calibrated(self) -> bool:
        """
        Checks if the IMU is calibrated
        :return: bool
        """
        try:
            return self.eval_string_expr("api.imu_is_calibrated()")
        except PyboardError as e:
            raise AntennyException(e)

    def imu_calibrate_accelerometer(self):
        """
        Starts the accelerometer calibration routine.
        :return: calibration results
        """
        try:
            return self.eval_string_expr("api.imu_calibrate_accelerometer()")
        except PyboardError as e:
            raise AntennyException(e)

    def imu_calibrate_magnetometer(self):
        """
        Starts the magnetometer calibration routine
        :return:
        """
        try:
            return self.eval_string_expr("api.imu_calibrate_magnetometer()")
        except PyboardError as e:
            raise AntennyException(e)

    def imu_calibrate_gyroscope(self):
        """
        Starts the gyroscope calibration routine
        :return:
        """
        try:
            return self.eval_string_expr("api.imu_calibrate_gyroscope()")
        except PyboardError as e:
            raise AntennyException(e)

    def imu_save(self, name: str = None, force: bool = False):
        """
        Saves the current calibration to the config
        :param force:
        :param name: A new config name, overwritten if not specified
        :return:
        """
        try:
            return self.eval_string_expr("api.imu_save(name=\"{}\", force={})".format(name, force))
        except PyboardError as e:
            raise AntennyException(e)

    def imu_load(self, name: str = None):
        """
        Reloads the calibration from the config
        :param name: A different config to be loaded if specified
        :return:
        """
        try:
            return self.eval_string_expr("api.imu_save(name=\"{}\")".format(name))
        except PyboardError as e:
            raise AntennyException(e)

    def imu_make_default(self):
        """
        Makes the current IMU calibration config default
        :return:
        """
        try:
            return self.eval_string_expr("api.imu_make_default()")
        except PyboardError as e:
            raise AntennyException(e)

    def imu_load_default(self):
        """
        Loads the default calibration config
        :return:
        """
        try:
            return self.eval_string_expr("api.imu_load_default()")
        except PyboardError as e:
            raise AntennyException(e)

    def imu_reset_calibration(self):
        """
        Resets the calibration on the IMU
        :return:
        """
        try:
            return self.eval_string_expr("api.imu_reset_calibration()")
        except PyboardError as e:
            raise AntennyException(e)

    #  Platform Functions

    def platform_init(self):
        """
        Initialize the antenny axis control system
        :return: AntennaController
        """
        try:
            return self.eval_string_expr("api.imu_reset_calibration()")
        except PyboardError as e:
            raise AntennyException(e)

    def platform_auto_calibrate_accelerometer(self):
        """
        Uses the servos to perform the accelerometer routine
        :return:
        """
        try:
            return self.eval_string_expr("api.platform_auto_calibrate_accelerometer()")
        except PyboardError as e:
            raise AntennyException(e)

    def platform_auto_calibrate_magnetometer(self):
        """
        Uses the servos to perform the magnetometer routine
        :return:
        """
        try:
            return self.eval_string_expr("api.platform_auto_calibrate_magnetometer()")
        except PyboardError as e:
            raise AntennyException(e)

    def platform_auto_calibrate_gyroscope(self):
        """
        Uses the servos to perform the gyroscope routine
        :return:
        """
        try:
            return self.eval_string_expr("api.platform_auto_calibrate_gyroscope()")
        except PyboardError as e:
            raise AntennyException(e)

    def platform_auto_calibrate_imu(self):
        """
        Uses the servos to automatically perform the IMU calibration
        :return:
        """
        try:
            return self.eval_string_expr("api.platform_auto_calibrate_imu()")
        except PyboardError as e:
            raise AntennyException(e)

    def platform_auto_calibrate_elevation_servo(self):
        """
        Uses the IMU to calibrate the elevation servo
        :return:
        """
        try:
            return self.eval_string_expr("api.platform_auto_calibrate_elevation_servo()")
        except PyboardError as e:
            raise AntennyException(e)

    def platform_auto_calibrate_azimuth_servo(self):
        """
        Uses the IMU to calibrate the azimuth servo
        :return:
        """
        try:
            return self.eval_string_expr("api.platform_auto_calibrate_azimuth_servo()")
        except PyboardError as e:
            raise AntennyException(e)

    def platform_auto_calibrate_servos(self):
        """
        Uses the IMU to automatically detect the min and max of the servos
        :return:
        """
        try:
            return self.eval_string_expr("api.platform_auto_calibrate_servos()")
        except PyboardError as e:
            raise AntennyException(e)

    def platform_auto_calibrate(self):
        """
        Uses the assembled platform construction to calibrate it's components
        :return:
        """
        try:
            return self.eval_string_expr("api.platform_auto_calibrate()")
        except PyboardError as e:
            raise AntennyException(e)

    def platform_set_azimuth(self, azimuth):
        """
        Sets the elevation of the antenna
        :param azimuth:
        :return:
        """
        try:
            return self.eval_string_expr("api.platform_set_azimuth({})".format(azimuth))
        except PyboardError as e:
            raise AntennyException(e)

    def platform_set_elevation(self, elevation):
        """
        Sets the elevation of the antenna
        :param elevation:
        :return:
        """
        try:
            return self.eval_string_expr("api.platform_set_elevation({})".format(elevation))
        except PyboardError as e:
            raise AntennyException(e)

    def platform_start(self):
        """
        Starts the movement of the platform
        :return:
        """
        try:
            return self.eval_string_expr("api.platform_start()")
        except PyboardError as e:
            raise AntennyException(e)

    def platform_stop(self):
        """
        Starts the movement of the platform
        :return:
        """
        try:
            return self.eval_string_expr("api.platform_stop()")
        except PyboardError as e:
            raise AntennyException(e)

    def platform_set_coordinates(self, azimuth, elevation):
        """
        Sets the coordinates of the antenna direction
        :param azimuth:
        :param elevation:
        :return:
        """
        try:
            return self.eval_string_expr("api.platform_set_coordinates({}, {})".format(azimuth, elevation))
        except PyboardError as e:
            raise AntennyException(e)

    def platform_orient(self):
        """
        Sets the coordinates of the antenna direction
        :param azimuth:
        :param elevation:
        :return:
        """
        try:
            return self.eval_string_expr("api.platform_orient()")
        except PyboardError as e:
            raise AntennyException(e)
