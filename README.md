# IoT Cat Feeder

เครื่องให้อาหารแมวอัตโนมัติ ควบคุมผ่านเว็บด้วย NodeMCU (ESP8266) และ servo

## โครงสร้าง

- `docs/` เอกสารโปรเจกต์ (ผังการต่อ, rubric)
- `docs/wiring_nodemcu_servo.html` ผังการต่อ NodeMCU + servo + powerbank
- `docs/Project_Rubric_Idea50_Circuit30_Doc20.xlsx` เกณฑ์การให้คะแนน

## สถานะ

- [x] ควบคุม LED ผ่านเว็บ (เปิด/ปิด)
- [ ] ทดสอบ servo
- [ ] ต่อ servo กับถังอาหาร
- [ ] เพิ่มการตั้งเวลาให้อาหาร
- [ ] เขียนเอกสาร SRS, SDD, Proposal

## ฮาร์ดแวร์

- NodeMCU v3 (ESP8266)
- Servo SG90 และ capacitor 470 µF 16V
- Breadboard, LED, ตัวต้านทาน 220 Ω
- Powerbank 5V (2A ขึ้นไป)
