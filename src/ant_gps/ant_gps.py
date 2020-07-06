import machine
from micropyGPS import MicropyGPS
import config as cfg
import logging
import uasyncio
import time

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

