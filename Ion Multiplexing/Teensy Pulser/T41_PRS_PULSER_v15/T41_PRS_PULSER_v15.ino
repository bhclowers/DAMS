

/*******************************************************
 * 
 * 
 * 
 * 
 * 
 * 
 * 
 * 
   Teensy 4.1 Synchronized Pulser
   BHC 07/19/2022
   Small Modifications by CNN to adapt different pin configurations

   NOTE:  This is a work in progress...use at your own risk.

          Combined with the compansion jupyter notebook, this code for a Teensy 4.1, provides a means to syncrhonize
          the delivery of the element within an arbitrary pulses sequence with an external clock. In this example case,
          a pseudo random sequence (PRS) designed for a Hadamard experiment is used. In short, this code reads a very simple
          csv containing your target pulse sequence from the SD card and with each tick of the clock changes the value 
          of an output pin that is mapped onto your PRS. The rate at which the sequence is output is directly linked to 
          sampling period set by the user.  For example, if the sampling period is 10 us and the sequence is 100 element long,
          the sequence will repeat for the user specified number of times every 1 ms. You must adjust these variables to fit your
          experiment. 

          Much of the variables and selection of the pulse sequence is exposed via the terminal commands.  If the unit gets into
          a funky state, reset the unit. 

          BTW, as of 2022, the Teensy 4.1 is a blazing fast microcontroller for less than $40 USD.  600 MHz processer!

          If you need extended memory for your pulse sequence, consider buying the addon RAM modules to boost the Teensy 
          memory to 16 MB.  

          Helpful/Informative Links:
          
          https://forum.pjrc.com/threads/60299-1-MSPS-on-a-T4-Is-this-possible/page2
          12-bit conversion, High Speed ADC clock, Medium Speed Sampling: 987,354 samples/second
          12-bit conversion, Very High Speed ADC clock, High Speed Sampling: 1,172,903 samples/second
          12-bit conversion, Very High Speed ADC clock, Very High Speed Sampling: 1,339,177 samples/second
          8-bit conversion, Very High Speed ADC clock, Very High Speed Sampling: 1,875,806 samples/second

          External Memory Usage:
          https://forum.pjrc.com/threads/63973-Using-PSRAM-Buffer-for-saving-arrays-before-serial-printing?highlight=PSRAM+Buffer

          Hooking up WIFI -- Not clear on the strategy -- tried and was unsuccessul with the listed hardware
          Ideally this could be done using wifi so the unit could be floated. 
          https://forum.pjrc.com/threads/27850-A-Guide-To-Using-ESP8266-With-TEENSY-3


          TODO: 
            Standardize Message/Error Flag

            Dump to SD Card
            Expose SD Card to WIFI or USB
            WIFI
            
            altium board pin key:

            Pin 5: delay; goes to 1 fiber optic
            Pin 7: In Clock to SMA closest to Fiber optics and 
            Pin 0- goes to Pin 4 from the modulemaster
            Pin 12 SMA closest to end of the board
            Pin 3: Out 2 goes to 2 fiber optics in middle
            Pin 9: goes to middle SMA
      
            
***************************************************************/
#include <ADC.h>
#include <SD.h>
#include <SPI.h>

File root;
File seqFile;

IntervalTimer PulserTimer;

//External Memory Stuff
extern "C" uint8_t external_psram_size;

//original pins below: 1,3,6

const int timerPin  = 1;//heartbeat and way too fast
const int pulsePin = 7;//digitizer triger 7 or 9
const int prsPin = 5; //sequence output change to 3 for 2, 5 for one

// MARKHI and MARKLO are used to observe timing on oscilloscope
#define  MARKHI digitalWriteFast(timerPin, HIGH);
#define  MARKLO digitalWriteFast(timerPin, LOW);

#define  PULSEHI digitalWriteFast(pulsePin, HIGH);
#define  PULSELO digitalWriteFast(pulsePin, LOW);

#define  PRSHI digitalWriteFast(prsPin, HIGH);
#define  PRSLO digitalWriteFast(prsPin, LOW);

