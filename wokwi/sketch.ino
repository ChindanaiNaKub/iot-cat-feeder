#include <ESP32Servo.h>

const int SERVO_PIN = 18;
const unsigned long OPEN_MS = 1000;

Servo flap;

void setup() {
  Serial.begin(115200);
  flap.attach(SERVO_PIN);
  flap.write(0);
}

void loop() {
  Serial.println("open");
  flap.write(90);
  delay(OPEN_MS);
  Serial.println("close");
  flap.write(0);
  delay(OPEN_MS);
}
