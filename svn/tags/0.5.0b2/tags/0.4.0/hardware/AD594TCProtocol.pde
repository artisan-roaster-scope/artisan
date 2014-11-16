// AD594TC.pde
//
// output on serial port: Analog channels from AD594.
// reply to command with protocol "CCaaaa"

const int analogInPinBT = A0;  // Analog input pin that the AD594/BT TC is connected to
const int analogInPinET = A1;  // Analog input pin that the AD594/ET TC is connected to

// Functions
void logger(char mode)
  // print temperatures to serial
{
  int tempBT;
  int tempET;   

  float voltageBT = (analogRead(analogInPinBT) * 5000.0) / 1024.0;
  float voltageET = (analogRead(analogInPinET) * 5000.0) / 1024.0;
  
  // the AD594 output is not strictly 10mV/deg
  // this formula is much closer to the truth
  float celsiusBT = voltageBT / (10.0 + ((0.5 / 2732.0) * voltageBT));
  float celsiusET = voltageET / (10.0 + ((0.5 / 2732.0) * voltageET));   
  
  // return temperature in requested unit
  if (mode == 'C'){
    tempBT = celsiusBT;
    tempET = celsiusET;   
  }
  else if (mode == 'F')
  {
    tempBT = (celsiusBT * 9/5) + 32;
    tempET = (celsiusET * 9/5) + 32; 
  }
  else
   {
    tempBT = 0;
    tempET = 0; 
  }

  Serial.print("0,");      // Ambient temp (we don't know)
  Serial.print(tempBT);    // BT
  Serial.print(",");   
  Serial.print(tempET);    // ET
  Serial.print("\n");
};


// MAIN
//
void setup()
{
  delay(100);
  Serial.begin(19200);
  Serial.flush();
}

// -----------------------------------------------------------------

// -----------------------------------------------------------------
void loop()
{
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
        logger(cmd1); // output results to serial port
    }
}
