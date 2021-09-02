import random
import time
import machine

from ssd1306 import SSD1306_I2C
import machine

from screen.screen import ScreenController
from config.config import Config

MAX_CHAR_LINES = 4
MAX_CHAR_WIDTH = 16

class Ssd1306ScreenController(ScreenController):
    """Controller for SSD1306 OLED screen display."""

    def __init__(self, i2c: machine.I2C, width: int = 128, height: int = 32):
        """Initialize the SSD1306 screen with a given width, height, and I2C
        connection.
        """
        self.ssd_screen = SSD1306_I2C(width, height, i2c)
        self._line_buffers = ['a: ', 'b: ', 'c: ', 'd: ']
        self.screen_id = Config('antenny').get('screen_timer_id')
        self.screen_loop_timer = machine.Timer(self.screen_id) #hardcoded 2. need to fix
        self.loop_frequency = 1000
        
    def start(self):
        self.start_loop()

    def stop(self):
        self.stop_loop()

    def start_loop(self):
        """
        Initializes the screen timer interrupt
        :return:
        """
        self.screen_loop_timer.init(period=self.loop_frequency, mode=machine.Timer.PERIODIC, \
                                 callback=lambda a: self.update())

    def stop_loop(self):
        """
        Stops the PID timer
        :return:
        """
        self.screen_loop_timer.deinit()


    def update_line(self, str_data, line_num):
        line_num = abs(line_num)
        assert line_num < MAX_CHAR_LINES
        str_data = str_data[0:MAX_CHAR_WIDTH]
        self._line_buffers[line_num] = str_data
        
    def update(self):
        self.ssd_screen.fill(0)
        self.ssd_screen.text(self._line_buffers[0], 0, 0)
        self.ssd_screen.text(self._line_buffers[1], 0, 8)
        self.ssd_screen.text(self._line_buffers[2], 0, 16)
        self.ssd_screen.text(self._line_buffers[3], 0, 24)
        self.ssd_screen.show()
        
    def display(self, data) -> None:
        """Display a 3-tuple of numeric data, e.g. a tuple of Euler headings"""
        if len(data) != 3:
            raise ValueError("SSD1306 screen only configured to accept 3 numbers.")

        self.ssd_screen.fill(0)
        self.ssd_screen.text("{:08.3f}".format(data[0]), 0, 0)
        self.ssd_screen.text("{:08.3f}".format(data[1]), 0, 8)
        self.ssd_screen.text("{:08.3f}".format(data[2]), 0, 16)
        self.ssd_screen.show()

