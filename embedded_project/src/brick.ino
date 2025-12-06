#include <Arduino.h>
#include <WiFi.h>
#include <WiFiUdp.h>

const char* WIFI_SSID = "brick";
const char* WIFI_PASS = "defeater";

// Ports and secret, make the ports unique and 1024 < (DISCOVERY_PORT != CONTROL_PORT) < 65536
const uint16_t DISCOVERY_PORT = 65130;   // UDP discovery
const uint16_t CONTROL_PORT   = 65131;   // TCP control 
const char* SECRET_KEY = "passw"; //make sure this matches the secret key in the python side

// Discovery timing
const unsigned long BROADCAST_INTERVAL_MS = 1500; // send a broadcast every 1.5s until paired
const unsigned long DISCOVERY_CHECK_MS = 100; // how often we check for incoming replies
const uint TCP_READ_TIMEOUT_MS = 3000;


WiFiUDP udp;
WiFiServer controlServer(CONTROL_PORT);
const int LEN_RCV_ARR = 2; //change this according to the length of the array you send on the python side

// pairing state
bool paired = false;
IPAddress pairedIP;
unsigned long lastBroadcastMillis = 0;

const int IN1_FL = 26;  // IN1 (front-left)
const int IN2_FL = 27;  // IN2 (front-left)
const int IN3_FR = 32;  // IN3 (front-right)
const int IN4_FR = 14;  // IN4 (front-right)

const int IN1_BR = 4;   // IN1 (back-right)
const int IN2_BR = 2;   // IN2 (back-right)
const int IN3_BL = 18;  // IN3 (back-left)
const int IN4_BL = 5;   // IN4 (back-left)

// Durations
const unsigned long DRIVE_MS   = 1500; // drive straight for 2 seconds
const unsigned long TURN_45_MS = 600;  // approximate 45° tank turn right
const unsigned long TURN_90_MS = 1200; 

void motorForward(int in1, int in2) {
  digitalWrite(in1, HIGH);
  digitalWrite(in2, LOW);
}

void motorBackward(int in1, int in2) {
  digitalWrite(in1, LOW);
  digitalWrite(in2, HIGH);
}

void motorStop(int in1, int in2) {
  digitalWrite(in1, LOW);
  digitalWrite(in2, LOW);
}

// These functions are named for **physical** motion:
// "*Forward*" in the name = car goes forward on the floor.

void frontLeftForward()    { motorBackward(IN1_FL, IN2_FL); }
void frontLeftBackward()   { motorForward(IN1_FL, IN2_FL); }

void frontRightForward()   { motorBackward(IN3_FR, IN4_FR); }
void frontRightBackward()  { motorForward(IN3_FR, IN4_FR); }

void backRightForward()    { motorBackward(IN1_BR, IN2_BR); }
void backRightBackward()   { motorForward(IN1_BR, IN2_BR); }

void backLeftForward()     { motorBackward(IN3_BL, IN4_BL); }
void backLeftBackward()    { motorForward(IN3_BL, IN4_BL); }

void stopAll() {
  motorStop(IN1_FL, IN2_FL);
  motorStop(IN3_FR, IN4_FR);
  motorStop(IN1_BR, IN2_BR);
  motorStop(IN3_BL, IN4_BL);
}

// Straight forward (car moves forward)
void driveForwardStraight(unsigned long ms) {
  frontLeftForward();
  frontRightForward();
  backLeftForward();
  backRightForward();
  delay(ms);
  stopAll();
}

// Tank turn RIGHT in place: car rotates to the right (physically)
void turnRightInPlace(unsigned long ms) {
  // left side backward, right side forward (pattern we know turns right)
  frontLeftBackward();
  backLeftBackward();
  frontRightForward();
  backRightForward();
  delay(ms);
  stopAll();
}

void driveBackwardStraight(unsigned long ms) {
  frontLeftBackward();
  frontRightBackward();
  backLeftBackward();
  backRightBackward();
  delay(ms);
  stopAll();
}

// Tank turn LEFT in place (opposite of turnRightInPlace)
void turnLeftInPlace(unsigned long ms) {
  // left side forward, right side backward (tune if needed)
  frontLeftForward();
  backLeftForward();
  frontRightBackward();
  backRightBackward();
  delay(ms);
  stopAll();
}


// High-level motions for the test sequence
void doForward() {
  Serial.println("MOVE 1: FORWARD");
  driveForwardStraight(DRIVE_MS);
}

void doBackward() {
  Serial.println("MOVE 2: BACKWARD");
  driveBackwardStraight(DRIVE_MS);
}

void doLeft() {
  Serial.println("MOVE 3: LEFT (turn left 90°, then forward)");
  turnLeftInPlace(TURN_90_MS);
  delay(200);
  driveForwardStraight(DRIVE_MS);
}

void doRight() {
  Serial.println("MOVE 4: RIGHT (turn right 90°, then forward)");
  turnRightInPlace(TURN_90_MS);
  delay(200);
  driveForwardStraight(DRIVE_MS);
}

void doForwardRight() {
  Serial.println("MOVE 5: FORWARD-RIGHT (turn right 45°, then forward)");
  turnRightInPlace(TURN_45_MS);
  delay(200);
  driveForwardStraight(DRIVE_MS);
}

void doForwardLeft() {
  Serial.println("MOVE 6: FORWARD-LEFT (turn left 45°, then forward)");
  turnLeftInPlace(TURN_45_MS);
  delay(200);
  driveForwardStraight(DRIVE_MS);
}

void doBackwardRight() {
    Serial.println("MOVE 7: BACKWARD-RIGHT (turn left 45°, then backward)");
    turnLeftInPlace(TURN_45_MS);
    delay(200);
    driveBackwardStraight(DRIVE_MS);
}

