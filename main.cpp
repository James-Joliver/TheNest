#include <Arduino.h>
#include <SCServo.h>
#include <WiFi.h>
#include <PubSubClient.h>

SMS_STS sms_sts;
// the UART used to control servos.
// GPIO 16 - S_RXD, GPIO 17 - S_TXD, as default.
#define S_RXD 16
#define S_TXD 17

int TEST_ID = 1;

void findServo(int ID);

WiFiClient espClient;
PubSubClient client(espClient);

void setup()
{
  // MQTT Setup
  WiFi.begin("SSID", "PASSWORD");
  client.setServer("somethin", 8888);

  // Motor Setup
  Serial.begin(115200);
  Serial2.begin(1000000, SERIAL_8N1, S_RXD, S_TXD);
  sms_sts.pSerial = &Serial2;
  delay(1000);
  sms_sts.EnableTorque(TEST_ID, 1);
  sms_sts.WheelMode(TEST_ID);
  sms_sts.WriteSpe(1, 0, 50); // servo(ID1) speed=3400，acc=50，move to position=4095.
}

/////// MAIN LOOP ///////

void loop()
{
  int Load = sms_sts.ReadLoad(TEST_ID);
  int Current = sms_sts.ReadCurrent(TEST_ID);
  Serial.print("Load: ");
  Serial.print(Load);
  Serial.print("    Current: ");
  Serial.println(Current);
  delay(10);
}

/////// FUNCTIONS ///////

void findServo(int ID)
{
  int result = sms_sts.Ping(ID);
  if (result != -1)
  {
    Serial.print("Servo ID:");
    Serial.println(ID, DEC);
    delay(200);
  }
  else
  {
    Serial.println("Ping servo ID error at ID: ");
    Serial.println(ID, DEC);
    delay(200);
  }
}

void removeBattery(int ID, int speed, int threshold) 
{
  client.publish("Arm", "Remove Begin");
  Serial.println("Removing Depleted Battery");

  // move forward
  sms_sts.WriteSpe(ID, speed, 50);

  // arm has not reached a wall
  bool stalled = false;

  // stop once arm has fully latched to the battery
  while(!stalled) {
    int currentLoad = sms_sts.ReadLoad(ID);

    int loadMagnitude = (currentLoad < 0) ? -currentLoad : currentLoad;
    
    Serial.println("Current load: ");
    Serial.println(loadMagnitude);

    if (loadMagnitude >= threshold) {
      stalled = true;
    }
  }

  // move back with battery
  sms_sts.WriteSpe(ID, -speed, 30);
  delay(200);
  sms_sts.WriteSpe(ID, 0, 50);

  client.publish("Arm", "Remove End");
}

void insertBattery(int ID, int speed, int threshold) 
{
  client.publish("Arm", "Insert Begin");
  Serial.println("Inserting New Battery");

  // move forward
  sms_sts.WriteSpe(ID, speed, 50);

  // arm has not reached a wall
  bool stalled = false;

  // stop once arm has pushed battery as far as possible
  while(!stalled) {
    int currentLoad = sms_sts.ReadLoad(ID);

    int loadMagnitude = (currentLoad < 0) ? -currentLoad : currentLoad;
    
    Serial.println("Current load: ");
    Serial.println(loadMagnitude);

    if (loadMagnitude >= threshold) {
      stalled = true;
    }
  }

  client.publish("Arm", "Insert End");
}