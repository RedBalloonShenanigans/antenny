from abc import abstractmethod


class MotorController:
    """Interface for servomotor mux controller."""

    @abstractmethod
    def set_position(self, index, degrees=None, radians=None, us=None, duty=None):
        raise NotImplementedError()

    @abstractmethod
    def degrees(self, index):
        """Return the position in degrees of the servo with the given index."""
        raise NotImplementedError()

    @abstractmethod
    def smooth_move(self, index, degrees, delay):
        """Move the servo with the given index to a specified position and with
        a given initial delay.
        """
        raise NotImplementedError()

    @abstractmethod
    def release(self, index):
        """Set the duty cycle of the servo with the given index to 0."""
        raise NotImplementedError()

    # @abc.abstractmethod
    # # TODO: NOT NEEDED - this is for TANK
    # def speed(self, index, value=None):
    #     return
