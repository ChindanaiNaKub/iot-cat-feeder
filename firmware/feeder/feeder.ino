// เครื่องให้อาหารแมวอัตโนมัติ — NodeMCU v3 + SG90 + HC-SR04 สองตัว
//
// เวอร์ชัน 2: เพิ่มเซ็นเซอร์ตรวจจับแมวและวัดระดับอาหาร
// ยังไม่รวม load cell เพราะโมดูล HX711 ยังไม่ได้บัดกรีขา
//
// ขาที่ใช้
//   servo      สัญญาณ D5   (GPIO14)
//   ตรวจจับแมว  TRIG D6     (GPIO12)   ECHO D7 (GPIO13)  ผ่านตัวแบ่ง 2.2k/3.3k
//   วัดระดับ    TRIG D1     (GPIO5)    ECHO D2 (GPIO4)   ผ่านตัวแบ่ง 2.2k/3.3k
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
const int OPEN_DEG = 90;             // ค่าชั่วคราว ให้รัน servo_test หามุมจริงก่อน แล้วใส่ค่าที่ได้ลบ 5
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
  char lastTime[6] = "-";
  const char* lastSource = "";
} feeder;

// ห้าครั้งล่าสุดแบบวงกลม ไม่มี String จึงไม่กิน heap
const int HISTORY_N = 5;
struct FeedLog { char time[6]; const char* source; };
FeedLog history[HISTORY_N];
int historyCount = 0;
int historyHead = 0;   // ช่องถัดไปที่จะเขียน

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
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#f4efe6">
<meta name="color-scheme" content="light">
<title>เครื่องให้อาหารแมว</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='9' fill='%231d5c43'/%3E%3Ccircle cx='16' cy='18' r='6' fill='%23fffcf7'/%3E%3C/svg%3E">
<style>
  :root{
    --paper:#f4efe6; --surface:#fffcf7; --ink:#221d18; --muted:#665c51;
    --line:rgba(34,29,24,.14); --line-soft:rgba(34,29,24,.08);
    --green:#1d5c43; --green-soft:rgba(29,92,67,.10);
    --amber:#a85400; --amber-soft:rgba(168,84,0,.10);
    --red:#9b2c2c; --red-soft:rgba(155,44,44,.10);
    --ease:cubic-bezier(.25,1,.5,1);
  }
  @property --p{syntax:"<number>";inherits:false;initial-value:0}
  *{box-sizing:border-box}
  html{-webkit-text-size-adjust:100%}
  body{
    margin:0;background:var(--paper);color:var(--ink);font-size:14px;line-height:1.5;
    font-family:"Noto Sans Thai","Sarabun",system-ui,-apple-system,"Segoe UI",sans-serif;
    -webkit-font-smoothing:antialiased;
    padding:env(safe-area-inset-top) 0 env(safe-area-inset-bottom);
  }
  main{max-width:460px;margin:0 auto;padding:22px 18px 26px;transition:opacity .25s var(--ease)}
  body.off main{opacity:.55}

  /* ---------- identity + clock ---------- */
  .top{display:flex;align-items:flex-start;justify-content:space-between;gap:14px;margin-bottom:20px}
  h1{margin:0;font-size:16.5px;font-weight:600;letter-spacing:-.01em}
  .tag{display:flex;align-items:center;gap:7px;margin:6px 0 0;font-size:11.5px;color:var(--muted);font-variant-numeric:tabular-nums}
  .live{width:7px;height:7px;border-radius:50%;background:var(--green);box-shadow:0 0 0 3px var(--green-soft);flex:none}
  body.off .live{background:var(--red);box-shadow:0 0 0 3px var(--red-soft)}
  .clock{text-align:right;line-height:1}
  .clock b{font-size:22px;font-weight:600;letter-spacing:-.02em;font-variant-numeric:tabular-nums}
  .clock small{display:block;margin-top:5px;font-size:10.5px;color:var(--muted)}

  /* ---------- flap state ---------- */
  .flap{position:relative;overflow:hidden;display:flex;align-items:center;gap:12px;
        padding:14px 16px 15px;border-radius:18px;border:1px solid rgba(29,92,67,.16);
        background:var(--green-soft);transition:background .22s var(--ease),border-color .22s var(--ease)}
  .flap .dot{width:10px;height:10px;border-radius:50%;background:var(--green);flex:none}
  .flap b{display:block;font-size:15px;font-weight:600;line-height:1.25}
  .flap .sub{display:block;margin-top:2px;font-size:12px;color:var(--muted);font-variant-numeric:tabular-nums}
  .flap .today{margin-left:auto;text-align:right;font-size:10.5px;color:var(--muted);line-height:1.3}
  .flap .today b{font-size:18px;color:var(--ink);font-variant-numeric:tabular-nums}
  .flap[data-open="1"]{background:var(--amber-soft);border-color:rgba(168,84,0,.22)}
  .flap[data-open="1"] .dot{background:var(--amber);animation:pulse 1.4s var(--ease) infinite}
  .flap[data-open="1"] b{color:var(--amber)}
  .flap[data-open="1"]::after{content:"";position:absolute;left:0;bottom:0;height:2px;width:100%;
        background:var(--amber);transform-origin:left;animation:drain .95s linear forwards}
  @keyframes pulse{0%,100%{box-shadow:0 0 0 0 rgba(168,84,0,.4)}50%{box-shadow:0 0 0 7px rgba(168,84,0,0)}}
  @keyframes drain{from{transform:scaleX(1)}to{transform:scaleX(0)}}

  /* ---------- live panels ---------- */
  .grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:12px}
  .panel{background:var(--surface);border:1px solid var(--line-soft);border-radius:18px;padding:14px 15px}
  .panel h2{margin:0;font-size:12px;font-weight:500;color:var(--muted)}
  .panel p{margin:0;font-size:11.5px;color:var(--muted);text-align:center;line-height:1.4}

  .dial{--p:0;--tone:var(--green);position:relative;width:100%;max-width:110px;aspect-ratio:1;margin:14px auto 12px;display:grid;place-items:center}
  .ring{position:absolute;inset:0;border-radius:50%;
        background:conic-gradient(var(--tone) calc(var(--p) * 1%), rgba(34,29,24,.07) 0);
        -webkit-mask:radial-gradient(farthest-side,#0000 calc(100% - 11px),#000 calc(100% - 10px));
        mask:radial-gradient(farthest-side,#0000 calc(100% - 11px),#000 calc(100% - 10px));
        transition:--p .7s var(--ease)}
  .dialIn{text-align:center;line-height:1}
  .dialIn b{font-size:29px;font-weight:600;letter-spacing:-.03em;font-variant-numeric:tabular-nums}
  .dialIn span{font-size:12.5px;color:var(--muted)}

  .radar{position:relative;width:100%;max-width:110px;aspect-ratio:1;margin:14px auto 12px;display:grid;place-items:center}
  .radar i{position:absolute;border-radius:50%;border:1px solid rgba(34,29,24,.12);inset:0}
  .radar i:nth-child(2){inset:17px;border-color:rgba(34,29,24,.16)}
  .radar i:nth-child(3){inset:34px;border-color:rgba(34,29,24,.2)}
  .radarIn{position:relative;text-align:center;line-height:1}
  .radarIn b{font-size:22px;font-weight:600;letter-spacing:-.02em;font-variant-numeric:tabular-nums}
  .radarIn span{display:block;margin-top:2px;font-size:10.5px;color:var(--muted)}
  .radar.near i{border-color:rgba(168,84,0,.28)}
  .radar.near .radarIn b{color:var(--amber)}
  .radar.near::after{content:"";position:absolute;inset:0;border-radius:50%;
        border:1px solid rgba(168,84,0,.35);animation:radar 2.2s var(--ease) infinite}
  @keyframes radar{0%{transform:scale(.62);opacity:.9}100%{transform:scale(1);opacity:0}}

  /* ---------- schedule + log ---------- */
  .head{display:flex;align-items:baseline;justify-content:space-between;gap:10px;margin-bottom:9px}
  .head h2{margin:0;font-size:12.5px;font-weight:500;color:var(--muted)}
  .head span{font-size:11.5px;color:var(--muted);font-variant-numeric:tabular-nums}
  .sched{margin-top:20px}
  .chips{display:flex;gap:8px;margin:0;padding:0;list-style:none}
  .chip{flex:1;padding:9px 4px 8px;border-radius:12px;border:1px solid var(--line);
        text-align:center;font-size:14px;font-weight:500;font-variant-numeric:tabular-nums;
        color:var(--ink);transition:background .2s var(--ease),color .2s var(--ease),border-color .2s var(--ease)}
  .chip small{display:block;margin-top:1px;font-size:10px;font-weight:400;color:var(--muted)}
  .chip.next{background:var(--green);border-color:var(--green);color:#fff}
  .chip.next small{color:rgba(255,255,255,.78)}

  .log{margin-top:20px}
  .log ol{list-style:none;margin:0;padding:0;border-top:1px solid var(--line-soft)}
  .log li{display:flex;align-items:center;gap:10px;padding:10px 0;
          border-bottom:1px solid var(--line-soft);font-size:13.5px}
  .log time{min-width:46px;font-weight:600;font-variant-numeric:tabular-nums}
  .badge{font-size:11px;padding:2px 9px;border-radius:999px;
         background:var(--green-soft);color:var(--green)}
  .badge[data-kind="sensor"]{background:var(--amber-soft);color:var(--amber)}
  .badge[data-kind="timer"]{background:rgba(34,29,24,.06);color:var(--muted)}
  .log li.empty{padding:15px 0 14px;font-size:12.5px;color:var(--muted)}

  /* ---------- action ---------- */
  #feed{width:100%;min-height:56px;margin-top:22px;padding:0 20px;
        font:inherit;font-size:15.5px;font-weight:600;color:#fff;
        background:var(--green);border:0;border-radius:14px;cursor:pointer;
        box-shadow:0 8px 18px -8px rgba(29,92,67,.55);
        transition:transform .12s var(--ease),background .18s var(--ease),box-shadow .18s var(--ease)}
  #feed:hover{background:#17503a}
  #feed:active{transform:scale(.985);box-shadow:0 4px 10px -6px rgba(29,92,67,.5)}
  #feed:focus-visible{outline:3px solid var(--ink);outline-offset:2px}
  #feed:disabled{background:#57625b;box-shadow:none;cursor:default;transform:none}

  .foot{display:flex;justify-content:space-between;gap:10px;margin:15px 0 0;
        font-size:11px;color:var(--muted);font-variant-numeric:tabular-nums}

  .toast{position:fixed;left:50%;bottom:calc(24px + env(safe-area-inset-bottom));z-index:20;
         transform:translate(-50%,14px);padding:10px 18px;border-radius:999px;
         background:var(--ink);color:#fff;font-size:13px;opacity:0;pointer-events:none;
         box-shadow:0 10px 26px rgba(20,15,10,.28);
         transition:opacity .2s var(--ease),transform .2s var(--ease)}
  .toast.show{opacity:1;transform:translate(-50%,0)}

  @media (prefers-reduced-motion:reduce){
    *,*::before,*::after{animation:none!important;transition:none!important}
  }
</style>
</head>
<body>
<main>
  <div class="top">
    <div>
      <h1>เครื่องให้อาหารแมว</h1>
      <p class="tag"><span class="live"></span><span id="net">กำลังเชื่อมต่อบอร์ด</span></p>
    </div>
    <div class="clock">
      <b id="clock">--:--</b>
      <small>เวลาเครื่อง</small>
    </div>
  </div>

  <section class="flap" id="flap" data-open="0">
    <span class="dot" aria-hidden="true"></span>
    <div>
      <b id="flapLabel" aria-live="polite">ฝาปิดสนิท</b>
      <span class="sub" id="flapSub">รอสถานะจากบอร์ด</span>
    </div>
    <div class="today"><b id="count">–</b>ครั้งวันนี้</div>
  </section>

  <div class="grid">
    <section class="panel">
      <h2>อาหารคงเหลือ</h2>
      <div class="dial" id="dial">
        <div class="ring" id="ring" aria-hidden="true"></div>
        <div class="dialIn"><b id="level">–</b><span>%</span></div>
      </div>
      <p id="levelNote">รอค่าจากเซ็นเซอร์</p>
    </section>

    <section class="panel">
      <h2>แมวอยู่ใกล้</h2>
      <div class="radar" id="radar">
        <i aria-hidden="true"></i><i aria-hidden="true"></i><i aria-hidden="true"></i>
        <div class="radarIn"><b id="catCm">–</b><span>ซม.</span></div>
      </div>
      <p id="catNote">ยังไม่รู้ระยะ</p>
    </section>
  </div>

  <section class="sched">
    <div class="head">
      <h2>ตั้งเวลาไว้</h2>
      <span id="next">–</span>
    </div>
    <ul class="chips" id="chips"></ul>
  </section>

  <section class="log">
    <div class="head">
      <h2>ประวัติการให้อาหาร</h2>
      <span id="logCount"></span>
    </div>
    <ol id="hist"></ol>
  </section>

  <button id="feed" type="button">ให้อาหารเดี๋ยวนี้</button>
  <p class="foot"><span id="rssi">สัญญาณ –</span><span>อัปเดตทุก 2 วินาที</span></p>
</main>

<div class="toast" id="toast" role="status" aria-live="polite"></div>

<noscript><p style="text-align:center;color:#6e6459">หน้านี้ต้องเปิด JavaScript เพื่ออ่านสถานะจากบอร์ด</p></noscript>

<script>
  var $ = function (id) { return document.getElementById(id); };
  var busy = false, lastState = null;

  function toMin(hhmm) {
    var p = String(hhmm).split(':');
    return (+p[0]) * 60 + (+p[1]);
  }

  function kindOf(src) {
    if (src.indexOf('เซ็นเซอร์') === 0) return 'sensor';
    if (src.indexOf('ตั้งเวลา') === 0) return 'timer';
    return 'web';
  }

  function countdownText(mins) {
    if (mins < 60) return 'อีก ' + mins + ' นาที';
    var h = Math.floor(mins / 60), m = mins % 60;
    return 'อีก ' + h + ' ชม.' + (m ? ' ' + m + ' น.' : '');
  }

  function renderChips(schedule, now) {
    var times = String(schedule || '').split('·').map(function (s) { return s.trim(); })
                .filter(function (s) { return /^\d\d:\d\d$/.test(s); });
    var next = null;
    if (/^\d\d:\d\d/.test(now) && times.length) {
      var cur = toMin(now), best = 1e9;
      times.forEach(function (t) {
        var d = toMin(t) - cur;
        if (d <= 0) d += 1440;
        if (d < best) { best = d; next = { t: t, d: d }; }
      });
    }
    var list = $('chips');
    list.textContent = '';
    times.forEach(function (t) {
      var li = document.createElement('li');
      li.className = 'chip' + (next && next.t === t ? ' next' : '');
      li.textContent = t;
      if (next && next.t === t) {
        var s = document.createElement('small');
        s.textContent = countdownText(next.d);
        li.appendChild(s);
      }
      list.appendChild(li);
    });
    $('next').textContent = next ? 'รอบถัดไป ' + next.t : 'รอเวลาเครื่อง';
  }

  function renderHistory(hist) {
    var list = $('hist');
    list.textContent = '';
    if (!hist || !hist.length) {
      var li = document.createElement('li');
      li.className = 'empty';
      li.textContent = 'ยังไม่มีประวัติในรอบนี้ กดปุ่มด้านล่างเพื่อเริ่ม';
      list.appendChild(li);
      $('logCount').textContent = '';
      return;
    }
    hist.forEach(function (h) {
      var li = document.createElement('li');
      var t = document.createElement('time');
      t.textContent = h.t;
      var b = document.createElement('span');
      b.className = 'badge';
      b.dataset.kind = kindOf(h.s);
      b.textContent = h.s;
      li.appendChild(t); li.appendChild(b);
      list.appendChild(li);
    });
    $('logCount').textContent = hist.length >= 5 ? '5 ครั้งล่าสุด' : hist.length + ' ครั้งล่าสุด';
  }

  function render(s) {
    lastState = s;

    var open = !!s.open;
    $('flap').dataset.open = open ? '1' : '0';
    $('flapLabel').textContent = open ? 'ฝาเปิดอยู่' : 'ฝาปิดสนิท';
    $('flapSub').textContent = open ? 'กำลังเทอาหาร เดี๋ยวปิดเอง'
      : (s.last && s.last !== '-' ? 'ล่าสุด ' + s.last + ' · ' + s.source : 'ยังไม่เคยให้อาหาร');
    $('count').textContent = s.count;

    var pct = (typeof s.level === 'number') ? s.level : -1;
    var ring = $('ring');
    var tone = pct < 15 ? '--red' : pct < 40 ? '--amber' : '--green';
    ring.style.setProperty('--p', pct < 0 ? 0 : pct);
    ring.style.setProperty('--tone', 'var(' + tone + ')');
    $('level').textContent = pct < 0 ? '–' : pct;
    $('levelNote').textContent = pct < 0 ? 'อ่านค่าไม่ได้ ตรวจเซ็นเซอร์'
      : pct < 15 ? 'ใกล้หมดแล้ว เติมอาหาร'
      : pct < 40 ? 'เหลือน้อย' : 'ยังมีพอ';

    var near = (typeof s.near === 'number') ? s.near : -1;
    var cat = !!s.cat && near >= 0;
    $('radar').classList.toggle('near', cat);
    $('catCm').textContent = near < 0 ? '–' : Math.round(near);
    $('catNote').textContent = near < 0 ? 'อ่านระยะไม่ได้' : (cat ? 'แมวอยู่ใกล้ถัง' : 'ไม่พบแมว');

    $('clock').textContent = /^\d\d:\d\d/.test(s.time || '') ? s.time.slice(0, 5) : '--:--';
    $('net').textContent = 'Wi-Fi ' + (s.ip || '–');
    $('rssi').textContent = 'สัญญาณ ' + s.rssi + ' dBm';
    document.body.classList.remove('off');
    $('feed').disabled = busy;

    renderChips(s.schedule, s.time);
    renderHistory(s.hist);
  }

  function offline() {
    document.body.classList.add('off');
    $('net').textContent = 'ต่อบอร์ดไม่ได้ กำลังลองใหม่';
    $('rssi').textContent = 'สัญญาณขาด';
  }

  function toast(msg) {
    var el = $('toast');
    el.textContent = msg;
    el.classList.add('show');
    clearTimeout(toast.timer);
    toast.timer = setTimeout(function () { el.classList.remove('show'); }, 2200);
  }

  function refresh() {
    if (document.hidden) return;
    fetch('/status', { cache: 'no-store' })
      .then(function (r) { return r.json(); })
      .then(render)
      .catch(offline);
  }

  $('feed').addEventListener('click', function () {
    if (busy) return;
    busy = true;
    var b = $('feed');
    b.disabled = true;
    b.textContent = 'กำลังให้อาหาร…';
    fetch('/feed', { method: 'POST', cache: 'no-store' })
      .then(function (r) { if (!r.ok) throw 0; return r.json(); })
      .then(function (s) { render(s); toast('ให้อาหารแล้ว'); })
      .catch(function () { offline(); toast('สั่งไม่สำเร็จ ลองอีกครั้ง'); })
      .then(function () {
        setTimeout(function () {
          busy = false;
          b.disabled = false;
          b.textContent = 'ให้อาหารเดี๋ยวนี้';
          refresh();
        }, 1200);
      });
  });

  document.addEventListener('visibilitychange', refresh);
  refresh();
  setInterval(refresh, 2000);
</script>
</body>
</html>
)HTML";

// ---------------------------------------------------------------- เซ็นเซอร์
void feed(const char* source);   // ประกาศเองเพราะ checkPresence เรียกก่อนนิยาม

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

void markFeed(const char* source) {
  char stamp[6] = "--:--";
  time_t now = time(nullptr);
  if (now > 1600000000) {
    struct tm t;
    localtime_r(&now, &t);
    snprintf(stamp, sizeof(stamp), "%02d:%02d", t.tm_hour, t.tm_min);
    if (t.tm_mday != feeder.lastDay) {
      feeder.lastDay = t.tm_mday;
      feeder.countToday = 0;
    }
  }
  memcpy(feeder.lastTime, stamp, sizeof(stamp));
  feeder.countToday++;
  feeder.lastSource = source;

  memcpy(history[historyHead].time, stamp, sizeof(stamp));
  history[historyHead].source = source;
  historyHead = (historyHead + 1) % HISTORY_N;
  if (historyCount < HISTORY_N) historyCount++;
}

void feed(const char* source) {
  markFeed(source);
  servo.write(OPEN_DEG);
  feeder.open = true;
  feeder.openedAt = millis();
  Serial.print("ให้อาหาร: ");
  Serial.println(source);
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

// คืน reference ของ buffer เดียว ไม่สร้าง String ใหม่ทุกครั้งที่ถูกเรียก
const String& statusJson() {
  static String out;
  static bool sized = false;
  if (!sized) { out.reserve(720); sized = true; }

  char num[64];
  int pct = hopperPercent();

  out = "{\"open\":";
  out += feeder.open ? "true" : "false";
  snprintf(num, sizeof(num), ",\"count\":%d,\"last\":\"", feeder.countToday);
  out += num;
  out += feeder.lastTime;
  out += "\",\"source\":\"";
  out += feeder.lastSource;
  out += "\",\"time\":\"";
  out += clockText();
  out += "\",\"schedule\":\"";
  out += scheduleText();
  out += "\",\"ip\":\"";
  out += WiFi.localIP().toString();
  snprintf(num, sizeof(num),
           "\",\"rssi\":%d,\"level\":%d,\"near\":%.1f,\"cat\":%s,\"cap\":%d,\"hist\":[",
           WiFi.RSSI(), pct, presence.last, catNow ? "true" : "false", presenceToday);
  out += num;

  for (int i = 0; i < historyCount; i++) {
    int idx = (historyHead - 1 - i + HISTORY_N * 2) % HISTORY_N;
    if (i) out += ",";
    out += "{\"t\":\"";
    out += history[idx].time;
    out += "\",\"s\":\"";
    out += history[idx].source;
    out += "\"}";
  }
  out += "]}";
  return out;
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
  delay(200);
  Serial.println();
  Serial.println("=== IoT Cat Feeder v2 ===");
  Serial.print("reset reason: ");
  Serial.println(ESP.getResetReason());
  Serial.print("free heap: ");
  Serial.println(ESP.getFreeHeap());

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
    server.send(200, "application/json; charset=utf-8", statusJson());
  });
  server.onNotFound([]() {
    server.send(404, "text/plain; charset=utf-8", "ไม่พบหน้านี้");
  });
  server.begin();
}

void loop() {
  server.handleClient();

  // บรรทัดสถานะทุก 2 วินาที ถ้าบรรทัดนี้หยุดไหล แปลว่าลูปค้าง
  static unsigned long lastStatus = 0;
  if (millis() - lastStatus > 2000) {
    lastStatus = millis();
    Serial.printf("flap %s  meals %d  level %d%%  near %.1f cm  cat %s  rssi %d\n",
                  feeder.open ? "open" : "shut",
                  feeder.countToday,
                  hopperPercent(),
                  presence.last,
                  catNow ? "yes" : "no",
                  WiFi.RSSI());
  }

  unsigned long now = millis();
  sampleRanger(presence, now);
  sampleRanger(level, now);
  checkPresence();

  if (feeder.open && millis() - feeder.openedAt > OPEN_MS) closeFlap();

  checkSchedule();
  keepWifi();
}
