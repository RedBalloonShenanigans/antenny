import machine
import time

from micropyGPS import MicropyGPS

from gps.gps import GPSController, GPSStatus


class BasicGPSController(GPSController):
    def __init__(self, tx, rx):
        #hardcoded 2, please fix
        self._gps_uart = machine.UART(2, 9600, rx=rx, tx=tx,
                                      timeout=10)
        self._gps_uart.init()
        self._gps = MicropyGPS()
        self._model = None
        
    def run(self):
        # TODO: Why do we need to constantly update the GPS values here?
        while True:
            try:
                self._update_gps()
            except Exception as e:
                print(e)
            time.sleep(1)

    def get_status(self) -> GPSStatus:
        self._model = GPSStatus(
            self._gps.valid,
            self._gps.latitude,
            self._gps.longitude,
            self._gps.altitude,
            self._gps.speed,
            self._gps.course,
            self._gps.timestamp,
        )
        return self._model

    def _update_gps_single(self):
        g_sentence = self._gps_uart.readline()
        if g_sentence:
            g_sentence = g_sentence.decode("ascii")
            #print(g_sentence)
            for g_word in g_sentence:
                self._gps.update(g_word)
            
    def _update_gps(self):
        print("Starting update GPS")
        g_sentence = self._gps_uart.readline()
        while True:
            while g_sentence:
                print(g_sentence)
                g_sentence = g_sentence.decode("ascii")
                for g_word in g_sentence:
                    self._gps.update(g_word)
                self._model = GPSStatus(
                    self._gps.valid,
                    self._gps.latitude,
                    self._gps.longitude,
                    self._gps.altitude,
                    self._gps.speed,
                    self._gps.course,
                    self._gps.timestamp,
                )
                g_sentence = self._gps_uart.readline()
            time.sleep(1)
