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
const char *ID = "ESP_POS";

IPAddress broker(10, 42, 0, 1); // IP address of your MQTT broker eg. 192.168.1.50
WiFiClient wclient;

PubSubClient client(wclient); // Setup MQTT client
TaskHandle_t Task1;           // Establish task for MQTT stuff to run on

// connection functions
void setup_wifi();
void reconnect();
void MQTT_Task(void *pvParameters);

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

void pinch();
void push();

// Variables

// stepper movement functions & setup
#define EN_PIN 13
#define DIR_PIN 12
#define STEP_PIN 14
#define DIAG_PIN 21
#define SW_RX 16
#define SW_TX 17

// Driver Setup
#define SERIAL_PORT Serial2 // For TMC UART
#define R_SENSE 0.11f
#define DRIVER_ADDRESS 0b00

TMC2209Stepper driver(&SERIAL_PORT, R_SENSE, DRIVER_ADDRESS);

// Functions
void moveStep();
void checkStallGuard();
void findZero();
void alignEmpty();
void alignNew();

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
            Serial.println("POSITION PUUUUSH");
            pinch();
        }
        else if (payloadStr == "POS_PUSH")
        {
            push();
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
    Serial.begin(115200); // Start serial communication at 115200 baud

    // MQTT Setup
    setup_wifi(); // Connect to network
    client.setServer(broker, 1883);
    client.setCallback(callback); // Initialize the callback routine

    // Servo Setup
    Serial2.begin(1000000, SERIAL_8N1, S_RXD, S_TXD);
    sms_sts.pSerial = &Serial2;
    delay(100);

    for (int i = 0; i < 3; i++)
    {
        sms_sts.WheelMode(i);
        sms_sts.WriteSpe(i, 0, 0); // servo(ID1) speed=3400，acc=50，move to position=4095.
    }

    // Create background task that connection stuff will run on
    xTaskCreatePinnedToCore(
        MQTT_Task,   // Function to implement task
        "MQTT_Task", // Task name
        10000,       // Stack size in words
        NULL,        // Task input parameter
        1,           // Task priority
        &Task1,      // Task handle
        0            // Core the task will run on
    );
}

// Main loop running on core 0

#define MQTT_RECONNECT_INTERVAL_MS 500

void MQTT_Task(void *pvParameters)
{
    TickType_t lastReconnectAttempt = 0;

    for (;;)
    {
        if (!client.connected())
        {
            TickType_t now = xTaskGetTickCount();
            if ((now - lastReconnectAttempt) >= pdMS_TO_TICKS(MQTT_RECONNECT_INTERVAL_MS))
            {
                lastReconnectAttempt = now;
                Serial.println("Attemping Reconnect...");
                reconnect(); // non-blocking, single attempt only
            }
        }
        else
        {
            client.loop();
        }

        vTaskDelay(pdMS_TO_TICKS(10)); // more frequent, keeps watchdog fed
    }
}

// void MQTT_Task(void *pvParameters)
// {
//     for (;;)
//     { // Standard FreeRTOS infinite loop
//         if (!client.connected())
//         {
//             // Attempt to connect ONCE.
//             // Don't use a 'while' loop inside reconnect()!
//             reconnect();
//         }
//         else
//         {
//             // Only loop if connected
//             client.loop();
//         }

//         // This delay is your safety net.
//         // It must be reached frequently to feed the Watchdog.
//         vTaskDelay(pdMS_TO_TICKS(50));
//     }
// }

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
        if (client.connect(ID, NULL, NULL, "ESP/POS/Status", 0, true, "Disconnected")) // Defines LWT topic and message
        {
            client.publish("ESP/POS/Status", "Connected", true); // Publish connection status
            client.subscribe("NEST/Status");                     // Subscribe to the topic
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

void pinch()
{
    Serial.println("Enabling");
    sms_sts.EnableTorque(1, 1);
    sms_sts.EnableTorque(3, 1);
    Serial.println("Setting Speed");
    sms_sts.WriteSpe(1, 3400, 50); // servo(ID1) speed=3400，acc=50，move to position=4095.
    sms_sts.WriteSpe(3, 3400, 50); // servo(ID3) speed=3400，acc=50，move to position=4095.

    delay(5000);

    Serial.println("Stopping");
    sms_sts.WriteSpe(1, 0, 50); // servo(ID1) speed=3400，acc=50，move to position=4095.
    sms_sts.WriteSpe(3, 0, 50); // servo(ID3) speed=3400，acc=50，move to position=4095.

    sms_sts.EnableTorque(1, 0);
    sms_sts.EnableTorque(3, 0);

    client.publish("ESP/POS/Pinch", "Complete");
}

void push()
{
    sms_sts.EnableTorque(2, 1);
    sms_sts.WriteSpe(2, 3400, 50);

    delay(5000);

    sms_sts.WriteSpe(2, 0, 50);
    sms_sts.EnableTorque(2, 0);

    client.publish("ESP/POS/Push", "Complete");
}
