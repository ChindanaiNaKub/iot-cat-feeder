// ทดสอบ servo SG90 บน NodeMCU v3 (ESP8266)
// สัญญาณ -> D5 (GPIO14), VCC -> VIN (5V), GND -> GND
// Capacitor 470uF คร่อม VCC/GND ใกล้ servo (+ ไป VCC, - ไป GND)
#include <Servo.h>

const int SERVO_PIN = D5;
const int CLOSED_DEG = 0;   // ปรับหลังประกอบฝาถังอาหาร
const int OPEN_DEG = 180;

Servo flap;

void setup() {
  Serial.begin(115200);
  flap.attach(SERVO_PIN);
  flap.write(CLOSED_DEG);
  Serial.println("servo test: open/close every 2s");
}

void loop() {
  Serial.println("open");
  flap.write(OPEN_DEG);
  delay(1000);
  Serial.println("close");
  flap.write(CLOSED_DEG);
  delay(1000);
}
