"""
game_config.py
Game configurations, stage telemetry, Kana pools, and path resolution for Hiragana Road Fighter.
"""

import os
import sys

# Display and Target Frame Rate
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
TARGET_FPS = 60

# Road & Arcade Viewport Geometry (1080p Cockpit)
GAME_X = 280.0
GAME_W = 960.0
ROAD_MARGIN = 160.0
ROAD_WIDTH = GAME_W - (ROAD_MARGIN * 2.0)  # 640.0 px wide 4-lane highway
PLAYER_SCREEN_Y = 840.0

# Version & Release Metadata
GAME_VERSION = "0.2.0"
GITHUB_REPO = "deck-labs/hiragana-road-fighter"
VERSION_CHECK_URL = "https://raw.githubusercontent.com/deck-labs/hiragana-road-fighter/main/version.json"
RELEASES_API_URL = "https://api.github.com/repos/deck-labs/hiragana-road-fighter/releases/latest"

# Gameplay Mechanics & Balancing
STAGE_TRACK_LENGTH = 36000.0   # Exactly 36,000 units across all 5 stages
GAME_SPEED_SCALE = 0.5         # 50% arcade speed scale for readable kana recognition
MAX_FUEL = 100.0
FUEL_REWARD = 30.0             # +30% fuel on correct Kana match
FUEL_PENALTY = 15.0            # -15% fuel penalty on wrong car collision
SCORE_REWARD = 50.0

# Total Stages
TOTAL_STAGES = 5

STAGE_NAMES = {
    1: "FOREST HIGHWAY",
    2: "COASTAL BRIDGE",
    3: "COASTAL BEACH",
    4: "MOUNTAIN PASS",
    5: "NEON METROPOLIS"
}

STAGE_ENV_NOTES = {
    1: "BROAD HIGHWAY // EXPANSIVE STRAIGHTAWAYS // DENSE FORESTRY",
    2: "COASTAL OCEAN BRIDGE // NARROW CHOKEPOINTS // STEEL SPANS",
    3: "TROPICAL BEACH SHORELINE // CONTINUOUS SWEEPING CURVES",
    4: "MOUNTAIN CANYON PASS // ROCKY CLIFF GORGE // TIGHT S-CURVES",
    5: "NEON CITY EXPRESSWAY // HIGH-SPEED URBAN SWEEPS // SKYSCRAPERS"
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
