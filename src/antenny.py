import sys
import machine
from machine import Pin
import logging
import time
import utime
import uasyncio
import ssd1306
import _thread
from bno055 import *
from servtor import ServTor
from micropyGPS import MicropyGPS
import socket

import config as cfg

EL_SERVO_INDEX = cfg.get("elevation_servo_index")
AZ_SERVO_INDEX = cfg.get("azimuth_servo_index")

# Registers 0x55 through 0x6A are used for storing calibration data. Address
# reference can be found in BNO055 datasheet, section 4.3 "Register Description"
IMU_CALIBRATION_REGISTERS = {
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

class AntGPS:
    def __init__(self):
        self._gps_uart = machine.UART(1, 9600)
        self._gps_uart.init(tx=cfg.get("gps_uart_tx"),
                rx=cfg.get("gps_uart_rx"))
        self._gps = MicropyGPS()
        self._loop = uasyncio.get_event_loop()

        self.valid = None
        self.latitude = None
        self.longitude = None
        self.altitude = None
        self.timestamp = None
        self.speed = None
        self.course = None

    def start(self):
        self.update_gps()

    def _update_gps(self):
        g_sentence = self._gps_uart.readline()
        while g_sentence:
            logging.debug(g_sentence)
            g_sentence = g_sentence.decode('ascii')
            logging.debug(g_sentence)
            for l in g_sentence:
                self._gps.update(l)
            self.valid = self._gps.valid
            self.latitude = self._gps.latitude
            self.longitude = self._gps.longitude
            self.altitude = self._gps.altitude
            self.timestamp = self._gps.timestamp
            self.speed = self._gps.speed
            self.course = self._gps.course

            g_sentence = self._gps_uart.readline()

    def update_gps(self):
        while True:
            try:
                self._update_gps()
            except Exception as e:
                logging.info(e)

            time.sleep(1)



class TelemetrySenderUDP:

    def __init__(self):
        self.socket_lock = _thread.allocate_lock()
        self.cur_telem = {}
        self.cur_telem['euler'] = ()
        self.cur_telem['gps'] = ()
        self.cur_telem['last_time'] = 0
        self.dstaddr = cfg.get("telem_destaddr")
        self.dstport = cfg.get("telem_destport")
        self.mcast_send_socket = None
        self.initSocket()

    def initSocket(self):
        self.mcast_send_socket = socket.socket(socket.AF_INET,
                socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        #self.mcast_send_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

    def set_destination(self, multicast_ipaddr):
        self.dstaddr = multicast_ipaddr
        self.initSocket()

    def updateTelem(self, dict_vals):
        for key, val in dict_vals.items():
            with self.socket_lock:
                self.cur_telem[key] = val

    def sendTelemTick(self):
        with self.socket_lock:
            tick_str = ujson.dumps(self.cur_telem)
            self.mcast_send_socket.sendto(tick_str, (self.dstaddr, self.dstport))


class AntKontrol:
    #Antenna Kontrol has
    #BNO055 absolute orientation sensor
    #16 channel pwm breakout servo controller
    #GPS antenna - TODO

    #MAX_AZ_DELTA = 20 #per second, max azimuth degrees
    #MAX_EL_DELTA = 20 #per second, max elevation degrees

    def __init__(self):
        self.telem = TelemetrySenderUDP()

        self._az_direction = -1
        self._el_direction = 1

        # locks
        self.bno_lock = _thread.allocate_lock()
        self._loop = uasyncio.get_event_loop()
        self._gps = AntGPS()
        self._gps_thread = _thread.start_new_thread(self._gps.start, ())

        self._i2c_servo_mux = machine.I2C(0, scl=Pin(cfg.get("i2c_servo_scl"),
            Pin.OUT, Pin.PULL_DOWN), sda=Pin(cfg.get("i2c_servo_sda"), Pin.OUT,
                Pin.PULL_DOWN))

        self._i2c_bno055 = machine.I2C(1,
                scl=machine.Pin(cfg.get("i2c_bno_scl"), Pin.OUT,
                    Pin.PULL_DOWN), sda=machine.Pin(cfg.get("i2c_bno_sda"),
                        Pin.OUT, Pin.PULL_DOWN))
        # on [60] ssd1306
        self._i2c_screen = machine.I2C(-1,
                scl=machine.Pin(cfg.get("i2c_screen_scl"), Pin.OUT,
                    Pin.PULL_DOWN), sda=machine.Pin(cfg.get("i2c_screen_sda"),
                        Pin.OUT, Pin.PULL_DOWN))
        self._pinmode = False
        # Sync time
        # Find latitude and longitude
        self._servo_mux = ServTor(self._i2c_servo_mux, min_us=500, max_us=2500, degrees=180)
        self._screen = ssd1306.SSD1306_I2C(128, 32, self._i2c_screen)

        self._cur_azimuth_degree = None
        self._cur_elevation_degree = None
        self._target_azimuth_degree = None
        self._target_elevation_degree = None

        self._bno = BNO055(self._i2c_bno055, sign=(0,0,0))

        self._euler = None
        self._pinned_euler = None
        self._pinned_servo_pos = None
        time.sleep(5)
        self.conf_bno()
        time.sleep(1)

        self._servo_mux.position(EL_SERVO_INDEX, 90)
        time.sleep(0.1)
        self._servo_mux.position(AZ_SERVO_INDEX, 90)
        time.sleep(0.1)

        cur_orientation = self._bno.euler()
        self._el_target = self._el_last = cur_orientation[EL_SERVO_INDEX]
        self._az_target = self._az_last = cur_orientation[AZ_SERVO_INDEX]
        self._el_last_raw = 90.0
        self._az_last_raw = 90.0
        self.do_euler_calib()

        self._el_moving = False
        self._az_moving = False

        self._el_max_rate = cfg.get("elevation_max_rate")
        self._az_max_rate = cfg.get("azimuth_max_rate")

        self._orientation_thread = _thread.start_new_thread(self.update_orientation, ())
        logging.info("starting screen thread")
        self._run_telem_thread = True
        self._telem_thread = _thread.start_new_thread(self.send_telem, ())
        self._screen_thread = _thread.start_new_thread(self.display_status, ())
        self._move_thread = _thread.start_new_thread(self.move_loop, ())

    def save_ant_calib(self):
        calib = [self._servo_mux.degrees[0], self._servo_mux.degrees[0], \
                 self._el_offset, self._az_offset,]
        with open('.ant_calib', 'w') as cf:
            ujson.dump(calib, cf)

    def load_ant_calib(self):
        with open('.ant_calib', 'r') as cf:
            calib = ujson.load(cf)
            self._servo_mux.degrees[0] = calib[0]
            self._servo_mux.degrees[1] = calib[1]
            self._el_offset = calib[2]
            self._az_offset = calib[3]

    def conf_bno(self):
        with self.bno_lock:
            logging.info('Initializing BNO055')

            self._bno.mode(0)
            time.sleep(0.1)
            self._bno.orient()
            time.sleep(0.1)
            self._bno.set_offsets()
            time.sleep(0.1)
            self._bno.mode(0x0C)
            logging.info('done initializing')

    def update_az_el(self, az_degree, el_degree):
        self._target_azimuth_degree = az_degree
        self._target_elevation_degree = el_degree


    def _measure_az(self, min_angle, max_angle):
        with self.bno_lock:
            self._servo_mux.position(AZ_SERVO_INDEX, min_angle)
            time.sleep(0.3)
            self._euler = self._bno.euler()
            a1 = self._euler[1]
            time.sleep(1)
            self._servo_mux.position(AZ_SERVO_INDEX, max_angle)
            time.sleep(0.3)
            self._euler = self._bno.euler()
            a2 = self._euler[1]
            time.sleep(1)
            return (a1, a2)

    def get_euler(self):
        with self.bno_lock:
            self._euler = self._bno.euler()

    def test_az_axis(self):
        #measure servo pwm parameters
        self.c_az=90
        time.sleep(1)
        self.get_euler()
        self.c_az=80
        time.sleep(2)
        self.get_euler()
        a1 = self._euler[1]
        self.c_az=100
        time.sleep(2)
        self.get_euler()
        a2 = self._euler[1]

        #should be 20 degrees. what did we get
        observed_angle = abs(a1) + a2
        angle_factor = observed_angle/20.0
        self._servo_mux.degrees[1] *= angle_factor
        print("Observed angle: {} factor: {}".format(observed_angle, angle_factor))

    def test_el_axis(self):
        #measure servo pwm parameters
        self.c_az=90.0
        time.sleep(1)
        self._servo_mux.position(0, 90)
        time.sleep(1)
        self.get_euler()
        self._servo_mux.position(0, 70)
        time.sleep(2)
        self.get_euler()
        a1 = self._euler[0]
        self._servo_mux.position(0, 110)
        time.sleep(2)
        self.get_euler()
        a2 = self._euler[0]

        #should be 20 degrees. what did we get
        observed_angle = a1 - a2
        angle_factor = observed_angle/4.0
        self._servo_mux.degrees[0] *= angle_factor
        print("Observed angle: {} factor: {}".format(observed_angle, angle_factor))

    #I got az and el backwards. use for now, change all later
    def auto_zero_az(self):
        #automatically find az offset
        self._servo_mux.position(AZ_SERVO_INDEX, 90)
        self._servo_mux.position(EL_SERVO_INDEX, 90)
        time.sleep(1)
        a1 = 60
        a2 = 120
        p_center = 100
        while abs(p_center) > 0.1:
            p1, p2 = self._measure_az(a1, a2)
            p_center = (p1+p2)/2
            print("a1: {},{} a2: {},{} a-center: {}".format(a1, p1, a2, p2, p_center))
            if p_center > 0:
                a2 = a2 - abs(p_center)
            else:
                a1 = a1 + abs(p_center)

        min_y = 100
        min_angle = None
        cur_angle = avg_angle = (a1+a2)/2-1.5
        while cur_angle < avg_angle+1.5:
            self._servo_mux.position(AZ_SERVO_INDEX, cur_angle)
            time.sleep(0.2)
            self._euler = self._bno.euler()
            cur_y = abs(self._euler[1])
            if cur_y < min_y:
                min_y = cur_y
                min_angle = cur_angle
            cur_angle += 0.1

        time.sleep(1)
        a_center = min_angle
        self._servo_mux.position(AZ_SERVO_INDEX, a_center)
        print ("a-center: {}".format(a_center))
        self._euler = self._bno.euler()
        self._az_offset = a_center-90.0

    def auto_calibration(self):
        # read from BNO055 sensor, move antenna
        # soft home, etc
        self._servo_mux.position(AZ_SERVO_INDEX, 90)
        self._servo_mux.position(EL_SERVO_INDEX, 90)
        time.sleep(1)

        self._servo_mux.position(EL_SERVO_INDEX, 180)
        time.sleep(1)
        self._servo_mux.position(EL_SERVO_INDEX, 0)
        time.sleep(1)
        self._servo_mux.position(EL_SERVO_INDEX, 180)
        time.sleep(1)
        self._servo_mux.position(EL_SERVO_INDEX, 0)
        time.sleep(1)

        self._servo_mux.position(AZ_SERVO_INDEX, 180)
        time.sleep(1)
        self._servo_mux.position(AZ_SERVO_INDEX, 0)
        time.sleep(1)
        self._servo_mux.position(AZ_SERVO_INDEX, 180)
        time.sleep(1)
        self._servo_mux.position(AZ_SERVO_INDEX, 0)
        time.sleep(1)

        self._servo_mux.position(AZ_SERVO_INDEX, 90)
        self._servo_mux.position(EL_SERVO_INDEX, 90)
        time.sleep(1)


        self._servo_mux.position(EL_SERVO_INDEX, 0)
        self._euler = self._bno.euler()
        x1 = self._euler[0]
        time.sleep(1)
        self._servo_mux.position(EL_SERVO_INDEX, 180)
        self._euler = self._bno.euler()
        x2 = self._euler[0]
        time.sleep(1)
        self._servo_mux.position(AZ_SERVO_INDEX, 0)
        self._euler = self._bno.euler()
        y1 = self._euler[1]
        time.sleep(1)
        self._servo_mux.position(AZ_SERVO_INDEX, 180)
        self._euler = self._bno.euler()
        y2 = self._euler[1]

        return ("[{}] - [{}] [{}] - [{}]".format(x1,x2,y1,y2))


    def calibrate_elevation(self):
        #while not self._bno.calibrated():
        #    self._bno.set_offsets()
        #    logging.info("BNO055 not calibrated. Retrying in 10")
        #    time.sleep(10)

        AZ_SOFT_MIN = 30.0
        AZ_SOFT_MAX = 160.0
        min_error = 1000

        for i in range(AZ_SOFT_MIN*10, AZ_SOFT_MAX*10, 1):
            self._servo_mux.position(AZ_SERVO_INDEX, float(i)/10)
            y_angle = self._bno.euler()[1]
            err_val = i - y_angle
            print("{setv} - {y_angle} - {err_val}".format(setv=i,\
                                                          y_angle=y_angle,\
                                                          err_val=err_val))
            time.sleep(0.2)

    def touch(self):
        #self._status_bno = self._bno.calibrated()
        #self._euler = self._bno.euler()
        self._status_gps = self._gps.valid
        self._gps_position = [self._gps.latitude, self._gps.longitude]
        self._elevation_servo_position = self._servo_mux.position(EL_SERVO_INDEX)
        self._azimuth_servo_position = self._servo_mux.position(AZ_SERVO_INDEX)

    def updateTelem(self):
        self.telem.updateTelem({'euler': self._euler})
        self.telem.updateTelem({'last_time': utime.ticks_ms()})
        self.telem.updateTelem({'gps_long': self._gps.longitude})
        self.telem.updateTelem({'gps_lat': self._gps.latitude})
        self.telem.updateTelem({'gps_valid': self._gps.valid})
        self.telem.updateTelem({'gps_altitude': self._gps.altitude})
        self.telem.updateTelem({'gps_speed': self._gps.speed})
        self.telem.updateTelem({'gps_course': self._gps.course})

    def display_status(self):
        while True:
            try:
                self.touch()
                self._screen.fill(0)

                self._screen.text("{:08.3f}".format(self._euler[0]), 0, 0)
                self._screen.text("{:08.3f}".format(self._euler[1]), 0, 8)
                self._screen.text("{:08.3f}".format(self._euler[2]), 0, 16)
                #self._screen.text("{:08.3f}".format(self._gps_position[0]), 64, 0)
                #self._screen.text("{:08.3f}".format(self._gps_position[1]), 64, 8)
                self._screen.show()
            except Exception as e:
                logging.info("here{}".format(str(e)))
            time.sleep(.2)

    def send_telem(self):
        while self._run_telem_thread:
            try:
                self.touch()
                self.updateTelem()
                self.telem.sendTelemTick()
            except Exception as e:
                logging.info("here{}".format(str(e)))
            time.sleep(.2)

    def pin(self):
        self._pinned_euler = self._euler
        self._pinned_servo_pos = [self._el_last, self._az_last]
        self._pinmode = True

    def unpin(self):
        self._pinned_euler = None
        self._pinned_servo_pos = None
        self._pinmode = False

    def do_euler_calib(self):
        cur_imu = self._bno.euler()
        self._el_target = cur_imu[EL_SERVO_INDEX]
        self._az_target = cur_imu[AZ_SERVO_INDEX]

        self._el_offset = cur_imu[EL_SERVO_INDEX] - self._el_last_raw
        self._az_offset = cur_imu[AZ_SERVO_INDEX] - self._az_last_raw


    def do_move_mode(self):
        el_delta_deg = self._el_target - ((self._el_last_raw + self._el_offset) % 360)
        az_delta_deg = self._az_target - (self._az_last_raw - self._az_offset)

        print("delta {} = {} - {} - {}".format(az_delta_deg, self._az_target, \
                                               self._az_last_raw, self._az_offset))

        if self._el_moving or self._pinmode:
            # goes from 0 - 180, or whaterver max is
            if abs(el_delta_deg) < self._el_max_rate:
                self._el_last_raw = self._el_last_raw + el_delta_deg
                self._servo_mux.position(EL_SERVO_INDEX, self._el_last_raw)
                self._servo_mux.release(EL_SERVO_INDEX)
                self._el_moving = False
            else:
                if el_delta_deg > 0:
                    self._el_last_raw = self._el_last_raw + self._el_max_rate * self._el_direction
                else:
                    self._el_last_raw = self._el_last_raw - self._el_max_rate * self._el_direction
                self._servo_mux.position(EL_SERVO_INDEX, self._el_last_raw)
                self._el_moving = True

        if self._az_moving or self._pinmode:
            # -90 to +90, but antenny can only move from 0 - 90
            print(az_delta_deg)
            if abs(az_delta_deg) < self._az_max_rate:
                self._az_last_raw = self._az_last_raw + az_delta_deg
                self._servo_mux.position(AZ_SERVO_INDEX, self._az_last_raw)
                self._servo_mux.release(AZ_SERVO_INDEX)
                self._az_moving = False
            else:
                if az_delta_deg > 0:
                    self._az_last_raw = self._az_last_raw + self._az_max_rate * self._az_direction
                else:
                    self._az_last_raw = self._az_last_raw - self._az_max_rate * self._az_direction
                self._servo_mux.position(AZ_SERVO_INDEX, self._az_last_raw)
                self._az_moving = True

    def do_pin_mode(self):
        delta_x = self._pinned_euler[0] - self._euler[0]
        delta_y = self._pinned_euler[1] - self._euler[1]
        logging.info("d-x {}, d-y {}".format(delta_x, delta_y))
        self._el_target = self._el_last + delta_x * -1
        self._az_target = self._az_last + delta_y
        self.do_move_mode()

    def update_orientation(self):
        while True:
            try:
                with self.bno_lock:
                    self._euler = self._bno.euler()
            except:
                print("BOO")
                None

    def move_loop(self):
        while True:
            while self._az_moving or self._el_moving or self._pinmode:
                try:

                    if self._pinned_euler:
                        self.do_pin_mode()
                    else:
                        self.do_move_mode()
                    time.sleep(0.1)
                except Exception as e:
                    logging.info(e)
            time.sleep(0.1)

    def set_el_deg(self, deg):
        self._el_moving = True
        self._el_target = deg

    def set_az_deg(self, deg):
        self._az_moving = True
        self._az_target = deg


    @property
    def az(self):
        return self._az_last_raw

    @az.setter
    def az(self, deg):
        self.set_az_deg(deg)

    @property
    def c_az(self):
        return self._az_last + self._az_offset

    @az.setter
    def c_az(self, deg):
        self.set_az_deg(deg+ self._az_offset)

    @property
    def c_el(self):
        return self._el_last + self._el_offset

    @az.setter
    def c_el(self, deg):
        self.set_el_deg(deg + self._el_offset)

    @property
    def el(self):
        return self._el_last

    @el.setter
    def el(self, deg):
        self.set_el_deg(deg)

    #tank control
    TANK_LEFT = [1,2]
    TANK_RIGHT = [0,3]
    TANK_MOTORS = [0,1,2,3]

    def tank_forward(self, speed):
        for i in self.TANK_MOTORS:
            self._servo_mux.speed(i, abs(speed))

    def tank_backward(self, speed):
        for i in self.TANK_MOTORS:
            self._servo_mux.speed(i, -1*abs(speed))

    def tank_leftward(self, speed):
        for i in self.TANK_LEFT:
            self._servo_mux.speed(i, abs(speed))
        for i in self.TANK_RIGHT:
            self._servo_mux.speed(i, -1*abs(speed))

    def tank_rightward(self, speed):
        for i in self.TANK_RIGHT:
            self._servo_mux.speed(i, abs(speed))
        for i in self.TANK_LEFT:
            self._servo_mux.speed(i, -1*abs(speed))

    def imu_status(self):
        output = ""
        output += 'Temperature {}°C'.format(self._bno.temperature()) + "\n"
        output += 'Mag       x {:5.0f}    y {:5.0f}     z {:5.0f}'.format(*self._bno.mag()) + "\n"
        output += 'Gyro      x {:5.0f}    y {:5.0f}     z {:5.0f}'.format(*self._bno.gyro()) + "\n"
        output += 'Accel     x {:5.1f}    y {:5.1f}     z {:5.1f}'.format(*self._bno.accel()) + "\n"
        output += 'Lin acc.  x {:5.1f}    y {:5.1f}     z {:5.1f}'.format(*self._bno.lin_acc()) + "\n"
        output += 'Gravity   x {:5.1f}    y {:5.1f}     z {:5.1f}'.format(*self._bno.gravity()) + "\n"
        output += 'Heading     {:4.0f} roll {:4.0f} pitch {:4.0f}'.format(*self._bno.euler()) + "\n"
        return output

    def motor_status(self):
        # TODO
        pass

    def calibration_routine(self):
        return self.auto_calibration()

    def motor_test(self):
        # TODO
        pass

    def calibration_status(self):
        """
        Returns the calibration values of the connected IMU in tuple form:
        (system, gyro, accelerometer, magnetometer)
        """
        return tuple(self._bno.cal_status())

    def save_calibration(self):
        """
        Save data currently stored in IMU calibration registers to the config file.

        Calibration data consists of sensor offsets and sensor radius: switch into
        config mode, read/write, then switch out
        """
        old_mode = self._bno.mode(CONFIG_MODE)
        for register_name, register_address in IMU_CALIBRATION_REGISTERS.items():
            try:
                cfg.set(register_name, self._bno._read(register_address))
            except OSError:
                return None
        self._bno.mode(old_mode)
        return True

    def upload_calibration(self):
        """
        Upload stored calibration values to the connected IMU.
        """
        old_mode = self._bno.mode(CONFIG_MODE)
        for register_name, register_address in IMU_CALIBRATION_REGISTERS.items():
            try:
                self._bno._write(register_address, cfg.get(register_name))
            except OSError:
                return None
        self._bno.mode(old_mode)
        return True