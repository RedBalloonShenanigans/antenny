from motor.motor import MotorController


class MockMotorController(MotorController):
    """Interface for servomotor mux controller."""

    def __init__(self):
        self._position = 90.

    def set_position(self, index, degrees=None, radians=None, us=None, duty=None):
        self._position = degrees

    def get_position(self, index, degrees=None, radians=None, us=None, duty=None):
        return self._position

    def degrees(self, index):
        """Return the position in degrees of the servo with the given index."""
        return self._position

    def smooth_move(self, index, degrees, delay):
        """Move the servo with the given index to a specified position and with
        a given initial delay.
        """
        self._position = degrees

    def release(self, index):
        """Set the duty cycle of the servo with the given index to 0."""
        pass
