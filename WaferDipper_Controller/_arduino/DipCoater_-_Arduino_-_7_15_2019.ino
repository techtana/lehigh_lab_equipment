// ******************************************************** //
// ******************************************************** //
// *********************  Definitions  ******************** //
// ******************************************************** //
// ******************************************************** //
#include "TeensyStep.h"


bool newData = false;
bool isAbsTarget = false;
bool isSpecialCmd = false;
constexpr byte numChars = 64; // Arduino RX buffer is set to be 32 bytes. https://forum.arduino.cc/index.php?topic=369658.0
constexpr int numMotor = 2;  // specify the number of motors, use to set up
char receivedChars[numChars]; // Array to store received data
char tempChars[numChars]; // Array to store temporary data
char tempNum[numChars];

int M1_loc = 0;
int M1_speed = 0;
int M2_loc = 0;
int M2_speed = 0;
int wait_time = 0;
int calibArray[numMotor] = {} ;

// Button setup
constexpr int testMotor1 = 11;      // pin for motor 1 calibration
constexpr int testMotor2 = 12;      // pin for motor 2 calibration

// Motors Setup
int bufferdist = 10;
int M1_pitch = 5; // mm per revolution
int M2_pitch = 5; // mm per revolution
int M1_spr = 25000;  // steps per revolution
int M2_spr = 25000;  // steps per revolution
int M1_availableStep = (260-bufferdist)*M1_spr/M1_pitch; // length in millimeters to Steps
int M2_availableStep = (150-bufferdist)*M2_spr/M2_pitch; // length in millimeters to Steps

constexpr int M1_defaultSpeed = 50000; // steps/s (300k max)
constexpr int M2_defaultSpeed = 50000; // steps/s (300k max)
constexpr int M1_defaultAcc = 300000; // steps/s^2 (500k max)
constexpr int M2_defaultAcc = 300000; // steps/s^2 (500k max)

Stepper motor_1(23, 22);  //STEP pin =  23, DIR pin = 22
Stepper motor_2(21, 20);  //STEP pin =  21, DIR pin = 20
StepControl controller;


// ******************************************************** //
// ******************************************************** //
// ********************  Functions  *********************** //
// ******************************************************** //
// ******************************************************** //


void motorOriginCalibration(){
  motor_1.setTargetRel(M1_spr/M1_pitch*300);  // small increment of 1 degree
  motor_1.setMaxSpeed(M1_defaultSpeed);
  controller.moveAsync(motor_1);
  while (digitalRead(testMotor1)){
    /* NOTE:
     * Cannot do a motor-stuck stop b/c the
     * position reading continues as motors
     * stall and not actually stuck. Otherwise,
     * this would be a good idea.
     */
  }
  controller.stop();
  motor_1.setTargetRel(-M1_spr);  // Backward the linear actuator for 1 rotation
  controller.move(motor_1);

  motor_2.setTargetRel(M2_spr/M2_pitch*200);
  motor_2.setMaxSpeed(M2_defaultSpeed);
  controller.moveAsync(motor_2);
  while (digitalRead(testMotor2));
  controller.stop();
  motor_2.setTargetRel(-M2_spr);  // Backward the linear actuator for 1 rotation
  controller.move(motor_2);

  calibArray[0] = motor_1.getPosition();  // return number of steps from motor initiation
  calibArray[1] = motor_2.getPosition();  // return number of steps from motor initiation

  Serial.println(calibArray[0]);
  Serial.println(calibArray[1]);

  Serial.println("<Origin calibration completed>");
}

void safetyStopOrigin(){
  while (not digitalRead(testMotor1) or not digitalRead(testMotor2)){
    controller.stop();
    delay(500);
    // motor_1.setTargetRel(-M1_spr);  // Backward the linear actuator for 1 rotation
    // controller.move(motor_1);
    if(not digitalRead(testMotor1)){ motor_1.setTargetRel(-M1_spr); controller.move(motor_1); }  // Backward the linear actuator for 1 rotation
    if(not digitalRead(testMotor2)){ motor_2.setTargetRel(-M2_spr); controller.move(motor_2); }  // Backward the linear actuator for 1 rotation
    Serial.println(F("safety stop"));
  }
}

void sendCoordinates(){  // Get motor positions then send out through serials
  Serial.print("<locX:" + String(calibArray[1]-motor_2.getPosition()));
  Serial.println(",locY:" + String(calibArray[0]-motor_1.getPosition()) + ">");
  delay(500);
}

