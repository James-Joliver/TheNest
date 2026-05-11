/*
DisconnectTest.cpp
*/

// MQTT Libraries
#include <WiFi.h>
#include <PubSubClient.h>

// Servo Libraries
#include <Arduino.h>
#include <SCServo.h>

// Stepper Libraries
#include <TMCStepper.h>


const char *ssid = "TheNestNetwork"; // name of your WiFi network
const char *password = "raspberry";  // password of the WiFi network
const char *ID = "ESP_SWAP";

IPAddress broker(10, 42, 0, 1); // IP address of your MQTT broker eg. 192.168.1.50
WiFiClient wclient;

PubSubClient client(wclient); // Setup MQTT client
TaskHandle_t Task1;           // Establish task for MQTT stuff to run on

// connection functions
void setup_wifi();
void reconnect();
void MQTT_Task(void * pvParameters);


// servo movement functions & setup
    SMS_STS sms_sts;
    // the UART used to control servos.
    // GPIO 16 - S_RXD, GPIO 17 - S_TXD, as default.
    #define S_RXD 16
    #define S_TXD 17

    int TEST_ID = 1;
    
    // Functions
    void removeBattery(int ID, int speed, int threshold);
    void insertBattery(int ID, int speed, int threshold);

    // Variables
    

// stepper movement functions & setup
    #define EN_PIN           13 
    #define DIR_PIN          12 
    #define STEP_PIN         14
    #define DIAG_PIN         21
    #define SW_RX            16
    #define SW_TX            17


    // Driver Setup
    #define SERIAL_PORT      Serial2 // For TMC UART
    #define R_SENSE          0.11f
    #define DRIVER_ADDRESS   0b00

    TMC2209Stepper driver(&SERIAL_PORT, R_SENSE, DRIVER_ADDRESS);

    // Functions
    void moveStep();
    void checkStallGuard();
    void findZero();
    void alignEmpty();
    void alignNew();

    void IRAM_ATTR handleStall() 
    {
    digitalWrite(EN_PIN, HIGH); 
    }

    // Variables
    int stepTime;
    int microstepts = 8;
    int stepThreshold = 30;
    int location;

// Function that listens for commands from pi
void callback(char *topic, byte *payload, unsigned int length)
{
    String payloadStr;
    String topicStr(topic); // Convert topic to String for easier comparison

    // Convert payload to String
    for (int i = 0; i < length; i++)
    {
        payloadStr += (char)payload[i];
    }

    Serial.print("Message arrived [");
    Serial.print(topic);
    Serial.print("] ");
    Serial.println(payloadStr);
    if (topicStr == "NEST/System/State")
    {
      if (payloadStr == "POS_PINCH")
      {
        delay(100);
        sms_sts.WriteSpe(1,500,50);
        Serial.println("Moving?");
        client.publish("ESP/POS/Pinch", "In Progress");
        delay(1000);
        sms_sts.WriteSpe(1,0,50);
        client.publish("ESP/POS/Pinch", "Complete");
      }
      else if (payloadStr == "SWAP_ALIGN_EMPTY")
      {
        Serial.println("Align to rail 1");
        alignEmpty();
      }
      else if (payloadStr == "SWAP_REMOVE")
      {

      }
      else if (payloadStr == "SWAP_ALIGN_NEW")
      {
        alignNew();
      }
      else if (payloadStr == "SWAP_INSERT")
      {

      }
    }
    else if (topicStr == "NEST/Status")
    {
        Serial.print("Received status from Nest: ");
        Serial.println(payloadStr);
    }
}

void setup()
{
    Serial.begin(115200);       // Start serial communication at 115200 baud

    // MQTT Setup
    setup_wifi(); // Connect to network
    client.setServer(broker, 1883);
    client.setCallback(callback); // Initialize the callback routine

    // Servo Setup
    Serial2.begin(1000000, SERIAL_8N1, S_RXD, S_TXD);
    sms_sts.pSerial = &Serial2;
    delay(100);
    sms_sts.EnableTorque(TEST_ID, 1);
    sms_sts.WheelMode(TEST_ID);
    sms_sts.WriteSpe(1, 0, 50); // servo(ID1) speed=3400，acc=50，move to position=4095.

    // Stepper Setup
        // Prepare pins
        pinMode(EN_PIN, OUTPUT);
        pinMode(STEP_PIN, OUTPUT);
        pinMode(DIR_PIN, OUTPUT);
        pinMode(DIAG_PIN, INPUT);

        digitalWrite(EN_PIN, HIGH); // Start driver as disabled (Active LOW)

    driver.begin();

    driver.toff(5); // Enables driver in software
    driver.rms_current(600); // Set RMS current
    driver.microsteps(microstepts); // Set microsteps to 1/16th a step

    driver.pwm_autoscale(true); // needed for stealthChop (quiet operation)
    driver.blank_time(24);
    driver.TCOOLTHRS(0xFFFFF); // 20bit max
    driver.semin(5);
    driver.semax(2);
    driver.sedn(0b01);
    driver.en_spreadCycle(0);


    driver.SGTHRS(stepThreshold);

    attachInterrupt(digitalPinToInterrupt(DIAG_PIN), handleStall, RISING);

    

    // Create background task that connection stuff will run on
    xTaskCreatePinnedToCore
    (
        MQTT_Task,      // Function to implement task
        "MQTT_Task",    // Task name
        10000,          // Stack size in words
        NULL,           // Task input parameter
        1,              // Task priority
        &Task1,         // Task handle
        0               // Core the task will run on
    );


}

