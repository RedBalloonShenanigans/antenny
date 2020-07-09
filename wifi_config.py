import json

def query_wifi():
    wifi_dict = {}
    wifi_dict['ssid'] = input('Your SSID: ')
    wifi_dict['key'] = input('Your Password: ')
    with open('wifi_config.json', 'w') as f:
        json.dump(wifi_dict, f)
    
    webrepl_pass = input('Create WiFi console password: ')
    with open('webrepl_cfg.py', 'w') as f:
        f.write("PASS = '{}'\n".format(webrepl_pass))

if __name__ == '__main__':
    query_wifi()
