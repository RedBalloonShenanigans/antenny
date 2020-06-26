# bno055_test.py Simple test program for MicroPython bno055 driver

# Copyright (c) Peter Hinch 2019
# Released under the MIT licence.

import machine
import time
import config as cfg
from bno055 import *

def main():
    # Pyboard hardware I2C
    print("Running main")

    i2c = machine.I2C(-1, scl=machine.Pin(cfg.get("i2c_bno_scl"),
        machine.Pin.OUT, machine.Pin.PULL_DOWN),
        sda=machine.Pin(cfg.get("i2c_bno_sda"), machine.Pin.OUT,
            machine.Pin.PULL_DOWN))

    imu = BNO055(i2c, sign=(0,0,0))
    bno = imu

    print()
    print('Initializing BNO055')
    bno.mode(0)
    time.sleep(0.1)
    bno.orient()
    time.sleep(0.1)
    try:
        bno.set_offsets()
    except:
        bno.pull_offsets()
        bno.set_offsets()
    time.sleep(0.1)
    bno.mode(0x0C)
    print('done initializing')

    calibrated = False
    while True:
        time.sleep(1)
        if not calibrated:
            calibrated = imu.calibrated()
            print('Calibration required: sys {} gyro {} accel {} mag {}'.format(*imu.cal_status()))
        print('Temperature {}°C'.format(imu.temperature()))
        print('Mag       x {:5.0f}    y {:5.0f}     z {:5.0f}'.format(*imu.mag()))
        print('Gyro      x {:5.0f}    y {:5.0f}     z {:5.0f}'.format(*imu.gyro()))
        print('Accel     x {:5.1f}    y {:5.1f}     z {:5.1f}'.format(*imu.accel()))
        print('Lin acc.  x {:5.1f}    y {:5.1f}     z {:5.1f}'.format(*imu.lin_acc()))
        print('Gravity   x {:5.1f}    y {:5.1f}     z {:5.1f}'.format(*imu.gravity()))
        print('Heading     {:4.0f} roll {:4.0f} pitch {:4.0f}'.format(*imu.euler()))

main()
