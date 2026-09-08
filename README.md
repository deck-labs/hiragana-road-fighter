# Hiragana Road Fighter (ひらがな ロードファイター)

[![Language](https://img.shields.io/badge/Language-Python%203.13-blue.svg)](https://www.python.org/)
[![Engine](https://img.shields.io/badge/Engine-Pygame%202.6-yellow.svg)](https://www.pygame.org/)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%2F%20SteamOS%20(Steam%20Deck)-orange.svg)](https://store.steampowered.com/steamdeck)
[![Stages](https://img.shields.io/badge/Stages-7%20Courses%20(A%2C%20KA%2C%20SA%2C%20TA%2C%20NA%2C%20HA%2C%20MA)-brightgreen.svg)](#7-stages--hiragana-syllabus)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)
[![Download AppImage](https://img.shields.io/badge/Download-Latest%20AppImage-00C853?style=flat&logo=appimage&logoColor=white)](https://github.com/deck-labs/hiragana-road-fighter/raw/main/Hiragana_Road_Fighter-x86_64.AppImage)

A retro Japanese Hiragana learning arcade racer built in Python (Pygame), inspired by Konami's arcade classic *Road Fighter*. Players master reading and recognizing Hiragana characters at adrenaline-pumping speeds of up to 240 KM/H!

<div align="center">

<a href="https://github.com/deck-labs/hiragana-road-fighter/raw/main/Hiragana_Road_Fighter-x86_64.AppImage">
  <img src="https://img.shields.io/badge/⬇%20DOWNLOAD%20LATEST%20APPIMAGE-v0.3.0%20(Linux%20%2F%20Steam%20Deck)-00C853?style=for-the-badge&logo=appimage&logoColor=white" height="46" alt="Download Latest AppImage">
</a>

<br>
<sub><b>Standalone Linux Binary:</b> No installation required. Works directly with Steam / Steam Deck!</sub>

</div>

---

## ⚡ Direct Download (Standalone AppImage)

You do **not** need to install Python, dependencies, or compile code. You can download and launch the standalone Linux AppImage directly:

<div align="center">

<a href="https://github.com/deck-labs/hiragana-road-fighter/raw/main/Hiragana_Road_Fighter-x86_64.AppImage">
  <img src="https://img.shields.io/badge/⬇%20DOWNLOAD%20APPIMAGE-v0.3.0%20(Standalone%20x86__64)-00E676?style=for-the-badge&logo=linux&logoColor=black" height="48" alt="Download AppImage">
</a>

<br>
<sub><b>Filename:</b> <code>Hiragana_Road_Fighter-x86_64.AppImage</code> | <b>Size:</b> ~41 MB | <b>Architecture:</b> x86_64 (Linux / Steam Deck)</sub>

</div>

### 🚀 One-Line Terminal Shortcut (Download & Run)

Paste this single command into your terminal (Steam Deck Konsole, Arch, Ubuntu, Fedora) to download and launch immediately:

```bash
curl -sSL https://raw.githubusercontent.com/deck-labs/hiragana-road-fighter/main/download.sh | bash
```

Or download manually:

```bash
curl -L -o Hiragana_Road_Fighter-x86_64.AppImage https://raw.githubusercontent.com/deck-labs/hiragana-road-fighter/main/Hiragana_Road_Fighter-x86_64.AppImage
chmod +x Hiragana_Road_Fighter-x86_64.AppImage
./Hiragana_Road_Fighter-x86_64.AppImage
```

---

## 📸 Screenshots

| Stage 1: Forest Highway (あいうえお) | Stage 2: Coastal Bridge (かきくけこ) |
| :---: | :---: |
| ![Stage 1](screenshots/hud_stage1.png) | ![Stage 2](screenshots/hud_stage2.png) |

| Stage 3: Coastal Beach (さしすせそ) | Stage 4: Mountain Pass (たちつてと) |
| :---: | :---: |
| ![Stage 3](screenshots/hud_stage3.png) | ![Stage 4](screenshots/hud_stage4.png) |

| Stage 5: Neon Metropolis (なにぬねの) | Stage 6: Volcano Caldera (はひふへほ) |
| :---: | :---: |
| ![Stage 5](screenshots/hud_stage5.png) | ![Stage 6](screenshots/hud_stage6.png) |

| Stage 7: Glacier Tundra (まみむめも) |
| :---: |
| ![Stage 7](screenshots/hud_stage7.png) |

---

## 🏎️ 7 Stages & Hiragana Syllabus

All 7 stages feature an identical 36,000-meter course length with distinct environmental scenery, road curvature, and Hiragana character sets:

| Stage | Theme | Hiragana Set | Romaji Sounds |
| :--- | :--- | :---: | :--- |
| **01** | **Forest Highway** | `あ` `い` `う` `え` `お` | `a`, `i`, `u`, `e`, `o` |
| **02** | **Coastal Bridge** | `か` `き` `く` `け` `こ` | `ka`, `ki`, `ku`, `ke`, `ko` |
| **03** | **Coastal Beach** | `さ` `し` `す` `せ` `そ` | `sa`, `shi`, `su`, `se`, `so` |
| **04** | **Mountain Pass** | `た` `ち` `つ` `て` `と` | `ta`, `chi`, `tsu`, `te`, `to` |
| **05** | **Neon Metropolis** | `な` `に` `ぬ` `ね` `の` | `na`, `ni`, `nu`, `ne`, `no` |
| **06** | **Volcano Caldera** | `は` `ひ` `ふ` `へ` `ほ` | `ha`, `hi`, `fu` / `hu`, `he`, `ho` |
| **07** | **Glacier Tundra** | `ま` `み` `む` `め` `も` | `ma`, `mi`, `mu`, `me`, `mo` |

---

## 🎮 Gameplay Mechanics

1. **Read & Intercept**:
   - Your red sports car features an **illuminated pearl-white racing plate** displaying your target Japanese Hiragana character in bold crimson calligraphy.
   - Traffic vehicles ahead bear **Romaji pronunciations** on high-contrast white decal plates framed in dark steel.
   - Identify your car's target Hiragana and ram into the vehicle displaying the matching Romaji sound!
2. **Refuel & Score**:
   - **Correct Match**: Restores **+30% Fuel** and awards **+50 Points**, immediately advancing to the next Kana in the syllabus.
   - **Mismatched Collision**: Costs **-15% Fuel** and triggers an impact spinout wobble!
3. **Survive & Clear**:
   - Complete the 36,000-meter course before your fuel runs out.
   - Clearing Stage 7 triggers the grand victory screen (**"ALL STAGES CLEARED!"**) and returns to the Title Screen.

---

## 🕹️ Controls

The game includes universal gamepad support (Steam Deck, Xbox, 8BitDo, PlayStation, Nintendo Switch) and keyboard input:

| Action | Controller / Gamepad | Keyboard |
| :--- | :--- | :--- |
| **Steer Left / Right** | D-Pad / Left Analog Stick | `Left` / `Right` or `A` / `D` |
| **Turbo Boost (240 km/h)** | `(A)` / `(B)` / `RT` / `RB` | `Up` / `W` / `Space` |
| **Brake / Slow** | `(X)` / `(Y)` / `LT` / `LB` | `Down` / `S` |
| **Pause & Resume** | `SELECT` (`Back` / `View` / `Minus`) | `P` |
| **Options / Audio Volume** | `START` (`Options` / `Plus` / `Menu`) | `ESC` / `Enter` |
| **Quick Quit to Desktop** | `SELECT + START` (Simultaneously) | Gamepad combo |

### Quality of Life & Polish
* **Auto-Resolution & Adaptive Aspect Ratio**: Automatically detects the maximum native resolution supported by your display hardware. On Steam Deck (1280x800) and 16:10 displays (1920x1200), runs in native 16:10 aspect ratio with **ZERO black bars** (no letterbox or pillarbox bars) and crisp 100% isotropic 2:3 scaling. Also natively supports 16:9 (1080p, 1440p, 4K UHD), 21:9 Ultrawide, and full stretch mode, toggleable on-the-fly in the in-game Options menu (`AUTO` vs `FULL (STRETCH)`). Mouse and touch coordinates automatically translate to virtual coordinates.
* **In-Game Online System Updater**: Check for updates directly from the Title Screen. Safely updates the AppImage in-place without altering file paths or filenames, guaranteeing that Steam shortcuts, desktop launchers, and scripts never break.
* **Complete Audio Mute on Pause**: All engine sound loops, turbo whoosh, SFX, and music are completely silenced while paused.
* **Idle Mouse Auto-Hide**: Mouse cursor auto-hides after 2 seconds of inactivity, with Steam Deck trackpad micro-jitter filtering.
* **Pixel-Crisp Steering**: The player car remains strictly upright during lane shifts with zero sprite distortion. Smooth antialiased rotozoom is reserved exclusively for impact spinouts.

---

## 💻 Running from Source

### Prerequisites
- Python 3.10+
- Pygame (`pip install pygame`)

### Launching:
```bash
# 1. Clone repository
git clone https://github.com/deck-labs/hiragana-road-fighter.git
cd hiragana-road-fighter

# 2. Install Pygame
pip install pygame

# 3. Launch game
./run.sh
# (Or: python3 python/main.py)
```

---

## 📦 Building the Standalone AppImage

To package a standalone, dependency-free Linux AppImage:

```bash
./build_appimage.sh
```

This compiles the Python codebase using PyInstaller, bundles all assets, generates a 256x256 icon, and packages a portable `x86_64` AppImage that runs on any modern Linux distribution without requiring Python or system libraries.

---

## 📜 License

MIT License. Open source and free for educational and personal use.
