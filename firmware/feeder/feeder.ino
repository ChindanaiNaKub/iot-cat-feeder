// เครื่องให้อาหารแมวอัตโนมัติ — NodeMCU v3 + SG90
//
// วิธีใช้
// 1. สร้างไฟล์ secrets.h ข้างๆ ไฟล์นี้ ใส่ชื่อและรหัส Wi-Fi (ดู secrets.example.h)
// 2. เลือกบอร์ด NodeMCU 1.0 (ESP-12E Module) แล้วอัปโหลด
// 3. เปิด Serial Monitor 115200 รอจนขึ้น IP แล้วเปิดเบราว์เซอร์ไปที่ IP นั้น
// 4. ตอนใช้งานจริงให้จ่ายไฟจาก powerbank 2A พอร์ต USB ของโน้ตบุ๊กจ่ายกระแสไม่พอ servo

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

const int SERVO_PIN = D5;
const int CLOSED_DEG = 0;
const int OPEN_DEG = 180;           // servo ตัวนี้ให้ระยะจริงราว 95 องศา
const unsigned long OPEN_MS = 900;  // เปิดฝาค้างไว้กี่มิลลิวินาที

const int SCHEDULE_COUNT = 3;
const int SCHEDULE_HOUR[SCHEDULE_COUNT] = {8, 13, 18};
const int SCHEDULE_MINUTE = 0;
const long TZ_OFFSET = 7 * 3600;    // ไทย UTC+7 ไม่มีเวลาแสงอาทิตย์ออมทรัพย์

struct Feeder {
  bool open = false;
  unsigned long openedAt = 0;
  int countToday = 0;
  int lastDay = -1;
  String lastTime = "-";
  String lastSource = "";
} feeder;
// shortcut: ประวัตินับเฉพาะใน RAM รีเซ็ตเมื่อรีบูต ถ้าต้องเก็บข้ามรีบูตให้ย้ายไป EEPROM

Servo servo;
ESP8266WebServer server(80);
int lastMinuteKey = -1;
unsigned long lastWifiTry = 0;
bool announced = false;

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
  char buf[260];
  snprintf(buf, sizeof(buf),
           "{\"open\":%s,\"count\":%d,\"last\":\"%s\",\"source\":\"%s\",\"time\":\"%s\","
           "\"schedule\":\"%s\",\"ip\":\"%s\",\"rssi\":%d}",
           feeder.open ? "true" : "false",
           feeder.countToday,
           feeder.lastTime.c_str(),
           feeder.lastSource.c_str(),
           clockText().c_str(),
           scheduleText().c_str(),
           WiFi.localIP().toString().c_str(),
           WiFi.RSSI());
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

  if (feeder.open && millis() - feeder.openedAt >= OPEN_MS) closeFlap();

  checkSchedule();
  keepWifi();
}
