# Hiragana Road Fighter (ひらがな ロードファイター)

[![Language](https://img.shields.io/badge/Language-C%2B%2B17-blue.svg)](https://en.wikipedia.org/wiki/C%2B%2B17)
[![Framework](https://img.shields.io/badge/Library-SDL2%20%2F%20FreeType2-brightgreen.svg)](https://libsdl.org/)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%2F%20SteamOS%20(Steam%20Deck)-orange.svg)](https://store.steampowered.com/steamdeck)
[![Release](https://img.shields.io/badge/Release-v0.01-red.svg)](https://github.com/deck-labs/hiragana-road-fighter/releases)

A retro Japanese Hiragana learning arcade racer built from scratch in C++ and SDL2, inspired by Konami's arcade classic *Road Fighter*. Players learn to read and recognize Hiragana at adrenaline-pumping speeds of up to 240 KM/H!

---

## ⚡ Direct Download Shortcuts (AppImage Only)

You do **not** need to clone this repository, install dependencies, or compile source code. You can download and launch the standalone AppImage directly using any of these shortcuts:

### 🚀 Option 1: One-Click Browser Download

[![Direct Download AppImage](https://img.shields.io/badge/⬇%20DOWNLOAD%20APPIMAGE-(17%20MB)-00c853?style=for-the-badge&logo=linux&logoColor=white)](https://github.com/deck-labs/hiragana-road-fighter/releases/latest/download/Hiragana_Road_Fighter-x86_64.AppImage)

| Download Target | Direct Shortcut Link | Description |
| :--- | :--- | :--- |
| **Direct AppImage Release** | [📥 **Download Hiragana Road Fighter AppImage**](https://github.com/deck-labs/hiragana-road-fighter/releases/latest/download/Hiragana_Road_Fighter-x86_64.AppImage) | Standalone Linux executable (17 MB) |
| **Repository File Link** | [📄 **Download from Repository**](https://github.com/deck-labs/hiragana-road-fighter/raw/main/Hiragana_Road_Fighter-x86_64.AppImage) | Raw direct download from Git tree |

### 💻 Option 2: One-Line Terminal Shortcut (Auto Download & Run)

Paste this single command into your terminal (Steam Deck Konsole, Arch, Ubuntu, Fedora) to download and launch immediately:

```bash
curl -sSL https://raw.githubusercontent.com/deck-labs/hiragana-road-fighter/main/download.sh | bash
```

Or download manually via `curl` / `wget`:

```bash
curl -LO https://github.com/deck-labs/hiragana-road-fighter/releases/latest/download/Hiragana_Road_Fighter-x86_64.AppImage
chmod +x Hiragana_Road_Fighter-x86_64.AppImage
./Hiragana_Road_Fighter-x86_64.AppImage
```

---

## Screenshots

| Stage 1: Forest Highway | Stage 2: Coastal Bridge |
| :---: | :---: |
| ![Stage 1](screenshots/hud_stage1.png) | ![Stage 2](screenshots/hud_stage2.png) |

| Stage 3: Coastal Beach | Display Auto-Detection & Pause Menu |
| :---: | :---: |
| ![Stage 3](screenshots/hud_stage3.png) | ![Pause Menu](screenshots/hud_pause.png) |

---

## Gameplay & Educational Mechanics

1. **Read & Match**:
   - Your red sports car features an illuminated pearl-white racing plate displaying your target **Japanese Hiragana** character.
   - Traffic vehicles ahead bear **Romaji sounds** (e.g. `a`, `i`, `u`, `e`, `o`, `ka`, `ki`, etc.) on high-contrast white decal plates.
   - Study your car's Hiragana and ram into the vehicle with the matching Romaji sound!
2. **Refuel & Score**:
   - **Correct Match**: Restores **+30% Fuel** and awards **+50 Points**, immediately advancing you to the next Kana in the syllabus.
   - **Mismatched Collision**: Costs **-10% Fuel** and triggers a skid spinout!
3. **Survive & Clear**:
   - Complete the 1.6 KM course before your fuel runs dry. Stage 1 takes place on a high-speed Forest Highway; Stage 2 takes you onto a narrow Coastal Bridge with dynamic road tapering.

---

## Modern AAA HUD & Cockpit Cluster

- **Holographic Target Kana Scanner**: Displays your vehicle's active Hiragana in a dedicated **54px bold** holographic chamber with real-time collision feedback (`★ PERFECT MATCH! ★` vs `⚠ WRONG VEHICLE HIT! ⚠`) and combo streak tracking. *(Does not spoil the Romaji answer, preserving the learning challenge!)*
- **Digital Instrument Cluster**:
  - Ultra-bold 52px digital speedometer (`KM/H`).
  - Dynamic drive-mode telemetry pill (`TURBO BOOST // HI`, `BRAKE // LOW`, `CRUISE // MID`, `! SPINOUT SKID !`).
  - 24-segmented LED tachometer (cyan → yellow → pulsing redline).
- **High-Voltage Power Cell**:
  - 16 discrete LED battery cells that shift from emerald green (`>50%`) to yellow (`25-50%`) to a flashing red low-fuel alert (`<25%`).
- **Left GPS Telemetry Rail**:
  - Miniature vertical dual-rail highway corridor with checkpoint laser gates at 25%, 50%, and 75%.
  - Player GPS sports car beacon with pulsing radar ring and forward headlights.
  - Digital remaining distance telemetry readout.
- **Display Auto-Detection**:
  - Automatically detects maximum monitor/display resolution (FHD, QHD, 4K, Steam Deck 1280x800).
  - Automatically computes and applies the optimal aspect ratio (16:10 for Steam Deck, 16:9 for HDTVs, 4:3 for CRT, 21:9 for ultrawide).

---

## Controls

The game features full controller support (Steam Deck, Xbox, PlayStation, 8BitDo) and keyboard input:

| Action | Controller | Keyboard |
| :--- | :--- | :--- |
| **Steer** | D-Pad / Left Analog Stick | Left / Right (or A / D) |
| **Turbo Boost** | (A) / (B) / Up / RT | Up (or W) / Space |
| **Brake / Drift** | (X) / (Y) / Down / LT | Down (or S) |
| **Pause & Resume** | SELECT / START | ESC / P / Tab |
| **Quick Quit** | SELECT + START (Simultaneously) | Q |

---

## Download & Run (Standalone AppImage)

A pre-packaged, standalone Linux AppImage is included directly in this repository and available via GitHub Releases:

```bash
# Make executable and launch
chmod +x Hiragana_Road_Fighter-x86_64.AppImage
./Hiragana_Road_Fighter-x86_64.AppImage
```

The AppImage bundles all required shared libraries (`libSDL2`, `libfreetype`, `libharfbuzz`, `libpng`) and Japanese Noto CJK Bold fonts. It runs on any modern 64-bit Linux distribution including SteamOS, Arch Linux, Ubuntu, Fedora, Debian, and openSUSE.

---

## Building from Source

### Prerequisites
- GCC / G++ supporting C++17
- SDL2 development headers (`libsdl2-dev` or `sdl2`)
- FreeType2 development headers (`libfreetype6-dev` or `freetype2`)

### Build Steps
```bash
# 1. Clone repository
git clone https://github.com/deck-labs/hiragana-road-fighter.git
cd hiragana-road-fighter

# 2. Build C++ binary
cd cpp
./build.sh

# 3. Run game
./road_fighter_cpp
```

### Packaging AppImage
To rebuild the standalone AppImage:
```bash
./build_appimage.sh
```

---

## License

MIT License. Open source and free for educational and personal use.
