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

// Revision history:
// 20110408 Created.
// 20110409 Reversed the BT and ET values in the output stream.
//          Shortened the banner display time to avoid timing issues with Artisan
//          Echo all commands to the LCD
// 20110413 Added support for Artisan 0.4.1
// 20110414 Reduced filtering levels on BT, ET
//          Improved robustness of checkSerial() for stops/starts by Artisan
//          Revised command format to include newline character for Artisan 0.4.x

// The user.h file contains user-definable compiler options
// It must be located in the same folder as aArtisan.pde
//#include <Wire.h>
#include "user.h"
//#include <TypeK.h>
//#include <cADC.h> // MCP3424

// ------------------------ other compile directives
#define DP 1  // decimal places for output on serial port

#define MAX_COMMAND 80 // max length of a command string

boolean Cscale = true; // Default for AD594

const int analogInPinBT = A0;  // Analog input pin that the AD594/BT TC is connected to
const int analogInPinET = A1;  // Analog input pin that the AD594/ET TC is connected to

// global values
float BT, ET; // Bean, environmental temps

char command[MAX_COMMAND+1]; // input buffer for commands from the serial port

// -------------------------------------
void append( char* str, char c ) { // reinventing the wheel
  int len = strlen( str );
  str[len] = c;
  str[len+1] = '\0';
}

// ----------------------------------------------------
float convertUnits ( float t ) {
  if( Cscale ) return t;
  else return ((t* 9/5) + 32);
}

// ------------------------------------------------------------------
void logger()
{
  // print ambient
  Serial.print("0");      // Ambient temp (we don't know)
  Serial.print( "," );
  // print BT
  Serial.print( convertUnits( BT ), DP );
  Serial.print( "," );
  // print ET
  Serial.println( convertUnits( ET ), DP );
}

// -------------------------------------
void processCommand() {  // a newline character has been received, so process the command
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

// ----------------------------------
void checkStatus( uint32_t ms ) { // this is an active delay loop
  uint32_t tod = millis();
  while( millis() < tod + ms ) {
    checkSerial();
    // add future code here to detect LCDapter button presses, etc.
  }
}

// --------------------------------------------------------------------------
void get_samples() // this function talks to the amb sensors
{
  int tempBT;
  int tempET;   

  float voltageBT = (analogRead(analogInPinBT) * 5000.0) / 1024.0;
  float voltageET = (analogRead(analogInPinET) * 5000.0) / 1024.0;

  // the AD594 output is not strictly 10mV/deg
  // this formula is much closer to the truth
  BT = voltageBT / (10.0 + ((0.5 / 2732.0) * voltageBT));
  ET = voltageET / (10.0 + ((0.5 / 2732.0) * voltageET));
};

// ------------------------------------------------------------------------
// MAIN
//
void setup()
{
  delay(100);
  Serial.begin(BAUD);
}

// -----------------------------------------------------------------
void loop()
{
  get_samples();
  checkSerial(); // Has a command been received?
}


