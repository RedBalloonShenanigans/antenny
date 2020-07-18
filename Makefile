setup:
	git submodule update --init

nyanshell: setup
	python3 setup.py install


_check_serial_param:
	@[ "${SERIAL}" ] || ( echo "SERIAL flag is not set\nSet SERIAL to your ESP32's port"; exit 1 )

nyansat: _check_serial_param setup
	python3 wifi_config.py
	mpfshell -o ser:$(SERIAL) -s esp32_install.mpf
	rm wifi_config.json

all: nyanshell nyansat

.PHONY: setup nyanshell nyansat _check_serial_param all
