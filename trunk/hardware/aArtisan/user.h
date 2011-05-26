// user.h
//---------
// This file contains user definable compiler directives for aArtisan

// *************************************************************************************
// NOTE TO USERS: the following parameters should be
// be reviewed to suit your preferences and hardware setup.  
// First, load and edit this sketch in the Arduino IDE.
// Next compile the sketch and upload it to the Arduino.

#define EEPROM_ARTISAN // comment this line out if no calibration information stored in 64K EEPROM
//#define CELSIUS // if defined, output is in Celsius units; otherwise Fahrenheit
#define LCD // if output on an LCD screen is desired
#define LCDAPTER // if the I2C LCDapter board is to be used
//#define ARTISAN04x
//#define ARTISAN03x

#define BAUD 19200  // serial baud rate
#define BT_FILTER 10 // filtering level (percent) for BT
#define ET_FILTER 10 // filtering level (percent) for ET
#define AMB_FILTER 70 // 70% filtering on ambient sensor readings

// default values for systems without calibration values stored in EEPROM
#define CAL_GAIN 1.00 // you may substitute a known gain adjustment from calibration
#define UV_OFFSET 0 // you may subsitute a known value for uV offset in ADC
#define AMB_OFFSET 0.0 // you may substitute a known value for amb temp offset (Celsius)


// *************************************************************************************

