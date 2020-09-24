EESchema Schematic File Version 4
EELAYER 30 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 8 9
Title ""
Date ""
Rev ""
Comp ""
Comment1 ""
Comment2 ""
Comment3 ""
Comment4 ""
$EndDescr
$Comp
L Connector_Generic:Conn_01x06 P4
U 1 1 5F927499
P 5550 3450
F 0 "P4" H 5550 3800 50  0000 C CNN
F 1 "Header_6" H 5550 3050 50  0000 C CNN
F 2 "Connector_PinHeader_1.00mm:PinHeader_1x06_P1.00mm_Vertical" H 5550 3450 50  0001 C CNN
F 3 "~" H 5550 3450 50  0001 C CNN
	1    5550 3450
	-1   0    0    -1  
$EndComp
Text GLabel 6200 3250 2    50   BiDi ~ 0
I2C_SDA3
Wire Wire Line
	5750 3250 6200 3250
Text GLabel 6200 3450 2    50   BiDi ~ 0
RXD2
Text GLabel 6200 3550 2    50   BiDi ~ 0
TXD2
Wire Wire Line
	5750 3450 6200 3450
Wire Wire Line
	5750 3550 6200 3550
Text GLabel 6200 3750 2    50   BiDi ~ 0
I2C_SCL3
Wire Wire Line
	5750 3750 6200 3750
$Comp
L power:VCC #PWR0174
U 1 1 5F928149
P 6850 3600
F 0 "#PWR0174" H 6850 3450 50  0001 C CNN
F 1 "VCC" H 6865 3773 50  0000 C CNN
F 2 "" H 6850 3600 50  0001 C CNN
F 3 "" H 6850 3600 50  0001 C CNN
	1    6850 3600
	1    0    0    -1  
$EndComp
Wire Wire Line
	5750 3650 6850 3650
$Comp
L power:GND #PWR0175
U 1 1 5F92893F
P 7150 3750
F 0 "#PWR0175" H 7150 3500 50  0001 C CNN
F 1 "GND" H 7155 3577 50  0000 C CNN
F 2 "" H 7150 3750 50  0001 C CNN
F 3 "" H 7150 3750 50  0001 C CNN
	1    7150 3750
	1    0    0    -1  
$EndComp
Wire Wire Line
	5750 3350 7150 3350
Wire Wire Line
	7150 3350 7150 3750
Wire Wire Line
	6850 3600 6850 3650
Text Notes 4850 3600 2    50   ~ 0
I2C_SCL3_IO23\nI2C_SDA3_IO25\n\nRXD2_IO32\nTXD2_IO33
$EndSCHEMATC
