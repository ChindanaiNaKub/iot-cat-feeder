# IoT Cat Feeder

เครื่องให้อาหารแมวอัตโนมัติ ควบคุมผ่านเว็บด้วย NodeMCU (ESP8266) และ servo

## โครงสร้าง

- `docs/plan.md` แผนงาน ลำดับงาน และความเสี่ยง
- `docs/build/out/` เอกสารส่งอาจารย์ฉบับภาษาอังกฤษ (docx และ pdf) คือ Proposal, SRS, SDD
- `docs/build/` สคริปต์ที่สร้างเอกสารทั้งสามฉบับและแผนภาพ รัน `python3 build.py` เพื่อสร้างใหม่
- `docs/proposal.md`, `docs/srs.md`, `docs/sdd.md` ฉบับร่างภาษาไทย ใช้เป็น quick reference
- `docs/` เอกสารโปรเจกต์ (ผังการต่อ, rubric)
- `docs/wiring_nodemcu_servo.html` ผังการต่อ NodeMCU + servo + powerbank
- `docs/feeder_3d.html` ภาพรวม 3D ของเครื่องทั้งเครื่อง หมุนดูได้และกดปุ่มให้อาหารจำลอง
- `firmware/servo_test/servo_test.ino` โค้ดทดสอบ servo บนบอร์ดจริง (D5, VIN, GND)
- `firmware/feeder/feeder.ino` โค้ดหลัก หน้าเว็บ + ปุ่มให้อาหาร + ตั้งเวลา NTP + ประวัติการให้อาหาร
- `docs/Project_Rubric_Idea50_Circuit30_Doc20.xlsx` เกณฑ์การให้คะแนน

## สถานะ

- [x] ต่อวงจร NodeMCU + servo + capacitor บน breadboard
- [x] ทดสอบ servo (ต้องจ่ายไฟจาก powerbank พอร์ต USB โน้ตบุ๊กจ่ายไม่พอ)
- [x] หน้าเว็บกดให้อาหาร ปิดฝาอัตโนมัติ ใช้จากมือถือได้
- [ ] ตั้งเวลาให้อาหาร (เขียนโค้ดแล้ว รอทดสอบกับเวลาจริง)
- [ ] ต่อ servo กับถังอาหาร
- [ ] เซ็นเซอร์วัดระดับอาหาร (FC-51)
- [ ] เขียนเอกสาร SRS, SDD, Proposal

## ฮาร์ดแวร์

- NodeMCU v3 (ESP8266)
- Servo SG90 และ capacitor 470 µF 16V
- Breadboard, LED, ตัวต้านทาน 220 Ω
- Powerbank 5V (2A ขึ้นไป)
