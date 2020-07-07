from typing import cast


from rbs_tui_dom.dom import DOMWindow
from rbs_tui_dom.dom.text import DOMText
from rbs_tui_dom.entity import EntityEventType

from nyansat.host.client import NyanSatClient


class TelemetryView:
    def __init__(
            self,
            window: DOMWindow,
            client: NyanSatClient
    ):
        self._dom_window = window
        self._dom_altitude = cast(DOMText, window.get_element_by_id("gps_altitude_value"))
        self._dom_azimuth = cast(DOMText, window.get_element_by_id("antenna_azimuth"))
        self._dom_coordinates = cast(DOMText, window.get_element_by_id("gps_coordinates_value"))
        self._dom_elevation = cast(DOMText, window.get_element_by_id("antenna_elevation"))
        self._dom_speed = cast(DOMText, window.get_element_by_id("gps_speed_value"))

        self._client = client
        self._client.telemetry_entity.altitude_observable.add_observer(
            EntityEventType.VALUE_CHANGED,
            self._render_altitude,
        )
        self._client.telemetry_entity.azimuth_observable.add_observer(
            EntityEventType.VALUE_CHANGED,
            self._render_azimuth,
        )
        self._client.telemetry_entity.coordinates_lat_observable.add_observer(
            EntityEventType.VALUE_CHANGED,
            self._render_coordinates,
        )
        self._client.telemetry_entity.coordinates_lng_observable.add_observer(
            EntityEventType.VALUE_CHANGED,
            self._render_coordinates,
        )
        self._client.telemetry_entity.elevation_observable.add_observer(
            EntityEventType.VALUE_CHANGED,
            self._render_elevation,
        )
        self._client.telemetry_entity.speed_observable.add_observer(
            EntityEventType.VALUE_CHANGED,
            self._render_speed,
        )
        self._render_altitude()
        self._render_azimuth()
        self._render_coordinates()
        self._render_elevation()
        self._render_speed()

    def _is_loaded(self):
        return self._client.telemetry_entity.is_loaded

    def _render_altitude(self, *args):
        if not self._is_loaded():
            value = "N/A"
        else:
            altitude = self._client.telemetry_entity.model.altitude.value
            value = f"{altitude:.2f}m"
        self._dom_altitude.set_value(value)

    def _render_azimuth(self, *args):
        if not self._is_loaded():
            value = "N/A"
        else:
            azimuth = self._client.telemetry_entity.model.azimuth.value
            value = f"{azimuth:.2f}º"
        self._dom_azimuth.set_value(value)

    def _render_coordinates(self, *args):
        if not self._is_loaded():
            value = "N/A"
        else:
            lat = self._client.telemetry_entity.model.coordinates_lat.value
            lng = self._client.telemetry_entity.model.coordinates_lng.value
            value = f"{lat:3.2f}, {lng:3.2f}"
        self._dom_coordinates.set_value(value)

    def _render_elevation(self, *args):
        if not self._is_loaded():
            value = "N/A"
        else:
            elevation = self._client.telemetry_entity.model.elevation.value
            value = f"{elevation:.2f}º"
        self._dom_elevation.set_value(value)

    def _render_speed(self, *args):
        if not self._is_loaded():
            value = "N/A"
        else:
            speed = self._client.telemetry_entity.model.speed.value
            value = f"{speed:.2f}m/s"
        self._dom_speed.set_value(value)
