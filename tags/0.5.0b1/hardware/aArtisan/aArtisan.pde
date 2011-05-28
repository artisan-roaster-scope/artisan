// aArtisan.pde
// ------------

// This sketch responds to a "READ\n" command on the serial line (Artisan 0.3.x)
// or "RF2000\n" or "RC2000\n" on the serial line (Artisan 0.4.x)
// and outputs ambient temperature, bean temperature, environmental temperature
//
// Written to support the Artisan roasting scope //http://code.google.com/p/artisan/

// *** BSD License ***
// ------------------------------------------------------------------------------------------
// Copyright (c) 2011, MLG Properties, LLC
// All rights reserved.
//
// Contributor:  Jim Gallt
//
// Redistribution and use in source and binary forms, with or without modification, are 
// permitted provided that the following conditions are met:
//
//   Redistributions of source code must retain the above copyright notice, this list of 
//   conditions and the following disclaimer.
//
//   Redistributions in binary form must reproduce the above copyright notice, this list 
//   of conditions and the following disclaimer in the documentation and/or other materials 
//   provided with the distribution.
//
//   Neither the name of the copyright holder(s) nor the names of its contributors may be 
//   used to endorse or promote products derived from this software without specific prior 
//   written permission.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS 
// OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF 
// MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL 
// THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, 
// SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF 
// SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) 
// HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, 
// OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS 
// SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
// ------------------------------------------------------------------------------------------

#define BANNER_ARTISAN "aARTISAN V1.04"

// Revision history:
// 20110408 Created.
// 20110409 Reversed the BT and ET values in the output stream.
//          Shortened the banner display time to avoid timing issues with Artisan
//          Echo all commands to the LCD
// 20110413 Added support for Artisan 0.4.1
// 20110414 Reduced filtering levels on BT, ET
//          Improved robustness of checkSerial() for stops/starts by Artisan
//          Revised command format to include newline character for Artisan 0.4.x

// this library included with the arduino distribution
#include <Wire.h>

// The user.h file contains user-definable compiler options
// It must be located in the same folder as aArtisan.pde
#include "user.h"

// these "contributed" libraries must be installed in your sketchbook's arduino/libraries folder
#include <TypeK.h>
#include <cADC.h> // MCP3424
#ifdef LCD
#include <cLCD.h> // required only if LCD is used
#endif

// ------------------------ other compile directives
#define MIN_DELAY 300   // ms between ADC samples (tested OK at 270)
#define NCHAN 2   // number of TC input channels
#define TC_TYPE TypeK  // thermocouple type / library
#define DP 1  // decimal places for output on serial port
#define D_MULT 0.001 // multiplier to convert temperatures from int to float

#define MAX_COMMAND 80 // max length of a command string

#ifdef EEPROM_ARTISAN // optional code if EEPROM flag is active
#include <mcEEPROM.h>
// eeprom calibration data structure
struct infoBlock {
  char PCB[40]; // identifying information for the board
  char version[16];
  float cal_gain;  // calibration factor of ADC at 50000 uV
  int16_t cal_offset; // uV, probably small in most cases
  float T_offset; // temperature offset (Celsius) at 0.0C (type T)
  float K_offset; // same for type K
};
mcEEPROM eeprom;
infoBlock caldata;
#endif

#ifdef CELSIUS
boolean Cscale = true;
#else
boolean Cscale = false;
#endif

// class objects
cADC adc( A_ADC ); // MCP3424
ambSensor amb( A_AMB ); // MCP9800
filterRC fT[NCHAN]; // filter for logged ET, BT

// ---------------------------------- LCD interface definition
#ifdef LCD
// LCD output strings
char st1[6],st2[6];
#ifdef LCDAPTER
  #define BACKLIGHT lcd.backlight();
  cLCD lcd; // I2C LCD interface
#else // parallel interface, standard LiquidCrystal
  #define BACKLIGHT ;
  #define RS 2
  #define ENABLE 4
  #define D4 7
  #define D5 8
  #define D6 12
  #define D7 13
  LiquidCrystal lcd( RS, ENABLE, D4, D5, D6, D7 ); // standard 4-bit parallel interface
#endif
#endif
// --------------------------------------------- end LCD interface

// array to store temperatures for each channel
int32_t temps[NCHAN]; //  stored temperatures are divided by D_MULT

// global values
float AT, BT, ET; // ambient, bean, environmental temps

char command[MAX_COMMAND+1]; // input buffer for commands from the serial port

// -------------------------------------
void append( char* str, char c ) { // reinventing the wheel
  int len = strlen( str );
  str[len] = c;
  str[len+1] = '\0';
}

// -------------------------------------
void checkSerial() {  // buffer the input from the serial port
  char c;
  while( Serial.available() > 0 ) {
    c = Serial.read();
    // check for newline, buffer overflow
    if( ( c == '\n' ) || ( strlen( command ) == MAX_COMMAND ) ) { 
      processCommand();
      strcpy( command, "" ); // empty the buffer
    } // end if
    else {
      append( command, c );
    } // end else
  } // end while
}

