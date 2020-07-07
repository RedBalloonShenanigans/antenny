from ssd1306 import SSD1306_I2C

from .screen import ScreenController


class Ssd1306ScreenController(ScreenController):
    """Controller for SSD1306 OLED screen display."""

    def __init__(self, i2c: machine.I2C, width: int = 128, height: int = 32):
        """Initialize the SSD1306 screen with a given width, height, and I2C
        connection.
        """
        self.ssd_screen = SSD1306_I2C(width, height, i2c)

    def display(self, data) -> None:
        """Display a 3-tuple of numeric data, e.g. a tuple of Euler headings"""
        if len(data) != 3:
            raise ValueError("SSD1306 screen only configured to accept 3 numbers.")

        self.ssd_screen.fill(0)
        self.ssd_screen.text("{:08.3f}".format(data[0]), 0, 0)
        self.ssd_screen.text("{:08.3f}".format(data[1]), 0, 8)
        self.ssd_screen.text("{:08.3f}".format(data[2]), 0, 16)
        self.ssd_screen.show()

