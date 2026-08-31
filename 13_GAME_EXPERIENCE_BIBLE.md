# 13 Game Experience Bible — MASTER GAME ART, GRAPHICS, UX & GAME DESIGN KNOW-HOW

> Version 1.0 — Production Bible for AI_ORCHESTRA, Codex, Gemini, Art Pipeline and future game team.
> Game Experience Layer above the Game Engine: binds `08_DESIGN_SYSTEM.md`, the Art Bible
> (`AI ORCHESTRA KNOW-HOW` / `CODEX ART PRODUCTION KNOW-HOW`) and AI_ORCHESTRA routing into one
> system, so the team never ships "ระบบเสร็จแต่ไม่สนุก" or "ภาพสวยแต่ Core Loop ไม่ชัด".

---

# 0. PURPOSE

เอกสารนี้เป็น Source of Truth สำหรับงานทั้งหมดที่เกี่ยวข้องกับ:

```text
GAME ART
GRAPHICS
CHARACTER
MONSTER
BOSS
ITEM
ARTIFACT
WEAPON
BACKGROUND
ENVIRONMENT
ICON
UI ART
ANIMATION
MOTION
VFX
PARTICLE
SHADER
SOUND FEEDBACK
GAME UX
GAME DESIGN
LEVEL / PROGRESSION DESIGN
GAME FEEL
```

เป้าหมายไม่ใช่เพียง:

> ทำเกมให้สวย

แต่คือ:

> ทำให้ผู้เล่น "เข้าใจ → รู้สึก → ลงมือ → ได้รับ Feedback → รู้สึกเติบโต → อยากกลับมาเล่นอีก"

---

# 1. MASTER EXPERIENCE

The System — Awakening ต้องให้ความรู้สึกว่า:

```text
ชีวิตจริง
↓
ถูกตรวจพบโดย SYSTEM
↓
ถูกแปลงเป็น QUEST
↓
ผู้เล่นลงมือจริง
↓
SYSTEM ยืนยันการกระทำ
↓
โลก RPG ตอบสนอง
↓
ตัวละครแข็งแกร่งขึ้น
↓
ผู้เล่นเห็นความเปลี่ยนแปลง
↓
เกิดแรงจูงใจกลับไปทำสิ่งจริงอีกครั้ง
```

ดังนั้น Art, UX และ Game Design ต้องสนับสนุน Core Loop เดียวกัน

---

# 2. MASTER VISUAL DIRECTION

ชื่อ Visual System:

# SYSTEM FANTASY

สูตรหลัก:

```text
PROGRESSION FANTASY
+
AI HOLOGRAPHIC SYSTEM
+
PREMIUM RPG
+
JUICY MOBILE GAME FEEDBACK
+
ORIGINAL IP
```

---

# 3. THREE VISUAL LAYERS

## Layer A — REALITY

ใช้กับ:

* Home
* Quest planning
* Settings
* Evidence
* Daily tasks

Mood:

```text
Dark
Calm
Clean
Focused
Readable
Minimal distraction
```

---

## Layer B — SYSTEM

ใช้เมื่อ:

* Quest generated
* Proof scanning
* Verification
* Level calculation
* Skill analysis
* System notification

Mood:

```text
Cyan
Electric blue
Glass
HUD
Grid
Scanline
Hologram
Digital precision
```

---

## Layer C — FANTASY / REWARD

ใช้เมื่อ:

* Quest Complete
* Chest
* Loot
* Level Up
* Awakening
* Achievement
* Boss Victory

Mood:

```text
Gold
Purple
Magenta
Crystal
Runes
Aura
Particles
Energy
Impact
```

---

# 4. VISUAL HIERARCHY RULE

ทุกหน้าต้องมี:

```text
1 PRIMARY FOCUS
2 SECONDARY INFORMATION
3 SUPPORTING DETAIL
```

ห้าม:

```text
ทุกอย่าง Glow
ทุกอย่าง Animate
ทุกอย่าง Legendary
ทุกอย่างส่งเสียง
```

ถ้าทุกอย่างสำคัญ:

> ไม่มีอะไรสำคัญเลย

---

# 5. ART STYLE BIBLE

Character และ World Artwork ควรมี:

```text
Original fantasy design
Readable silhouette
Premium game illustration
Controlled detail
Strong value separation
Mobile readability
Clear focal point
Consistent material language
```

หลีกเลี่ยงการ copy:

```text
existing character
existing costume
existing weapon silhouette
existing logo
existing UI composition
existing franchise item
recognisable proprietary design
```

Reference ใช้เพื่อ:

```text
Mood
Lighting
Genre grammar
Composition principles
RPG hierarchy
```

ไม่ใช่สร้างสำเนา

---

# 6. MASTER COLOR LANGUAGE

## SYSTEM

```text
Cyan
Ice blue
Deep navy
White
```

## REWARD

```text
Gold
Purple
Magenta
Prismatic highlights
```

## DANGER

```text
Red
Orange
Dark crimson
```

ใช้เฉพาะ:

```text
warnings
boss threat
critical state
```

ไม่ใช้แดงกับทุก action

---

# 7. RARITY VISUAL SYSTEM

Rarity ไม่ควรสื่อด้วยสีอย่างเดียว

ต้องเปลี่ยน:

```text
Color
Frame geometry
Glow
Particles
Animation
Sound
Material
Reveal duration
```

ตัวอย่าง:

```text
COMMON
Grey / White
Simple border
No major particle

UNCOMMON
Green
Minor accent geometry

RARE
Cyan
Energy trace

EPIC
Purple
Animated rune detail

LEGENDARY
Gold
Strong frame
Light sweep
Particle burst

MYTHIC
Magenta / Crimson
Complex geometry
Aura

TRANSCENDENT
Iridescent
Unique motion
Prismatic effects
```

---

# 8. ASSET TAXONOMY

