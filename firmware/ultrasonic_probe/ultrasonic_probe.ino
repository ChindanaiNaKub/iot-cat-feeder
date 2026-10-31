// ตรวจว่าขา ECHO ของ HC-SR04 ส่งสัญญาณกลับมาจริงไหม
// ใช้เมื่อ ultrasonic_test ขึ้นค่าว่างหรือ -1 ตลอด
//
// ต่อเหมือนกัน:  ตรวจจับแมว TRIG D6 / ECHO D7 ผ่านตัวแบ่ง 1k+2k
//                วัดระดับ    TRIG D1 / ECHO D2 ผ่านตัวแบ่ง 1k+2k

const int TRIGS[] = {D6, D1};
const int ECHOS[] = {D7, D2};
const char *NAMES[] = {"presence  D6/D7", "level     D1/D2"};

void setup() {
  Serial.begin(115200);
  delay(200);
  Serial.println();
  Serial.println("=== ultrasonic probe ===");
  Serial.println("echo idle = สถานะขา ECHO ตอนยังไม่ยิง");
  Serial.println("pulse     = ความยาวพัลส์ที่วัดได้ หน่วยไมโครวินาที");
  Serial.println();

  for (int i = 0; i < 2; i++) {
    pinMode(TRIGS[i], OUTPUT);
    pinMode(ECHOS[i], INPUT);
    digitalWrite(TRIGS[i], LOW);
  }
  delay(300);
}

void loop() {
  for (int i = 0; i < 2; i++) {
    int trig = TRIGS[i];
    int echo = ECHOS[i];

    Serial.print(NAMES[i]);
    Serial.print("  echo idle=");
    Serial.print(digitalRead(echo));

    digitalWrite(trig, LOW);
    delayMicroseconds(4);
    digitalWrite(trig, HIGH);
    delayMicroseconds(10);
    digitalWrite(trig, LOW);

    unsigned long us = pulseIn(echo, HIGH, 30000);

    Serial.print("  pulse=");
    Serial.print(us);
    Serial.print(" us");

    if (us == 0) {
      Serial.print("   << ไม่มีสัญญาณกลับ");
    } else if (us >= 30000) {
      Serial.print("   << ECHO ค้างสูงตลอด");
    } else {
      Serial.print("   << ได้ ");
      Serial.print(us / 58.0, 1);
      Serial.print(" cm");
    }
    Serial.println();
    delay(60);
  }
  delay(400);
}