const int ledPin = 13;
#define  LEDHI digitalWriteFast(ledPin, HIGH);
#define  LEDLO digitalWriteFast(ledPin, LOW);


// 6240 at 4 us is 25 ms length of IMS spectrum
uint32_t DAQMAX = 300;//This is your target value for collection, user defined in usec. //5040 CNN 2/18/22
uint16_t samplePeriod = 1;//value in microseconds, 5 us or 1/0.000005 Hz or 200000 sps; Changed default to 1usec to match HiKE defaults CNN 02/18/22

//A larger array than needed to allocated. The timing is synchronized
//by the fastest process (i.e. ADC sampling). 
//With a 16 bit integer there is a range from 0-65535
//With an ADC resolution of 12 there is a range of 0-4096 for each reading
//This means you can have a maximum of 16 averages per spectral range and then
//you need to move to the next range in the buffer.
//Moved array to 32 bit which allows for up to >1E6 averages or sums

//Data Container
#define SPECMAX 1000000
//Maximum number of averages is arbitrary and limited based upon how long you expect each buffer fill to take
#define MAXREPEATS 10000

//EXTMEM uint32_t prsBuffer[SPECMAX];
EXTMEM int prsBuffer[SPECMAX];
volatile uint32_t prsIndex;
//parse data vals
volatile uint32_t prsLength = 0;
uint32_t arrPointer = 0;       //array pointer


volatile bool doneFlag = false;
volatile bool sentflag = false;

//Sequence Repeat and Indexing Variables
//volatile uint32_t curState = 0; 
volatile byte curState = 0; 
volatile uint32_t numRepeats = 1000;
volatile uint32_t curRepeat;

//Pulsing Variables
uint16_t pulseCount = 1; //12 at 4 us is 48 us; initially 100; 
uint16_t pulseMax = 10000; //arbitrary right now
volatile bool pulseEnable = false;

const int chipSelect = BUILTIN_SDCARD;

volatile uint16_t curFileNum = 0;
volatile uint16_t selFileNum = 0;
volatile uint16_t fileNum = 0;
volatile uint16_t maxFiles = 0;

String targetFileName;

String blank = String("");
String inStr = blank;    // A string to hold incoming commands

void setup() {
  // put your setup code here, to run once:
  while (!Serial) {}
  Serial.begin(9600);

  Serial.print("Initializing SD card...");
  if (!SD.begin(chipSelect)) {
    Serial.println("initialization failed!");
    return;
  }
  Serial.println("initialization done.");

  uint8_t size = external_psram_size;
  Serial.printf("EXTMEM Memory Available, %d Mbyte\n", size);

  //LED Control
  pinMode(ledPin, OUTPUT);
  
  //Pulse Setup
  pinMode(timerPin, OUTPUT);
  pinMode(prsPin, OUTPUT);
  pinMode(pulsePin, OUTPUT);  

  delay(2000);
  memset(prsBuffer, 0, sizeof(prsBuffer));

  prompt();

  

  
}
void loop() {
  while (Serial.available()){
    serialEvent();
  }
  
}


//Functions for Serial Input
// Show help menu
void usage() {
  Serial.println("\n\nCommand Set:\n");
  
  Serial.println("  P<value>  Pulse Period (Multiples of sampling period)");//Done
  Serial.println("  S<value>  Sampling Period (Integer in microseconds)");//Done
  Serial.println("  A<value>  Number of Repeats ");//Done
  Serial.println("  M<value>  Maximum number of data points per buffer (Max: 25000). More are possible, contact Clowers");//DONE
  Serial.println("  F<value>  Load file into memory for pulsing, Integer value is the file designation as listed by sending `L`");
  
  Serial.println("  L         List files on SD");
  Serial.println("  C         Clear Buffers");//DONE
  Serial.println("  R         Run, start output PRS cycle");//Done
  Serial.println("  X         Show Settings");//Done
  Serial.println("  H or ?    This message");//Done
  Serial.println("  O         Give fiber optic output pin");//may want a different command to change this on the fly, but probably not. More for troublshooting
  Serial.println("");
}