```text
/assets

characters/
classes/
portraits/
companions/

monsters/
bosses/

items/
weapons/
armor/
artifacts/
consumables/

skills/
achievements/
titles/

quests/

environments/
backgrounds/
locations/
tower/
sanctuary/

ui/
frames/
panels/
buttons/
icons/
badges/

vfx/
particles/
shaders/

textures/
patterns/
runes/

marketing/
social/
store/
```

---

# 9. ASSET NAMING STANDARD

รูปแบบ:

```text
category_subject_variant_rarity_version
```

ตัวอย่าง:

```text
item_echo_blade_01_epic_v01.webp

monster_voidling_02_common_v03.webp

character_scholar_awakened_v02.webp

bg_system_chamber_night_v01.webp
```

---

# 10. ASSET MANIFEST

ห้าม frontend กระจาย path แบบ hard-code

ใช้ Asset Registry

ตัวอย่าง:

```json
{
  "id": "item_echo_blade_01",
  "category": "weapon",
  "rarity": "epic",
  "file": "/assets/items/item_echo_blade_01_epic_v01.webp",
  "aspectRatio": "1:1",
  "transparent": true,
  "status": "approved",
  "version": 1
}
```

---

# 11. ASSET LIFECYCLE

```text
REQUESTED
↓
DRAFT
↓
REVIEW
↓
APPROVED
↓
OPTIMIZED
↓
INTEGRATED
↓
DEPRECATED
```

Frontend Production ใช้:

```text
APPROVED
```

เท่านั้น

---

# 12. ART PRODUCTION PIPELINE

```text
GAME NEED
↓
ART REQUEST
↓
CATEGORY TEMPLATE
↓
STYLE BIBLE
↓
PROMPT GENERATION
↓
GENERATE VARIANTS
↓
ART QA
↓
IP / SIMILARITY CHECK
↓
SELECT
↓
POST PROCESS
↓
OPTIMIZE
↓
MANIFEST
↓
IMPLEMENT
↓
VISUAL QA
```

---

# 13. AI ART PROMPT FORMULA

```text
MASTER STYLE
+
ASSET CATEGORY
+
SUBJECT DNA
+
COMPOSITION
+
MATERIAL
+
LIGHTING
+
RARITY
+
GAMEPLAY PURPOSE
+
BACKGROUND REQUIREMENT
+
NEGATIVE CONSTRAINTS
```

---

# 14. CHARACTER ART SYSTEM

Character ต้องไม่ถูกสร้างเป็นภาพ random ใหม่ทุกครั้ง

ต้องมี:

# CHARACTER DNA

ตัวอย่าง:

```json
{
  "character_id": "player_archetype_scholar",

  "silhouette": "slender layered fantasy-tech",

  "primary_shapes": [
    "triangle",
    "vertical lines"
  ],

  "materials": [
    "dark fabric",
    "silver alloy",
    "cyan crystal"
  ],

  "motifs": [
    "archive rune",
    "floating data ring"
  ],

  "energy": "cyan",

  "personality_visual": [
    "precise",
    "analytical"
  ]
}
```

---

# 15. CHARACTER DESIGN CHECKLIST

ทุก Character ต้องผ่าน:

```text
✓ silhouette recognizable
✓ readable at thumbnail
✓ clear primary shape
✓ clear class identity
✓ limited visual noise
✓ original design
✓ color hierarchy
✓ animation-ready
✓ equipment areas readable
✓ evolution potential
```

---

# 16. CHARACTER SHEET

ก่อนสร้าง Production Character ต้องมี:

```text
Front
3/4
Side
Back

Face
Expression

Weapon / Tool

Material reference

Color palette

Scale reference

Key poses
```

หลังอนุมัติ:

```text
DESIGN LOCK
```

---

# 17. CHARACTER EVOLUTION SYSTEM

ตัวละครต้องเปลี่ยนตาม Progression

ไม่จำเป็นต้องสร้าง character ใหม่ทุก level

ใช้ Layered Evolution:

```text
LEVEL 1
Base Outfit

↓

LEVEL 5
Accessory

↓

LEVEL 10
Class Detail

↓

LEVEL 20
Aura

↓

LEVEL 30
Artifact

↓

AWAKENING
Major silhouette transformation
```

---

# 18. CLASS VISUAL LANGUAGE

ทุก Class ต้องมี:

```text
Shape Language
Motif
Material
Energy
Animation Style
VFX Language
Symbol
```

ตัวอย่าง:

## SCHOLAR

```text
Shapes:
Circles / vertical lines

Motifs:
Books / data rings / glyphs

Energy:
Cyan

Motion:
Precise / controlled
```

## VANGUARD

```text
Shapes:
Squares / broad forms

Motifs:
Shield / metal / runic plates

Motion:
Heavy / grounded
```

ห้ามยึดกับรูปร่างหรือเพศของผู้เล่น

---

# 19. CHARACTER PORTRAIT SYSTEM

Portrait ต้องมีหลาย state:

```text
Neutral
Quest
Victory
Level Up
Awakening
Boss
Low-energy UI state
```

แต่ควร reuse asset อย่างฉลาด

เช่น:

```text
base portrait
+
lighting
+
overlay
+
particles
+
frame
```

แทนการ generate ภาพใหม่ทั้งหมด

---

# 20. MONSTER DESIGN

Monster ต้องตอบคำถาม:

```text
มันคืออะไร?
ผู้เล่นต้องรู้สึกอะไร?
Threat level เท่าไร?
อ่าน silhouette ออกไหม?
เกี่ยวกับ theme อะไร?
```

---

# 21. MONSTER CATEGORIES

```text
MINION
ELITE
NEMESIS
BOSS
WORLD BOSS
EVENT CREATURE
```

---

# 22. MONSTER SHAPE LANGUAGE

## LOW THREAT

```text
Round
Small
Simple
Readable
```

## MEDIUM

```text
Angular
More asymmetrical
More layered
```

## HIGH THREAT

