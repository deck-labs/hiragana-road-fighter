"""
entities.py
PlayerCar and TrafficCar entities with physics, Kana/Romaji roofs, collision, and VFX.
"""

import math
import random
import pygame
from game_config import (
    PLAYER_SCREEN_Y, COLOR_BARRIER_RED, COLOR_WHITE, COLOR_GOLD,
    get_asset_path
)

class PlayerCar:
    WIDTH = 68.0
    HEIGHT = 130.0
    
    def __init__(self, font_cjk: pygame.font.Font):
        self.x = 680.0
        self.y = PLAYER_SCREEN_Y
        self.speed_kmh = 80.0
        self.max_cruise_speed = 160.0
        self.max_turbo_speed = 240.0
        self.is_turbo = False
        self.is_braking = False
        self.wobble_timer = 0.0
        self.rotation = 0.0
        self.current_kana = "あ"
        self.font_cjk = font_cjk
        self.is_sparking = False
        self.spark_side = 0 # -1 left, +1 right
        
        # Load sprite
        spr_path = get_asset_path("sprites/player_car.png")
        try:
            raw = pygame.image.load(spr_path).convert_alpha()
            self.sprite = pygame.transform.scale(raw, (int(self.WIDTH), int(self.HEIGHT)))
        except Exception as e:
            print(f"Warning: Player sprite load failed: {e}")
            self.sprite = pygame.Surface((int(self.WIDTH), int(self.HEIGHT)), pygame.SRCALPHA)
            pygame.draw.rect(self.sprite, (220, 40, 40), (0, 0, int(self.WIDTH), int(self.HEIGHT)), border_radius=8)

        self.composite_sprite = self._build_composite_sprite()

    def _build_composite_sprite(self) -> pygame.Surface:
        """High-contrast illuminated racing roof decal with pearl-white backing and crimson glyph."""
        surf = self.sprite.copy()
        if self.font_cjk and self.current_kana:
            pw, ph = 46, 44
            px = int(self.WIDTH * 0.5) - pw // 2
            py = 64 - ph // 2
            # Outer dark bezel
            pygame.draw.rect(surf, (20, 25, 35), (px, py, pw, ph), border_radius=5)
            # Metallic gold border
            pygame.draw.rect(surf, (255, 215, 0), (px + 1, py + 1, pw - 2, ph - 2), 2, border_radius=4)
            # Brilliant pearl white plate
            pygame.draw.rect(surf, (252, 252, 255), (px + 3, py + 3, pw - 6, ph - 6), border_radius=3)
            # Bold rich crimson Hiragana glyph
            txt = self.font_cjk.render(self.current_kana, True, (190, 15, 20))
            surf.blit(txt, txt.get_rect(center=(int(self.WIDTH * 0.5), 64)))
        return surf

    def update_kana(self, kana: str):
        if self.current_kana != kana:
            self.current_kana = kana
            self.composite_sprite = self._build_composite_sprite()

    def handle_input(self, steer_axis: float, turbo_down: bool, brake_down: bool, delta: float):
        self.is_turbo = turbo_down
        self.is_braking = brake_down
        
        # Acceleration / Braking
        if self.is_braking:
            self.speed_kmh = max(0.0, self.speed_kmh - 180.0 * delta)
        elif self.is_turbo:
            self.speed_kmh = min(self.max_turbo_speed, self.speed_kmh + 75.0 * delta)
        else:
            if self.speed_kmh < self.max_cruise_speed:
                self.speed_kmh = min(self.max_cruise_speed, self.speed_kmh + 50.0 * delta)
            else:
                self.speed_kmh = max(self.max_cruise_speed, self.speed_kmh - 45.0 * delta)
                
        # Steering
        steer_spd = 220.0 * (self.speed_kmh / 160.0)
        self.x += steer_axis * steer_spd * delta
        
        # Wobble decay & rotation (only tilts during spin/wobble from impact, perfectly upright during steering)
        if self.wobble_timer > 0.0:
            self.wobble_timer -= delta
            self.rotation = math.sin(self.wobble_timer * 35.0) * 0.15
        else:
            self.rotation = 0.0

    def check_road_bounds(self, road_edges: tuple[float, float]):
        r_left, r_right = road_edges
        left_bound = r_left + (self.WIDTH * 0.5)
        right_bound = r_right - (self.WIDTH * 0.5)
        
        if self.x < left_bound:
            self.x = left_bound
            self.speed_kmh = max(30.0, self.speed_kmh - 4.0)
            self.is_sparking = True
            self.spark_side = -1
        elif self.x > right_bound:
            self.x = right_bound
            self.speed_kmh = max(30.0, self.speed_kmh - 4.0)
            self.is_sparking = True
            self.spark_side = 1
        else:
            self.is_sparking = False

    def trigger_wobble(self):
        self.wobble_timer = 0.5
        self.speed_kmh = max(40.0, self.speed_kmh * 0.75)

    def get_hitbox(self) -> pygame.Rect:
        # Match visual bounds of car chassis
        hw = self.WIDTH * 0.85
        hh = self.HEIGHT * 0.90
        return pygame.Rect(self.x - hw * 0.5, self.y - hh * 0.5, hw, hh)

    def render(self, surface: pygame.Surface):
        # 1. Turbo Flames
        if self.is_turbo and self.speed_kmh > 100.0:
            fl_h = random.uniform(14.0, 26.0)
            fl_w = 6.0
            left_fl_x = self.x - 14.0
            right_fl_x = self.x + 8.0
            fl_y = self.y + (self.HEIGHT * 0.5) - 4.0
            
            # Yellow/Orange/Cyan glow
            for fl_x in [left_fl_x, right_fl_x]:
                pygame.draw.polygon(surface, (255, 180, 20), [
                    (fl_x, fl_y),
                    (fl_x + fl_w, fl_y),
                    (fl_x + fl_w * 0.5, fl_y + fl_h)
                ])
                pygame.draw.polygon(surface, (0, 220, 255), [
                    (fl_x + 1.5, fl_y),
                    (fl_x + fl_w - 1.5, fl_y),
                    (fl_x + fl_w * 0.5, fl_y + fl_h * 0.6)
                ])
                
        # 2. Car Body with High-Contrast Roof Decal (stays 100% crisp upright during steering, smooth antialiased rotozoom only on crash wobble)
        surf_to_draw = self.composite_sprite
        if abs(self.rotation) > 0.005:
            deg = -math.degrees(self.rotation)
            surf_to_draw = pygame.transform.rotozoom(self.composite_sprite, deg, 1.0)
            
        rect = surf_to_draw.get_rect(center=(int(round(self.x)), int(round(self.y))))
        surface.blit(surf_to_draw, rect)
            
        # 3. Guardrail Sparks
        if self.is_sparking:
            spk_x = self.x + (self.spark_side * self.WIDTH * 0.5)
            for _ in range(3):
                ox = random.uniform(-6, 6)
                oy = random.uniform(0, 16)
                sz = random.uniform(2, 5)
                pygame.draw.circle(surface, (255, 235, 80), (int(spk_x + ox), int(self.y + oy)), int(sz))


