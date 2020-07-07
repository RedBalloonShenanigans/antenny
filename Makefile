.PHONY: setup all nyanshell nyansat

all: nyanshell nyansat

check:
	@[ "${SERIAL}" ] || ( echo "SERIAL flag is not set\nSet SERIAL to your ESP32's port"; exit 1 )

setup:
	git submodule init
	git submodule update

nyanshell:
	pip3 install -r nyanshell/requirements.txt
	pip3 install ./nyanshell

nyansat: setup check
	mpfshell -n -c "open ser:$(SERIAL); mput nyansat/*\.py *\.py"

