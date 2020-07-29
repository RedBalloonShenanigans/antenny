#!/bin/bash

python3 ../../microcontrollers/esptool/esptool.py --chip esp32 --port /dev/ttyUSB0 --baud 460800 erase_flash
python3 ../../microcontrollers/esptool/esptool.py --chip esp32 --port /dev/ttyUSB0 --baud 460800 write_flash -z 0x1000 esp32-idf3-20191220-v1.12.bin
make nyansat SERIAL=/dev/ttyUSB0
