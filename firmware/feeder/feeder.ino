// เครื่องให้อาหารแมวอัตโนมัติ — NodeMCU v3 + SG90 + HC-SR04 สองตัว
//
// เวอร์ชัน 2: เพิ่มเซ็นเซอร์ตรวจจับแมวและวัดระดับอาหาร
// ยังไม่รวม load cell เพราะโมดูล HX711 ยังไม่ได้บัดกรีขา
//
// ขาที่ใช้
//   servo      สัญญาณ D5   (GPIO14)
//   ตรวจจับแมว  TRIG D6     (GPIO12)   ECHO D7 (GPIO13)  ผ่านตัวแบ่ง 1k/2k
//   วัดระดับ    TRIG D1     (GPIO5)    ECHO D2 (GPIO4)   ผ่านตัวแบ่ง 1k/2k
//
// วิธีใช้
// 1. สร้าง secrets.h ข้างๆ ไฟล์นี้ ใส่ชื่อและรหัส Wi-Fi (ดู secrets.example.h)
// 2. เลือกบอร์ด NodeMCU 1.0 (ESP-12E Module) แล้วอัปโหลด
// 3. เปิด Serial Monitor 115200 รอจนขึ้น IP แล้วเปิดเบราว์เซอร์ไปที่ IP นั้น
// 4. จ่ายไฟจาก powerbank 2A พอร์ต USB ของโน้ตบุ๊กจ่ายกระแสไม่พอ servo

#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <Servo.h>
#include <time.h>

#if __has_include("secrets.h")
  #include "secrets.h"
#else
  #define WIFI_SSID "CHANGE_ME"
  #define WIFI_PASS "CHANGE_ME"
#endif

// ---------------------------------------------------------------- ขา
const int SERVO_PIN = D5;
const int PRESENCE_TRIG = D6;
const int PRESENCE_ECHO = D7;
const int LEVEL_TRIG = D1;
const int LEVEL_ECHO = D2;

// ---------------------------------------------------------------- ค่าปรับแต่ง
const int CLOSED_DEG = 0;
const int OPEN_DEG = 180;            // ถ้า servo สั่นหรือฝาชน ให้ลดค่านี้ลงตามที่วัดได้จริง
const unsigned long OPEN_MS = 900;

const int SCHEDULE_COUNT = 3;
const int SCHEDULE_HOUR[SCHEDULE_COUNT] = {8, 13, 18};
const int SCHEDULE_MINUTE = 0;
const long TZ_OFFSET = 7 * 3600;     // ไทย UTC+7

const float NEAR_CM = 60.0;          // ระยะที่ถือว่าแมวเข้ามาใกล้
const float LEVEL_EMPTY_CM = 18.0;   // ระยะจากเซ็นเซอร์ถึงก้นถังตอนถังว่าง ต้องวัดเอง
const float LEVEL_FULL_CM = 4.0;     // ระยะตอนอาหารเต็มถัง ต้องวัดเอง

const unsigned long COOLDOWN_MS = 30UL * 60UL * 1000UL;  // พักหลังให้อาหารเพราะแมวมา
const int PRESENCE_CAP = 6;          // ให้เพราะแมวมาได้กี่ครั้งต่อวัน

const unsigned long SAMPLE_MS = 60;  // อ่านเซ็นเซอร์แต่ละตัวทุกกี่มิลลิวินาที
const int BUF_N = 5;                 // เก็บค่าล่าสุดกี่ครั้งเพื่อหาค่ากลาง
const unsigned long ECHO_TIMEOUT_US = 12000;  // ประมาณ 2 เมตร

// ---------------------------------------------------------------- โครงสร้าง
struct Feeder {
  bool open = false;
  unsigned long openedAt = 0;
  int countToday = 0;
  int lastDay = -1;
  String lastTime = "-";
  String lastSource = "";
} feeder;

// อ่านทีละครั้งต่อรอบ ไม่บล็อกนาน เหมือน ultrasonic_test แต่ไม่วนรัว
struct Ranger {
  int trig;
  int echo;
  float buf[BUF_N];
  int filled = 0;
  int next = 0;
  unsigned long dueAt = 0;
  float last = -1;
};

