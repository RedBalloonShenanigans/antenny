class MotorController():
    """Interface for servomotor mux controller."""

    def position(self, index, degrees=None, radians=None, us=None, duty=None):
        return

    def degrees(self, index):
        """Return the position in degrees of the servo with the given index."""
        return

    def smooth_move(self, index, degrees, delay):
        """Move the servo with the given index to a specified position and with
        a given initial delay.
        """
        return

    def release(self, index):
        """Set the duty cycle of the servo with the given index to 0."""
        return

    # @abc.abstractmethod
    # # TODO: NOT NEEDED - this is for TANK
    # def speed(self, index, value=None):
    #     return