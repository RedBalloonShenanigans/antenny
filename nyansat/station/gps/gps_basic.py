import machine
import time

from micropyGPS import MicropyGPS

from gps.gps import GPSController, GPSStatus


class BasicGPSController(GPSController):
    def __init__(self, tx, rx):
        self._gps_uart = machine.UART(1, 9600)
        self._gps_uart.init(tx=tx,
                            rx=rx)
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
        return self._model

    def _update_gps(self):
        g_sentence = self._gps_uart.readline()
        while g_sentence:
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