Ranger presence = {PRESENCE_TRIG, PRESENCE_ECHO, {0}, 0, 0, 0, -1};
Ranger level = {LEVEL_TRIG, LEVEL_ECHO, {0}, 0, 0, 0, -1};

Servo servo;
ESP8266WebServer server(80);
int lastMinuteKey = -1;
unsigned long lastWifiTry = 0;
bool announced = false;

int confirmCount = 0;
unsigned long cooldownUntil = 0;
int presenceToday = 0;
int presenceDay = -1;
bool catNow = false;

// ---------------------------------------------------------------- หน้าเว็บ
const char PAGE[] PROGMEM = R"HTML(<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#f7f2e9">
<title>เครื่องให้อาหารแมว</title>
<style>
  :root{--ink:#2a2622;--muted:#6b635a;--line:rgba(42,38,34,.12);--accent:#2f6fd0}
  *{box-sizing:border-box}
  body{margin:0;min-height:100vh;background:#f7f2e9;color:var(--ink);
       font-family:"Noto Sans Thai",system-ui,-apple-system,sans-serif;
       display:flex;justify-content:center}
  main{width:100%;max-width:420px;padding:30px 20px 40px}
  h1{font-size:19px;margin:0 0 2px;letter-spacing:-.01em}
  .sub{margin:0 0 20px;color:var(--muted);font-size:12.5px}
  .card{background:#fff;border:1px solid var(--line);border-radius:14px;padding:4px 16px;
        box-shadow:0 6px 20px rgba(60,45,25,.06)}
  .row{display:flex;justify-content:space-between;align-items:baseline;gap:12px;
       padding:12px 0;border-bottom:1px solid var(--line);font-size:13.5px;color:var(--muted)}
  .row:last-child{border-bottom:0}
  .row b{color:var(--ink);font-weight:600;text-align:right}
  #state.open{color:var(--accent)}
  #cat.near{color:#b45309}
  button{width:100%;margin-top:18px;padding:16px;font:inherit;font-size:15px;font-weight:600;
         color:#fff;background:var(--accent);border:0;border-radius:12px;cursor:pointer;
         transition:opacity .15s ease}
  button:disabled{opacity:.55;cursor:default}
  .foot{margin-top:16px;font-size:11.5px;color:var(--muted);text-align:center;line-height:1.8}
</style>
</head>
<body>
<main>
  <h1>เครื่องให้อาหารแมว</h1>
  <p class="sub">กดปุ่มเพื่อให้อาหารได้ทันที</p>

  <section class="card">
    <div class="row"><span>สถานะฝา</span><b id="state">กำลังโหลด</b></div>
    <div class="row"><span>ให้อาหารวันนี้</span><b id="count">-</b></div>
    <div class="row"><span>ครั้งล่าสุด</span><b id="last">-</b></div>
    <div class="row"><span>อาหารคงเหลือ</span><b id="level">-</b></div>
    <div class="row"><span>แมวอยู่ใกล้</span><b id="cat">-</b></div>
    <div class="row"><span>เวลาบนเครื่อง</span><b id="time">-</b></div>
    <div class="row"><span>ตั้งเวลาไว้</span><b id="sched">-</b></div>
  </section>

  <button id="feed">ให้อาหารเดี๋ยวนี้</button>
  <p class="foot" id="net">กำลังเชื่อมต่อบอร์ด</p>
</main>
<script>
  const $ = id => document.getElementById(id);

  async function refresh() {
    try {
      const r = await fetch('/status', { cache: 'no-store' });
      const s = await r.json();
      $('state').textContent = s.open ? 'เปิดอยู่' : 'ปิดสนิท';
      $('state').className = s.open ? 'open' : '';
      $('count').textContent = s.count + ' ครั้ง';
      $('last').textContent = s.last === '-' ? 'ยังไม่เคย' : s.last + (s.source ? ' (' + s.source + ')' : '');
      $('level').textContent = s.level < 0 ? 'อ่านไม่ได้' : s.level + ' %';
      $('cat').textContent = s.near < 0 ? 'อ่านไม่ได้'
        : (s.cat ? 'ใช่  ' + s.near.toFixed(0) + ' ซม.' : 'ไม่  ' + s.near.toFixed(0) + ' ซม.');
      $('cat').className = s.cat ? 'near' : '';
      $('time').textContent = s.time;
      $('sched').textContent = s.schedule;
      $('net').textContent = 'Wi-Fi ' + s.rssi + ' dBm · ' + s.ip;
    } catch (e) {
      $('net').textContent = 'ขาดการเชื่อมต่อกับบอร์ด';
    }
  }

  $('feed').onclick = async () => {
    const b = $('feed');
    b.disabled = true;
    try { await fetch('/feed', { method: 'POST' }); } catch (e) {}
    setTimeout(() => { b.disabled = false; refresh(); }, 1300);
  };

  refresh();
  setInterval(refresh, 2000);
</script>
</body>
</html>)HTML";