// Display the internals
void showSettings() {
  Serial.println("");
  Serial.println("");
  Serial.print("Sampling Period (us): ");
  Serial.print("\t");
  Serial.println(samplePeriod);
  
  Serial.print("Pulse Width in sampling cycles: ");
  Serial.print("\t");
  Serial.println(pulseCount);
  //Serial.println("Multiply Sampling Period by Pulse Cycles for actual width in us");

uint16_t tempTotWidth= samplePeriod*pulseCount;
Serial.print("Actual Pulse width in us: ");
Serial.print("\t");
Serial.println(tempTotWidth);

  Serial.print("Number of Repeats: ");
  Serial.print("\t");
  Serial.println(numRepeats);

  Serial.print("Maximum Number of Data Points per Spectrum: ");
  Serial.print("\t");
  Serial.println(DAQMAX);
  
}

// Show prompt and flush input
void prompt() {
  Serial.println("\nTeensy 4.1 PRS Widget");
  Serial.println("Go Cougs!\n");
  inStr = blank;
}

// Process a byte of command input when it shows up
void serialEvent() {
  static unsigned int op = 0;
  static int inData = 0;
//  long tmp;

  // get the new byte:
  inData = Serial.read();
  //Uncomment if you want an echo
//  Serial.write(inData);
//  Serial.println("");

  // On a carriage return we want to process the full message
  // otherwise we just keep scanning/buffering.
  if (inData != 13) {    // Carriage return
    inStr += String(char(inData));
    return;
  }

  // No command given
  if (inStr.length() == 0) {
    inStr = blank;
    return;
  }

  inStr.toUpperCase();

  op = inStr.charAt(0);
  switch (op) {
  case 72:    // H
  case 63:    // ?
    usage();
    inStr = blank;
//    prompt();
    return;
  case 88:    // X
    showSettings();
    inStr = blank;
    return;
  case 82:    // R
    SendSeq();
    inStr = blank;
    return;
  
  case 67:    // C
    memset(prsBuffer, 0, sizeof(prsBuffer));
    inStr = blank;
    return;
    
    return;

    
case 79: //O for Optic. Will Tell which pin is selected to give output based on gating needs (one or 2) CNN 08/03/2022
if (prsPin==3){
Serial.println(" ");
Serial.println("  2 Fiber optic outputs closest to SMAs selected");
 Serial.println("  Ready to use for FT");
}

else if(prsPin==5){
Serial.println(" ");
Serial.println("  1 Fiber optic output closest to USB selected");
 Serial.println("  Ready to use for PRS");
}

else{
Serial.println(" ");
Serial.println("  Incorrect output pin selected for fiber optic");
 Serial.println("  Request Ignored...");
}

inStr = blank;
return;
  case 80:    // P
    // Pulse Width in multiples of the sampling period
    uint16_t tempPulseCount; //12 at 4 us is 48 us
    tempPulseCount = inStr.substring(1).toInt();
    if(tempPulseCount<1){//changed from <= to <1; CNN 2/18/22
      Serial.println(" ");
      Serial.println("  Invald Request: Pulse Width is < 1");
      Serial.println("  Request Ignored...");
    }
    else if(tempPulseCount>pulseMax){
      Serial.println(" ");
      Serial.println("  Invald Request: Pulse Width too large");
      Serial.println("  Request Ignored...");
    }
    else{
      pulseCount = tempPulseCount;
    }
    showSettings();
    inStr = blank;
    return;
  case 83:    // S
    // Sampling Period in microseconds 
    uint16_t tempSP;
    tempSP = inStr.substring(1).toInt();
    if(tempSP>=2000){  //Arbitrary at this stage
      Serial.println(" ");
      Serial.println("  Invald Request: Sampling Period is too large");
      Serial.println("  Request Ignored...");
    }
    else if(tempSP<1){//changed from <= to <1; CNN 2/18/22
      Serial.println(" ");
      Serial.println("  Invald Request: Pulse Period is less than 1");
      Serial.println("  Request Ignored...");
    }
    else{
      samplePeriod = tempSP;
    }
    showSettings();
    inStr = blank;
    return;
 
  case 65:    // A
    // SET Number of Averages or Repeats
    uint16_t tempNA;
    tempNA = inStr.substring(1).toInt();
    if(tempNA>=MAXREPEATS){  
      Serial.println(" ");
      Serial.println("  Invald Request: Number of Averages is too large");
      Serial.println("  Request Ignored...");
    }
    else if(tempNA<1){
      Serial.println(" ");
      Serial.println("  Invald Request: Number of Averages is less than 1");
      Serial.println("  Request Ignored...");
    }
    else{
      numRepeats = tempNA;
    }
    showSettings();
    inStr = blank;
    return;

  case 77:    // M
    // SET Number of Data Points to Collect
    uint32_t tempMP;
    tempMP = inStr.substring(1).toInt();
    if(tempMP>=SPECMAX){  //Fixed to maximum length of each buffer
      Serial.println(" ");
      Serial.println("  Invald Request: Number of points is too large");
      Serial.println("  Request Ignored...");
    }
    else if(tempMP<1){
      Serial.println(" ");
      Serial.println("  Invald Request: Number of points is less than 1");
      Serial.println("  Request Ignored...");
    }
    else{
      DAQMAX = tempMP;
    }
    showSettings();
    inStr = blank;
    return;
    
  case 76:    // L List Files
    root = SD.open("/");
    
    parseDirectory(root, 1);
    inStr = blank;
    return;

  case 70:    // F  //83 is S
    // Select file based upon a number
    uint16_t tempFileNum; 
    tempFileNum = inStr.substring(1).toInt();
    if(tempFileNum<1){
      Serial.println(" ");
      Serial.println("  Invald Request: File selected is < 1");
      Serial.println("  Request Ignored...");
    }
    else if(tempFileNum>=maxFiles+1){
      Serial.println(" ");
      Serial.println("  Invald Request: File number is too too large");
      Serial.println("  Request Ignored...");
    }
    else{
      selFileNum = tempFileNum;
//      Serial.print("Selected File: ");
//      Serial.println(selFileNum);
      getFile(root, selFileNum);
      readCSV(targetFileName);
      printBuffer();
      
    }
    
    inStr = blank;
    return;
     
  default:
    Serial.println("   Bad Command (" + inStr + ").  Type ? for help");
    inStr = blank;
    return;
    
  }
}


