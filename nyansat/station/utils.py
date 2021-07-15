import machine
from antenny_threading import Queue

from antenny import AntennyAPI
from multi_client.follower import AntennyFollowerNode, MCAST_PORT, UDPFollowerClient
import time

def initialize_i2c_bus(config_version: int):
    """
    Configure I2C pin layout according to the manual.
    """
    if config_version == 1:
        pins = [4, 14, 15, 16, 17, 19]
    elif config_version == 2:
        pins = [23, 25, 26, 27, 2, 4]
    else:
        print(
                "WARNING: antenny board revision == -1, if you have an antenny v1 or v2 board, "
                "please config.set('antenny_board_version', {1, 2})")
        pins = []
    for pin_idx in pins:
        pin = machine.Pin(pin_idx, machine.Pin.OUT)
        pin.value(0)


def join_leader(my_id: int, api: AntennyAPI):
    """
    Join a leader.
    """
    udp_client = UDPFollowerClient(Queue(), Queue(), MCAST_PORT)
    follower = AntennyFollowerNode(my_id, udp_client, api)
    try:
        udp_client.start()
        follower.start()
        while not follower.follow(0x42):
            time.sleep(1)
    except Exception as e:
        print(e)
        udp_client.stop()
        follower.stop()
        return
    follower.join()
    udp_client.join()

