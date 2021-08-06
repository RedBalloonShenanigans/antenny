setup:
	git submodule update --init

nyanshell: setup
	python3 setup.py install

_check_serial_param:
	@[ "${SERIAL}" ] || ( echo "SERIAL flag is not set\nSet SERIAL to your ESP32's port"; exit 1 )

clean: _check_serial_param
	echo "\n" > empty_file.py
	mpfshell -o ser:$(SERIAL) -s esp32_clean.mpf
	rm empty_file.py

reinstall: _check_serial_param
	mpfshell -o ser:$(SERIAL) -s esp32_reinstall.mpf

nyansat: _check_serial_param setup
	python3 -m nyansat.station.installer $(SERIAL)

all: nyanshell nyansat

.PHONY: setup nyanshell clean reinstall nyansat _check_serial_param all
