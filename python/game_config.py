"""
game_config.py
Game configurations, stage telemetry, Kana pools, and path resolution for Hiragana Road Fighter.
"""

import os
import sys

# Virtual Canvas & Display Defaults
VIRTUAL_WIDTH = 1920
VIRTUAL_HEIGHT = 1080
SCREEN_WIDTH = VIRTUAL_WIDTH
SCREEN_HEIGHT = VIRTUAL_HEIGHT
TARGET_FPS = 60

# Road & Arcade Viewport Geometry (1080p Cockpit)
GAME_X = 280.0
GAME_W = 960.0
ROAD_MARGIN = 160.0
ROAD_WIDTH = GAME_W - (ROAD_MARGIN * 2.0)  # 640.0 px wide 4-lane highway
PLAYER_SCREEN_Y = 840.0

# Version & Release Metadata
GAME_VERSION = "0.5.0"
GITHUB_REPO = "deck-labs/hiragana-road-fighter"
VERSION_CHECK_URL = "https://raw.githubusercontent.com/deck-labs/hiragana-road-fighter/main/version.json"
RELEASES_API_URL = "https://api.github.com/repos/deck-labs/hiragana-road-fighter/releases/latest"

# Gameplay Settings
STAGE_TRACK_LENGTH = 36000.0
GAME_SPEED_SCALE = 0.5
BASE_SPEED = 80.0
TURBO_SPEED = 240.0
SPEED_ACCEL = 120.0
SPEED_DECEL = 80.0
BRAKE_DECEL = 220.0
STEER_SPEED = 420.0
MAX_FUEL = 100.0
FUEL_REWARD = 30.0
FUEL_PENALTY = 15.0
SCORE_REWARD = 50.0

# Total Stages
TOTAL_STAGES = 10

STAGE_NAMES = {
    1: "FOREST HIGHWAY",
    2: "COASTAL BRIDGE",
    3: "COASTAL BEACH",
    4: "MOUNTAIN PASS",
    5: "NEON METROPOLIS",
    6: "VOLCANO CALDERA",
    7: "GLACIER TUNDRA",
    8: "SAKURA BOULEVARD",
    9: "SUNSET CANYON",
    10: "FUJI SPEEDWAY"
}

STAGE_ENV_NOTES = {
    1: "BROAD HIGHWAY // EXPANSIVE STRAIGHTAWAYS // DENSE CEDAR",
    2: "COASTAL OCEAN BRIDGE // STEEL SPANS // NARROW PASSES",
    3: "TROPICAL BEACH SHORELINE // CONTINUOUS SWEEPS",
    4: "MOUNTAIN PASS // ROCKY GORGE // TIGHT S-CURVES",
    5: "NEON EXPRESSWAY // HIGH-SPEED SWEEPS // SKYSCRAPERS",
    6: "VOLCANIC OBSIDIAN RIDGE // MAGMA CRAGS // FAST APEXES",
    7: "FROST GLACIER // POLAR ICEFALL // ICY APEXES",
    8: "CHERRY BLOSSOM BOULEVARD // SPRING DRIFT // SAKURA PETALS",
    9: "RED ROCK CANYON // DUSK MESAS // HIGH-SPEED GORGE SWEEPS",
    10: "FUJI SPEEDWAY // GRAND CHAMPIONSHIP // GOLDEN APEX"
}

