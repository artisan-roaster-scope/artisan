// TC4.pde
//
// Sketch to connect TC4 to Artisan
// output on serial port: ambient, T1, T2, T3, T4
// reply to command
//
// See TC4 Project page for contributed libraries and credit 

// this library included with the arduino distribution
#include <Wire.h>

// these "contributed" libraries must be installed in your sketchbook's arduino/libraries folder
#include <TypeK.h>
#include <cADC.h>
#include <PortsLCD.h>
#include <RF12.h> // needed to avoid a linker error :(

#define EEPROM_BRBN // comment out if no calibration information stored in 64K EEPROM

#define BAUD 19200  // serial baud rate
#define BT_FILTER 10 // filtering level (percent) for displayed BT
#define ET_FILTER 10 // filtering level (percent) for displayed ET

// needed for usesr without calibration values stored in EEPROM
#define CAL_GAIN 1.00 // substitute known gain adjustment from calibration
#define UV_OFFSET 0 // subsitute known value for uV offset in ADC
#define AMB_OFFSET 0.0 // substitute known value for amb temp offset (Celsius)

// ambient sensor should be stable, so quick variations are probably noise -- filter heavily
#define AMB_FILTER 70 // 70% filtering on ambient sensor readings

// *************************************************************************************

// ------------------------ other compile directives
#define MIN_DELAY 300   // ms between ADC samples (tested OK at 270)
#define NCHAN 4   // initialize with max number of TC input channels
#define TC_TYPE TypeK  // thermocouple type / library
#define DP 1  // decimal places for output on serial port
#define D_MULT 0.001 // multiplier to convert temperatures from int to float

// --------------------------------------------------------------
// global variables

#ifdef EEPROM_BRBN // optional code if EEPROM flag is active
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

// class objects
cADC adc( A_ADC ); // MCP3424
ambSensor amb( A_AMB ); // MCP9800
filterRC fT[NCHAN]; // filter for displayed/logged temperature channels
filterRC fRise[NCHAN]; // heavily filtered for calculating RoR

PortI2C myI2C (3);
LiquidCrystalI2C lcd (myI2C);

int32_t temps[NCHAN]; //  stored temperatures are divided by D_MULT
int32_t ftemps[NCHAN]; // heavily filtered temps
int32_t ftimes[NCHAN]; // filtered sample timestamps
int32_t flast[NCHAN]; // for calculating derivative
int32_t lasttimes[NCHAN]; // for calculating derivative

// LCD output strings
char smin[3],ssec[3],st1[6],st2[6],sRoR1[7];

// used in main loop
float timestamp = 0;

// --------------------------------------------
void updateLCD( float t1, float t2, float RoR ) {
  // form the timer output string in min:sec format
  int itod = round( timestamp );
  if( itod > 3599 ) itod = 3599;
  sprintf( smin, "%02u", itod / 60 );
  sprintf( ssec, "%02u", itod % 60 );
  lcd.setCursor(0,0);
  lcd.print( smin );
  lcd.print( ":" );
  lcd.print( ssec );
 
  // channel 2 temperature 
  int it02 = round( t2 );
  if( it02 > 999 ) it02 = 999;
  else if( it02 < -999 ) it02 = -999;
  sprintf( st2, "%3d", it02 );
  lcd.setCursor( 11, 0 );
  lcd.print( "ET " );
  lcd.print( st2 ); 

  // channel 1 RoR
  int iRoR = round( RoR );
  if( iRoR > 99 ) 
    iRoR = 99;
  else
   if( iRoR < -99 ) iRoR = -99; 
  sprintf( sRoR1, "%0+3d", iRoR );
  lcd.setCursor(0,1);
  lcd.print( "RoR1:");
  lcd.print( sRoR1 );

  // channel 1 temperature
  int it01 = round( t1 );
  if( it01 > 999 ) 
    it01 = 999;
  else
    if( it01 < -999 ) it01 = -999;
  sprintf( st1, "%3d", it01 );
  lcd.setCursor( 11, 1 );
  lcd.print("BT ");
  lcd.print(st1);
}

// ------------------------------------------------------------------
void logger(char mode)
{
  float t_amb;

  t_amb = amb.getAmbC();

  // return temperature in requested unit
  if (mode == 'C'){
    Serial.print(t_amb, DP );
  }
  else if (mode == 'F')
  {
    Serial.print((t_amb * 9/5) + 32, DP );
  }
  else
   {
    Serial.print(0);
  }
  
  // print temperature, rate for each channel
  for (int i = 0; i < NCHAN; i++) {
    Serial.print(",");

    if (mode == 'C'){
      Serial.print( D_MULT*temps[i], DP);
    }
    else if (mode == 'F')
    {  
      Serial.print((D_MULT*temps[i] * 9/5) + 32, DP );
    }
    else
     {
      Serial.print(0);
    }    
  }
  
  Serial.print("\n");
};

// --------------------------------------------------------------------------
void get_samples() // this function talks to the amb sensor and ADC via I2C
{
  int32_t v;
  TC_TYPE tc;
  float tempC;
  
  for( int j = 0; j < NCHAN; j++ ) { // one-shot conversions on both chips
    adc.nextConversion( j ); // start ADC conversion on channel j
    amb.nextConversion(); // start ambient sensor conversion
    delay( MIN_DELAY ); // give the chips time to perform the conversions
    amb.readSensor(); // retrieve value from ambient temp register
    v = adc.readuV(); // retrieve microvolt sample from MCP3424
    tempC = tc.Temp_C( 0.001 * v, amb.getAmbC() ); // convert to Celsius
    v = round(  tempC / D_MULT ); // store results as integers
    temps[j] = fT[j].doFilter( v ); // apply digital filtering for display/logging
    ftemps[j] =fRise[j].doFilter( v ); // heavier filtering for RoR
  }
};
  
// ------------------------------------------------------------------------
// MAIN
//
void setup()
{
  delay(100);
  Wire.begin(); 
  Serial.begin(BAUD);
  Serial.flush();
  amb.init( AMB_FILTER );  // initialize ambient temp filtering

  lcd.begin(20, 4);
  lcd.backlight();
  
#ifdef EEPROM_BRBN
  // read calibration and identification data from eeprom
  if( eeprom.read( 0, (uint8_t*) &caldata, sizeof( caldata) ) == sizeof( caldata ) ) {
//    Serial.println("# EEPROM data read: ");
//    Serial.print("# ");
//    Serial.print( caldata.PCB); Serial.print("  ");
//    Serial.println( caldata.version );
//    Serial.print("# ");
//    Serial.print( caldata.cal_gain, 4 ); Serial.print("  ");
//    Serial.println( caldata.K_offset, 2 );
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
}

char command[32];

// -----------------------------------------------------------------
void loop()
{
  get_samples(); // retrieve values from MCP9800 and MCP3424
  timestamp = float( millis() ) * 0.001;
  updateLCD( D_MULT*temps[0], D_MULT*temps[1], 0 );  
  
  char cmd0;
  char cmd1;
  char arg0;
  char arg1;
  char arg2;
  char arg3; 

  // protocol is "CCaaaa", two bytes of command, four bytes of args
  if( Serial.available() >= 6 ) {  // command length is 6 bytes
     cmd0 = Serial.read();
     cmd1 = Serial.read();
     arg0 = Serial.read();
     arg1 = Serial.read();
     arg2 = Serial.read();
     arg3 = Serial.read();
   }

  if (cmd0 == 'R') {
     NCHAN = arg0;
     logger(cmd1); // output results to serial port
    }
}