/*****************************************************
 * This is the intervaltimer interrupt handler
 ******************************************************/
void PRSChore(void){

  MARKHI;
  if(prsIndex < DAQMAX){  // sample until end of buffer    
    curState = prsBuffer[prsIndex];
    if(curState){
      PRSHI;
    }
    else{
      PRSLO;
    }
    
    prsIndex++;
  }
  MARKLO;
  // ADMARHI to ADMARKLO takes about 180nS at 600MHz

  //Pulsing Control
  if(pulseEnable){
    if(prsIndex==1){ //Setting to 1, because we counted up from 0. 
      PULSEHI;
    }
    
    if(prsIndex>pulseCount){
      PULSELO;
      pulseEnable = false;
    }
  }
  if(prsIndex%DAQMAX == 0){//case where the target number of acquisitions has completed
    
    prsIndex = 0;
    pulseEnable = true;
    curRepeat+=1;
//    if(curRepeat == numRepeats){
//      curRepeat = 0;//reset averages for a given segment
//    }
  }
}

/******************************************************
   Read MAXSAMPLES from ADC at user-defined intervals
   set in microseconds
   Store the results in adcbuffer
 *****************************************************/
void SendSeq(void) {
//  Need to reset memory here?
//  Serial.println("Reading ADC Samples");
  prsIndex = 0;
  curRepeat = 0;//reset counter so the system can repeat.
  pulseEnable = true;
  doneFlag = false;
  LEDHI;

  PulserTimer.begin(PRSChore,samplePeriod);  // start timer at 4 microsecond intervals
  
  while (curRepeat < numRepeats);

  PULSELO;
  PRSLO;
  PulserTimer.end();  // stop the timer
  doneFlag = true;
  Serial.println("Number of cycles");
  Serial.print(curRepeat);
  Serial.print(" @ ");
  Serial.print(DAQMAX);
  Serial.println(" samples each");
  Serial.println("!");
  LEDLO;
}


