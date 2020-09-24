EESchema Schematic File Version 4
EELAYER 30 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 7 9
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
L Connector_Generic:Conn_01x05 P2
U 1 1 5F924E3E
P 5250 3750
F 0 "P2" H 5168 3325 50  0000 C CNN
F 1 "Header_5" H 5168 3416 50  0000 C CNN
F 2 "Connector_PinHeader_1.00mm:PinHeader_1x05_P1.00mm_Vertical" H 5250 3750 50  0001 C CNN
F 3 "~" H 5250 3750 50  0001 C CNN
	1    5250 3750
	-1   0    0    1   
$EndComp
Text GLabel 6300 3550 2    50   BiDi ~ 0
BNO_RESET
Wire Wire Line
	5450 3550 6300 3550
Text GLabel 6300 3650 2    50   BiDi ~ 0
I2C_SDA
Text GLabel 6300 3750 2    50   BiDi ~ 0
I2C_SCL
Wire Wire Line
	5450 3650 6300 3650
Wire Wire Line
	5450 3750 6300 3750
$Comp
L power:VCC #PWR0172
U 1 1 5F925E97
P 6900 3750
F 0 "#PWR0172" H 6900 3600 50  0001 C CNN
F 1 "VCC" H 6915 3923 50  0000 C CNN
F 2 "" H 6900 3750 50  0001 C CNN
F 3 "" H 6900 3750 50  0001 C CNN
	1    6900 3750
	1    0    0    -1  
$EndComp
Wire Wire Line
	5450 3850 6900 3850
Wire Wire Line
	6900 3850 6900 3750
$Comp
L power:GND #PWR0173
U 1 1 5F92625D
P 6000 4100
F 0 "#PWR0173" H 6000 3850 50  0001 C CNN
F 1 "GND" H 6005 3927 50  0000 C CNN
F 2 "" H 6000 4100 50  0001 C CNN
F 3 "" H 6000 4100 50  0001 C CNN
	1    6000 4100
	1    0    0    -1  
$EndComp
Wire Wire Line
	5450 3950 6000 3950
Wire Wire Line
	6000 3950 6000 4100
Text Notes 3950 3900 0    50   ~ 0
I2C_SCL_IO26\nI2C_SCL_IO27
$EndSCHEMATC
