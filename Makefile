setup:
	git submodule init
	git submodule update

nyanshell: setup
	cd lib/rbs-tui-dom && python3 setup.py install
	pip3 install -r nyanshell/requirements.txt
	pip3 install ./nyanshell


_check_serial_param:
	@[ "${SERIAL}" ] || ( echo "SERIAL flag is not set\nSet SERIAL to your ESP32's port"; exit 1 )

nyansat: _check_serial_param setup
	mpfshell -n -c "open ser:$(SERIAL); mput nyansat/station*\.py *\.py"

all: nyanshell nyansat

.PHONY: setup nyanshell nyansat _check_serial_param all