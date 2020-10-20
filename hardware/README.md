# RBS Antenny Board 

If you want make your life a little simpler, we have a custom PCB for you! The Antenny board was designed and assembled by Red Balloon Security and you the ability to plug and play the NyanSat basic station with one single board and no complex wiring. Antenny combines the EPS32 (with Bluetooth and WIFI support), a 16 channel PWM driver, and a motor driver with a maximum output of maximum 27W at 6V. The RBS Antenny board can easily handle the movement control of NyanSat antenna gimbal, and you can load your own custom code to adjust it however you like. The onboard reserved I2C channel connectors allow you to extend the basic NyanSat setup with an RBS custom made IMU module, OLED screen and GPS module. After DEF CON, you can even repurpose the board for your future projects requiring microcontrollers and motor drivers.

The RBS Antenny board is designed using Altium Designer and Assembled by in-house pick and place machine in Manhattan, New York. Hardware design will be open sourced through our [GitHub repo](https://github.com/RedBalloonShenanigans/antenny/tree/master/hardware), and you can buy them in our store [link[. Feel free to check it out or make your own!  

## required items that are NOT included in package

- [Jumper Wires](https://www.amazon.com/EDGELEC-Breadboard-Optional-Assorted-Multicolored/dp/B07GD2BWPY/)
- [pin headers](https://www.amazon.com/MCIGICM-Header-2-45mm-Arduino-Connector/dp/B07PKKY8BX/)
- Soldering Iron Kit
- Power supply (6v-30v) or lipo battery

## Antenny board hardware setup guide and schematic

- [Setup guide and import updates](https://github.com/RedBalloonShenanigans/antenny/tree/master/hardware/Antenny_board_hardware_setup_guide.pdf)
Antenny V2 and V3 board have the similar pin layout. Please use this Antenny V2 Guide as reference.

- [Antenny V1 Board Schematic](https://github.com/RedBalloonShenanigans/antenny/tree/master/hardware/Antenny_V1_Schematic.pdf)

- [Antenny V2 Board Schematic](https://github.com/RedBalloonShenanigans/antenny/tree/master/hardware/Antenny_V2_Schematic.pdf)

- [Antenny V3 Board Schematic](https://github.com/RedBalloonShenanigans/antenny/tree/master/hardware/Antenny_V3_Schematic.pdf)

- [Antenny V5 Board Schematic](https://github.com/RedBalloonShenanigans/antenny/tree/master/hardware/Antenny_V5_Schematic.pdf)

- [IMU V2 Board Schematic](https://github.com/RedBalloonShenanigans/antenny/tree/master/hardware/IMU_V2_Schematic.pdf)

- [Antenny V3 Board Gerber files and NC Drill files for PCB manufacuture](https://github.com/RedBalloonShenanigans/antenny/tree/master/hardware/Gerber_NC_Drill_Antenna_base_v3)

- [Antenny V5 Board Gerber files and NC Drill files for PCB manufacuture](https://github.com/RedBalloonShenanigans/antenny/tree/master/hardware/Gerber_NC_Drill_Antenna_base_v5)

- [IMU v2 Board Gerber files and NC Drill files for PCB manufacuture](https://github.com/RedBalloonShenanigans/antenny/tree/master/hardware/Gerber_NC_Drill_IMU_standalone_v2)

## Antenny_board folder

These folder contains the RBS Antenny Board Altium Designer source file. 

- Antenna_base_v1

Verison 1.0 of RBS Antenny Board Layout

P6 GND; P5 VCCV6; P4 PWM

- Antenna_base_v2

Verison 2.0 of RBS Antenny Board Layout

- Antenna_base_v3

Verison 3.0 of RBS Antenny Board Layout

## IMU_board folder 

These folder contains the IMU board Altium Designer source file. 

- IMU_board_v1

Verison 1.0 of RBS IMU Board Layout

- IMU_board_v2

Verison 2.0 of RBS IMU Board Layout