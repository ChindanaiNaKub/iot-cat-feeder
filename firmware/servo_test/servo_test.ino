// ทดสอบหมุนไปกลับ: 0 -> TEST_DEG -> 0 วนซ้ำ เพื่อดูว่าเซอร์โวกลับมาปิดสนิทที่จุดเดิมได้
//
// สัญญาณ -> D5 (GPIO14), VCC -> VIN (5V), GND -> GND
// จ่ายไฟจาก powerbank ไม่ใช่พอร์ตโน้ตบุ๊ก

#include <Servo.h>

const int SERVO_PIN = D5;
const int HOME_DEG = 0;        // จุดปิดฝา ต้องตรงกับ CLOSED_DEG ใน feeder.ino
const int TEST_DEG = 135;       // มุมที่ลอง แก้แล้วอัปโหลดใหม่
const unsigned long HOLD_MS = 1000;

Servo flap;

void goTo(int deg) {
  Serial.print("servo -> ");
  Serial.print(deg);
  Serial.println(" deg");
  flap.write(deg);
  delay(HOLD_MS);
}

void setup() {
  Serial.begin(115200);
  delay(200);
  Serial.println();
  flap.attach(SERVO_PIN);
  goTo(HOME_DEG);
}

void loop() {
  goTo(TEST_DEG);
  goTo(HOME_DEG);
}