```text
Large silhouette
Sharp shapes
Strong asymmetry
Dominant focal point
```

---

# 23. NEMESIS DESIGN

Nemesis เป็น:

> Visual metaphor ของอุปสรรค

ไม่ใช่คำตัดสินผู้ใช้

ตัวอย่าง:

```text
THE DELAYER
Theme:
Delay / unfinished tasks

Visual:
Fragmented clock
Chains of unfinished pages
Distorted system timer
```

ผู้เล่นลด HP ผ่าน:

```text
real verified actions
```

---

# 24. BOSS DESIGN

Boss ต้องมี:

```text
Readable silhouette
Dominant motif
Weak-point language
Threat VFX
Unique animation
Unique arena mood
Clear progression feedback
```

Boss UI ต้องบอก:

```text
HP
Phase
Contribution
Event Goal
```

อย่างชัดเจน

---

# 25. ITEM DESIGN SYSTEM

Item ต้องอ่านออกใน:

```text
64×64
128×128
```

ดังนั้น:

```text
strong silhouette
one dominant shape
limited detail
clear material
rarity readable
```

---

# 26. ITEM TYPES

```text
Weapon
Armor
Accessory
Artifact
Charm
Relic
Material
Quest Item
Cosmetic
```

---

# 27. ITEM ART RULE

Item Prompt ต้องระบุ:

```text
centered object
isolated
transparent background
game inventory icon
strong silhouette
single focal object
no text
no watermark
```

---

# 28. ARTIFACT DESIGN

Artifact ต้องรู้สึกพิเศษกว่า Item

เพิ่ม:

```text
Story
Rune
Energy
Unique shape
Visual effect
Lore connection
```

---

# 29. EQUIPMENT VISUAL SYSTEM

Equipment บางชิ้นควรเปลี่ยน Character

แต่ MVP ไม่จำเป็นต้องสร้าง outfit combinatorial ทั้งหมด

ใช้:

```text
Base Character
+
Artifact overlay
+
Aura
+
Weapon
+
Frame
```

---

# 30. BACKGROUND / ENVIRONMENT SYSTEM

Environment ต้องบอก progression

ตัวอย่าง:

```text
LEVEL 1
Dark System Chamber

LEVEL 10
System Archive

LEVEL 20
Awakening Hall

LEVEL 30
Astral Citadel

HIGH LEVEL
Transcendent Realm
```

---

# 31. ENVIRONMENT LAYERS

Background ที่ดีควรมี:

```text
Foreground
Midground
Background
Atmosphere
Lighting
Gameplay-safe area
```

UI Background ต้องไม่แย่ง readability

---

# 32. UI SAFE ZONE

ภาพ background/banner ต้องเว้น:

```text
Text safe area
CTA safe area
Portrait safe area
Mobile crop safe area
```

AI Art Prompt ต้องรู้ safe zone ตั้งแต่ก่อน generate

---

# 33. PARALLAX SYSTEM

Background สามารถแบ่ง:

```text
Layer 1 — far
Layer 2 — architecture
Layer 3 — particles
Layer 4 — foreground
```

แล้วใช้ parallax เล็กน้อย

ช่วยสร้าง depth โดยไม่ต้องใช้ 3D

---

# 34. PROCEDURAL GRAPHICS

ไม่ควรใช้ Generative Image ทุกอย่าง

Codex/Gemini สามารถสร้าง:

```text
SVG rune
rarity frame
HUD grid
scan line
progress ring
badge
icon geometry
particles
gradient
energy line
procedural texture
```

ข้อดี:

```text
cheap
consistent
responsive
lightweight
animatable
```

---

# 35. RUNE GENERATOR

Rune grammar สามารถสร้างจาก:

```text
Circle
Triangle
Hexagon
Arc
Line
Dot
Orbit
Radial segment
```

สร้าง procedural SVG จาก seed

เช่น:

```text
rarity
class
achievement
quest type
```

---

# 36. ANIMATION PHILOSOPHY

Animation ต้องมีหน้าที่

ทุก animation ต้องตอบว่า:

```text
Communicate?
Guide attention?
Confirm action?
Create impact?
Build anticipation?
```

ถ้าไม่มี:

```text
remove it
```

---

# 37. MOTION PERSONALITIES

## SYSTEM MOTION

```text
Fast
Precise
Snap
Scan
Digital
```

## NORMAL UI

```text
Smooth
Spring
Controlled
```

## REWARD

```text
Anticipation
Pause
Impact
Release
```

## BOSS

```text
Heavy
Slow buildup
Powerful impact
```

---

# 38. ANIMATION TIMING SYSTEM

ตัวอย่าง:

```text
Micro feedback
80–180 ms

UI transition
180–350 ms

Reward
500–1500 ms

Major Level Up
1–3 sec

Awakening
special cinematic
```

อย่าทำทุก action ช้าเพราะ cinematic

---

# 39. JUICY UI PRINCIPLES

ใช้:

```text
squash
stretch
bounce
overshoot
particles
counter animation
screen flash
reward fly-in
micro camera shake
sound
haptic
```

แต่ต้องมี:

```text
REDUCED MOTION
```

---

# 40. BUTTON FEEDBACK

Button interaction:

```text
Idle
↓
Hover
↓
Press
↓
Release
↓
Success / Loading
```

Press ควรมี:

```text
scale down
shadow reduction
click sound optional
```

---

# 41. QUEST COMPLETE SEQUENCE

ตัวอย่าง:

```text
Verification PASS
↓
brief system scan
↓
QUEST COMPLETE
↓
impact
↓
EXP counter
↓
Stat growth
↓
Chest materializes
↓
CTA: OPEN
```

---

# 42. LEVEL UP SEQUENCE

```text
EXP bar approaches threshold
↓
slow final fill
↓
brief pause
↓
burst
↓
LEVEL UP
↓
new unlock preview
```

---

# 43. CHEST OPEN SEQUENCE