// ---------------------------------------------------------------- เซ็นเซอร์
float readOnce(Ranger &r) {
  digitalWrite(r.trig, LOW);
  delayMicroseconds(4);
  digitalWrite(r.trig, HIGH);
  delayMicroseconds(10);
  digitalWrite(r.trig, LOW);

  unsigned long us = pulseIn(r.echo, HIGH, ECHO_TIMEOUT_US);
  if (us == 0) return -1;
  float cm = us / 58.0;
  if (cm < 2.0 || cm > 250.0) return -1;
  return cm;
}

void sampleRanger(Ranger &r, unsigned long now) {
  if (now < r.dueAt) return;
  r.dueAt = now + SAMPLE_MS;

  float cm = readOnce(r);
  if (cm < 0) return;

  r.buf[r.next] = cm;
  r.next = (r.next + 1) % BUF_N;
  if (r.filled < BUF_N) r.filled++;

  float sorted[BUF_N];
  for (int i = 0; i < r.filled; i++) sorted[i] = r.buf[i];
  for (int i = 1; i < r.filled; i++) {
    float key = sorted[i];
    int j = i - 1;
    while (j >= 0 && sorted[j] > key) { sorted[j + 1] = sorted[j]; j--; }
    sorted[j + 1] = key;
  }
  r.last = sorted[r.filled / 2];
}

int hopperPercent() {
  if (level.last < 0 || level.filled == 0) return -1;
  float span = LEVEL_EMPTY_CM - LEVEL_FULL_CM;
  if (span <= 0) return -1;
  float pct = (LEVEL_EMPTY_CM - level.last) / span * 100.0;
  if (pct < 0) pct = 0;
  if (pct > 100) pct = 100;
  return (int)(pct + 0.5);
}

void checkPresence() {
  catNow = (presence.last > 0 && presence.last <= NEAR_CM);

  if (!catNow) {
    confirmCount = 0;
    return;
  }
  if (confirmCount < 3) {
    confirmCount++;
    return;
  }
  if (feeder.open) return;
  if (millis() < cooldownUntil) return;

  if (feeder.lastDay != -1 && presenceDay != feeder.lastDay) {
    presenceDay = feeder.lastDay;
    presenceToday = 0;
  }
  if (presenceToday >= PRESENCE_CAP) return;

  feed("เซ็นเซอร์");
  presenceToday++;
  cooldownUntil = millis() + COOLDOWN_MS;
  confirmCount = 0;
}

// ---------------------------------------------------------------- เวลาและการให้อาหาร
String scheduleText() {
  String s = "";
  for (int i = 0; i < SCHEDULE_COUNT; i++) {
    char buf[6];
    snprintf(buf, sizeof(buf), "%02d:%02d", SCHEDULE_HOUR[i], SCHEDULE_MINUTE);
    if (i) s += " · ";
    s += buf;
  }
  return s;
}

String clockText() {
  time_t now = time(nullptr);
  if (now < 1600000000) return "--:--:--";
  struct tm t;
  localtime_r(&now, &t);
  char buf[10];
  snprintf(buf, sizeof(buf), "%02d:%02d:%02d", t.tm_hour, t.tm_min, t.tm_sec);
  return String(buf);
}