void doBackwardLeft() {
    Serial.println("MOVE 8: BACKWARD-LEFT (turn left 45°, then backward)");
    turnRightInPlace(TURN_45_MS);
    delay(200);
    driveBackwardStraight(DRIVE_MS);
}

typedef void (*DriveFn)();

DriveFn DRIVE_TABLE[8] = {
  doForwardLeft,     // 0, 0
  doLeft,  // 0, 1
  doBackwardLeft, // 0, 2
  doBackward, //0, 3
  doForwardRight, // 1, 0
  doRight, //1, 1
  doBackwardRight, // 1, 2 
  doForward //1, 3
};

void useReceivedData(uint8_t arr[]) {
    uint8_t first = arr[0];
    uint8_t second  = arr[1];
    if (first > 1 || second > 3) {
        Serial.println("Command out of range, ignoring");
        return;
    }
    uint8_t index = first * 4 + second;
    DriveFn fn = DRIVE_TABLE[index];
    if (fn != nullptr) {
        fn();
    }


}

void setupWiFi() {
  Serial.printf("Connecting to WiFi '%s'...\n", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED) {
    delay(250);
    Serial.print('.');
    if (millis() - start > 30000) {
      Serial.println("\nWiFi connect failed - restarting...");
      ESP.restart();
    }
  }
  Serial.println();
  Serial.print("WiFi connected. IP: ");
  Serial.println(WiFi.localIP());
  Serial.print("Subnet mask: ");
  Serial.println(WiFi.subnetMask());
}

void sendDiscoveryBroadcast() {
  IPAddress bcast = IPAddress(255, 255, 255, 255);
  const char* msg = SECRET_KEY;
  udp.beginPacket(bcast, DISCOVERY_PORT);
  udp.write((const uint8_t*) msg, strlen(msg));
  udp.endPacket();
  Serial.printf("Broadcasted discovery to %s:%u\n", bcast.toString().c_str(), DISCOVERY_PORT);
}

bool checkDiscoveryReplies() {
  int packetSize = udp.parsePacket();
  if (packetSize <= 0) return false;
  // read packet
  char buf[512];
  int len = udp.read(buf, sizeof(buf)-1);
  if (len <= 0) return false;
  buf[len] = '\0';
  IPAddress remote = udp.remoteIP();
  uint16_t remotePort = udp.remotePort();
  Serial.printf("UDP packet from %s:%u -> %s\n", remote.toString().c_str(), remotePort, buf);

  // If the payload contains SECRET_KEY anywhere, accept
  if (strstr(buf, SECRET_KEY) != nullptr) {
    pairedIP = remote;
    paired = true;
    Serial.printf("Paired with %s (secret found in UDP reply)\n", pairedIP.toString().c_str());
    return true;
  }
  return false;
}

void handleControlClient(WiFiClient &client) {
  // Only accept commands from pairedIP
  IPAddress remote = client.remoteIP();
  if (remote != pairedIP) {
    Serial.printf("Rejected TCP connection from unauthorized IP %s\n", remote.toString().c_str());
    client.stop();
    return;
  }
  // Serial.printf("inc %s : ", remote.toString().c_str());
  client.setTimeout(TCP_READ_TIMEOUT_MS); // 3s timeout for reading commands
  uint8_t rcv_arr[LEN_RCV_ARR];
  unsigned long start = millis();
  uint motor_index = 0;
  while (millis() - start < TCP_READ_TIMEOUT_MS && client.connected()) {
    if (client.available()) {
      uint8_t c = client.read();
      rcv_arr[motor_index++] = c;
      if (motor_index >= LEN_RCV_ARR) break;
    } else {
      delay(2);
    }
  }

  useReceivedData(rcv_arr);

  client.stop();
  Serial.println("end");
}

void setup() {
  Serial.begin(115200);
  delay(200);
  setupWiFi();

  pinMode(IN1_FL, OUTPUT);
  pinMode(IN2_FL, OUTPUT);
  pinMode(IN3_FR, OUTPUT);
  pinMode(IN4_FR, OUTPUT);
  pinMode(IN1_BR, OUTPUT);
  pinMode(IN2_BR, OUTPUT);
  pinMode(IN3_BL, OUTPUT);
  pinMode(IN4_BL, OUTPUT);

  stopAll();
  // start UDP for discovery
  if (udp.begin(DISCOVERY_PORT) == 1) {
    Serial.printf("UDP discovery listening on port %u\n", DISCOVERY_PORT);
  } else {
    Serial.printf("Failed to begin UDP on port %u (but continuing)\n", DISCOVERY_PORT);
  }
  while (!paired) {
    Serial.print("*");
    unsigned long now = millis();
    if (now - lastBroadcastMillis >= BROADCAST_INTERVAL_MS) {
      sendDiscoveryBroadcast();
      lastBroadcastMillis = now;
    }
    delay(DISCOVERY_CHECK_MS);
    // check UDP replies repeatedly
    if (checkDiscoveryReplies()) {
      // paired becomes true inside checkDiscoveryReplies()
      // stop UDP discovery (we can keep the UDP object but stop reading)
      udp.stop();
      Serial.println("Stopped UDP discovery.");
      // start the TCP control server
      controlServer.begin();
      Serial.printf("TCP control server started on port %u. Waiting for connections from %s\n", CONTROL_PORT, pairedIP.toString().c_str());
    }
  }

}



void loop() {
  WiFiClient client = controlServer.available();
  if (client) {
    handleControlClient(client);
  }
  // small sleep to yield
  delay(5);
}






