```text
Chest appears
↓
Idle pulse
↓
User taps
↓
Anticipation
↓
Light leak
↓
Rarity pre-signal
↓
Reveal
↓
Item
↓
Reward settles
```

แต่:

> RNG ต้องเกิด server-side และ persist ก่อน animation

Animation ไม่ใช่ authority

---

# 44. VFX TAXONOMY

```text
system_scan
quest_accept
quest_complete
proof_verified
proof_failed
xp_gain
stat_gain
level_up
loot_spawn
chest_open
rare_reveal
epic_reveal
legendary_reveal
awakening
boss_hit
boss_phase
boss_defeat
achievement_unlock
```

---

# 45. PARTICLE RULE

Particles ต้องมี:

```text
spawn
velocity
lifetime
scale
opacity
gravity
blend mode
```

จำกัดจำนวนเพื่อ performance

---

# 46. VFX PERFORMANCE TIERS

```text
LOW
minimal particles

MEDIUM
standard

HIGH
full VFX
```

สามารถเลือกตาม device performance

---

# 47. SCREEN SHAKE

ใช้เล็กน้อยสำหรับ:

```text
legendary reveal
boss hit
major level up
```

ห้ามใช้กับ:

```text
normal navigation
typing
every button
```

ต้องสามารถ disable ได้

---

# 48. SHADER / ADVANCED EFFECTS

อนาคตสามารถใช้:

```text
hologram
dissolve
energy distortion
chromatic separation
glow
rim lighting
portal
```

MVP ใช้ CSS / SVG / Canvas ก่อนถ้าเพียงพอ

---

# 49. SOUND DESIGN

Audio categories:

```text
UI
SYSTEM
REWARD
COMBAT
AMBIENCE
MUSIC
```

---

# 50. SOUND HIERARCHY

## Button

สั้น เบา

## Quest Complete

ชัดเจน

## Legendary

ใหญ่กว่า

## Awakening

ใหญ่ที่สุด

ต้องไม่ทำ Reward ทุกชิ้นดังเท่ากัน

---

# 51. AUDIO ACCESSIBILITY

ต้องมี:

```text
Master volume
Music
SFX
Mute
```

ข้อมูลสำคัญห้ามสื่อด้วยเสียงอย่างเดียว

---

# 52. GAME UX MASTER PRINCIPLE

UI คือ:

> สิ่งที่ผู้เล่นเห็น

UX คือ:

> สิ่งที่ผู้เล่นเข้าใจ รู้สึก และสามารถทำได้

Game Design คือ:

> เหตุผลที่ผู้เล่นอยากทำมันซ้ำ

---

# 53. CORE UX LOOP

```text
UNDERSTAND
↓
DECIDE
↓
ACT
↓
FEEDBACK
↓
REWARD
↓
UNDERSTAND PROGRESS
↓
NEXT ACTION
```

ทุก screen ต้องช่วยผู้เล่นเดินต่อใน loop นี้

---

# 54. THREE-SECOND RULE

ภายใน ~3 วินาทีหลังเปิดหน้าหลัก ผู้เล่นควรตอบได้:

```text
ฉันอยู่ Level อะไร?
วันนี้ต้องทำอะไร?
สิ่งสำคัญที่สุดคืออะไร?
ฉันกดตรงไหนต่อ?
```

---

# 55. HOME SCREEN UX

Priority:

```text
1 Current character/progress
2 Primary Quest
3 Daily progression
4 Secondary content
5 Navigation
```

ไม่ควรวาง:

```text
20 widgets
multiple currencies
10 CTA
```

ในหน้าแรก

---

# 56. QUEST BOARD UX

แต่ละ Quest Card ต้องเห็น:

```text
Fantasy Title
Real Objective
Estimated Time
Difficulty
Stat
Proof Method
Reward
Status
```

ก่อน Accept

---

# 57. PROOF UX

Proof ต้องถูกบอก:

```text
ก่อนเริ่ม Quest
```

ไม่ใช่หลังผู้ใช้ทำเสร็จ

ตัวอย่าง:

```text
Proof:
Built-in timer

or

Upload activity screenshot
```

---

# 58. PROOF FRICTION

เป้าหมาย:

```text
Proof เกิดโดยธรรมชาติระหว่างการทำกิจกรรม
```

ดีที่สุด:

```text
Code
→ Git records proof
```

ดีกว่า:

```text
Code
→ stop
→ take screenshot
→ upload
→ explain
```

---

# 59. VERIFICATION UX

State:

```text
SUBMITTING
PROCESSING
VERIFIED
NEED MORE EVIDENCE
FAILED
```

ห้ามปล่อย spinner ไม่สิ้นสุด

---

# 60. NEED MORE EVIDENCE UX

พูดว่า:

```text
ระบบยังยืนยันระยะทางจากภาพนี้ไม่ได้
ลองส่งภาพที่เห็นระยะทางชัดขึ้น
```

ไม่พูดว่า:

```text
คุณโกง
```

---

# 61. ONBOARDING DESIGN

Onboarding ต้องเป็น Experience

ไม่ใช่ questionnaire 15 หน้า

Flow:

```text
SYSTEM INITIALIZING
↓
Identity setup
↓
Choose goals
↓
Choose available activity types
↓
First simple Quest
↓
Complete
↓
First Reward
↓
Character Activated
```

---

# 62. TIME TO FIRST REWARD

เป้าหมาย:

```text
First Session
```

ผู้ใช้ควรได้ Reward แรก

อย่าให้ต้องเล่นหลายวันก่อนเข้าใจความสนุก

---

# 63. TUTORIAL PRINCIPLE

ใช้:

```text
Learn by doing
```

แทน:

```text
อ่านข้อความ tutorial ยาว
```

สอน Feature เมื่อ Feature กำลังจะถูกใช้

---

# 64. PROGRESSIVE DISCLOSURE

Day 1:

