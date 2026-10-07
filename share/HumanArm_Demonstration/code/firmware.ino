/* One-finger bench demonstrator - Arduino UNO R3, D9 signal.
   Separate regulated 6 V servo supply; common GND; physical motor-power E-stop.
   Boot DISARMED. No automatic motion. This firmware is NOT a safety controller.
   Default travel is deliberately restricted to 1450..1550 microseconds.
   Loosen the tendon and check the mechanical neutral before first ARM.
   Serial 115200: ARM, SET 1450..1550, KEEPALIVE, STATUS, DISARM.
   Loss of valid keepalive for 750 ms detaches PWM, but does not remove power.
*/
#include <Servo.h>
#include <stdlib.h>
#include <string.h>

const byte SERVO_PIN = 9;
const int MIN_US = 1450;
const int MAX_US = 1550;
const int CENTER_US = 1500;
const unsigned long WATCHDOG_MS = 750;
Servo tendonServo;
bool armed = false;
int currentUs = CENTER_US;
int targetUs = CENTER_US;
unsigned long lastAlive = 0;
unsigned long lastStep = 0;
char commandLine[40];
byte commandLength = 0;
bool discardLine = false;

void disarm(const __FlashStringHelper *reason) {
  tendonServo.detach();
  pinMode(SERVO_PIN, OUTPUT);
  digitalWrite(SERVO_PIN, LOW);
  digitalWrite(LED_BUILTIN, LOW);
  armed = false;
  Serial.println(reason);
}

void command(char *line) {
  if (strcmp(line, "DISARM") == 0) {
    disarm(F("DISARMED"));
  } else if (strcmp(line, "ARM") == 0) {
    currentUs = targetUs = CENTER_US;
    tendonServo.writeMicroseconds(CENTER_US);
    tendonServo.attach(SERVO_PIN, 900, 2100);
    lastAlive = lastStep = millis();
    armed = true;
    digitalWrite(LED_BUILTIN, HIGH);
    Serial.println(F("ARMED 1500"));
  } else if (strcmp(line, "KEEPALIVE") == 0) {
    if (armed) lastAlive = millis();
  } else if (strcmp(line, "STATUS") == 0) {
    Serial.print(armed ? F("ARMED ") : F("DISARMED "));
    Serial.print(currentUs); Serial.print(' '); Serial.println(targetUs);
  } else if (strncmp(line, "SET ", 4) == 0) {
    char *end = NULL;
    long pulse = strtol(line + 4, &end, 10);
    if (!armed) { Serial.println(F("ERROR DISARMED")); return; }
    if (end == line + 4 || *end != '\0' || pulse < MIN_US || pulse > MAX_US) {
      disarm(F("ERROR RANGE OR FORMAT; DISARMED")); return;
    }
    targetUs = (int)pulse;
    lastAlive = millis();
    Serial.print(F("TARGET ")); Serial.println(targetUs);
  } else {
    disarm(F("ERROR COMMAND; DISARMED"));
  }
}

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  Serial.begin(115200);
  disarm(F("READY DISARMED; D9; 1450..1550 us"));
}

void loop() {
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (discardLine) {
      if (c == '\n') discardLine = false;
      continue;
    }
    if (c == '\r') continue;
    if (c == '\n') {
      commandLine[commandLength] = '\0';
      if (commandLength) command(commandLine);
      commandLength = 0;
    } else if (commandLength < sizeof(commandLine)-1) {
      commandLine[commandLength++] = c;
    } else {
      commandLength = 0;
      discardLine = true;
      disarm(F("ERROR LINE TOO LONG; DISARMED"));
    }
  }
  unsigned long now = millis();
  if (armed && now-lastAlive > WATCHDOG_MS) {
    disarm(F("WATCHDOG; DISARMED"));
  }
  if (armed && now-lastStep >= 20) {
    lastStep = now;
    int delta = targetUs-currentUs;
    currentUs += constrain(delta, -2, 2);
    tendonServo.writeMicroseconds(currentUs);
  }
}
