# NyanSat

Make your own base station to communicate with satellites!

## Setting Up

These set up procedures expect that your base station is fully assembled and your ESP32 is flashed with Micropython firmware. If not, check the NyanSat website for detailed steps on how to assemble your hardware, plus some tips on avoiding common pitfalls.

### Set up your host environment

NyanShell provides a convenient shell interface to communicate with your NyanSat base station. To install this interface, simply type `make nyanshell` in the project directory.

### Set up your base station environment

Once your host is set up, you can install NyanSat on your ESP32. First, determine which serial port corresponds to your ESP32. Then from the project directory, run `make nyansat SERIAL=<your ESP32 serial port>` to install it on your ESP32.

## Features

### Easy Pin Setup and Profile Management

If your pin configuration is different from the default values, you can easily change to them by running the `setup <profile_name>` command. This command creates a new profile with your given name and switches to it. 

If you have multiple pin configurations on the ESP32, you can switch between them using the `switch_config <profile_name>` command. This command switches to your chosen profile, leaving the original one intact, but not in use.

### Telemetry

The NyanShell interface puts key metrics front and center from your base station. The interface displays the azimuth, elevation, and (if equipped with GPS module) your ground coordinates.

### IMU Calibration Guide (BNO055 specific)

Calibrating IMU's are difficult; the BNO055 is especially tough. NyanShell provides a calibration command to easily poll the calibration status of your BNO055. If the IMU is not calibrated, the command guides you through the process with on screen instructions and real time feedback on the calibration status. To start, simply type `calibrate` into the shell and follow the instructions until your IMU is calibrated.

If you have a predefined configuration with an IMU calibration profile, you can use the profile management commands to load the IMU calibration values.

### Motor Accuracy Plot

Your motor may _tell_ you that it moved a degree, but 

## Dependencies

NyanShell:
- MPFShell
- TUI-DOM

NyanSat:
- Logging
- PCA9685 Adafruit Library
- BNO055 Adafruit Library, adapted for use in Micropython by Peter Hinch
- SSD1306