```text
Quest
EXP
Level
Chest
Inventory
```

ค่อยเปิด:

```text
Skills
Achievement
Nemesis
Class
Tower
Boss
```

ภายหลัง

---

# 65. INFORMATION ARCHITECTURE

Main navigation ไม่ควรเยอะเกินไป

ตัวอย่าง:

```text
HOME
QUEST
INVENTORY
PROFILE
```

Secondary:

```text
Codex
Achievement
Settings
```

---

# 66. THREE-ACTION PRINCIPLE

Action สำคัญควรเข้าถึงได้ภายในประมาณ:

```text
1–3 interactions
```

เช่น:

```text
Home
→ Quest
→ Accept
```

---

# 67. MOBILE THUMB ZONE

Primary actions บน Mobile:

```text
lower / reachable area
```

โดยเฉพาะ:

```text
Accept
Submit
Open
Continue
```

อย่าให้ CTA หลักอยู่มุมที่เข้าถึงยากโดยไม่มีเหตุผล

---

# 68. ACCESSIBILITY

ต้องรองรับ:

```text
Text scaling
Screen reader
Keyboard
Focus states
Color contrast
Reduced motion
Color-independent status
Large interaction targets
Captions where applicable
```

---

# 69. COLOR BLINDNESS

ห้ามใช้:

```text
red = fail
green = pass
```

เพียงอย่างเดียว

ต้องมี:

```text
icon
label
shape
```

ร่วมด้วย

---

# 70. GAME DESIGN CORE LOOP

The System Core Loop:

```text
Receive Quest
↓
Real Action
↓
Proof
↓
Verification
↓
Reward
↓
Character Growth
↓
Unlock
↓
Next Quest
```

---

# 71. META LOOP

ระยะยาว:

```text
Daily Quest
↓
Weekly Progress
↓
Skill Mastery
↓
Class
↓
Awakening
↓
Season / Major Goal
```

---

# 72. MICRO LOOP

ภายในไม่กี่วินาที:

```text
Tap
↓
Feedback
↓
Progress
↓
Next interaction
```

Game Feel เกิดจาก Micro Loop นี้จำนวนมาก

---

# 73. GAME MECHANICS

Core mechanics ของโปรเจกต์นี้ไม่ใช่:

```text
เดิน
กระโดด
โจมตี
```

แต่คือ:

```text
Accept
Commit
Perform
Prove
Verify
Grow
Collect
Unlock
```

ชีวิตจริงเป็น Gameplay Input

---

# 74. QUEST DIFFICULTY DESIGN

Difficulty ดูจาก:

```text
Time
Complexity
Effort
Skill Gap
Uncertainty
Number of objectives
```

ไม่ใช่แค่ Duration

---

# 75. PERSONAL DIFFICULTY

Quest เดียวกัน:

```text
User A = EASY
User B = HARD
```

ได้

ระบบต้องใช้:

```text
history
completion behavior
available time
user preference
```

---

# 76. GAME BALANCE

Game Balance ต้องควบคุม:

```text
EXP velocity
Level velocity
Stat velocity
Chest frequency
Rare frequency
Achievement frequency
Quest difficulty
Completion rate
```

---

# 77. REWARD CADENCE

ผู้เล่นต้องได้:

## Micro Reward

```text
button feedback
progress
small XP
```

## Session Reward

```text
Quest Complete
Chest
```

## Weekly Reward

```text
Milestone
Achievement
```

## Long-term Reward

```text
Class
Awakening
Major visual evolution
```

---

# 78. ANTICIPATION

Reward ไม่ควร reveal ทันทีทุกครั้ง

Flow:

```text
Signal
↓
Anticipation
↓
Reveal
```

แต่ต้องไม่ยืดเยื้อจนรำคาญ

---

# 79. REWARD PREDICTABILITY

ต้องมีทั้ง:

```text
Guaranteed Reward
+
Optional Surprise
```

เช่น:

```text
Quest:
Guaranteed 240 EXP

Possible:
Rare Chest
```

---

# 80. ECONOMY PRINCIPLE

MVP ใช้ economy ให้น้อย

```text
EXP
Stats
Items
Chest
```

อย่าเพิ่ม:

```text
Gold
Diamond
Gem
Token
Energy
Ticket
Dust
```

พร้อมกันโดยไม่มีเหตุผล

---

# 81. GACHA PRESENTATION

Gacha ใน MVP เป็น:

```text
Reward Presentation
```

ไม่ใช่การพนันด้วยเงินจริง

Random reward ต้องมี:

```text
server-side RNG
persisted result
clear rarity system
```

---

# 82. DUPLICATE ITEM UX

Duplicate ไม่ควรรู้สึกว่า:

```text
ไม่ได้อะไรเลย
```

อนาคตอาจ:

```text
convert to essence
upgrade
collection progression
```

---

# 83. COLLECTION UX

Codex:

```text
Found
Not Found
???
```

ใช้ Mystery กระตุ้น Exploration

---

# 84. CHARACTER PROGRESSION UX

Progress ต้องเห็นผ่านหลายช่องทาง:

```text
Number
Visual
Sound
Animation
Unlock
Collection
```

อย่าพึ่ง EXP number อย่างเดียว

---

# 85. LEVEL-UP MEANING

Level Up ที่ไม่มีอะไรเกิดขึ้นจะหมดความหมาย

บาง Level ควรมี:

```text
new Quest tier
cosmetic
frame
title
class hint
feature unlock
```

---

# 86. CLASS DISCOVERY

Class สามารถเกิดหลังระบบสังเกตผู้ใช้ช่วงหนึ่ง

ตัวอย่าง:

```text
SYSTEM ANALYSIS COMPLETE

Dominant:
INT
WIL

Possible Class:
ARCHITECT
```

ให้ User มี autonomy ในการเลือก

---

# 87. NEMESIS LOOP

```text
Player identifies obstacle
↓
System gives fantasy representation
↓
Verified actions deal damage
↓
Boss evolves
↓
Milestone victory
```

