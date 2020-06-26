# bno055_base.py Minimal MicroPython driver for Bosch BNO055 nine degree of
# freedom inertial measurement unit module with sensor fusion.

# The MIT License (MIT)
#
# Copyright (c) 2017 Radomir Dopieralski for Adafruit Industries.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# This is a port of the Adafruit CircuitPython driver to MicroPython, with
# modified/enhanced functionality.

# Original Author: Radomir Dopieralski
# Ported to MicroPython and extended by Peter Hinch
# This port copyright (c) Peter Hinch 2019

import utime as time
import ustruct
from micropython import const

_CHIP_ID = const(0xa0)

_CONFIG_MODE = const(0)
_NDOF_MODE = const(0x0c)

_POWER_NORMAL = const(0x00)
_POWER_LOW = const(0x01)
_POWER_SUSPEND = const(0x02)

_MODE_REGISTER = const(0x3d)
_PAGE_REGISTER = const(0x07)
_CALIBRATION_REGISTER = const(0x35)
_TRIGGER_REGISTER = const(0x3f)
_POWER_REGISTER = const(0x3e)
_ID_REGISTER = const(0x00)

class BNO055_BASE:

    def __init__(self, i2c, address=0x28, crystal=True, transpose=(0, 1, 2), sign=(0, 0, 0)):
        self._i2c = i2c
        self.address = address
        self.crystal = crystal
        self.mag = lambda : self.scaled_tuple(0x0e, 1/16)  # microteslas (x, y, z)
        self.accel = lambda : self.scaled_tuple(0x08, 1/100)  # m.s^-2
        self.lin_acc = lambda : self.scaled_tuple(0x28, 1/100)  # m.s^-2
        self.gravity = lambda : self.scaled_tuple(0x2e, 1/100)  # m.s^-2
        self.gyro = lambda : self.scaled_tuple(0x14, 1/16)  # deg.s^-1
        self.euler = lambda : self.scaled_tuple(0x1a, 1/16)  # degrees (heading, roll, pitch)
        self.quaternion = lambda : self.scaled_tuple(0x20, 1/(1<<14), bytearray(8), '<hhhh')  # (w, x, y, z)
        try:
            chip_id = self._read(_ID_REGISTER)
        except OSError:
            raise RuntimeError('No BNO055 chip detected.')
        if chip_id != _CHIP_ID:
            raise RuntimeError("bad chip id (%x != %x)" % (chip_id, _CHIP_ID))
        self.reset()

    def reset(self):
        self.mode(_CONFIG_MODE)
        try:
            self._write(_TRIGGER_REGISTER, 0x20)
        except OSError: # error due to the chip resetting
            pass
        # wait for the chip to reset (650 ms typ.)
        time.sleep_ms(700)
        self._write(_POWER_REGISTER, _POWER_NORMAL)
        self._write(_PAGE_REGISTER, 0x00)
        self._write(_TRIGGER_REGISTER, 0x80 if self.crystal else 0)
        time.sleep_ms(500 if self.crystal else 10)  # Crystal osc seems to take time to start.
        if hasattr(self, 'orient'):
            self.orient()  # Subclass
        self.mode(_NDOF_MODE)

    def scaled_tuple(self, addr, scale, buf=bytearray(6), fmt='<hhh'):
        return tuple(b*scale for b in ustruct.unpack(fmt, self._readn(buf, addr)))

    def temperature(self):
        t = self._read(0x34)  # Celcius signed (corrected from Adafruit)
        return t if t < 128 else t - 256

    # Return bytearray [sys, gyro, accel, mag] calibration data.
    def cal_status(self, s=bytearray(4)):
        cdata = self._read(_CALIBRATION_REGISTER)
        s[0] = (cdata >> 6) & 0x03  # sys
        s[1] = (cdata >> 4) & 0x03  # gyro
        s[2] = (cdata >> 2) & 0x03  # accel
        s[3] = cdata & 0x03  # mag
        return s

    def calibrated(self):
        s = self.cal_status()
        # https://learn.adafruit.com/adafruit-bno055-absolute-orientation-sensor/device-calibration
        return min(s[1:]) == 3 and s[0] > 0

    # read byte from register, return int
    def _read(self, memaddr, buf=bytearray(1)):  # memaddr = memory location within the I2C device
        self._i2c.readfrom_mem_into(self.address, memaddr, buf)
        return buf[0]

    # write byte to register
    def _write(self, memaddr, data, buf=bytearray(1)):
        buf[0] = data
        self._i2c.writeto_mem(self.address, memaddr, buf)

    # read n bytes, return buffer
    def _readn(self, buf, memaddr):  # memaddr = memory location within the I2C device
        self._i2c.readfrom_mem_into(self.address, memaddr, buf)
        return buf

    def mode(self, new_mode=None):
        old_mode = self._read(_MODE_REGISTER)
        if new_mode is not None:
            self._write(_MODE_REGISTER, _CONFIG_MODE)  # This is empirically necessary if the mode is to be changed
            time.sleep_ms(20)  # Datasheet table 3.6
            if new_mode != _CONFIG_MODE:
                self._write(_MODE_REGISTER, new_mode)
                time.sleep_ms(10)  # Table 3.6
        return old_mode

    def external_crystal(self):
        return bool(self._read(_TRIGGER_REGISTER) & 0x80)
