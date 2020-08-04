"""
Antenny main entry point, runs after boot.py.
"""
import time
import machine
import webrepl

# Account for the fact that libraries like logging and asyncio need to be installed, after a
#   successful connection on reboot.
failed_imports = False

try:
    import logging
    import antenny
    from antenny_threading import Queue
    from config.config import ConfigRepository
    from multi_client.follower import AntennyFollowerNode, MCAST_PORT, UDPFollowerClient
except ImportError as e:
    print(e)
    failed_imports = True


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


if not failed_imports:
    initialize_i2c_bus()
    # leave this global so the entire system has access to the AntKontrol instance
    api = antenny.esp32_antenna_api_factory()
    config = api.config
    if config.get('use_webrepl'):
        webrepl.start()
else:
    print("WARNING: necessary imports failed, please reboot the device after installing the "
          "necessary dependencies")
    api = None
    config = ConfigRepository()


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
