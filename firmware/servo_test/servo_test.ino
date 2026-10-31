// หามุมที่ servo หมุนได้จริง ก่อนเอาค่าไปใส่ OPEN_DEG ใน feeder.ino
//
// สัญญาณ -> D5 (GPIO14), VCC -> VIN (5V), GND -> GND
// จ่ายไฟจาก powerbank ไม่ใช่พอร์ตโน้ตบุ๊ก
//
// วิธีใช้
// 1. อัปโหลดแล้วเปิด Serial Monitor 115200
// 2. servo จะไล่มุมทีละ 10 องศา ค้างไว้ 1.2 วินาที แล้วพิมพ์มุมออกมา
// 3. สังเกตตอนฝาเปิดสุด ถ้าได้ยินเสียงหึ่งๆ หรือฝาไม่ขยับแล้วแต่ servo ยังดัง
//    แปลว่าชนระยะ ให้จดมุมก่อนหน้านั้นไว้
// 4. เอาค่านั้นลบ 5 องศา ไปใส่ OPEN_DEG ใน feeder.ino

#include <Servo.h>

const int SERVO_PIN = D5;
const int STEP_DEG = 10;
const unsigned long HOLD_MS = 1200;

Servo flap;

void setup() {
  Serial.begin(115200);
  delay(200);
  Serial.println();
  Serial.println("servo sweep: 0 -> 180 -> 0");
  Serial.println("ฟังเสียงหึ่งๆ ตอนฝาชนระยะ แล้วจดมุมก่อนหน้านั้น");
  flap.attach(SERVO_PIN);
  flap.write(0);
  delay(800);
}

void stepTo(int angle) {
  Serial.print("angle ");
  Serial.println(angle);
  flap.write(angle);
  delay(HOLD_MS);
}

void loop() {
  for (int a = 0; a <= 180; a += STEP_DEG) stepTo(a);
  delay(1500);
  for (int a = 180; a >= 0; a -= STEP_DEG) stepTo(a);
  delay(2500);
}