_latin_fonts: dict[int, pygame.font.Font] = {}

def get_latin_font(size: int) -> pygame.font.Font:
    """Cache Latin fonts of varying sizes for dynamic Romaji plate scaling."""
    if size not in _latin_fonts:
        path = get_asset_path("fonts/DejaVuSans-Bold.ttf")
        try:
            _latin_fonts[size] = pygame.font.Font(path, size)
        except Exception:
            _latin_fonts[size] = pygame.font.SysFont("sans-serif", size, bold=True)
    return _latin_fonts[size]


class TrafficCar:
    WIDTH = 68.0
    HEIGHT = 130.0
    
    _textures = {}

    def __init__(self, romaji: str, start_world_y: float, lane_idx: int, speed: float, color: str, font_latin: pygame.font.Font = None):
        self.romaji = romaji
        self.world_y = start_world_y
        self.speed_kmh = speed
        self.color_name = color
        
        lane_fractions = [0.125, 0.375, 0.625, 0.875]
        self.lane_fraction = lane_fractions[max(0, min(3, lane_idx))]
        
        self.x = 0.0
        self.y = -500.0
        self.is_active = True
        self.is_matched = False
        self.wobble_timer = 0.0
        self.match_anim_timer = 0.0
        self.to_remove = False
        
        raw_sprite = self._get_texture(color)
        self.sprite = self._build_traffic_sprite(raw_sprite, romaji)

    @classmethod
    def _get_texture(cls, color: str) -> pygame.Surface:
        if color not in cls._textures:
            path = get_asset_path(f"sprites/traffic_{color}.png")
            try:
                raw = pygame.image.load(path).convert_alpha()
                cls._textures[color] = pygame.transform.scale(raw, (int(cls.WIDTH), int(cls.HEIGHT)))
            except Exception as e:
                print(f"Warning: Traffic sprite {color} load failed: {e}")
                s = pygame.Surface((int(cls.WIDTH), int(cls.HEIGHT)), pygame.SRCALPHA)
                pygame.draw.rect(s, (40, 120, 220), (0, 0, int(cls.WIDTH), int(cls.HEIGHT)), border_radius=8)
                cls._textures[color] = s
        return cls._textures[color]

    @classmethod
    def _build_traffic_sprite(cls, base_sprite: pygame.Surface, romaji: str) -> pygame.Surface:
        """High-contrast illuminated white decal plate with dark racing bezel and charcoal Romaji."""
        surf = base_sprite.copy()
        if romaji:
            pw, ph = 46, 44
            px = int(cls.WIDTH * 0.5) - pw // 2
            py = 64 - ph // 2
            # Outer dark bezel
            pygame.draw.rect(surf, (15, 20, 30), (px, py, pw, ph), border_radius=5)
            # Steel frame
            pygame.draw.rect(surf, (75, 95, 125), (px + 1, py + 1, pw - 2, ph - 2), 2, border_radius=4)
            # Crisp pure white backing
            pygame.draw.rect(surf, (255, 255, 255), (px + 3, py + 3, pw - 6, ph - 6), border_radius=3)
            
            # Dynamic font sizing for perfect fit within decal plate
            clean_ro = romaji.upper().strip()
            if len(clean_ro) == 1:
                fnt = get_latin_font(24)
            elif len(clean_ro) == 2:
                fnt = get_latin_font(20)
            else:
                fnt = get_latin_font(17)
                
            # Deep charcoal/navy Romaji on pure white plate for razor-sharp legibility at high speed
            txt = fnt.render(clean_ro, True, (12, 18, 30))
            surf.blit(txt, txt.get_rect(center=(int(cls.WIDTH * 0.5), 64)))
        return surf

    def update(self, delta: float):
        if not self.is_active:
            if self.is_matched:
                self.match_anim_timer += delta
                if self.match_anim_timer >= 0.30:
                    self.to_remove = True
            elif self.wobble_timer > 0.0:
                self.wobble_timer -= delta
                self.world_y += self.speed_kmh * 3.0 * delta
                if self.wobble_timer <= 0.0:
                    self.to_remove = True
            return
            
        # Move along track
        self.world_y += self.speed_kmh * 3.0 * delta

    def update_screen_pos(self, track_distance: float, road_edges: tuple[float, float], player_screen_y: float = None, screen_h: float = None):
        # Screen Y
        base_y = player_screen_y if player_screen_y is not None else PLAYER_SCREEN_Y
        self.y = base_y - (self.world_y - track_distance)
        
        # Follow road edges smoothly
        r_left, r_right = road_edges
        r_width = r_right - r_left
        car_margin = (self.WIDTH * 0.5) + 8.0
        avail_width = max(self.WIDTH, r_width - (car_margin * 2.0))
        self.x = r_left + car_margin + (self.lane_fraction * avail_width)
        
        # Despawn bounds
        max_y = (screen_h + 120.0) if screen_h is not None else 1300.0
        if self.y > max_y or self.y < -500.0:
            self.to_remove = True

    def trigger_match(self):
        self.is_matched = True
        self.is_active = False
        self.match_anim_timer = 0.0

    def trigger_crash(self):
        self.is_active = False
        self.wobble_timer = 0.5
        self.speed_kmh = max(20.0, self.speed_kmh * 0.5)

    def get_hitbox(self) -> pygame.Rect:
        hw = self.WIDTH * 0.85
        hh = self.HEIGHT * 0.90
        return pygame.Rect(self.x - hw * 0.5, self.y - hh * 0.5, hw, hh)

    def render(self, surface: pygame.Surface):
        if self.to_remove:
            return
            
        if self.is_matched:
            # Scale up and fade out
            scale_fac = 1.0 + self.match_anim_timer * 1.5
            alpha = max(0, int(255 * (1.0 - self.match_anim_timer * 4.0)))
            sw = int(self.WIDTH * scale_fac)
            sh = int(self.HEIGHT * scale_fac)
            scaled = pygame.transform.scale(self.sprite, (sw, sh))
            scaled.set_alpha(alpha)
            rect = scaled.get_rect(center=(int(round(self.x)), int(round(self.y))))
            surface.blit(scaled, rect)
            return
            
        surf_to_draw = self.sprite
        if self.wobble_timer > 0.0:
            angle = math.sin(self.wobble_timer * 40.0) * 15.0
            surf_to_draw = pygame.transform.rotozoom(self.sprite, angle, 1.0)
            
        rect = surf_to_draw.get_rect(center=(int(round(self.x)), int(round(self.y))))
        surface.blit(surf_to_draw, rect)