void parseDirectory(File dir, bool printOut) {
   curFileNum = 0;
   maxFiles = 0;
   while(true) {
     
     File entry =  dir.openNextFile();
     if (! entry) {
       // no more files
       //Serial.println("**nomorefiles**");
       break;
     }

     if(!entry.isDirectory()){
       curFileNum++; 
       if(printOut){
         Serial.print("File Num: ");
         Serial.print(curFileNum);
         Serial.print('\t');
         Serial.print(entry.name());
         Serial.println();
       }
       
  
     }
     entry.close();
   }
   maxFiles = curFileNum;
//   Serial.print("Max Files: ");
//   Serial.println(maxFiles);
}

void getFile(File dir, uint16_t targetFileNum) {
   
   root = SD.open("/");
   parseDirectory(root, 0);
   dir = SD.open("/");
   maxFiles+=1;
   
   curFileNum = 0;
   while(true){
     File entry =  dir.openNextFile();
     if (! entry) {
       break;
     }

     if(!entry.isDirectory()){
       curFileNum++; 
       if(targetFileNum == curFileNum){
         Serial.print(entry.name());
         Serial.println();
         targetFileName = entry.name();
       }
        
     }
     entry.close();
    }

  }


void printBuffer(){
  //cycle through data array
  for(uint32_t i = 0; i < prsLength; i++){ 
    Serial.println(prsBuffer[i]);
//    Serial.print(", ");
  }

  Serial.println();
  Serial.println(prsLength);
  Serial.println();
  Serial.println("--------------------------");  
}

void readCSV(String fileName){
  //https://forum.arduino.cc/t/read-csv-or-txt-from-sd-card-into-string-or-array/225446/9
  //https://forum.arduino.cc/t/opening-a-variable-filename-from-sd-card/362083/2
  
  char fileNameChar[fileName.length()];                       //convert to char Array
  fileName.toCharArray(fileNameChar, (fileName.length()+1));  //convert to char Array
  
  //Read file
  seqFile = SD.open(fileNameChar);
  
// re-open the file for reading:
  if (!seqFile) {
    Serial.println("Error opening: ");
    Serial.println(fileName);
    return;
  }

  // read from the file until there's nothing else in it:
  String l_line;
  l_line.reserve(128); //Avoids heap memory fragmentation
                       //Reserve space for your longest expected data line
  arrPointer = 0;
  while (seqFile.available()) {
    l_line = seqFile.readStringUntil('\n');
    l_line.trim();
    if (l_line != "") {
      int l_start_posn = 0;
      while (l_start_posn != -1){
        prsBuffer[arrPointer] = ENDF2(l_line,l_start_posn,',').toInt();
      }
//        Serial.println(ENDF2(l_line,l_start_posn,',').toInt());;
      arrPointer++;
      
        
      //
    } //skip blank (NULL) lines
//    Serial.println(datatemp);
  }//Read the file line by line
  prsLength = arrPointer;
  seqFile.close(); 
}

String ENDF2(String &p_line, int &p_start, char p_delimiter) {
//EXTRACT NEXT DELIMITED FIELD VERSION 2
//Extract fields from a line one at a time based on a delimiter.
//Because the line remains intact we dont fragment heap memory
//p_start would normally start as 0
//p_start increments as we move along the line
//We return p_start = -1 with the last field

  //If we have already parsed the whole line then return null
  if (p_start == -1) {
    return "";
  }

  int l_start = p_start;
  int l_index = p_line.indexOf(p_delimiter,l_start);
  if (l_index == -1) { //last field of the data line
    p_start = l_index;
    return p_line.substring(l_start);
  }
  else { //take the next field off the data line
    p_start = l_index + 1;
    return p_line.substring(l_start,l_index); //Include, Exclude
  }
}
