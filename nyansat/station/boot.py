import machine
import ujson


def do_connect():
    import network
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        with open('wifi_config.json', 'r') as f:
            wifi_dict = ujson.load(f)
        print('connecting to network...')
        sta_if.active(True)
        sta_if.connect(wifi_dict['ssid'], wifi_dict['key'])
        while not sta_if.isconnected():
            pass
    print('network config:', sta_if.ifconfig())


machine.freq(240000000)
do_connect()