ไม่ใช้ humiliation หรือ punishment

---

# 88. WORLD BOSS LOOP

```text
Community Verified Actions
↓
Damage
↓
Shared Progress
↓
Boss Phase
↓
Community Reward
```

Self-report ไม่ควรสร้าง competitive damage

---

# 89. GAME FEEL

Game Feel คือ:

> ความแตกต่างระหว่าง "ระบบทำงาน" กับ "รู้สึกสนุก"

ประกอบด้วย:

```text
Timing
Motion
Audio
Particles
Anticipation
Impact
Response
Clarity
```

---

# 90. INPUT RESPONSE TARGET

ผู้ใช้กดแล้วต้องมี feedback ทันที

แม้ backend ยังทำงาน

เช่น:

```text
Tap Submit
↓
button responds
↓
progress state appears
↓
network runs
```

ไม่ปล่อย UI เงียบ

---

# 91. LOADING UX

Loading ที่นาน:

แทน spinner อย่างเดียว

ใช้:

```text
Scanning evidence...
Checking quest conditions...
Preparing result...
```

แต่ต้องเป็นข้อความจริงตาม state

ไม่ fake progress ที่ทำให้เข้าใจผิด

---

# 92. ERROR UX

Error Message ต้องตอบ:

```text
เกิดอะไรขึ้น?
ข้อมูลหายไหม?
ทำอะไรต่อ?
Retry ได้ไหม?
```

---

# 93. FAILURE WITHOUT PUNISHMENT

Quest fail:

ไม่ใช้:

```text
YOU FAILED
YOU ARE WEAK
```

ใช้:

```text
QUEST INCOMPLETE

Progress recorded.
Try again or adjust the Quest.
```

---

# 94. RETURNER UX

เมื่อกลับมาหลังหายไป:

```text
SYSTEM RECONNECTED
```

เสนอ:

```text
Continue
New small Quest
Recap
```

ไม่ guilt-trip

---

# 95. STREAK DESIGN

Streak ต้องช่วย retention

ไม่ควรทำให้ผู้เล่นกลัวพลาด

ใช้:

```text
Grace
Streak Shield
Recovery
Weekly consistency
```

---

# 96. RETENTION DESIGN

Retention ไม่ควรเกิดจาก:

```text
fear
pressure
loss
```

ควรเกิดจาก:

```text
progress
curiosity
identity
collection
story
mastery
community
```

---

# 97. DAILY BOARD DESIGN

ไม่จำเป็นต้องมีทุก Stat ทุกวัน

ตัวอย่าง:

```text
MAIN QUEST
INT

SIDE QUEST
WIL

OPTIONAL
AGI

RECOVERY
VIT
```

---

# 98. COGNITIVE LOAD

ทุก screen ถาม:

```text
มีข้อมูลอะไรที่ User ไม่ต้องเห็นตอนนี้?
```

ซ่อนข้อมูล advanced จนกว่าจะจำเป็น

---

# 99. GAME DESIGN TELEMETRY

Track:

```text
Quest viewed
Quest accepted
Quest abandoned
Proof submitted
Verification failed
Quest completed
Chest opened
Item viewed
Return session
```

---

# 100. UX TELEMETRY

Track:

```text
time to first quest
time to first reward
submission abandonment
verification retry rate
menu depth
CTA conversion
error rate
```

---

# 101. BALANCE METRICS

Track:

```text
EXP / day
Level / week
Quest completion %
Chest / week
Rare / player
Stat distribution
```

---

# 102. ART PERFORMANCE BUDGET

Art ต้องมี Budget

เช่น:

```text
Hero background:
large but compressed

Inventory icon:
small

Particles:
runtime generated

UI:
SVG where possible
```

---

# 103. IMAGE FORMAT

Default:

```text
WebP
```

Transparent:

```text
WebP / PNG
```

Vector:

```text
SVG
```

Future:

```text
AVIF where supported/useful
```

---

# 104. RESPONSIVE ART

อย่าใช้ภาพ desktop แล้ว crop มือถือแบบสุ่ม

สร้าง:

```text
desktop composition
mobile-safe composition
```

หรือ safe crop metadata

---

# 105. SPRITE SYSTEM

หากใช้ Sprite:

```text
idle
appear
hover
impact
victory
```

จัด Sprite Atlas เมื่อ asset จำนวนมากขึ้น

---

# 106. PIXEL / SPRITE PIPELINE

หากใช้ PixelLab Pipeline:

```text
prompt/spec
↓
PixelLab
↓
raw/
↓
hash integrity
↓
review
↓
approved/
↓
optimized/
↓
manifest
```

`raw/` ต้องไม่ถูกแก้แบบสูญเสีย provenance โดยไม่มี version ใหม่

---

# 107. VIDEO / CINEMATIC PIPELINE

ใช้ cinematic เฉพาะ moment สำคัญ:

```text
Awakening
World Boss reveal
Season intro
Major achievement
```

ไม่ใช้ video กับ interaction ปกติ

---

# 108. CINEMATIC STRUCTURE

```text
Setup
↓
Reveal
↓
Transformation
↓
Impact
↓
Player Control Returns
```

ต้องมี:

```text
Skip
Reduced-motion alternative
```

เมื่อเหมาะสม

---

# 109. AI ART ORCHESTRA

Logical roles:

```text
ART DIRECTOR
↓
ASSET PLANNER
↓
PROMPT BUILDER
↓
GENERATOR
↓
ART QA
↓
IP CHECK
↓
OPTIMIZER
↓
ASSET REGISTRY
```

MVP ไม่จำเป็นต้องเป็น agent แยกจริงทั้งหมด

---

# 110. ART REQUEST SCHEMA

