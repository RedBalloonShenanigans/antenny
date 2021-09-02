import random
import time
import machine
from controller.controller import PlatformController
from config.config import Config

class GPSLocationController(PlatformController):

    def __init__(self, gps_controller):
        self.timer_id = Config('antenny').get('gps_timer_id')
        self.gps_loop_timer = machine.Timer(self.timer_id) #hardcoded 2. need to fix
        self.gps_controller = gps_controller
        self.loop_frequency = 200
        
    def start(self):
        self.start_loop()

    def stop(self):
        self.stop_loop()

    def start_loop(self):
        """
        Initializes the GPS timer interrupt
        :return:
        """
        self.gps_loop_timer.init(period=self.loop_frequency, mode=machine.Timer.PERIODIC, \
                                 callback=lambda a: self._gps_loop())

    def stop_loop(self):
        """
        Stops the PID timer
        :return:
        """
        self.gps_loop_timer.deinit()

    def _gps_loop(self):
        self.gps_controller._update_gps_single()
    
