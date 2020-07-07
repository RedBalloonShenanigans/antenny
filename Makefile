SERIAL=/dev/ttyUSB0

.PHONY: all nyanshell nyansat

all: nyanshell nyansat

nyanshell:
	pip3 install -r nyanshell/requirements.txt
	pip3 install ./nyanshell

nyansat:
	mpfshell -n -c "open ser:$(SERIAL); mput nyansat/*\.py *\.py"

