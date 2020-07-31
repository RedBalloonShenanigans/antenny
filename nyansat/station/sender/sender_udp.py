import logging
import socket
import struct

from antenny_threading import Thread
from imu.mock_imu import MockImuController
from gps.gps import GPSController
from imu.imu import ImuController

try:
    import utime as time
    import ujson as json
except ImportError:
    import time
    import json

try:
    from sender.sender import TelemetrySender
except ImportError:
    TelemetrySender = object

LOGGER = logging.getLogger("station.sender.udp")
NYANSAT_CLIENT_MAGIC = b"nyansat_client"

MCAST_GRP = '239.255.255.250'
MCAST_PORT = 31337
IS_ALL_GROUPS = False
INADDR_ANY = 0
MAX_MESSAGE_SIZE = 1024

DEFAULT_POLL_DELAY = 0.001


class AbstractTelemetrySender(Thread, TelemetrySender):

    def __init__(
            self,
            gps_controller: GPSController,
            imu_controller: ImuController,
            interval: float = 0.2
    ):
        super(AbstractTelemetrySender, self).__init__()
        self._gps_controller = gps_controller
        self._imu_controller = imu_controller
        self._interval = interval

    def run(self):
        while self.running:
            telemetry = self._fetch_telemetry_data()
            self._send_message(telemetry)
            time.sleep(self._interval)

    def _fetch_telemetry_data(self):
        """
        Format & enqueu teleme
        """
        if hasattr(time, 'tick_ms'):
            data = {"time": time.ticks_ms()}
        else:
            data = {"time": time.time()}
        imu_position = self._imu_controller.euler()
        if imu_position is not None:
            # TODO: these values need to be chosen based on a configuration index
            data.update({
                "azimuth": imu_position[1],
                "elevation": imu_position[0],
                # "z": imu_position[2],
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
        return data

    def _send_message(self, message: dict):
        raise NotImplementedError


def socket_inet_aton(ip_address: str):
    """
    Implementation of socket.inet_aton(), not implemented in micropython.
    """
    values = ip_address.split('.')
    result = b""
    for value in values:
        result += struct.pack("!B", int(value))
    return result


class UDPTelemetrySender(AbstractTelemetrySender):
    """
    UDP multicast implementation of a telemetry sender.
    """

    def __init__(
            self,
            broadcast_port: int,
            gps_controller: GPSController,
            imu_controller: ImuController,
            interval: float = 0.2
    ):
        super(UDPTelemetrySender, self).__init__(gps_controller, imu_controller, interval)
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind(('', broadcast_port))
        self._port = broadcast_port

    def _send_message(self, message: dict):
        self._socket.sendto(json.dumps(message).encode('utf8'), (MCAST_GRP, self._port))


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    from gps.mock_gps_controller import MockGPSController

    sender = UDPTelemetrySender(
            MCAST_PORT,
            MockGPSController(),
            MockImuController(),
    )
    sender.start()
    time.sleep(int(1e3))
    sender.stop()
