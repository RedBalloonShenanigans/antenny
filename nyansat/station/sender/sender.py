
class TelemetrySender():
    """Sends IMU and motor telemetry data from board to be received by some client."""

    def start(self) -> None:
        """Begin sending telemetry data to client."""
        raise NotImplementedError()

    def stop(self) -> None:
        """Stop sending telemetry data to client."""
        raise NotImplementedError()