STAGE_KANA = {
    1: [
        {"kana": "あ", "romaji": "a"},
        {"kana": "い", "romaji": "i"},
        {"kana": "う", "romaji": "u"},
        {"kana": "え", "romaji": "e"},
        {"kana": "お", "romaji": "o"}
    ],
    2: [
        {"kana": "か", "romaji": "ka"},
        {"kana": "き", "romaji": "ki"},
        {"kana": "く", "romaji": "ku"},
        {"kana": "け", "romaji": "ke"},
        {"kana": "こ", "romaji": "ko"}
    ],
    3: [
        {"kana": "さ", "romaji": "sa"},
        {"kana": "し", "romaji": "shi"},
        {"kana": "す", "romaji": "su"},
        {"kana": "せ", "romaji": "se"},
        {"kana": "そ", "romaji": "so"}
    ],
    4: [
        {"kana": "た", "romaji": "ta"},
        {"kana": "ち", "romaji": "chi"},
        {"kana": "つ", "romaji": "tsu"},
        {"kana": "て", "romaji": "te"},
        {"kana": "と", "romaji": "to"}
    ],
    5: [
        {"kana": "な", "romaji": "na"},
        {"kana": "に", "romaji": "ni"},
        {"kana": "ぬ", "romaji": "nu"},
        {"kana": "ね", "romaji": "ne"},
        {"kana": "の", "romaji": "no"}
    ],
    6: [
        {"kana": "は", "romaji": "ha"},
        {"kana": "ひ", "romaji": "hi"},
        {"kana": "ふ", "romaji": "fu"},
        {"kana": "へ", "romaji": "he"},
        {"kana": "ほ", "romaji": "ho"}
    ],
    7: [
        {"kana": "ま", "romaji": "ma"},
        {"kana": "み", "romaji": "mi"},
        {"kana": "む", "romaji": "mu"},
        {"kana": "め", "romaji": "me"},
        {"kana": "も", "romaji": "mo"}
    ],
    8: [
        {"kana": "ら", "romaji": "ra"},
        {"kana": "り", "romaji": "ri"},
        {"kana": "る", "romaji": "ru"},
        {"kana": "れ", "romaji": "re"},
        {"kana": "ろ", "romaji": "ro"}
    ],
    9: [
        {"kana": "や", "romaji": "ya"},
        {"kana": "ゆ", "romaji": "yu"},
        {"kana": "よ", "romaji": "yo"},
        {"kana": "わ", "romaji": "wa"},
        {"kana": "を", "romaji": "wo"}
    ],
    10: [
        {"kana": "ん", "romaji": "n"},
        {"kana": "わ", "romaji": "wa"},
        {"kana": "れ", "romaji": "re"},
        {"kana": "ね", "romaji": "ne"},
        {"kana": "る", "romaji": "ru"},
        {"kana": "ろ", "romaji": "ro"}
    ]
}

TRAFFIC_COLORS = ["blue", "green", "yellow", "purple", "cyan", "orange"]

# Color Palette (RGB tuples)
COLOR_BG            = (15, 18, 24)
COLOR_PANEL_BG      = (10, 20, 36)
COLOR_PANEL_BORDER  = (0, 115, 191)
COLOR_WATER_DEEP    = (14, 48, 95)
COLOR_WATER_MID     = (24, 80, 145)
COLOR_WATER_SWELL   = (40, 115, 185)
COLOR_WATER_FOAM    = (215, 240, 255)
COLOR_BRIDGE_SHADOW = (8, 22, 42)
COLOR_WALKWAY_DARK  = (95, 100, 105)
COLOR_RAILING       = (190, 198, 205)
COLOR_BARRIER_RED   = (225, 45, 45)
COLOR_GOLD          = (255, 215, 0)
COLOR_CYAN          = (0, 217, 255)
COLOR_WHITE         = (255, 255, 255)
COLOR_BLACK         = (0, 0, 0)
COLOR_BEZEL         = (5, 8, 14)
COLOR_NEON_PURPLE   = (175, 45, 245)
COLOR_NEON_AMBER    = (255, 165, 0)
COLOR_NEON_CYAN     = (0, 235, 255)

def get_base_dir() -> str:
    """Resolve base directory whether running as source or frozen PyInstaller/AppImage bundle."""
    if getattr(sys, 'frozen', False):
        return getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.isdir(os.path.join(cur_dir, 'assets')):
        return cur_dir
    parent_dir = os.path.dirname(cur_dir)
    if os.path.isdir(os.path.join(parent_dir, 'assets')):
        return parent_dir
    return cur_dir

