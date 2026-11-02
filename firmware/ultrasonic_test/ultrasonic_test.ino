// ทดสอบ HC-SR04 สองตัวบน NodeMCU v3
//
// ตัวที่ 1 ตรวจจับแมว:  TRIG = D6 (GPIO12), ECHO = D7 (GPIO13)
// ตัวที่ 2 วัดระดับอาหาร: TRIG = D1 (GPIO5),  ECHO = D2 (GPIO4)
//
// ECHO จ่าย 5V ต้องผ่านตัวแบ่ง 2.2k ต่ออนุกรม แล้ว 3.3k ลงกราวด์
// ถ้าใช้ HC-SR04P ที่จ่าย 3.3V ได้ ให้ต่อตรงและข้ามตัวแบ่ง
//
// เปิด Serial Monitor 115200 แล้วเอามือกวาดหน้าตัวที่ 1 ดูว่าค่าเปลี่ยนตาม

const int PRESENCE_TRIG = D6;
const int PRESENCE_ECHO = D7;
const int LEVEL_TRIG = D1;
const int LEVEL_ECHO = D2;

const int SAMPLES = 7;
const float MIN_CM = 2.0;
const float MAX_CM = 300.0;

void setup() {
  Serial.begin(115200);
  Serial.println();
  Serial.println("HC-SR04 test");
  Serial.println("near = <= 60 cm");

  pinMode(PRESENCE_TRIG, OUTPUT);
  pinMode(PRESENCE_ECHO, INPUT);
  pinMode(LEVEL_TRIG, OUTPUT);
  pinMode(LEVEL_ECHO, INPUT);
  digitalWrite(PRESENCE_TRIG, LOW);
  digitalWrite(LEVEL_TRIG, LOW);
}

float readCm(int trig, int echo) {
  digitalWrite(trig, LOW);
  delayMicroseconds(4);
  digitalWrite(trig, HIGH);
  delayMicroseconds(10);
  digitalWrite(trig, LOW);

  unsigned long us = pulseIn(echo, HIGH, 20000);
  if (us == 0) return -1;
  return us / 58.0;
}

// ค่ากลางของหลายครั้ง กัน echo หลอกครั้งเดียว
float medianCm(int trig, int echo) {
  float buf[SAMPLES];
  int n = 0;
  for (int i = 0; i < SAMPLES; i++) {
    float v = readCm(trig, echo);
    if (v > MIN_CM && v < MAX_CM) buf[n++] = v;
    delay(12);
  }
  if (n == 0) return -1;

  for (int i = 1; i < n; i++) {
    float key = buf[i];
    int j = i - 1;
    while (j >= 0 && buf[j] > key) {
      buf[j + 1] = buf[j];
      j--;
    }
    buf[j + 1] = key;
  }
  return buf[n / 2];
}

void loop() {
  float presence = medianCm(PRESENCE_TRIG, PRESENCE_ECHO);
  float level = medianCm(LEVEL_TRIG, LEVEL_ECHO);

  Serial.print("presence ");
  if (presence < 0) Serial.print("----");
  else Serial.print(presence, 1);
  Serial.print(" cm  ");
  Serial.print(presence > 0 && presence <= 60 ? "NEAR" : "far ");

  Serial.print("   |   level ");
  if (level < 0) Serial.print("----");
  else Serial.print(level, 1);
  Serial.println(" cm");

  delay(250);
}
