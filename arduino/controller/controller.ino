#include "Wire.h"
#include "Servo.h"

#include "DHT.h"
 
#define DHTPIN A1 // Digital pin connected to the DHT sensor
#define DHTTYPE DHT11 

#define SERVO_PIN 6 // Digital pin connected to the DHT sensor

#define seconds() ((int)(millis()/1000))
#define SAMPLE_TIME 1 // do PID each second

#define VALVE_OFFSET 90

#define SLAVE_ADDRESS 0x08 //SLAVE Unique ID in the BUS
 
// Connect pin 1 (on the left) of the sensor to +5V
// NOTE: If using a board with 3.3V logic like an Arduino Due connect pin 1
// to 3.3V instead of 5V!
// Connect pin 2 of the sensor to whatever your DHTPIN is
// Connect pin 3 (on the right) of the sensor to GROUND (if your sensor has 3 pins)
// Connect pin 4 (on the right) of the sensor to GROUND and leave the pin 3 EMPTY (if your sensor has 4 pins)
// Connect a 10K resistor from pin 2 (data) to pin 1 (power) of the sensor
DHT dht(DHTPIN, DHTTYPE);

String inputString = "";//Store i2c data
String outputString = "";//enqueue i2c data
boolean stringComplete = false;  // whether the string is complete

Servo valveServo; // Servo controller
int currentPos = 0; // Servo position 0 = midpoint

float tSetPoint;

float kp = 5, ki = 2.5, kd = 0.02;

long time;
long et;

long pTime, lTime, rTime, sampleTime, reportTime;

float dt, error, pError;

float integralError = 0;
float derivativeError = 0;

float h;
float t;


void receiveData(int bytecount)
{
  char inChar;

  for (int i = 0; i < bytecount; i++) {
    inChar = Wire.read();
    inputString += String(inChar);
    Serial.println(inputString);
  }

  stringComplete = true;

}
void sendData()
{
  if ( outputString != "" )
  {
    Wire.write(outputString.c_str());
    outputString = "";
  }

}
 
void setup() 
{
  Serial.begin(9600);
  while(!Serial);
  Serial.println("setpoint, temperature, valve");

  dht.begin();

  Wire.begin(SLAVE_ADDRESS);

  Wire.onReceive(receiveData);
  Wire.onRequest(sendData);

  valveServo.attach(SERVO_PIN);
  valveServo.write(VALVE_OFFSET + currentPos); 

  tSetPoint = dht.readTemperature();

  pinMode(LED_BUILTIN, OUTPUT);

  for( int i = 0; i < 3; ++i)
  {
    digitalWrite(LED_BUILTIN, HIGH);   // turn the LED on (HIGH is the voltage level)
    delay(1000);                       // wait for a second
    digitalWrite(LED_BUILTIN, LOW);    // turn the LED off by making the voltage LOW
    delay(1000);                       // wait for a second
  }

}
 
void loop() 
{
  // Reading temperature or humidity takes about 250 milliseconds!
  h = dht.readHumidity();
  t = dht.readTemperature();

  // Check if any reads failed and exit early (to try again).
  if (isnan(t) || isnan(h)) 
  {
    Serial.println("Failed to read from DHT");
  } 
  else
  {


    et = millis() - sampleTime;

    if ( et > SAMPLE_TIME)
    {

      Serial.print(tSetPoint);
      Serial.print(" ");
      Serial.print(t);

      sampleTime = millis();
      dt = (float)et/1000;

      error = tSetPoint - t;

      integralError = integralError + (float)error * dt;
      derivativeError = (float)(error - pError)/dt;

      pError = error;

      currentPos = VALVE_OFFSET + (int)(kp*error + ki * integralError + kd * derivativeError);
      currentPos = constrain(currentPos,0,180); //valve limits

      valveServo.write(currentPos);

      Serial.print(" ");
      Serial.println(currentPos);

    }


    outputString = String("{sensor: 'dht11', t:"+String(t)+",h:"+String(h)+"}");

    // Serial.print("Humidity: ");
    // Serial.print(h);
    // Serial.print(" %t");
    // Serial.print("Temperature: ");
    // Serial.print(t);
    // Serial.println(" *C");
  }
}
