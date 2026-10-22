# Wokwi simulation (ESP32 + servo)

ตัวอย่างวงจร servo สำหรับดูบน Wokwi ใช้ ESP32 แทน ESP8266 เพราะ Wokwi ไม่รองรับ ESP8266

## วิธีเปิด

1. ไปที่ https://wokwi.com แล้วสร้าง project ใหม่แบบ ESP32
2. ลบไฟล์ `sketch.ino` เดิม แล้ววางเนื้อหาจาก `sketch.ino` ในโฟลเดอร์นี้
3. เพิ่มไฟล์ `diagram.json` โดยวางเนื้อหาทับของเดิม
4. ใส่ `ESP32Servo` ในไฟล์ `libraries.txt` (ถ้ามี) หรือเพิ่มจาก Library Manager
5. กด Start เพื่อดูวงจรและ servo หมุน 0° ↔ 90°

## หมายเหตุ

- สาย servo: สีส้มไป D18, สีแดงไป VIN, สีดำไป GND
- ค่าขา ESP32 ต่างจาก NodeMCU ผังนี้ใช้เพื่อดูลอจิกเท่านั้น ไม่ใช่การต่อจริง
- Wi-Fi และหน้าเว็บไม่ทำงานบน Wokwi ให้ทดสอบบนบอร์ดจริงแทน
