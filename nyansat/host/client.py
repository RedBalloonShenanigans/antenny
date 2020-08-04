import asyncio
import json
import socket
import struct
from asyncio import AbstractEventLoop
from dataclasses import dataclass
from typing import Any, Dict, Optional

from rbs_tui_dom.entity import ObservableEntity, UpdatablePropertyValue, ObservableProperty

TELEMETRY_ENTITY_ID = b"root"

MCAST_GRP = '239.255.255.250'
MCAST_PORT = 31337
MAX_MESSAGE_SIZE = 1024
_DEFAULT_TIMEOUT = 0.0001


@dataclass
class TelemetryEntityData:
    id: bytes
    ip: UpdatablePropertyValue[str]
    port: UpdatablePropertyValue[int]
    coordinates_lng: UpdatablePropertyValue[float]
    coordinates_lat: UpdatablePropertyValue[float]
    altitude: UpdatablePropertyValue[float]
    speed: UpdatablePropertyValue[float]
    azimuth: UpdatablePropertyValue[float]
    elevation: UpdatablePropertyValue[float]


class ObservableTelemetryEntity(ObservableEntity[TelemetryEntityData]):
    def __init__(self, identifier: bytes, telemetry: Dict[str, Any] = None):
        self.ip_observable = ObservableProperty("ip")
        self.port_observable = ObservableProperty("port")
        self.coordinates_lng_observable = ObservableProperty("coordinates_lng")
        self.coordinates_lat_observable = ObservableProperty("coordinates_lat")
        self.altitude_observable = ObservableProperty("altitude")
        self.speed_observable = ObservableProperty("speed")
        self.azimuth_observable = ObservableProperty("azimuth")
        self.elevation_observable = ObservableProperty("elevation")
        super().__init__(identifier, [], telemetry)

    def _create_entity_data(self, telemetry: Dict[str, Any]) -> Optional[TelemetryEntityData]:
        if telemetry is None:
            return telemetry
        return TelemetryEntityData(
                telemetry.get("id"),
                UpdatablePropertyValue(self.ip_observable, telemetry.get("ip")),
                UpdatablePropertyValue(self.port_observable, telemetry.get("port")),
                UpdatablePropertyValue(self.coordinates_lng_observable,
                                       telemetry.get("coordinates_lng")),
                UpdatablePropertyValue(self.coordinates_lat_observable,
                                       telemetry.get("coordinates_lat")),
                UpdatablePropertyValue(self.altitude_observable, telemetry.get("altitude")),
                UpdatablePropertyValue(self.speed_observable, telemetry.get("speed")),
                UpdatablePropertyValue(self.azimuth_observable, telemetry.get("azimuth")),
                UpdatablePropertyValue(self.elevation_observable, telemetry.get("elevation")),
        )

    def update_from_model(self, telemetry: Dict[str, Any]):
        self.set_model(self._create_entity_data(telemetry))


class NyanSatTelemetryClient(object):

    def __init__(
            self,
            event_loop: AbstractEventLoop,
            listen_port: int,
            interval: float = 0.2,
            offline_timeout: int = 2,
    ):
        self._event_loop = event_loop
        self._interval = interval
        self._offline_timeout = offline_timeout
        self._mcast_socket: Optional[socket.socket] = None
        self.telemetry_entity = ObservableTelemetryEntity(TELEMETRY_ENTITY_ID)
        self.telemetry_entity.update_from_model({})
        self._initialize_mcast_socket(listen_port)
        self._running = False
        self.is_connected_observable: ObservableProperty[bool] = ObservableProperty("is_connected")
        self.is_connected: UpdatablePropertyValue[bool] = \
            UpdatablePropertyValue(self.is_connected_observable, False)

    def _initialize_mcast_socket(self, listen_port: int):
        self._mcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._mcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._mcast_socket.bind((MCAST_GRP, listen_port))
        mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
        self._mcast_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        self._mcast_socket.settimeout(_DEFAULT_TIMEOUT)

    async def _recv_from_multicast(self) -> Optional[bytes]:
        try:
            return await self._event_loop.run_in_executor(
                    None,
                    self._mcast_socket.recvfrom,
                    (MAX_MESSAGE_SIZE),
            )
        except OSError:
            return None

    async def _recv_loop(self):
        last_contact = self._offline_timeout
        while self._running:
            data = await self._recv_from_multicast()
            if data is not None:
                last_contact = 0
                message, (hostname, port) = data
                message = dict(json.loads(message.decode('utf-8')))
                message["ip"] = hostname
                message["port"] = port
                self.telemetry_entity.update_from_model(message)
            else:
                # data is None (i.e. socket timeout)
                last_contact += self._interval
            self.is_connected.value = last_contact < self._offline_timeout
            await asyncio.sleep(self._interval)

    async def start(self):
        self._running = True
        await asyncio.ensure_future(self._recv_loop())

    async def stop(self):
        self._running = False


async def main():
    event_loop = asyncio.get_event_loop()
    client = NyanSatTelemetryClient(event_loop, 31337)
    await client.start()
    await asyncio.sleep(10)
    await client.stop()


if __name__ == '__main__':
    asyncio.run(main())
