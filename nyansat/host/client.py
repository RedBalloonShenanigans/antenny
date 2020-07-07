import asyncio
from dataclasses import dataclass
from random import random
from typing import Any, Dict, Optional

from rbs_tui_dom.entity import ObservableEntity, UpdatablePropertyValue, ObservableProperty

TELEMETRY_ENTITY_ID = b"root"


@dataclass
class TelemetryEntityData:
    id: bytes
    coordinates_lng: UpdatablePropertyValue[float]
    coordinates_lat: UpdatablePropertyValue[float]
    altitude: UpdatablePropertyValue[float]
    speed: UpdatablePropertyValue[float]
    azimuth: UpdatablePropertyValue[float]
    elevation: UpdatablePropertyValue[float]


class ObservableTelemetryEntity(ObservableEntity[TelemetryEntityData]):
    def __init__(self, identifier: bytes, telemetry: Dict[str, Any] = None):
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
            UpdatablePropertyValue(self.coordinates_lng_observable, telemetry.get("coordinates_lng")),
            UpdatablePropertyValue(self.coordinates_lat_observable, telemetry.get("coordinates_lat")),
            UpdatablePropertyValue(self.altitude_observable, telemetry.get("altitude")),
            UpdatablePropertyValue(self.speed_observable, telemetry.get("speed")),
            UpdatablePropertyValue(self.azimuth_observable, telemetry.get("azimuth")),
            UpdatablePropertyValue(self.elevation_observable, telemetry.get("elevation")),
        )

    def update_from_model(self, telemetry: Dict[str, Any]):
        self.set_model(self._create_entity_data(telemetry))


class NyanSatClient:
    def __init__(self, hostname: str, port: int):
        self.telemetry_entity = ObservableTelemetryEntity(TELEMETRY_ENTITY_ID)
        self.is_connected_observable: ObservableProperty[bool] = ObservableProperty("is_connected")
        self.is_connected: UpdatablePropertyValue[bool] = \
            UpdatablePropertyValue(self.is_connected_observable, False)

        self._hostname = hostname
        self._port = port

    def _on_telemetry_update(self, raw_data: bytes):
        data = {
            "id": TELEMETRY_ENTITY_ID,
            # Parse the rest
        }
        self.telemetry_entity.update_from_model(data)

    def _on_connect(self):
        self.is_connected.value = True

    def _on_disconnect(self):
        self.is_connected.value = False

    async def _run_loop(self):
        await asyncio.sleep(1)
        mock_data = {
            "coordinates_lat": -48,
            "coordinates_lng": 55.54568,
            "altitude": 1895.54689,
            "speed": 0.265,
            "azimuth": -123.4567,
            "elevation": 59.546879,
        }
        self.telemetry_entity.update_from_model(mock_data)
        self._on_connect()
        for i in range(0, 20):
            await asyncio.sleep(0.5)
            mock_data["coordinates_lat"] += random()
            mock_data["coordinates_lng"] += random()
            mock_data["altitude"] += random()
            mock_data["speed"] += random()
            mock_data["azimuth"] += random()
            mock_data["elevation"] += random()
            self.telemetry_entity.update_from_model(mock_data)
        self._on_disconnect()

    async def start(self):
        asyncio.ensure_future(self._run_loop())