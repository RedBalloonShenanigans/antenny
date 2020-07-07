class MotorController(object):
    """Interface for servomotor mux controller."""

    def set_position(self, index, degrees=None, radians=None, us=None, duty=None):
        raise NotImplementedError()

    def degrees(self, index):
        """Return the position in degrees of the servo with the given index."""
        raise NotImplementedError()

    def smooth_move(self, index, degrees, delay):
        """Move the servo with the given index to a specified position and with
        a given initial delay.
        """
        raise NotImplementedError()

    def release(self, index):
        """Set the duty cycle of the servo with the given index to 0."""
        raise NotImplementedError()
