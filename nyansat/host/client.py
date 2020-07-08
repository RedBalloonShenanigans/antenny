import asyncio
import json
import logging
import socket
from asyncio import Future, BaseTransport, BaseProtocol
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from rbs_tui_dom.entity import ObservableEntity, UpdatablePropertyValue, ObservableProperty

TELEMETRY_ENTITY_ID = b"root"
TELEMETRY_CLIENT_MAGIC = b"nyansat_client"


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
            UpdatablePropertyValue(self.coordinates_lng_observable, telemetry.get("coordinates_lng")),
            UpdatablePropertyValue(self.coordinates_lat_observable, telemetry.get("coordinates_lat")),
            UpdatablePropertyValue(self.altitude_observable, telemetry.get("altitude")),
            UpdatablePropertyValue(self.speed_observable, telemetry.get("speed")),
            UpdatablePropertyValue(self.azimuth_observable, telemetry.get("azimuth")),
            UpdatablePropertyValue(self.elevation_observable, telemetry.get("elevation")),
        )

    def update_from_model(self, telemetry: Dict[str, Any]):
        self.set_model(self._create_entity_data(telemetry))


class NyanSatClient(BaseProtocol):
    def __init__(
            self,
            iface: str,
            port: int,
            station_ip: Optional[str],
            station_port: int,
            disconnect_timeout: float = 2
    ):
        self.telemetry_entity = ObservableTelemetryEntity(TELEMETRY_ENTITY_ID)
        self.telemetry_entity.update_from_model({})
        self.is_connected_observable: ObservableProperty[bool] = ObservableProperty("is_connected")
        self.is_connected: UpdatablePropertyValue[bool] = \
            UpdatablePropertyValue(self.is_connected_observable, False)

        self._hostname = iface
        self._port = port
        self._station_ip = station_ip
        self._station_port = station_port
        self._disconnect_task: Optional[Future] = None
        self._transport: Optional[BaseTransport] = None
        self._socket: Optional[socket.socket] = None
        self._disconnect_timeout = disconnect_timeout

    def _on_connect(self):
        self.is_connected.value = True

    def _on_disconnect(self):
        self.is_connected.value = False

    async def _run_disconnect_task(self):
        try:
            if self.is_connected.value is True:
                # Only wait to set stat as disconnected if it is current connected
                await asyncio.sleep(self._disconnect_timeout)
                self._on_disconnect()
            while True:
                await asyncio.sleep(1)
                # Keep advertising the client on the network
                if self._station_ip:
                    self._socket.sendto(
                        TELEMETRY_CLIENT_MAGIC,
                        (self._station_ip, self._station_port)
                    )
                else:
                    self._socket.sendto(
                        TELEMETRY_CLIENT_MAGIC,
                        ('<broadcast>', self._station_port)
                    )
        except asyncio.CancelledError:
            pass

    def datagram_received(self, data: bytes, addr: Tuple[str, int]):
        if self._disconnect_task:
            self._disconnect_task.cancel()
        try:
            data = dict(json.loads(data.decode('utf-8')))
            data["ip"] = addr[0]
            data["port"] = addr[1]
            self._on_connect()
            self.telemetry_entity.update_from_model(data)
            self._disconnect_task = asyncio.ensure_future(self._run_disconnect_task())
        except:
            logging.error(f"Failed to handle UDP packet: {data}", exc_info=True)

    async def start(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self._socket.bind((self._hostname, self._port))
        self._transport, _ = await asyncio.get_event_loop().create_datagram_endpoint(
            lambda: self,
            sock=self._socket
        )
        self._disconnect_task = asyncio.ensure_future(self._run_disconnect_task())

    async def stop(self):
        if self._socket:
            self._socket.close()
        if self._transport:
            self._transport.close()
        self._transport = None
        self._on_disconnect()