// -------------------------------------
void processCommand() {  // a newline character has been received, so process the command
#ifdef LCD
    lcd.setCursor( 0, 1 ); // echo all commands to the LCD
    lcd.print( command );
#endif
  if( ! strcmp( command, "RF2000" ) ) { // command received, read and output a sample
    Cscale = false;
    logger();
    return;
  }
  if( ! strcmp( command, "RC2000" ) ) { // command received, read and output a sample
    Cscale = true;
    logger();
    return;
  }
  if( ! strcmp( command, "READ" ) ) { // legacy code to support Artisan 0.3.4
    logger();
    return;
  }
}

// ----------------------------------
void checkStatus( uint32_t ms ) { // this is an active delay loop
  uint32_t tod = millis();
  while( millis() < tod + ms ) {
    checkSerial();
    // add future code here to detect LCDapter button presses, etc.
  }
}

// ----------------------------------------------------
float convertUnits ( float t ) {
  if( Cscale ) return F_TO_C( t );
  else return t;
}

// ------------------------------------------------------------------
void logger()
{
// print ambient
  Serial.print( convertUnits( AT ), DP );
  Serial.print( "," );
// print BT
  Serial.print( convertUnits( BT ), DP );
  Serial.print( "," );
// print ET
  Serial.println( convertUnits( ET ), DP );
}

// --------------------------------------------------------------------------
void get_samples( int nchan ) // this function talks to the amb sensor and ADC via I2C
{
  int32_t v;
  TC_TYPE tc;
  float tempF;
  
  for( int j = 0; j < nchan; j++ ) { // one-shot conversions on both chips
    adc.nextConversion( j ); // start ADC conversion on channel j
    amb.nextConversion(); // start ambient sensor conversion
    checkStatus( MIN_DELAY ); // give the chips time to perform the conversions
    amb.readSensor(); // retrieve value from ambient temp register
    v = adc.readuV(); // retrieve microvolt sample from MCP3424
    tempF = tc.Temp_F( 0.001 * v, amb.getAmbF() ); // convert uV to Celsius
    v = round( tempF / D_MULT ); // store results as integers
    AT = amb.getAmbF();
    temps[j] = fT[j].doFilter( v ); // apply digital filtering for display/logging
  }
  BT = 0.001 * temps[0];
  ET = 0.001 * temps[1];
};

#ifdef LCD
// --------------------------------------------
void updateLCD() {
  
 // AT
  int it01 = round( convertUnits( AT ) );
  if( it01 > 999 ) 
    it01 = 999;
  else
    if( it01 < -999 ) it01 = -999;
  sprintf( st1, "%4d", it01 );
  lcd.setCursor( 0, 0 );
  lcd.print("AMB:");
  lcd.print(st1);

  // BT
  it01 = round( convertUnits( BT ) );
  if( it01 > 999 ) 
    it01 = 999;
  else
    if( it01 < -999 ) it01 = -999;
  sprintf( st1, "%4d", it01 );
  lcd.setCursor( 9, 0 );
  lcd.print("BT:");
  lcd.print(st1);

  // ET
  int it02 = round( convertUnits( ET ) );
  if( it02 > 999 ) it02 = 999;
  else if( it02 < -999 ) it02 = -999;
  sprintf( st2, "%4d", it02 );
  lcd.setCursor( 9, 1 );
  lcd.print( "ET:" );
  lcd.print( st2 ); 
  
  lcd.setCursor( 0, 1 );
  lcd.print( "         ");
}
#endif

// ------------------------------------------------------------------------
// MAIN
//
void setup()
{
  delay(100);
  Wire.begin(); 
  Serial.begin(BAUD);
  amb.init( AMB_FILTER );  // initialize ambient temp filtering

#ifdef LCD
  lcd.begin(16, 2);
  BACKLIGHT;
  lcd.setCursor( 0, 0 );
  lcd.print( BANNER_ARTISAN ); // display version banner
#ifdef CELSIUS
  lcd.print( " C");
#else
  lcd.print( " F");
#endif // Celsius
#endif // LCD

#ifdef EEPROM_ARTISAN
  // read calibration and identification data from eeprom
  if( eeprom.read( 0, (uint8_t*) &caldata, sizeof( caldata) ) == sizeof( caldata ) ) {
    adc.setCal( caldata.cal_gain, caldata.cal_offset );
    amb.setOffset( caldata.K_offset );
  }
  else { // if there was a problem with EEPROM read, then use default values
    adc.setCal( CAL_GAIN, UV_OFFSET );
    amb.setOffset( AMB_OFFSET );
  }   
#else
  adc.setCal( CAL_GAIN, UV_OFFSET );
  amb.setOffset( AMB_OFFSET );
#endif

  fT[0].init( BT_FILTER ); // digital filtering on BT
  fT[1].init( ET_FILTER ); // digital filtering on ET

#ifdef LCD
  delay( 800 );
  lcd.clear();
#endif

}

// -----------------------------------------------------------------
void loop()
{
  get_samples( NCHAN );
  
#ifdef LCD
  updateLCD();
#endif

  checkSerial(); // Has a command been received?
}