```json
{
  "asset_id": "monster_voidling_001",
  "category": "monster",
  "purpose": "quest card enemy",
  "rarity": "common",
  "aspect_ratio": "1:1",
  "transparent": true,
  "style_version": "system-fantasy-v1",
  "required_safe_zone": null,
  "status": "requested"
}
```

---

# 111. AI ART VALIDATION

ตรวจ:

```text
✓ correct dimensions
✓ correct aspect ratio
✓ transparent when required
✓ no accidental text
✓ no watermark
✓ readable silhouette
✓ correct rarity
✓ correct style
✓ no obvious copied IP
✓ usable at thumbnail
✓ correct safe zone
```

---

# 112. CHARACTER CONSISTENCY QA

Compare:

```text
face structure
hair language
materials
motifs
silhouette
class symbol
energy
palette
```

ก่อน approve variant

---

# 113. MONSTER CONSISTENCY QA

ตรวจ:

```text
family identity
threat tier
environment relationship
silhouette differentiation
```

---

# 114. BACKGROUND QA

ตรวจ:

```text
UI readability
safe area
mobile crop
contrast
visual noise
atmosphere
performance
```

---

# 115. VFX QA

ตรวจ:

```text
purpose
timing
performance
readability
reduced motion
does not hide information
```

---

# 116. UX QA

ทุก Flow สำคัญ:

```text
Can user understand next action?

Can user go back?

Can user recover from error?

Does progress persist?

Is proof clear?

Is reward clear?

Does UI work mobile?

Does loading communicate state?
```

---

# 117. GAME DESIGN QA

ถาม:

```text
Why is this fun?

Why would user repeat it?

What does player learn?

What improves?

What decision exists?

What reward exists?

What becomes possible next?
```

---

# 118. DESIGN REVIEW GATE

Feature ไม่ควร Done ถ้ามีเพียง:

```text
code works
```

ต้องผ่าน:

```text
FUNCTIONAL
+
UNDERSTANDABLE
+
RESPONSIVE
+
ACCESSIBLE
+
REWARDING
```

---

# 119. MVP ART PRIORITY

ไม่ต้องสร้าง Asset 500 ชิ้น

เริ่ม:

```text
1 Hero Character

3 Character progression states

20 Item icons

5–6 rarity frames

5 Quest category icons

3–5 monster concepts

1 Nemesis

1 optional World Boss

3–5 major backgrounds

Core HUD assets

Reward VFX

Quest Complete VFX

Chest animations
```

---

# 120. ART PRIORITY ORDER

```text
1 Core Loop readability
2 Character identity
3 Reward presentation
4 Inventory assets
5 Quest identity
6 Backgrounds
7 Monster
8 Optional social content
9 Marketing
```

---

# 121. MVP UX PRIORITY

```text
1 Quest understandable
2 Proof understandable
3 Verification understandable
4 Reward impactful
5 Growth visible
6 Navigation simple
7 Error recoverable
8 Animation polished
```

---

# 122. GAME DESIGN PRIORITY

```text
CORE LOOP
↓
PROGRESSION
↓
REWARD
↓
QUEST VARIETY
↓
RETENTION
↓
SOCIAL
↓
META SYSTEM
```

---

# 123. AI_ORCHESTRA ART ROUTING

AI_ORCHESTRA ต้องเลือก:

```text
Can CSS do it?
↓ YES
Codex

Can SVG do it?
↓ YES
Codex/Gemini

Does it require generated art?
↓ YES
Art Pipeline

Does it require motion?
↓
CSS / Framer Motion first

Does it require advanced VFX?
↓
Canvas/WebGL later
```

---

# 124. COST-AWARE ART RULE

งบต่ำ:

```text
GENERATIVE ART
```

ใช้กับ:

```text
Hero
Character
Boss
Important Background
Major Artifact
```

ใช้ procedural สำหรับ:

```text
frames
icons
HUD
particles
runes
background patterns
progress bars
glow
```

---

# 125. AI UX AGENT

ก่อน implement screen:

AI UX Reviewer ต้องตรวจ:

```text
Primary user goal
Primary CTA
Expected state
Loading
Success
Failure
Back navigation
Mobile
Accessibility
Feedback
```

---

# 126. AI GAME DESIGN AGENT

ก่อนเพิ่ม Mechanic:

ตอบ:

```text
What behavior does this encourage?

How does user understand it?

What is the reward?

How is it balanced?

Can it be exploited?

Does it strengthen Core Loop?

What happens when user fails?

Can it be removed without breaking game?
```

---

# 127. GAME DESIGN ANTI-PATTERN

ห้ามเพิ่มระบบเพียงเพราะ:

```text
RPGs usually have it
```

เช่น:

```text
currency
energy
crafting
guild
shop
PvP
```

ต้องมี Product Reason ก่อน

---

# 128. UX ANTI-PATTERN

หลีกเลี่ยง:

```text
Popup after popup

Too many badges

Hidden navigation

Long onboarding

Fake progress bars

Unclear proof

Unskippable animation

Reward screen with no next action
```

---

# 129. ART ANTI-PATTERN

หลีกเลี่ยง:

```text
Every asset uses different style

Random AI characters

Too much detail

Weak silhouettes

Text generated inside art

No asset naming

No versioning

No provenance
```

---

# 130. ANIMATION ANTI-PATTERN

หลีกเลี่ยง:

```text
animation delays actual result

animation controls authoritative state

reward RNG happens client-side

constant camera shake

excessive glow

every element moves
```

---

# 131. UX ↔ GAME ENGINE CONTRACT

UX แสดงผลจาก Backend State

ไม่สร้าง state ของตัวเอง

ตัวอย่าง:

```text
Backend:
CHEST_OPENED

Frontend:
plays reveal
```

ไม่ใช่:

```text
Frontend animation completes
→ decides chest was opened
```

---

# 132. UX ↔ AI CONTRACT

AI output ไม่ควรขึ้นหน้าจอโดยตรงทุกกรณี

Flow:

```text
AI
↓
Schema validation
↓
Backend policy
↓
UI-safe response
```

