setup:
	git submodule update --init
	cd lib/BNO055; git checkout 4422248bc82a79b4aec9cc90599f28de60e37c76
	cd lib/PCA9685; git checkout 0fea2736f99a2840f0d644be866f6abd5bc14b48
	cd lib/micropython; git checkout c2317a3a8d5f184de2f816078d91be699274b94
	cd lib/micropygps; git checkout 95b739381c8feb7c6b91b46db42646074c52a609
	cd lib/simple-pid; git checkout 6f7846a2bd22f614713c237c4ce98df2a42664f7 
	cd lib/Adafruit_CircuitPython_BNO08x; git checkout 35fa82de11fc08de68211ddec8f3a050f95c5b84

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
