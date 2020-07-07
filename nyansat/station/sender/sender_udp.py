import _thread
import logging
import socket
import time
import utime

import ujson

from gps.gps import GPSController
from imu.imu import ImuController
from sender.sender import TelemetrySender

LOGGER = logging.getLogger("station.sender.udp")


class UDPTelemetrySender(TelemetrySender):
    """Send key-value data over UDP to be displayed on client end."""

    def __init__(
            self,
            gps_controller: GPSController,
            imu_controller: ImuController,
            hostname: str,
            port: int,
            interval: float = 0.2
    ):
        """Create a TelemetrySenderUDP object with destination address and port
        obtained from the current user-set config.
        """
        self._hostname = hostname
        self._port = port
        self._socket = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP
        )
        self._gps_controller = gps_controller
        self._imu_controller = imu_controller
        self._interval = interval
        self._stop = False
        self._thread = None

    def _send_telemetry(self):
        imu_position = self._imu_controller.euler()
        gps_status = self._gps_controller.get_status()
        data = ujson.dumps({
            "euler": imu_position,
            "gps_valid": gps_status.valid,
            "gps_long": gps_status.longitude,
            "gps_lat": gps_status.latitude,
            "gps_altitude": gps_status.altitude,
            "gps_speed": gps_status.speed,
            "gps_course": gps_status.course,
            "time": utime.ticks_ms(),
        })
        self._socket.sendto(data, (self._hostname, self._port))

    def _run_loop(self):
        while not self._stop:
            try:
                self._send_telemetry()
            except Exception:
                LOGGER.error("Failed to send telemetry")
            time.sleep(self._interval)
        self._thread = None

    def start(self):
        if self._thread:
            return
        self._stop = False
        self._thread = _thread.start_new_thread(self._run_loop, ())

    def stop(self):
        self._stop = True
        while self._thread is not None:
            time.sleep(self._interval)