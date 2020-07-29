import logging

from antenny_threading import Thread, Queue
from screen.screen import ScreenController

LOG = logging.getLogger('antenny.mock_screen')


class MockScreenController(ScreenController, Thread):
    """Interface for a generic screen controller, for displaying nyansat motor
    and IMU status."""

    def __init__(
            self,
            display_queue: Queue,
    ):
        Thread.__init__(self)
        self.display_queue = display_queue

    def run(self):
        previously_displayed = None
        while self.running:
            newly_displayed = self.display_queue.get()
            if newly_displayed != previously_displayed:
                self._display(newly_displayed)
            previously_displayed = newly_displayed

    def _display(self, data) -> None:
        LOG.info(data)

    def display(self, data) -> None:
        """Display a tuple of numeric data on screen."""
        self.display_queue.put(data)
