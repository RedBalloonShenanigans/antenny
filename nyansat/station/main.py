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


config = ConfigRepository()
if not failed_imports:
    initialize_i2c_bus(config.get('antenny_board_version'))
    # leave this global so the entire system has access to the AntKontrol instance
    api = antenny.esp32_antenna_api_factory()
else:
    print("WARNING: necessary imports failed, please reboot the device after installing the "
          "necessary dependencies")
    api = None

if config.get('use_webrepl'):
    webrepl.start()


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