void markFeed(const String &source) {
  time_t now = time(nullptr);
  if (now > 1600000000) {
    struct tm t;
    localtime_r(&now, &t);
    char buf[6];
    snprintf(buf, sizeof(buf), "%02d:%02d", t.tm_hour, t.tm_min);
    feeder.lastTime = buf;
    if (t.tm_mday != feeder.lastDay) {
      feeder.lastDay = t.tm_mday;
      feeder.countToday = 0;
    }
  }
  feeder.countToday++;
  feeder.lastSource = source;
}

void feed(const String &source) {
  markFeed(source);
  servo.write(OPEN_DEG);
  feeder.open = true;
  feeder.openedAt = millis();
  Serial.println("ให้อาหาร: " + source);
}

void closeFlap() {
  servo.write(CLOSED_DEG);
  feeder.open = false;
}

void checkSchedule() {
  time_t now = time(nullptr);
  if (now < 1600000000) return;

  struct tm t;
  localtime_r(&now, &t);
  int key = (t.tm_mday * 100 + t.tm_hour) * 100 + t.tm_min;
  if (key == lastMinuteKey) return;
  lastMinuteKey = key;

  for (int i = 0; i < SCHEDULE_COUNT; i++) {
    if (t.tm_hour == SCHEDULE_HOUR[i] && t.tm_min == SCHEDULE_MINUTE) {
      feed("ตั้งเวลา");
      return;
    }
  }
}

String statusJson() {
  char buf[420];
  int pct = hopperPercent();
  snprintf(buf, sizeof(buf),
           "{\"open\":%s,\"count\":%d,\"last\":\"%s\",\"source\":\"%s\",\"time\":\"%s\","
           "\"schedule\":\"%s\",\"ip\":\"%s\",\"rssi\":%d,"
           "\"level\":%d,\"near\":%.1f,\"cat\":%s,\"cap\":%d}",
           feeder.open ? "true" : "false",
           feeder.countToday,
           feeder.lastTime.c_str(),
           feeder.lastSource.c_str(),
           clockText().c_str(),
           scheduleText().c_str(),
           WiFi.localIP().toString().c_str(),
           WiFi.RSSI(),
           pct,
           presence.last,
           catNow ? "true" : "false",
           presenceToday);
  return String(buf);
}

void keepWifi() {
  if (WiFi.status() == WL_CONNECTED) {
    if (!announced) {
      announced = true;
      Serial.print("เปิดเว็บที่ http://");
      Serial.println(WiFi.localIP());
    }
    return;
  }

  announced = false;
  if (millis() - lastWifiTry < 5000) return;
  lastWifiTry = millis();
  Serial.println("ต่อ Wi-Fi ใหม่");
  WiFi.begin(WIFI_SSID, WIFI_PASS);
}

void setup() {
  Serial.begin(115200);
  servo.attach(SERVO_PIN);
  servo.write(CLOSED_DEG);

  pinMode(PRESENCE_TRIG, OUTPUT);
  pinMode(PRESENCE_ECHO, INPUT);
  pinMode(LEVEL_TRIG, OUTPUT);
  pinMode(LEVEL_ECHO, INPUT);
  digitalWrite(PRESENCE_TRIG, LOW);
  digitalWrite(LEVEL_TRIG, LOW);

  // ให้สองตัวยิงเหลื่อมกัน กันเสียงชนกัน
  presence.dueAt = millis();
  level.dueAt = millis() + SAMPLE_MS / 2;

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  configTime(TZ_OFFSET, 0, "pool.ntp.org", "time.nist.gov");

  server.on("/", []() {
    server.send_P(200, "text/html; charset=utf-8", PAGE);
  });
  server.on("/status", []() {
    server.send(200, "application/json; charset=utf-8", statusJson());
  });
  server.on("/feed", HTTP_POST, []() {
    feed("เว็บ");
    server.send(200, "application/json", "{\"ok\":true}");
  });
  server.onNotFound([]() {
    server.send(404, "text/plain; charset=utf-8", "ไม่พบหน้านี้");
  });
  server.begin();
}

void loop() {
  server.handleClient();

  unsigned long now = millis();
  sampleRanger(presence, now);
  sampleRanger(level, now);
  checkPresence();

  if (feeder.open && millis() - feeder.openedAt > OPEN_MS) closeFlap();

  checkSchedule();
  keepWifi();
}
