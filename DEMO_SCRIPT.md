# Demo Script — The System: Awakening × AI Orchestra (3 นาที)

> เป้าหมาย: กรรมการเห็น 2 อย่าง — (1) ผลิตภัณฑ์จริงที่ใช้งานได้บน production (2) AI บริษัทที่สร้างมันเองแบบโปร่งใส ภายใต้งบและกฎความปลอดภัย

## Prep ก่อนขึ้นเวที (5 นาที)

- [ ] เปิดแท็บ 1: `https://the-system-awakening-web.onrender.com/` (ล่วงหน้า ≥1 นาที กัน cold start)
- [ ] เปิดแท็บ 2: OFFICE HQ `http://localhost:4478/`
- [ ] เตรียมบัญชีสาธิต: สมัครไว้ก่อน (email demo) + เคลียร์ quest เก่าให้จบสถานะ
- [ ] เปิด Run Viewer filter "Commits" ให้เห็น timeline
- [ ] มีรูปหลักฐาน (screenshot จอ / นาฬิกาจับเวลา) ในเครื่องพร้อมอัปโหลด

## 0:00–0:25 Hook

> "นี่คือเกม RPG ของชีวิตจริง ที่โตแบบ deterministic — และทั้งเกมถูกสร้างโดยบริษัท AI ที่เราเขียนเอง งบ ฿900"

- โชว์หน้า login SYSTEM FANTASY 3 วินาที

## 0:25–1:30 Core Loop (ผลิตภัณฑ์)

1. Sign in → HUNTER STATUS (level orb, 5 stats, XP bar)
2. เลือก **Trial of Focus** (NORMAL·INT) → ACCEPT QUEST
3. ทำจริง: ตั้งจับเวลาบนจอ "30 นาที focus" → กลับมากรอก 30 + **แนบรูปหลักฐาน**
4. SUBMIT PROOF → CHECK VERIFICATION → worker ตัดสินใน ~2 วินาที (โชว์ PASS + EXP บวก)
5. OPEN PERSISTED CHEST → reveal animation → ของลง inventory
6. **Refresh หน้า** → ของยังอยู่ (server-authoritative, idempotent)

> จุดพูด: "ทุก state อยู่บน PostgreSQL หนึ่งจุดจริง — AI ไม่มีสิทธิ์แก้ game state (ADR 0003), รางวัล exactly-once"

## 1:30–2:30 The Company (AI Orchestra)

1. สลับแท็บ OFFICE HQ — agent 8 ตัวกำลังทำงาน (โชว์ bubble สถานะ + guest จากเครื่องอื่นถ้ามี)
2. ชี้ **Run Viewer** → filter Commits → "นี่คือ timeline ที่ AI สั่งงานตัวเองสร้าง production นี้ — ทุก commit มาจาก Codex ที่ Office จ้าง"
3. ชี้ Budget panel → "$X.XX spent จากเพดาน ฿900 — governor ตัดทุกครั้งก่อนเรียกโมเดล"
4. โชว์ guardrail: "คำสั่งอันตรายถูกบล็อกใน Run Viewer — BLOCKED พร้อมหลักฐาน"

## 2:30–3:00 ปิด

> "สถาปัตยกรรมเดียวกันนี้ขยายได้: เพิ่ม agent เพิ่มบริษัท โดยยังมี human gate, budget governor และ evidence trail — เกมคือหลักฐานว่ามันสร้างสินค้าจริงได้จริง"

- กลับไปหน้าเกมค้างไว้ที่ inventory (ภาพจำสุดท้าย = ของที่ "ได้จากการทำจริง")

## ถ้าถูกถาม (Q&A สั้น)

- **ทำไมต้อง deterministic?** กัน AI หลอกเลเวล — progression คำนวณจากกฎเดียวที่ test ครอบ (shared vectors TS/Python)
- **Verification ทำงานยังไง?** manual + รูป → deterministic rule; ต่อ AI verification ได้ผ่าน feature flag (ปิดอยู่ตามแผน)
- **AI ทำอะไรได้บ้างในระบบ?** วิเคราะห์/วางแผน/เขียนโค้ดผ่าน Codex — แต่ verify ด้วย test จริง + human gate ที่ release
- **ความปลอดภัย?** HttpOnly session + CSRF, uploads ตรวจ magic bytes, shell allowlist, secret redaction, rate limit

## Fallback ถ้าเน็ตหลุด

- วิดีโอสำรอง flow (อัดไว้ก่อนวันโชว์) + Run Viewer ยังโชว์ได้ offline
