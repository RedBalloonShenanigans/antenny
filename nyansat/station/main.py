import time
import logging
import antenny
import machine

from antenny_threading import Queue

from multi_client.follower import AntennyFollowerNode, MCAST_PORT, UDPFollowerClient


def initialize_i2c_bus():
    pin = machine.Pin(4, machine.Pin.OUT)
    pin.value(0)
    pin = machine.Pin(14, machine.Pin.OUT)
    pin.value(0)
    pin = machine.Pin(15, machine.Pin.OUT)
    pin.value(0)
    pin = machine.Pin(16, machine.Pin.OUT)
    pin.value(0)
    pin = machine.Pin(17, machine.Pin.OUT)
    pin.value(0)
    pin = machine.Pin(19, machine.Pin.OUT)
    pin.value(0)


logging.basicConfig(level=logging.DEBUG)
initialize_i2c_bus()
# leave this global so the entire system has access to the AntKontrol instance
api = antenny.esp32_antenna_api_factory()


def join_leader(my_id: int):
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
