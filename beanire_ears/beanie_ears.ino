int motor1pin1 = 10;
int motor1pin2 = 11;

unsigned long currentMillis = 0;
unsigned long previousMillis = 0;

bool active = false;
bool reportSerial = true;

int state = 0;
unsigned long t_seq = 0;
unsigned long t_duration = 0;

bool messageReceived = false;
//int earState = 0;

void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
  
  pinMode(motor1pin1, OUTPUT);
  pinMode(motor1pin2, OUTPUT);
  previousMillis = millis();

  // INITIALIZE
  calibrate_motor();

  ////TESTING
  pinMode(LED_BUILTIN, OUTPUT);
}

void loop() {

  // put your main code here, to run repeatedly:  
  int cmd = -1;
  if(Serial.available()){
    String val = Serial.readStringUntil('\n');
    val.trim();

    cmd = val.toInt(); 

    Serial.println(cmd);

  }

  run_motor(cmd);
}

void calibrate_motor () {
  analogWrite(motor1pin1, 255);
  analogWrite(motor1pin2, 0);

  delay(1000);

  analogWrite(motor1pin1, 0);
  analogWrite(motor1pin2, 0);
}

void run_motor(int cmd) {
  
  if(cmd == 0) { //FULL DOWN, MED (sleep)
    active = true;
    state = cmd;
    analogWrite(motor1pin1, 255);
    analogWrite(motor1pin2, 0);

    t_duration = 3000;
    t_seq = millis(); 
  }
  else if(cmd == 1) { //TO MIDDLE (listening)

    if(state == 3){
      active = true;
      state = cmd;
      analogWrite(motor1pin1, 200);
      analogWrite(motor1pin2, 0);

      t_duration = 200;
      t_seq = millis();

    }else if(state == 4){
      active = true;
      state = cmd;
      analogWrite(motor1pin1, 0);
      analogWrite(motor1pin2, 255);

      t_duration = 600;
      t_seq = millis();
    }
    else{
      active = true;
      state = cmd;
      analogWrite(motor1pin1, 0);
      analogWrite(motor1pin2, 255);

      t_duration = 600;
      t_seq = millis();
    }
  }
  else if(cmd == 2) { //WIGGLE
      active = true;
      state = cmd;
      analogWrite(motor1pin1, 0);
      analogWrite(motor1pin2, 150);

      t_duration = 2600;
      t_seq = millis();

  }
  else if(cmd == 3) { //Wiggle (positive)
    active = true;
    state = cmd;
    analogWrite(motor1pin1, 0);
    analogWrite(motor1pin2, 255);

    t_duration = 2600;
    t_seq = millis();
  }
  else if(cmd == 4) { //FULL DOWN (negative)
    active = true;
    state = cmd;
    analogWrite(motor1pin1, 255);
    analogWrite(motor1pin2, 0);

    t_duration = 3000;
    t_seq = millis(); 
  }
  else {
    if(millis() - t_seq > t_duration && active) {
      active = false;
      analogWrite(motor1pin1, 0);
      analogWrite(motor1pin2, 0);
    }
    else if (state == 2 && active) {
      int d = millis() - t_seq;
      int denom = d / 400;
      if(denom % 2 == 0) {
        analogWrite(motor1pin1, 0);
        analogWrite(motor1pin2, 150);
      }
      else {
        analogWrite(motor1pin1, 150);
        analogWrite(motor1pin2, 0);
      }
    }
    else if (state == 3 && active) {
      int d = millis() - t_seq;
      int denom = d / 200;
      if(denom % 2 == 0) {
        analogWrite(motor1pin1, 0);
        analogWrite(motor1pin2, 255);
      }
      else {
        analogWrite(motor1pin1, 255);
        analogWrite(motor1pin2, 0);
      }
    }
  }
}
