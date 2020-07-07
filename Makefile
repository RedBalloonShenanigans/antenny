SERIAL=ttyUSB0

.PHONY: all nyanshell nyansat

all: nyanshell nyansat

nyanshell:
	pip3 install -r requirements.txt
	pip3 install .

nyansat:
	mpfshell -n -c "open $(SERIAL); mput nyansat/*\.py *\.py"

