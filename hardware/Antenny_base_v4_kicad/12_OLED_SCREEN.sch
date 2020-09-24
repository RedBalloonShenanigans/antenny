EESchema Schematic File Version 4
EELAYER 30 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 9 9
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
L Connector_Generic:Conn_01x04 P3
U 1 1 5F929FC0
P 5600 3400
F 0 "P3" H 5600 3650 50  0000 C CNN
F 1 "Header_4" H 5500 3100 50  0000 C CNN
F 2 "Connector_PinHeader_1.00mm:PinHeader_1x04_P1.00mm_Vertical" H 5600 3400 50  0001 C CNN
F 3 "~" H 5600 3400 50  0001 C CNN
	1    5600 3400
	-1   0    0    -1  
$EndComp
$Comp
L power:GND #PWR0176
U 1 1 5F92A914
P 6300 3100
F 0 "#PWR0176" H 6300 2850 50  0001 C CNN
F 1 "GND" H 6305 2927 50  0000 C CNN
F 2 "" H 6300 3100 50  0001 C CNN
F 3 "" H 6300 3100 50  0001 C CNN
	1    6300 3100
	1    0    0    -1  
$EndComp
Wire Wire Line
	5800 3300 5800 2900
Wire Wire Line
	5800 2900 6300 2900
Wire Wire Line
	6300 2900 6300 3100
$Comp
L power:VCC #PWR0177
U 1 1 5F92AC85
P 6050 3300
F 0 "#PWR0177" H 6050 3150 50  0001 C CNN
F 1 "VCC" H 6065 3473 50  0000 C CNN
F 2 "" H 6050 3300 50  0001 C CNN
F 3 "" H 6050 3300 50  0001 C CNN
	1    6050 3300
	1    0    0    -1  
$EndComp
Wire Wire Line
	6050 3400 6050 3300
Wire Wire Line
	5800 3400 6050 3400
Text GLabel 6050 3500 2    50   BiDi ~ 0
I2C_SCL4
Wire Wire Line
	5800 3500 6050 3500
Text GLabel 6050 3600 2    50   BiDi ~ 0
I2C_SDA4
Wire Wire Line
	5800 3600 6050 3600
Text Notes 4900 3450 2    50   ~ 0
I2C_SCL4_IO19\nI2C_SDA4_IO18
$EndSCHEMATC
