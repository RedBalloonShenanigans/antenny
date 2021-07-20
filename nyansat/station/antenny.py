import webrepl
import machine
from api.api import AntennyAPI
from config.config import Config

def start():
    config = Config("antenny")

    if config.get('use_webrepl'):
        webrepl.start()

    api = AntennyAPI(config)
    api.init_components()
    if config.get("enable_demo"):
        interrupt_pin = machine.Pin(15, machine.Pin.IN, machine.Pin.PULL_UP)
        interrupt_pin.irq(trigger=machine.Pin.IRQ_FALLING, handler=api.antenna.pin_motion_test)
    api.start()
    return api