import webrepl
import machine
from api.api import AntennaController, AxisController, AntennyAPI
from antenny_threading import Queue
from config.config import Config
from exceptions import AntennyConfigException, AntennyIMUException, AntennyMotorException, AntennyGPSException, \
    AntennyTelemetryException, AntennyControllerException
from gps.gps_basic import BasicGPSController
from gps.mock_gps_controller import MockGPSController
from imu.imu_bno055 import Bno055ImuController
from imu.mock_imu import MockImuController
from motor.mock_motor import MockMotorController
from motor.motor_pca9685 import Pca9685Controller
from screen.mock_screen import MockScreenController
from screen.screen_ssd1306 import Ssd1306ScreenController
from sender.sender_udp import UDPTelemetrySender
from sender.mock_sender import MockTelemetrySender

def init_imu(config: Config, chain=None):
    if config.get("use_imu"):
        print("use_imu found in config: {}".format(config.get_name()))
        try:
            if chain is None:
                i2c_bno_scl = config.get("i2c_bno_scl")
                i2c_bno_sda = config.get("i2c_bno_sda")
                i2c_bno = machine.I2C(
                    -1,
                    scl=machine.Pin(i2c_bno_scl, machine.Pin.OUT, machine.Pin.PULL_DOWN),
                    sda=machine.Pin(i2c_bno_sda, machine.Pin.OUT, machine.Pin.PULL_DOWN),
                    freq=1000,
                )
            else:
                i2c_bno = chain
            imu = Bno055ImuController(
                i2c_bno,
                crystal=False,
                address=config.get("i2c_bno_address"),
                sign=(0, 0, 0)
            )
            print("IMU connected")
        except Exception as e:
            print("Failed to initialize IMU")
            raise AntennyIMUException("Failed to initialize IMU")
    else:
        imu = MockImuController()
        print("According to your config, ou do not have an IMU connected")
    return imu


def init_motor(config: Config, chain=None):
    if config.get("use_motor"):
        print("use_motor found in config: {}".format(config.get_name()))
        try:
            if chain is None:
                i2c_servo_scl = config.get("i2c_servo_scl")
                i2c_servo_sda = config.get("i2c_servo_sda")
                i2c_servo = machine.I2C(
                    0,
                    scl=machine.Pin(i2c_servo_scl, machine.Pin.OUT, machine.Pin.PULL_DOWN),
                    sda=machine.Pin(i2c_servo_sda, machine.Pin.OUT, machine.Pin.PULL_DOWN),
                )
            else:
                i2c_servo = chain
            motor = Pca9685Controller(
                i2c_servo,
                address=config.get("i2c_servo_address"),
                min_us=500,
                max_us=2500,
                degrees=180
            )
            print("Motor connected")
            safe_mode = False
        except Exception as e:
            print("Failed to initialize motor")
            raise AntennyMotorException("Failed to initialize motor")
    else:
        motor = MockMotorController()
        print("According to your config, you do not have a motor connected, entering Safe Mode")
        safe_mode = True
    return motor, safe_mode


def init_screen(config: Config, chain=None):
    if config.get("use_screen"):
        if chain is None:
            i2c_screen_scl = config.get("i2c_screen_scl")
            i2c_screen_sda = config.get("i2c_screen_sda")
            i2c_screen = machine.I2C(
                0,
                scl=machine.Pin(i2c_screen_scl, machine.Pin.OUT, machine.Pin.PULL_DOWN),
                sda=machine.Pin(i2c_screen_sda, machine.Pin.OUT, machine.Pin.PULL_DOWN),
            )
        else:
            i2c_screen = chain
        screen = Ssd1306ScreenController(
            i2c_screen,
        )
    else:
        screen = MockScreenController(Queue())
        print("According to your config, you do not have a screen connected")
    return screen


def init_gps(config):
    if config.get("use_gps"):
        print("use_gps found in config: {}".format(config.get_name()))
        try:
            gps = BasicGPSController(config.get("gps_uart_tx"), config.get("gps_uart_rx"))
        except Exception as e:
            print("Failed to initialize GPS")
            raise AntennyGPSException("Failed to initialize GPS")
    else:
        gps = MockGPSController()
        print("According to your config, you do not have a GPS connected")
    return gps


def init_telemetry(config, gps, imu, port=31337):
    if config.get("use_telemetry"):
        print("use_telemetry found in config")
        try:
            telemetry_sender = UDPTelemetrySender(port, gps, imu)
        except Exception as e:
            print("Failed to initialize telemetry sender")
            raise AntennyTelemetryException("Failed to initialize telemetry sender")
    else:
        telemetry_sender = MockTelemetrySender("localhost", 31337)
        print("According to your config, you do not have a telemetry enabled")
    return telemetry_sender


def init_controller(config: Config, imu, motor):
    try:
        print("Initializing AntennaController class")
        return AntennaController(
            AxisController(
                config.get("azimuth_servo_index"),
                imu,
                motor,
            ),
            AxisController(
                config.get("elevation_servo_index"),
                imu,
                motor,
            ),
        )
    except Exception as e:
        print("Failed to initialize AntennaController class")
        raise AntennyControllerException("Failed to initialize AntennaController class")


def init_api(config: Config):
    if not config.check():
        print("Config {} is not valid".format(config.get_name()))
        raise AntennyConfigException("Config {} is not valid".format(config.get_name()))

    imu = init_imu(config)
    motor, safe_mode = init_motor(config)
    screen = init_screen(config)
    gps = init_gps(config)
    telemetry_sender = init_telemetry(config, gps, imu)
    controller = init_controller(config, imu, motor)
    return AntennyAPI(
        controller,
        imu,
        config,
        screen,
        telemetry_sender,
        safe_mode,
    )


def start():
    config = Config()

    if config.get('use_webrepl'):
        webrepl.start()

    api = init_api(config)
    if config.get("enable_demo"):
        interrupt_pin = machine.Pin(15, machine.Pin.IN, machine.Pin.PULL_UP)
        interrupt_pin.irq(trigger=machine.Pin.IRQ_FALLING, handler=api.antenna.pin_motion_test)
    api.start()
    return api