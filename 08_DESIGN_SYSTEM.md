# 08 Design System — SYSTEM FANTASY v1

## 1. Visual DNA
Progression Fantasy + AI Holographic HUD + Premium RPG + Juicy Game UX.

## 2. Product States
- Reality: dark, calm, low noise
- System: cyan/blue HUD, scan, glass
- Fantasy: runes, aura, metal/crystal
- Reward: high contrast, glow, particles

## 3. Core Tokens
Background Void: #070A12
Panel: #0D1324
System Primary: #40D9FF
System Secondary: #657CFF
Success: #67E7A4
Danger: #FF506E
Common: #A7B0C0
Uncommon: #5EE38B
Rare: #3CCBFF
Epic: #B969FF
Legendary: #FFD56A
Mythic: #FF537E

## 4. Spacing Scale
4, 8, 12, 16, 24, 32, 48, 64

## 5. Radius
- System/HUD: 8–12px with chamfered accents
- Normal cards: 16–20px
- Reward ornaments: custom SVG frame

## 6. Typography
- Display: condensed/futuristic or fantasy-compatible
- Body: geometric sans
- Numbers: tabular/monospaced where appropriate

## 7. Component Primitives
Button, Card, SystemPanel, QuestCard, ProgressBar, StatChip, RarityFrame, ItemCard, Modal, Toast, Scanner, RewardReveal, ChestCard.

## 8. Mandatory Component States
Loading, Empty, Normal, Hover/Focus, Disabled, Success, Error, Retry.

## 9. Motion
System: fast/snap/scan.
Juicy UI: spring/bounce/overshoot.
Reward: anticipation → pause → impact → release.

Reduced-motion mode must replace shake/flash-heavy effects with opacity/scale transitions.

## 10. Accessibility Baseline
Target WCAG 2.2 AA where practical.
- visible keyboard focus
- adequate contrast
- non-color-only rarity/status indicators
- touch target sizing
- semantic labels
- reduced motion

## 11. Core Screen Blueprints
### Home/Profile
Player identity, level/XP, stats, power, active quest CTA, inventory shortcut.

### Quest Board
Seeded quest cards with category, difficulty, objective, reward preview.

### Verification
Evidence upload/manual entry, progress state, clear error/retry.

### Reward
Quest clear → EXP/stat count-up → chest granted.

### Gacha/Chest
Server-authoritative item already decided; client presents reveal only.

### Inventory
Filter by rarity/type; item instance cards.

## 12. Rarity Semantics
Rarity differs by border complexity, glow, ornament and motion — not color alone.
