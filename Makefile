setup:
	git submodule update --init
	cd lib/BNO055; git checkout 4422248bc82a79b4aec9cc90599f28de60e37c76
	cd lib/PCA9685; git checkout 0fea2736f99a2840f0d644be866f6abd5bc14b48
	cd lib/micropython; git checkout c2317a3a8d5f184de2f816078d91be699274b94

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