void recvWithMarkers(){ // https://forum.arduino.cc/index.php?topic=396450
  static boolean recvInProgress = false;
  static byte ndx = 0;
  char startMarker = '<';  // specify start of string
  char endMarker = '>';  // specify end of string
  char recv;

  while(Serial.available() > 0 && newData == false){
    recv = Serial.read();  // read the incoming data

    if (recvInProgress == true) {
      if (recv != endMarker) {
        receivedChars[ndx] = recv;  // record the string
        ndx++;
        // Clearing receivedChars[] array following RX Buffer size
        if (ndx >= numChars) { ndx = numChars - 1; }
      }
      else {
        receivedChars[ndx] = '\0';  // terminate the string
        recvInProgress = false;
        newData = true;
        ndx = 0;
      }
    }
    else if (recv == startMarker) {
      recvInProgress = true;
    }
  }
}

void initializeParameters(){
  M1_loc = 0;
  M1_speed = 0;
  M2_loc = 0;
  M2_speed = 0;
  isAbsTarget = false;  // natural target location as relative
  memset(receivedChars, 0, sizeof(receivedChars));
}

void parserArrayIndex(){
    char * strtokIndx; // this is used by strtok() as an index
    int i = 0;
    bool isNum = 1;
    char * tempNum;
    initializeParameters();

    strtokIndx = strtok(tempChars, ":");      // get the first part - the string
    while (strtokIndx != NULL){  // check if strtokIndx is present
      // check if token is a number
      tempNum = strtok(NULL, ",");
      for(int j=0; j<int(strlen(tempNum)) ; j++){
        if(not isdigit(tempNum[j]) and String(tempNum[j]) != "-"){
          isNum = 0;
          break;
        }
      }
      // if token is not a number, break while loop
      if(isNum == 0) { Serial.println("loop break"); initializeParameters(); break; }
      // if token is a number, continue
      // <Xr:600000,Xs:-50000,Yr:1200000,Ys:-50000,T:2>
      // <Xr:50000,Xs:-20000,Yr:0,Ys:0,T:0>
      // <Xabs:25000,Xs:-50000,Yabs:30000,Ys:-50000,T:2>
      // <Xabs:25000,Xs:-50000,Yabs:0,Ys:-50000,T:2>
      //
      if(String(strtokIndx) == "Yabs"){ M1_loc = atoi(tempNum); isAbsTarget = true; Serial.println("AbsX: " + String(isAbsTarget));}
      else if(String(strtokIndx) == "Xabs"){ M2_loc = atoi(tempNum); isAbsTarget = true; Serial.println("AbsY: " + String(isAbsTarget));}
      else if(String(strtokIndx) == "Yr"){ M1_loc = atoi(tempNum); }
      else if(String(strtokIndx) == "Ys"){ M1_speed = atoi(tempNum); }
      else if(String(strtokIndx) == "Xr"){ M2_loc = atoi(tempNum); }
      else if(String(strtokIndx) == "Xs"){ M2_speed = atoi(tempNum); }
      else if(String(strtokIndx) == "T"){ wait_time = atoi(tempNum); }
      else{ initializeParameters(); break; }
      strtokIndx = strtok(NULL, ":");
      i++;
    }

    // Show parsed data
    // Serial.println("Number of parameters received: " + String(i));
    Serial.println("<New data parsed>");
}