// Main loop running on core 0
void MQTT_Task(void * pvParameters) {
    for(;;) { // Standard FreeRTOS infinite loop
        if (!client.connected()) {
            // Attempt to connect ONCE. 
            // Don't use a 'while' loop inside reconnect()!
            reconnect(); 
        } else {
            // Only loop if connected
            client.loop();
        }

        // This delay is your safety net. 
        // It must be reached frequently to feed the Watchdog.
        vTaskDelay(pdMS_TO_TICKS(100)); 
    }
}

void loop()
{
}


void setup_wifi()
{

    Serial.print("\nConnecting to ");
    Serial.println(ssid);

    WiFi.mode(WIFI_STA);
    WiFi.disconnect(true);
    delay(100);
    WiFi.begin(ssid, password); // Connect to network

    while (WiFi.status() != WL_CONNECTED)
    { // Wait for connection
        delay(500);
        Serial.print(".");
    }

    Serial.println();
    Serial.println("WiFi connected");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
}

void reconnect()
{
    // Loop until we're reconnected
    while (!client.connected())
    {
        Serial.print("Attempting MQTT connection...");
        // Attempt to connect
        if (client.connect(ID, NULL, NULL, "ESP/SWAP/Status", 0, true, "Disconnected")) // Defines LWT topic and message
        {
            client.publish("ESP/SWAP/Status", "Connected", true); // Publish connection status
            client.subscribe("ESP/SWAP/Status");                   // Subscribe to the topic
            client.subscribe("NEST/System/State");
            Serial.println("connected");
            Serial.print("Subcribed to: ");
            Serial.println("NEST/System/State");
            Serial.println('\n');
        }
        else
        {
            Serial.println(" try again in 5 seconds");
            // Wait 5 seconds before retrying
            delay(5000);
        }
    }
}

// Servo Control Functions
void removeBattery(int ID, int speed, int threshold) 
{
  client.publish("NEST/System/PushPull/State", "Remove Begin");
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

// Stepper control functions

void moveStep() 
{
      digitalWrite(STEP_PIN, HIGH);
      delayMicroseconds(500);
      digitalWrite(STEP_PIN, LOW);
      delayMicroseconds(500);
}


void findZero()
{
  Serial1.println("Finding zero");
  digitalWrite(EN_PIN, LOW);

    // Set direction to move towards motor
    driver.shaft(true);

    // Move until checkStallGuard flips the enable pin
    while (digitalRead(EN_PIN == LOW))
    {
        moveStep();
    }

    location = 0;

  Serial1.println("Zeroed");
}

void alignEmpty()
{
  findZero();
  delay(100);

  Serial.println("Moving to rail 1");
  digitalWrite(EN_PIN, LOW);
  if (location == 0)
  {
    driver.shaft(false);
    for (int i = 0; i < 1600; ++i)
    {
      moveStep();
    }
  }
  else if (location == 2)
  {
    driver.shaft(true);
    for (int i = 0; i < 12400; ++i)
    {
      moveStep();
    }
  }
  Serial.println("Aligned to rail 1");

  location = 1;
  digitalWrite(EN_PIN, HIGH);
}

void alignNew()
{
  Serial.println("Moving to rail 2");
  digitalWrite(EN_PIN, LOW);

  if (location == 0)
  {
    for (int i = 0; i < 12400; ++i)
    {
      moveStep();
    }
  }
  else if (location == 0)
  driver.shaft(false);
    for (int i = 0; i < 14000; ++i)
    {
      moveStep();
    }


  Serial.println("Aligned to rail 2");

  location = 2;
  digitalWrite(EN_PIN, HIGH);
}
