from bno055 import *
import machine
from machine import Pin

import config

# Registers 0x55 through 0x6A are used for storing calibration data. Address
# reference can be found in BNO055 datasheet, section 4.3 "Register Description"
CALIBRATION_REGISTERS = {
    "acc_offset_x_lsb": 0x55,
    "acc_offset_x_msb": 0x56,
    "acc_offset_y_lsb": 0x57,
    "acc_offset_y_msb": 0x58,
    "acc_offset_z_lsb": 0x59,
    "acc_offset_z_msb": 0x5A,
    "mag_offset_x_lsb": 0x5B,
    "mag_offset_x_msb": 0x5C,
    "mag_offset_y_lsb": 0x5D,
    "mag_offset_y_msb": 0x5E,
    "mag_offset_z_lsb": 0x5F,
    "mag_offset_z_msb": 0x60,
    "gyr_offset_x_lsb": 0x61,
    "gyr_offset_x_msb": 0x62,
    "gyr_offset_y_lsb": 0x63,
    "gyr_offset_y_msb": 0x64,
    "gyr_offset_z_lsb": 0x65,
    "gyr_offset_z_msb": 0x66,
    "acc_radius_lsb": 0x67,
    "acc_radius_msb": 0x68,
    "mag_radius_lsb": 0x69,
    "mag_radius_msb": 0x6A
}

def calibration_status():
    """
    Returns the calibration values of the connected IMU in tuple form:
    (system, gyro, accelerometer, magnetometer)
    """

    try:
        i2c_bno055 = machine.I2C(1, scl=Pin(config.get('i2c_bno_scl'), Pin.OUT, Pin.PULL_UP), \
                                sda=Pin(config.get('i2c_bno_sda'), Pin.OUT, Pin.PULL_UP))
        bno = BNO055(i2c_bno055, sign=(0,0,0))
    except RuntimeError:
        return None

    return tuple(bno.cal_status())

def save_calibration():
    """
    Save data currently stored in IMU calibration registers to the config file.

    Calibration data consists of sensor offsets and sensor radius: switch into
    config mode, read/write, then switch out
    """
    try:
        i2c_bno055 = machine.I2C(1, scl=Pin(config.get('i2c_bno_scl'), Pin.OUT, Pin.PULL_UP), \
                                sda=Pin(config.get('i2c_bno_sda'), Pin.OUT, Pin.PULL_UP))
        bno = BNO055(i2c_bno055, sign=(0,0,0))
    except RuntimeError:
        return None


    old_mode = bno.mode(CONFIG_MODE)
    for register_name, register_address in CALIBRATION_REGISTERS.items():
        try:
            config.set(register_name, bno._read(register_address))
        except OSError:
            return None
    bno.mode(old_mode)
    return True

def upload_calibration():
    """
    Upload stored calibration values to the currently connected IMU.
    """
    try:
        i2c_bno055 = machine.I2C(1, scl=Pin(config.get('i2c_bno_scl'), Pin.OUT, Pin.PULL_UP), \
                                sda=Pin(config.get('i2c_bno_sda'), Pin.OUT, Pin.PULL_UP))
        bno = BNO055(i2c_bno055, sign=(0,0,0))
    except RuntimeError:
        return None

    old_mode = bno.mode(CONFIG_MODE)
    for register_name, register_address in CALIBRATION_REGISTERS.items():
        try:
            bno._write(register_address, config.get(register_name))
        except OSError:
            return None
    bno.mode(old_mode)
    return True
    