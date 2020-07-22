import antenny
import machine


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


initialize_i2c_bus()
# leave this global so the entire system has access to the AntKontrol instance
api = antenny.esp32_antenna_api_factory()
