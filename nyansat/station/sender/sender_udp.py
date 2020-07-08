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
NYANSAT_CLIENT_MAGIC = b"nyansat_client"


class UDPTelemetrySender(TelemetrySender):
    """Send key-value data over UDP to be displayed on client end."""

    def __init__(
            self,
            gps_controller: GPSController,
            imu_controller: ImuController,
            interval: float = 0.2
    ):
        """Create a TelemetrySenderUDP object with destination address and port
        obtained from the current user-set config.
        """
        self._socket = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP
        )
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind(('', 31337))
        self._gps_controller = gps_controller
        self._imu_controller = imu_controller
        self._interval = interval
        self._stop = False
        self._receiver = None
        self._send_thread = None
        self._receive_thread = None

    def _send_telemetry(self):
        if self._receiver is None:
            return

        data = {"time": utime.ticks_ms()}
        imu_position = self._imu_controller.euler()
        if imu_position is not None:
            data.update({
                "azimuth": imu_position[1],
                "elevation": imu_position[0]
            })
        gps_status = self._gps_controller.get_status()
        if gps_status is not None:
            data.update({
                "gps_valid": gps_status.valid,
                "coordinates_lng": gps_status.longitude,
                "coordinates_lat": gps_status.latitude,
                "altitude": gps_status.altitude,
                "speed": gps_status.speed,
            })
        self._socket.sendto(ujson.dumps(data).encode('utf-8'), self._receiver)

    def _run_send_loop(self):
        while not self._stop:
            try:
                self._send_telemetry()
            except Exception as e:
                LOGGER.error("Failed to send telemetry: {}".format(str(e)))
            time.sleep(self._interval)
        self._send_thread = None

    def _run_receive_loop(self):
        while not self._stop:
            try:
                message, receiver = self._socket.recvfrom(1024)
                if message == NYANSAT_CLIENT_MAGIC:
                    self._receiver = receiver
            except Exception:
                LOGGER.error("Failed to accept telemetry client")
            time.sleep(self._interval)
        self._receive_thread = None

    def start(self):
        print("START")
        self._stop = False
        self._send_thread = _thread.start_new_thread(self._run_send_loop, ())
        self._receive_thread = _thread.start_new_thread(self._run_receive_loop, ())

    def stop(self):
        self._stop = True
        while self._send_thread is not None or self._receive_thread is None:
            time.sleep(self._interval)