---

# 133. PROGRESS VISUALIZATION

Stats อาจแสดงด้วย:

```text
bars
radar
rings
cards
aura
character accessories
```

แต่ต้องอ่านตัวเลขได้ด้วย

---

# 134. SYSTEM CORE VISUAL

สร้าง Persistent Object เช่น:

```text
SYSTEM CORE
```

ทำหน้าที่เป็น visual identity ของ AI

Level เพิ่ม:

```text
more rings
more complexity
more glow
more functions
```

ช่วยให้ AI progression "มองเห็นได้"

---

# 135. UI PERSONALITY BY STATE

## NORMAL

Calm

## QUEST

Focused

## VERIFYING

Analytical

## SUCCESS

Energetic

## LEGENDARY

Spectacular

## ERROR

Clear, calm

ไม่ทำ Error Screen รุนแรงเกินจำเป็น

---

# 136. SOCIAL UX

ถ้าเพิ่ม World Boss:

ผู้เล่นควรเห็น:

```text
Your contribution
Community contribution
Boss state
Reward threshold
```

ไม่ควรเน้น comparison อย่างเดียว

---

# 137. COLLECTION MOTIVATION

ใช้:

```text
Set completion
Hidden item
Lore unlock
Visual evolution
```

เพื่อสร้าง motivation โดยไม่ต้องพึ่ง power creep

---

# 138. ACHIEVEMENT UX

Achievement ที่ดีต้อง:

```text
meaningful
specific
memorable
linked to real action
```

ไม่แจก Achievement ทุก 2 นาที

---

# 139. TITLE SYSTEM

Title เป็น Identity Reward

เช่น:

```text
ARCHIVE WALKER
FIRST AWAKENED
FOCUS FORGED
```

ควรมีความหมายจากประวัติการเล่นจริง

---

# 140. CONTENT DIVERSITY

Quest Board ต้อง monitor:

```text
same verb
same stat
same proof
same theme
same duration
```

ลด repetition

---

# 141. ART GENERATION DIVERSITY

Asset generator ต้องแยก:

```text
style consistency
```

ออกจาก:

```text
composition repetition
```

Style เหมือนกันได้

Composition ไม่ควรเหมือนกันทุกภาพ

---

# 142. DESIGN TOKENS

ระบบควรมี Token สำหรับ:

```text
color
spacing
radius
shadow
glow
font size
motion duration
z-index
rarity
```

ไม่ hardcode random values ใน component

---

# 143. VFX TOKENS

ตัวอย่าง:

```text
--vfx-system-glow
--vfx-rare-glow
--vfx-legendary-glow

--motion-fast
--motion-normal
--motion-reward

--particle-low
--particle-medium
--particle-high
```

---

# 144. EXPERIENCE TEST

Feature ไม่ถือว่าเสร็จจน tester ตอบได้:

```text
I knew what to do.
I knew what happened.
I understood the reward.
I could recover from errors.
I noticed my progress.
```

---

# 145. GOLDEN CORE LOOP EXPERIENCE

```text
Player opens app

↓

Character clearly visible

↓

One important Quest immediately understandable

↓

Proof requirement visible

↓

Player performs real action

↓

Submission simple

↓

System visibly analyzes

↓

Clear verified result

↓

Quest Complete impact

↓

EXP visibly moves

↓

Stat increases

↓

Chest appears

↓

Chest reveal feels exciting

↓

Item enters inventory

↓

Character/Profile visibly changes

↓

Next meaningful action is obvious
```

---

# 146. MASTER ART RULE

> Create a visual system, not a collection of unrelated images.

---

# 147. MASTER UX RULE

> Never make the player think about how the interface works when they should be thinking about their Quest.

---

# 148. MASTER GAME DESIGN RULE

> Every mechanic must create a meaningful decision, meaningful progress, meaningful feedback, or meaningful motivation.

---

# 149. MASTER ANIMATION RULE

> Motion must explain, guide, confirm, or reward.

---

# 150. MASTER VFX RULE

> Effects amplify importance; they do not create importance.

---

# 151. MASTER CHARACTER RULE

> Character growth must visually reflect real progression.

---

# 152. MASTER MONSTER RULE

> Monsters represent challenges, not judgments about the player.

---

# 153. MASTER ITEM RULE

> Every item must be readable, collectible, distinctive, and visually tied to the world.

---

# 154. MASTER BACKGROUND RULE

> Environment supports the experience; it must never fight UI readability.

---

# 155. MASTER AI ART RULE

> AI may generate assets, but the Art Bible defines identity.

---

# 156. MASTER GAME FEEL RULE

> Logic makes the game work. Feedback makes the game feel alive.

---

# 157. FINAL EXPERIENCE NORTH STAR

The System — Awakening ต้องสร้างความรู้สึก:

```text
I DID SOMETHING REAL

↓

THE SYSTEM SAW IT

↓

THE WORLD RESPONDED

↓

MY CHARACTER CHANGED

↓

I WANT TO SEE WHAT HAPPENS NEXT
```

ถ้าผู้เล่นได้รับความรู้สึกนี้:

```text
ART
+
UX
+
GAME DESIGN
+
AI
+
GAME ENGINE
```

กำลังทำงานเป็นระบบเดียวกัน

---

# FINAL MASTER PRINCIPLE

```text
REAL ACTION
      ↓
CLEAR UX
      ↓
TRUSTWORTHY PROOF
      ↓
SYSTEM FEEDBACK
      ↓
JUICY GAME FEEL
      ↓
MEANINGFUL REWARD
      ↓
VISIBLE CHARACTER EVOLUTION
      ↓
LONG-TERM PLAYER IDENTITY
```

The System — Awakening ต้องไม่เพียง "ดูเหมือนเกม"

แต่ต้อง:

# FEEL LIKE A GAME

# RESPOND LIKE A SYSTEM

# AND GROW FROM REAL LIFE
