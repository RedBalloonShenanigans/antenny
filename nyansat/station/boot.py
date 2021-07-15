import time
import ntptime

import machine
import network
import ujson

# Constants
STA_MODE = 0
AP_MODE = 1


class Connection(object):
    AP_SSID = 'ESP32AccessPoint'

    def __init__(
            self,
            connection_retries: int = 5,
    ):
        """Initialize interfaces and attempt connection."""
        self.sta_if = network.WLAN(network.STA_IF)
        self.ap = network.WLAN(network.AP_IF)
        self.mode = None
        self.num_retries = connection_retries

        with open('/configs/wifi_config.json', 'r') as f:
            wifi_dict = ujson.load(f)
            self.ssid = wifi_dict['ssid']
            self.password = wifi_dict['key']

        self.do_connect()

    def create_ap(self):
        """Create an access point."""
        self.ap.active(True)
        self.ap.config(essid=Connection.AP_SSID)

    def do_connect(self):
        """Try to connect to the SSID, if it fails, create an access point."""
        # Attempting STA connection
        print('connecting to network...')

        self.sta_if.active(True)
        self.sta_if.connect(self.ssid, self.password)
        for retry_count in range(self.num_retries):
            if self.sta_if.isconnected():
                break
            print("Waiting for connection {}/{}".format(retry_count, self.num_retries))
            time.sleep(1)

        # Success:
        if self.sta_if.isconnected():
            self.mode = STA_MODE
            print('network config:', self.sta_if.ifconfig())
            for _ in range(self.num_retries):
                try:
                    ntptime.settime()
                    break
                except:
                    pass
                time.sleep(1)

        # Failure, starting access point
        else:
            print('Could not connect, creating WiFi access point')
            self.sta_if.active(False)
            self.create_ap()
            self.mode = AP_MODE


if __name__ == '__main__':

    machine.freq(240000000)
    conn = Connection()
