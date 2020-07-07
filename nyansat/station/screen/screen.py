
class ScreenController():
    """Interface for a generic screen controller, for displaying nyansat motor
    and IMU status."""

    def display(self, data) -> None:
        """Display a tuple of numeric data on screen."""
        raise NotImplementedError()