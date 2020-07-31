from rbs_tui_dom.dom import DOMWindow, DOMStyle, Display
from rbs_tui_dom.entity import EntityEventType

from nyansat.host.client import NyanSatTelemetryClient


class RootView:
    def __init__(
            self,
            window: DOMWindow,
            client: NyanSatTelemetryClient,
    ):
        self._client = client
        self._dom_window = window
        self._dom_disconnected_container = window.get_element_by_id("disconnected_container")
        self._dom_telemetry_container = window.get_element_by_id("telemetry_container")
        self._client.is_connected_observable.add_observer(
            EntityEventType.VALUE_CHANGED,
            self._render
        )
        self._render()

    def _render(self, *args):
        if self._client.is_connected.value:
            self._dom_disconnected_container.set_style(DOMStyle(display=Display.NONE))
            self._dom_telemetry_container.set_style(DOMStyle(display=Display.BLOCK))
        else:
            self._dom_disconnected_container.set_style(DOMStyle(display=Display.BLOCK))
            self._dom_telemetry_container.set_style(DOMStyle(display=Display.NONE))