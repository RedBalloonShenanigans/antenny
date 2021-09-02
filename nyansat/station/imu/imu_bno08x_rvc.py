import time
import machine

from adafruit_bno08x_rvc import BNO08x_RVC
from imu.imu import ImuController
from config.config import Config

_BNO08X_DEFAULT_ADDRESS = 0x4B


class Bno08xUARTImuController(ImuController):
    """Controller for the Bosch BNO055 orientation sensor for antenny. This
    sensor actually provides more information than strictly needed, e.g.
    accelerometer, magnetometer, and temperature data.
    """
    def __init__(self, uart: machine.uart, reset: machine.Pin):
        """Initialize the BNO055 from a given micropython machine.I2C connection
        object, I2C device address, and an orientation sign integer 3-tuple.
        """
        self.bno = BNO08x_RVC(uart)
        self._is_calibrated = True
        self.reset = reset
        self.euler = None
        self.timer_id = Config('antenny').get('imu_timer_id')
        print("IMU-UARTD controller using timer hardware id: %d" % (self.timer_id))
        self.read_timer = machine.Timer(self.timer_id)

    def start(self):
        self.read_timer.init(period=10, mode=machine.Timer.PERIODIC, callback=self.__collect_euler)

    def stop(self):
        self.read_timer.deinit()

    def __collect_euler(self, timer):
        try:
            euler = self.bno.heading
            if euler is not None:
                self.euler = euler
            else:
                self.stop()
                self.start()
        except Exception as e:
            self.stop()
            self.start()
            print("The IMU has lost connection, re-starting")

    def get_elevation(self):
        """
        Gets the reported elevation
        :return:
        """
        elevation = abs(self.euler[1])
        new_elevation = abs(self.euler[1])
        while new_elevation != elevation:
            elevation = abs(self.euler[1])
            new_elevation = abs(self.euler[1])
        return elevation

    def get_azimuth(self):
        """
        Gets the reported azimuth
        :return:
        """
        azimuth = self.euler[0]
        new_azimuth = self.euler[0]
        while new_azimuth != azimuth:
            azimuth = self.euler[0]
            new_azimuth = self.euler[0]
        if azimuth < 0:
            azimuth = 360 + azimuth
        return azimuth

    def mode(self, mode):
        """
        Changes the device mode
        :param mode:
        :return:
        """
        print("BNO08x impl does not currently support mode switching")
        pass

    def get_euler(self) -> tuple:
        """
        Return Euler angles in degrees: (heading, roll, pitch).
        :return:
        """
        return self.euler

    def get_accelerometer_status(self):
        """
        Gets the calibration status of the accelerometer
        :return:
        """
        pass

    def get_magnetometer_status(self):
        """
        Gets the calibration status of the magnetometer
        :return:
        """
        pass

    def get_gyro_status(self):
        """
        Gets the calibration status of the gyroscope
        :return:
        """
        pass

    def prepare_calibration(self):
        """
        Prepares the IMU for calibration
        :return:
        """
        pass

    def is_calibrated(self):
        """
        Returns true if the imu is calibrated fully
        :return:
        """
        pass

    def set_accelerometer_calibration(self, calibration):
        """
        Sets the accelerometer calibration values to what is on the device
        :return:
        """
        pass

    def get_accelerometer_calibration(self):
        """
        Gets the current calibration registers
        :return:
        """
        pass

    def save_accelerometer_calibration(self):
        """
        Downloads the calibration registers from the device
        :return:
        """
        pass

    def set_magnetometer_calibration(self, calibration):
        """
        Sets the magnetometer calibration values to what is on the device
        :return:
        """
        raise NotImplementedError()

    def get_magnetometer_calibration(self):
        """
        Gets the current magnetometer calibration registers
        :return:
        """
        raise NotImplementedError()

    def save_magnetometer_calibration(self):
        """
        Downloads the calibration registers from the device
        :return:
        """
        pass

    def set_gyroscope_calibration(self, calibration):
        """
        Sets the gyroscope config calibration values to what is on the device
        :return:
        """
        raise NotImplementedError()

    def get_gyroscope_calibration(self):
        """
        Gets the current gyroscope calibration registers
        :return:
        """
        raise NotImplementedError()

    def save_gyroscope_calibration(self):
        """
        Downloads the calibration registers from the device
        :return:
        """
        pass

    def calibrate_accelerometer(self):
        """
        Manually calibrate the accelerometer
        :return:
        """
        pass
    def calibrate_magnetometer(self):
        """
        Manually calibrate the magnetometer
        :return:
        """
        pass

    def calibrate_gyroscope(self):
        """
        Manually calibrate the gyroscope
        :return:
        """
        pass

    def reset_calibration(self):
        """
        Resets the IMU's calibration
        :return:
        """
        self.reset.off()
        time.sleep(.5)
        self.reset.on()

    def upload_calibration_profile(self) -> None:
        """
        Uploads the current calibration profile to the device
        :return:
        """
        pass