def get_asset_path(subpath: str) -> str:
    """Return absolute path to an asset."""
    return os.path.join(get_base_dir(), 'assets', subpath)

def detect_maximum_resolution() -> tuple[int, int]:
    """Detect the maximum resolution supported by the system display."""
    import pygame
    candidates = []

    # 1. Check all connected desktop monitor sizes (Pygame 2)
    try:
        get_desktop_sizes = getattr(pygame.display, "get_desktop_sizes", None)
        if callable(get_desktop_sizes):
            sizes = get_desktop_sizes()
            if sizes:
                for sz in sizes:
                    if isinstance(sz, (tuple, list)) and len(sz) >= 2:
                        candidates.append((int(sz[0]), int(sz[1])))
    except Exception as e:
        print(f"[Display] Note querying desktop sizes: {e}")

    # 2. Check supported fullscreen display modes
    try:
        modes = pygame.display.list_modes()
        if modes and modes != -1:
            for m in modes:
                if isinstance(m, (tuple, list)) and len(m) >= 2:
                    candidates.append((int(m[0]), int(m[1])))
    except Exception as e:
        print(f"[Display] Note querying list_modes: {e}")

    # 3. Check current display info
    try:
        info = pygame.display.Info()
        if info.current_w > 0 and info.current_h > 0:
            candidates.append((int(info.current_w), int(info.current_h)))
    except Exception as e:
        print(f"[Display] Note querying display info: {e}")

    # Filter sensible resolutions (>= 640x400)
    valid_candidates = [
        (w, h) for (w, h) in candidates
        if w >= 640 and h >= 400
    ]

    if valid_candidates:
        # Maximize pixel area; break ties by wider width
        best = max(valid_candidates, key=lambda s: (s[0] * s[1], s[0]))
        return best

    return (VIRTUAL_WIDTH, VIRTUAL_HEIGHT)

def compute_aspect_ratio(w: int, h: int) -> tuple[float, str]:
    """Compute aspect ratio float and descriptive label."""
    if h <= 0:
        return (16.0 / 9.0, "16:9")
    ratio = w / h
    if abs(ratio - (16.0 / 10.0)) < 0.04:
        return (16.0 / 10.0, "16:10 (Steam Deck / Widescreen)")
    elif abs(ratio - (16.0 / 9.0)) < 0.04:
        return (16.0 / 9.0, "16:9 (Standard HDTV / Monitor)")
    elif abs(ratio - (4.0 / 3.0)) < 0.04:
        return (4.0 / 3.0, "4:3 (Classic CRT Arcade)")
    elif abs(ratio - (21.0 / 9.0)) < 0.12:
        return (21.0 / 9.0, "21:9 (Ultrawide)")
    elif abs(ratio - (32.0 / 9.0)) < 0.15:
        return (32.0 / 9.0, "32:9 (Super Ultrawide)")
    else:
        return (ratio, f"Custom ({w}x{h})")

def get_virtual_dimensions(w: int, h: int, aspect_mode: str = "auto") -> tuple[int, int]:
    """Calculate virtual canvas dimensions based on display ratio and aspect mode."""
    if h <= 0:
        return 1920, 1080
    ratio = w / h
    if aspect_mode == "auto":
        if 1.50 <= ratio <= 1.65:
            # 16:10 Native (Steam Deck 1280x800, 1920x1200, 2560x1600)
            return 1920, 1200
        elif 1.66 <= ratio <= 1.85:
            # 16:9 Native (1080p, 1440p, 4K UHD)
            return 1920, 1080
        elif ratio < 1.50:
            # Taller display (e.g. 4:3, 5:4)
            return 1920, int(round(1920 / ratio))
        else:
            # Ultrawide (21:9) -> render 16:9 virtual canvas with side pillarbox bezels
            return 1920, 1080
    elif aspect_mode == "16:9":
        return 1920, 1080
    else: # stretch
        return 1920, 1080
