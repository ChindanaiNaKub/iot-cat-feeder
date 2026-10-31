// ทดสอบและคาลิเบรต load cell 1 kg กับ HX711 บน NodeMCU v3
//
// DT  = D0 (GPIO16)
// SCK = D3 (GPIO0)
// VCC = 3V3  <- ต้องใช้ 3.3V ไม่ใช่ 5V เพราะขา DT จะจ่าย 5V เข้าบอร์ด
// GND = GND ร่วม
//
// ต้องติดตั้งไลบรารีก่อน: Library Manager -> "HX711" by Bogdan Necula
//
// ขั้นตอน
// 1. อัปโหลด แล้วเปิด Serial Monitor 115200
// 2. เอาของออกจากถ้วยให้หมด กด t เพื่อ tare
// 3. วางของที่รู้น้ำหนักลงไป จดค่า raw ที่ขึ้น
// 4. คำนวณ SCALE = (raw_มีของ - raw_ว่าง) / น้ำหนักเป็นกรัม
// 5. ใส่ค่านั้นที่ SCALE ด้านล่าง อัปโหลดใหม่ แล้วชั่งเทียบตาชั่งอีกครั้ง

#include "HX711.h"

const int DT_PIN = D0;
const int SCK_PIN = D3;

// 1.0 หมายถึงยังไม่คาลิเบรต ค่าที่แสดงจะเป็นค่าดิบ
float SCALE = 1.0;

HX711 scale;

void setup() {
  Serial.begin(115200);
  Serial.println();
  Serial.println("HX711 test");
  Serial.println("t = tare, r = อ่านซ้ำ 10 ครั้ง");
  scale.begin(DT_PIN, SCK_PIN);
  scale.set_scale(SCALE);
  delay(400);
}

void tare() {
  Serial.print("tare... ");
  scale.tare(20);
  Serial.println("done");
}

void loop() {
  if (Serial.available()) {
    char c = Serial.read();
    if (c == 't') tare();
    if (c == 'r') {
      Serial.print("raw avg: ");
      Serial.println(scale.read_average(10));
    }
  }

  if (scale.is_ready()) {
    long raw = scale.read_average(5);
    float grams = (raw - scale.get_offset()) / SCALE;
    Serial.print("raw ");
    Serial.print(raw);
    Serial.print("   grams ");
    Serial.println(grams, 2);
  } else {
    Serial.println("HX711 not ready: เช็คสาย DT, SCK และไฟเลี้ยง");
  }

  delay(500);
}