void motorCommand(){
  int abs_dir1 = 0;
  int abs_dir2 = 0;
  int motor_1_loc = calibArray[0]-motor_1.getPosition();
  int motor_2_loc = calibArray[1]-motor_2.getPosition();
  if(M1_speed == 0){ M1_speed = M1_defaultSpeed; }
  if(M2_speed == 0){ M2_speed = M2_defaultSpeed; }

  if(isAbsTarget == true){
    Serial.println("MOTOR 1 set target ABS");
    Serial.println(M1_loc);
    Serial.println(motor_1_loc);
    Serial.println(M1_loc + calibArray[0]);
    if(M1_loc <= motor_1_loc){ abs_dir1 = 1; }
    else if(M1_loc > motor_1_loc){ abs_dir1 = -1; }
    else{ Serial.println("EXCEPTION1"); return; }
    Serial.println("Dir 1: " + String(abs(M1_speed)*abs_dir1));
    motor_1.setMaxSpeed(abs(M1_speed)*abs_dir1);
    motor_1.setTargetAbs(-M1_loc + calibArray[0]);
  }  // Absolute command is used during program run
  else {
    motor_1.setTargetRel(M1_loc);
    Serial.println("MOTOR 1 set target Rel");
    motor_1.setMaxSpeed(M1_speed);
  }  // Relative command is used during manual run

  if(isAbsTarget == true){
    Serial.println("MOTOR 2 set target ABS");
    Serial.println(M2_loc);
    Serial.println(motor_2_loc);
    Serial.println(M2_loc + calibArray[1]);
    if(M2_loc <= motor_2_loc){ abs_dir2 = 1; }
    else if(M2_loc > motor_2_loc){ abs_dir2 = -1; }
    else{ Serial.println("EXCEPTION2"); return; }
    Serial.println("Dir 2: " + String(abs(M2_speed)*abs_dir2));
    motor_2.setMaxSpeed(abs(M2_speed)*abs_dir2);
    motor_2.setTargetAbs(-M2_loc + calibArray[1]);
  }  // Absolute command is used during program run
  else {
    motor_2.setTargetRel(M2_loc);
    Serial.println("MOTOR 2 set target Rel");
    motor_2.setMaxSpeed(M2_speed);
  }  // Relative command is used during manual run

  controller.moveAsync(motor_1, motor_2);
  Serial.println("<Ready>");
}

bool isInBound(){
  if (isAbsTarget == 1){
    // check absolute location
    return 1;
  }

  int val1 = motor_1.getPosition() - calibArray[0] + M1_loc*int(M1_speed/abs(M1_speed));
  int val2 = motor_2.getPosition() - calibArray[1] + M2_loc*int(M2_speed/abs(M2_speed));

  Serial.println(abs(val1));
  Serial.println(abs(val2));
  Serial.println(M1_availableStep);
  Serial.println(M2_availableStep);
  if ( 0 <= -val1 and -val1 <= M1_availableStep ){
    Serial.println("pass 1");
    if ( 0 <= -val2 and -val2 <= M2_availableStep ){
      Serial.println("pass 2");
        return 1;
    }
    else { return 0; }
  }
  else {
    Serial.println("NOT pass");
    return 0;
  }
}

// ******************************************************** //
// ******************************************************** //
// ********************  Setup Program  ******************* //
// ******************************************************** //
// ******************************************************** //

void setup()
{
  Serial.begin(9600);  // set the baud rate
  for(int i=0; i<3; i++){
    delay(1000);
    Serial.print(". ");
  }
  Serial.println("\n<Serial communication is ready>");
  pinMode(testMotor1, INPUT);
  pinMode(testMotor2, INPUT);

  // initialize the motors (default values)
  motor_1
    .setMaxSpeed(M1_defaultSpeed)
    .setAcceleration(M1_defaultAcc);
  motor_2
    .setMaxSpeed(M2_defaultSpeed)
    .setAcceleration(M2_defaultAcc);

  if(not digitalRead(testMotor1)){ motor_1.setTargetRel(-M1_spr); controller.move(motor_1); }  // Backward the linear actuator for 1 rotation
  if(not digitalRead(testMotor2)){ motor_2.setTargetRel(-M2_spr); controller.move(motor_2); }  // Backward the linear actuator for 1 rotation

}

// ******************************************************** //
// ******************************************************** //
// *********************  Main Program  ******************* //
// ******************************************************** //
// ******************************************************** //

void loop(){
  safetyStopOrigin();
  // sendCoordinates();
  recvWithMarkers();

  if (newData == true){
    Serial.println(receivedChars);
    strcpy(tempChars, receivedChars);
            // this temporary copy is necessary to protect the original data
            // because strtok() used in parseData() replaces the commas with \0

    // Special commands from python
    if(String(tempChars) == "Sending"){ Serial.println("<Ready>"); }
    else if(String(tempChars) == "Calibrate"){ Serial.println("Special request: Calibrate "); motorOriginCalibration(); }
    else if(String(tempChars) == "origin"){ Serial.println("Special request 1"); isSpecialCmd = true; }
    else if(String(tempChars) == "abort"){ Serial.println("Special request 2"); isSpecialCmd = true; }


    // Parsing recieved instructions
    else{
      parserArrayIndex();
      if (not isSpecialCmd and isInBound()){ motorCommand(); } // Deliver actions
      else { Serial.println("<ENTRY OUT OF BOUND>"); }
    }

    // Re-initialize all control parameters
    initializeParameters();
    newData = false;
    Serial.println("<Ready>");
  }
}