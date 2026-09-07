"""
road_renderer.py
Road curvature calculations, slice-by-slice rendering, stage environments, and finish line.
"""

import math
import random
import pygame
from game_config import (
    GAME_X, GAME_W, ROAD_MARGIN, SCREEN_WIDTH, SCREEN_HEIGHT,
    STAGE_TRACK_LENGTH, PLAYER_SCREEN_Y,
    COLOR_WATER_DEEP, COLOR_WATER_MID, COLOR_WATER_SWELL,
    COLOR_WATER_FOAM, COLOR_BRIDGE_SHADOW, COLOR_WALKWAY_DARK,
    COLOR_RAILING, COLOR_BARRIER_RED, COLOR_WHITE, COLOR_GOLD,
    COLOR_NEON_PURPLE, COLOR_NEON_AMBER, COLOR_NEON_CYAN,
    get_asset_path
)

class RoadRenderer:
    def __init__(self):
        self.track_distance = 0.0
        self.current_stage = 1
        self.frames = 0
        
        # Textures and sprites
        self.tex_asphalt = None
        self.tex_grass = None
        self.tex_concrete = None
        self.tex_water = None
        self.tex_sand = None
        self.tex_rock_ground = None
        
        self.tex_tree = None
        self.tex_palm_tree = None
        self.tex_pine_tree = None
        self.tex_boulder = None
        self.tex_finish_banner = None
        self.font_gantry = None
        
        # Scenery collections
        self.stage1_trees = []
        self.stage3_palms = []
        self.stage4_scenery = []
        self.stage5_buildings = []
        self.stage5_lamps = []
        self.stage5_gantries = []
        
        self._load_assets()
        self._generate_scenery()

    def _load_assets(self):
        def load_img(subpath):
            path = get_asset_path(subpath)
            try:
                surf = pygame.image.load(path)
                return surf.convert_alpha()
            except Exception as e:
                print(f"Warning: Failed to load {subpath}: {e}")
                # Fallback blank surface
                s = pygame.Surface((64, 64), pygame.SRCALPHA)
                s.fill((100, 100, 100, 255))
                return s

        self.tex_asphalt = load_img("textures/asphalt.png")
        self.tex_grass = load_img("textures/grass.png")
        self.tex_concrete = load_img("textures/concrete.png")
        self.tex_water = load_img("textures/water.png")
        self.tex_sand = load_img("textures/sand.png")
        self.tex_rock_ground = load_img("textures/rock_ground.png")
        
        self.tex_tree = load_img("sprites/tree.png")
        self.tex_palm_tree = load_img("sprites/palm_tree.png")
        self.tex_pine_tree = load_img("sprites/pine_tree.png")
        self.tex_boulder = load_img("sprites/boulder.png")
        self.tex_finish_banner = load_img("sprites/finish_banner.png")
        try:
            self.font_gantry = pygame.font.Font(get_asset_path("fonts/DejaVuSans-Bold.ttf"), 14)
        except Exception:
            self.font_gantry = pygame.font.Font(None, 16)

    def _generate_scenery(self):
        rng = random.Random(12345)
        
        # Stage 1: Trees on grass verges
        y = 200.0
        while y < STAGE_TRACK_LENGTH - 800.0:
            y += rng.uniform(180.0, 320.0)
            lx = rng.uniform(GAME_X + 25.0, GAME_X + 110.0)
            rx = rng.uniform(GAME_X + GAME_W - 110.0, GAME_X + GAME_W - 25.0)
            self.stage1_trees.append((lx, y))
            self.stage1_trees.append((rx, y))
            
        # Stage 3: Tropical Palms along beach
        y = 200.0
        while y < STAGE_TRACK_LENGTH - 800.0:
            y += rng.uniform(200.0, 360.0)
            px = rng.uniform(GAME_X + 25.0, GAME_X + 110.0)
            self.stage3_palms.append((px, y))
            
        # Stage 4: Mountain Canyon Pines and Boulders
        y = 200.0
        while y < STAGE_TRACK_LENGTH - 800.0:
            y += rng.uniform(160.0, 290.0)
            lx = rng.uniform(GAME_X + 18.0, GAME_X + 105.0)
            rx = rng.uniform(GAME_X + GAME_W - 105.0, GAME_X + GAME_W - 18.0)
            self.stage4_scenery.append({"pos": (lx, y), "is_pine": rng.random() > 0.45})
            self.stage4_scenery.append({"pos": (rx, y), "is_pine": rng.random() > 0.45})

        # Stage 5: Neon Metropolis Skyscrapers, Street Lamps, and Expressway Gantries
        y = 100.0
        while y < STAGE_TRACK_LENGTH - 400.0:
            bw = rng.uniform(85.0, 115.0)
            bh = rng.uniform(160.0, 280.0)
            lx = GAME_X + rng.uniform(4.0, 18.0)
            rx = (GAME_X + GAME_W) - bw - rng.uniform(4.0, 18.0)
            
            # Precompute window rows x cols
            rows = max(4, int(bh // 26))
            cols = max(3, int(bw // 18))
            win_palette = [
                (0, 225, 255),    # Neon Cyan
                (255, 180, 20),   # Warm Amber
                (245, 248, 255),  # Pure White
                (220, 60, 240),   # Neon Magenta
                (28, 34, 48),     # Unlit
                (28, 34, 48),     # Unlit
                (28, 34, 48)      # Unlit
            ]
            l_wins = [[rng.choice(win_palette) for _ in range(cols)] for _ in range(rows)]
            r_wins = [[rng.choice(win_palette) for _ in range(cols)] for _ in range(rows)]
            
            self.stage5_buildings.append({
                "x": lx, "y": y, "w": bw, "h": bh,
                "col": rng.choice([(18, 22, 34), (24, 28, 44), (14, 18, 30)]),
                "windows": l_wins,
                "beacon": rng.random() > 0.4
            })
            self.stage5_buildings.append({
                "x": rx, "y": y, "w": bw, "h": bh,
                "col": rng.choice([(18, 22, 34), (24, 28, 44), (14, 18, 30)]),
                "windows": r_wins,
                "beacon": rng.random() > 0.4
            })
            y += rng.uniform(220.0, 360.0)
            
        # Street lamps along left and right highway shoulders
        ly = 80.0
        while ly < STAGE_TRACK_LENGTH - 400.0:
            self.stage5_lamps.append(ly)
            ly += 180.0
            
        # Overhead expressway gantries
        gy = 2800.0
        while gy < STAGE_TRACK_LENGTH - 1500.0:
            self.stage5_gantries.append(gy)
            gy += 4500.0

    def get_road_edges(self, stage: int, world_y: float) -> tuple[float, float]:
        """Calculates (left_edge, right_edge) for any track coordinate."""
        normal_left = GAME_X + ROAD_MARGIN
        normal_right = GAME_X + GAME_W - ROAD_MARGIN
        
        if stage == 1 or world_y < 0.0:
            return (normal_left, normal_right)
            
        if stage == 2:
            # Elevated Bridge Bottlenecks
            if world_y >= STAGE_TRACK_LENGTH - 2000.0:
                return (normal_left, normal_right)
                
            seg_len = 2000.0
            seg_idx = int(world_y / seg_len)
            seg_pos = world_y % seg_len
            
            target_left = normal_left
            target_right = normal_right
            
            b_type = abs(seg_idx) % 3
            if b_type == 0:
                target_left = normal_left + 150.0   # Left pinch
            elif b_type == 1:
                target_right = normal_right - 150.0 # Right pinch
            else:
                target_left = normal_left + 100.0   # Center bottleneck
                target_right = normal_right - 100.0
                
            if seg_pos < 550.0:
                return (normal_left, normal_right)
            elif seg_pos < 800.0:
                t = (seg_pos - 550.0) / 250.0
                smooth_t = 0.5 - 0.5 * math.cos(t * math.pi)
                return (
                    normal_left + (target_left - normal_left) * smooth_t,
                    normal_right + (target_right - normal_right) * smooth_t
                )
            elif seg_pos < 1550.0:
                return (target_left, target_right)
            elif seg_pos < 1800.0:
                t = (seg_pos - 1550.0) / 250.0
                smooth_t = 0.5 - 0.5 * math.cos(t * math.pi)
                return (
                    target_left + (normal_left - target_left) * smooth_t,
                    target_right + (normal_right - target_right) * smooth_t
                )
            else:
                return (normal_left, normal_right)
                
        if stage == 3:
            # Coastal Beach Sweeping Curves
            if world_y >= STAGE_TRACK_LENGTH - 2400.0:
                return (normal_left, normal_right)
                
            seg_len = 2400.0
            seg_idx = int(world_y / seg_len)
            seg_pos = world_y % seg_len
            pattern = abs(seg_idx) % 4
            curve_shift = 0.0
            
            if pattern == 0:
                # Sweeping left bend
                if 350.0 <= seg_pos < 850.0:
                    t = (seg_pos - 350.0) / 500.0
                    curve_shift = -95.0 * (0.5 - 0.5 * math.cos(t * math.pi))
                elif 850.0 <= seg_pos < 1550.0:
                    curve_shift = -95.0
                elif 1550.0 <= seg_pos < 2050.0:
                    t = (seg_pos - 1550.0) / 500.0
                    curve_shift = -95.0 * (0.5 + 0.5 * math.cos(t * math.pi))
            elif pattern == 1:
                # Sweeping right ocean bend
                if 350.0 <= seg_pos < 850.0:
                    t = (seg_pos - 350.0) / 500.0
                    curve_shift = 95.0 * (0.5 - 0.5 * math.cos(t * math.pi))
                elif 850.0 <= seg_pos < 1550.0:
                    curve_shift = 95.0
                elif 1550.0 <= seg_pos < 2050.0:
                    t = (seg_pos - 1550.0) / 500.0
                    curve_shift = 95.0 * (0.5 + 0.5 * math.cos(t * math.pi))
            elif pattern == 2:
                # Coastal S-Chicane
                if 300.0 <= seg_pos < 800.0:
                    t = (seg_pos - 300.0) / 500.0
                    curve_shift = -90.0 * (0.5 - 0.5 * math.cos(t * math.pi))
                elif 800.0 <= seg_pos < 1600.0:
                    t = (seg_pos - 800.0) / 800.0
                    curve_shift = -90.0 + 180.0 * (0.5 - 0.5 * math.cos(t * math.pi))
                elif 1600.0 <= seg_pos < 2100.0:
                    t = (seg_pos - 1600.0) / 500.0
                    curve_shift = 90.0 * (0.5 + 0.5 * math.cos(t * math.pi))
            else:
                # Reverse S-Chicane
                if 300.0 <= seg_pos < 800.0:
                    t = (seg_pos - 300.0) / 500.0
                    curve_shift = 90.0 * (0.5 - 0.5 * math.cos(t * math.pi))
                elif 800.0 <= seg_pos < 1600.0:
                    t = (seg_pos - 800.0) / 800.0
                    curve_shift = 90.0 - 180.0 * (0.5 - 0.5 * math.cos(t * math.pi))
                elif 1600.0 <= seg_pos < 2100.0:
                    t = (seg_pos - 1600.0) / 500.0
                    curve_shift = -90.0 * (0.5 + 0.5 * math.cos(t * math.pi))
                    
            return (normal_left + curve_shift, normal_right + curve_shift)
            
        if stage == 4:
            # Mountain Canyon Pass & Technical Bottlenecks
            if world_y >= STAGE_TRACK_LENGTH - 2400.0:
                return (normal_left, normal_right)
                
            seg_len = 2400.0
            seg_idx = int(world_y / seg_len)
            seg_pos = world_y % seg_len
            pattern = abs(seg_idx) % 4
            
            cur_left = normal_left
            cur_right = normal_right
            
            if pattern == 0:
                # Canyon winding S-curves
                shift = 0.0
                if 250.0 <= seg_pos < 750.0:
                    t = (seg_pos - 250.0) / 500.0
                    shift = -110.0 * (0.5 - 0.5 * math.cos(t * math.pi))
                elif 750.0 <= seg_pos < 1550.0:
                    t = (seg_pos - 750.0) / 800.0
                    shift = -110.0 + 220.0 * (0.5 - 0.5 * math.cos(t * math.pi))
                elif 1550.0 <= seg_pos < 2100.0:
                    t = (seg_pos - 1550.0) / 550.0
                    shift = 110.0 * (0.5 + 0.5 * math.cos(t * math.pi))
                cur_left = normal_left + shift
                cur_right = normal_right + shift
            elif pattern == 1:
                # Canyon Gorge Bottleneck (narrows from 640px to 440px)
                pinch = 0.0
                if 350.0 <= seg_pos < 750.0:
                    t = (seg_pos - 350.0) / 400.0
                    pinch = 100.0 * (0.5 - 0.5 * math.cos(t * math.pi))
                elif 750.0 <= seg_pos < 1650.0:
                    pinch = 100.0
                elif 1650.0 <= seg_pos < 2050.0:
                    t = (seg_pos - 1650.0) / 400.0
                    pinch = 100.0 * (0.5 + 0.5 * math.cos(t * math.pi))
                cur_left = normal_left + pinch
                cur_right = normal_right - pinch
            elif pattern == 2:
                # Mountain Hairpin & Cliffside Switchback
                shift = 0.0
                pinch = 0.0
                if 300.0 <= seg_pos < 800.0:
                    t = (seg_pos - 300.0) / 500.0
                    shift = -120.0 * (0.5 - 0.5 * math.cos(t * math.pi))
                    pinch = 40.0 * (0.5 - 0.5 * math.cos(t * math.pi))
                elif 800.0 <= seg_pos < 1550.0:
                    shift = -120.0
                    pinch = 40.0
                elif 1550.0 <= seg_pos < 2100.0:
                    t = (seg_pos - 1550.0) / 550.0
                    shift = -120.0 * (0.5 + 0.5 * math.cos(t * math.pi))
                    pinch = 40.0 * (0.5 + 0.5 * math.cos(t * math.pi))
                cur_left = normal_left + shift + pinch * 0.5
                cur_right = normal_right + shift - pinch * 0.5
            else:
                # Alpine Ridge Bluff Bend
                shift = 0.0
                if 300.0 <= seg_pos < 800.0:
                    t = (seg_pos - 300.0) / 500.0
                    shift = 115.0 * (0.5 - 0.5 * math.cos(t * math.pi))
                elif 800.0 <= seg_pos < 1550.0:
                    t = (seg_pos - 800.0) / 750.0
                    shift = 115.0 - 200.0 * (0.5 - 0.5 * math.cos(t * math.pi))
                elif 1550.0 <= seg_pos < 2100.0:
                    t = (seg_pos - 1550.0) / 550.0
                    shift = -85.0 * (0.5 + 0.5 * math.cos(t * math.pi))
                cur_left = normal_left + shift
                cur_right = normal_right + shift
                
            return (cur_left, cur_right)

        if stage == 5:
            # Neon Metropolis Expressway - High-speed urban sweeps, flyover chicanes, and wide straights
            if world_y >= STAGE_TRACK_LENGTH - 2400.0:
                return (normal_left, normal_right)
                
            seg_len = 2400.0
            seg_idx = int(world_y / seg_len)
            seg_pos = world_y % seg_len
            pattern = abs(seg_idx) % 4
            
            shift = 0.0
            if pattern == 0:
                # Fast sweeping left expressway bend
                if 300.0 <= seg_pos < 850.0:
                    t = (seg_pos - 300.0) / 550.0
                    shift = -100.0 * (0.5 - 0.5 * math.cos(t * math.pi))
                elif 850.0 <= seg_pos < 1550.0:
                    shift = -100.0
                elif 1550.0 <= seg_pos < 2100.0:
                    t = (seg_pos - 1550.0) / 550.0
                    shift = -100.0 * (0.5 + 0.5 * math.cos(t * math.pi))
            elif pattern == 1:
                # Fast sweeping right expressway bend
                if 300.0 <= seg_pos < 850.0:
                    t = (seg_pos - 300.0) / 550.0
                    shift = 100.0 * (0.5 - 0.5 * math.cos(t * math.pi))
                elif 850.0 <= seg_pos < 1550.0:
                    shift = 100.0
                elif 1550.0 <= seg_pos < 2100.0:
                    t = (seg_pos - 1550.0) / 550.0
                    shift = 100.0 * (0.5 + 0.5 * math.cos(t * math.pi))
            elif pattern == 2:
                # Urban elevated flyover chicane (left to right)
                if 250.0 <= seg_pos < 750.0:
                    t = (seg_pos - 250.0) / 500.0
                    shift = -90.0 * (0.5 - 0.5 * math.cos(t * math.pi))
                elif 750.0 <= seg_pos < 1600.0:
                    t = (seg_pos - 750.0) / 850.0
                    shift = -90.0 + 180.0 * (0.5 - 0.5 * math.cos(t * math.pi))
                elif 1600.0 <= seg_pos < 2100.0:
                    t = (seg_pos - 1600.0) / 500.0
                    shift = 90.0 * (0.5 + 0.5 * math.cos(t * math.pi))
            else:
                # High-speed straight with subtle undulating overpass
                if 400.0 <= seg_pos < 900.0:
                    t = (seg_pos - 400.0) / 500.0
                    shift = 50.0 * (0.5 - 0.5 * math.cos(t * math.pi))
                elif 900.0 <= seg_pos < 1500.0:
                    shift = 50.0
                elif 1500.0 <= seg_pos < 2000.0:
                    t = (seg_pos - 1500.0) / 500.0
                    shift = 50.0 * (0.5 + 0.5 * math.cos(t * math.pi))
                    
            return (normal_left + shift, normal_right + shift)
            
        return (normal_left, normal_right)

    def draw_tiled_texture(self, surface, tex, rect):
        """Blit a repeating texture across rect."""
        if not tex:
            return
        tw, th = tex.get_size()
        rx, ry, rw, rh = int(rect[0]), int(rect[1]), int(rect[2]), int(rect[3])
        # Simple sub-surface or clipped tiling
        surface.set_clip(pygame.Rect(rx, ry, rw, rh))
        for x in range(rx, rx + rw, tw):
            for y in range(ry, ry + rh, th):
                surface.blit(tex, (x, y))
        surface.set_clip(None)

    def render(self, surface: pygame.Surface, stage: int, track_dist: float):
        self.frames += 1
        self.current_stage = stage
        self.track_distance = track_dist
        
        if stage == 1:
            self._render_stage1(surface)
        elif stage == 2:
            self._render_stage2(surface)
        elif stage == 3:
            self._render_stage3(surface)
        elif stage == 4:
            self._render_stage4(surface)
        else:
            self._render_stage5(surface)
            
        self._render_finish_line(surface)

    def _render_stage1(self, surface: pygame.Surface):
        # Grass verges on left & right
        self.draw_tiled_texture(surface, self.tex_grass, (GAME_X, 0, ROAD_MARGIN, SCREEN_HEIGHT))
        self.draw_tiled_texture(surface, self.tex_grass, (GAME_X + GAME_W - ROAD_MARGIN, 0, ROAD_MARGIN, SCREEN_HEIGHT))
        
        # Asphalt
        road_left = GAME_X + ROAD_MARGIN
        road_w = GAME_W - (ROAD_MARGIN * 2.0)
        self.draw_tiled_texture(surface, self.tex_asphalt, (road_left, 0, road_w, SCREEN_HEIGHT))
        
        # Lane Markings & Curbs
        lane_w = road_w / 4.0
        slice_h = 6
        for y in range(0, SCREEN_HEIGHT, slice_h):
            dash_y = (y + int(self.track_distance)) % 60
            if dash_y < 30:
                # White lane dividers
                pygame.draw.rect(surface, (240, 240, 240), (road_left + lane_w - 1.5, y, 3, slice_h))
                pygame.draw.rect(surface, (240, 240, 240), (road_left + lane_w * 3.0 - 1.5, y, 3, slice_h))
                # Yellow center divider
                pygame.draw.rect(surface, (255, 215, 30), (road_left + lane_w * 2.0 - 2.0, y, 4, slice_h))
                
            # Curbs
            is_red = ((int(y + self.track_distance) // 16) % 2 == 0)
            curb_col = COLOR_BARRIER_RED if is_red else COLOR_WHITE
            pygame.draw.rect(surface, curb_col, (road_left - 8, y, 8, slice_h))
            pygame.draw.rect(surface, curb_col, (road_left + road_w, y, 8, slice_h))
            
        # Trees
        for tx, ty in self.stage1_trees:
            scr_y = PLAYER_SCREEN_Y - (ty - self.track_distance)
            if -120 <= scr_y <= SCREEN_HEIGHT + 120 and self.tex_tree:
                surface.blit(pygame.transform.scale(self.tex_tree, (72, 90)), (tx - 36, scr_y - 90))

    def _render_stage2(self, surface: pygame.Surface):
        slice_h = 6
        wave_time = self.frames * 0.04
        
        # Deep Ocean base
        pygame.draw.rect(surface, COLOR_WATER_DEEP, (GAME_X, 0, GAME_W, SCREEN_HEIGHT))
        self.draw_tiled_texture(surface, self.tex_water, (GAME_X, 0, GAME_W, SCREEN_HEIGHT))
        
        for y in range(0, SCREEN_HEIGHT, slice_h):
            world_y = self.track_distance + (PLAYER_SCREEN_Y - y)
            r_left, r_right = self.get_road_edges(2, world_y)
            r_w = r_right - r_left
            
            deck_l = r_left - 24.0
            deck_r = r_right + 24.0
            shadow_l = deck_l - 14.0
            shadow_r = deck_r + 14.0
            
            # Waves swells
            wave_band = int(y * 0.45 + self.track_distance * 0.2 + math.sin(wave_time + y * 0.02) * 10.0) % 40
            if wave_band < 12:
                if shadow_l > GAME_X + 4.0:
                    pygame.draw.rect(surface, COLOR_WATER_MID, (GAME_X, y, shadow_l - GAME_X, slice_h))
                if GAME_X + GAME_W > shadow_r:
                    pygame.draw.rect(surface, COLOR_WATER_MID, (shadow_r, y, (GAME_X + GAME_W) - shadow_r, slice_h))
            elif wave_band < 18:
                if shadow_l > GAME_X + 8.0:
                    pygame.draw.rect(surface, COLOR_WATER_SWELL, (GAME_X + 2, y, shadow_l - GAME_X - 2, slice_h))
                if (GAME_X + GAME_W) - shadow_r > 8.0:
                    pygame.draw.rect(surface, COLOR_WATER_SWELL, (shadow_r + 2, y, (GAME_X + GAME_W) - shadow_r - 4, slice_h))
                    
            # Bridge Pylons
            pylon_cycle = int(world_y) % 400
            if pylon_cycle < 36:
                pygame.draw.rect(surface, (130, 135, 140), (deck_l - 28, y, 22, slice_h))
                pygame.draw.rect(surface, (130, 135, 140), (deck_r + 6, y, 22, slice_h))
                pygame.draw.rect(surface, (175, 180, 185), (deck_l - 28, y, 5, slice_h))
                pygame.draw.rect(surface, (175, 180, 185), (deck_r + 6, y, 5, slice_h))
                
            # Bridge Shadow & Catwalks
            if deck_l > GAME_X + 14.0:
                pygame.draw.rect(surface, COLOR_BRIDGE_SHADOW, (deck_l - 14, y, 14, slice_h))
            if (GAME_X + GAME_W) >= deck_r + 14.0:
                pygame.draw.rect(surface, COLOR_BRIDGE_SHADOW, (deck_r, y, 14, slice_h))
                
            pygame.draw.rect(surface, (145, 150, 155), (deck_l, y, 16, slice_h))
            pygame.draw.rect(surface, (145, 150, 155), (deck_r - 16, y, 16, slice_h))
            
            # Railing
            pygame.draw.rect(surface, COLOR_RAILING, (deck_l, y, 3, slice_h))
            pygame.draw.rect(surface, COLOR_RAILING, (deck_r - 3, y, 3, slice_h))
            
            # Asphalt
            pygame.draw.rect(surface, (61, 64, 69), (r_left, y, r_w, slice_h))
            
            # Dashed lanes
            lane_w = r_w / 4.0
            dash_cycle = (int(y + self.track_distance)) % 60
            if dash_cycle < 30:
                pygame.draw.rect(surface, (240, 240, 240), (r_left + lane_w - 1.5, y, 3, slice_h))
                pygame.draw.rect(surface, (240, 240, 240), (r_left + lane_w * 3.0 - 1.5, y, 3, slice_h))
                pygame.draw.rect(surface, (255, 215, 30), (r_left + lane_w * 2.0 - 2.0, y, 4, slice_h))
                
            # Curbs
            is_red = ((int(y + self.track_distance) // 16) % 2 == 0)
            curb_col = COLOR_BARRIER_RED if is_red else COLOR_WHITE
            pygame.draw.rect(surface, curb_col, (r_left - 8, y, 8, slice_h))
            pygame.draw.rect(surface, curb_col, (r_right, y, 8, slice_h))

    def _render_stage3(self, surface: pygame.Surface):
        slice_h = 6
        wave_time = self.frames * 0.04
        
        # Base Sand background
        self.draw_tiled_texture(surface, self.tex_sand, (GAME_X, 0, GAME_W, SCREEN_HEIGHT))
        
        # Ocean Backdrop on right half
        ocean_base_x = GAME_X + GAME_W * 0.42
        ocean_base_w = GAME_W * 0.58
        pygame.draw.rect(surface, COLOR_WATER_DEEP, (ocean_base_x, 0, ocean_base_w, SCREEN_HEIGHT))
        self.draw_tiled_texture(surface, self.tex_water, (ocean_base_x, 0, ocean_base_w, SCREEN_HEIGHT))
        
        for y in range(0, SCREEN_HEIGHT, slice_h):
            world_y = self.track_distance + (PLAYER_SCREEN_Y - y)
            r_left, r_right = self.get_road_edges(3, world_y)
            r_w = r_right - r_left
            
            # Left Sand Verge
            sand_l_w = r_left - GAME_X
            if sand_l_w > 0:
                pygame.draw.rect(surface, (235, 214, 158), (GAME_X, y, sand_l_w, slice_h))
                
            # Right Shoreline & Waves
            dry_sand_edge = r_right + 8.0
            wave_surge = math.sin(wave_time * 1.6 + world_y * 0.014) * 16.0 + math.cos(wave_time * 0.7 + y * 0.03) * 7.0
            max_wash_reach = r_right + 18.0
            water_edge_x = max(max_wash_reach, min(GAME_X + GAME_W - 50.0, r_right + 42.0 - wave_surge))
            
            if water_edge_x > dry_sand_edge:
                pygame.draw.rect(surface, (235, 212, 153), (dry_sand_edge, y, water_edge_x - dry_sand_edge, slice_h))
                
            # Wet Sand Zone
            if water_edge_x > max_wash_reach:
                wet_w = min(water_edge_x - max_wash_reach, 24.0)
                pygame.draw.rect(surface, (168, 140, 97), (water_edge_x - wet_w, y, wet_w, slice_h))
                
            # Multi-depth ocean
            ocean_w = (GAME_X + GAME_W) - water_edge_x
            if ocean_w > 0:
                # Turquoise shallows
                shallow_w = min(ocean_w, 65.0)
                pygame.draw.rect(surface, (20, 158, 184), (water_edge_x, y, shallow_w, slice_h))
                
                # Mid-depth azure
                if ocean_w > 65.0:
                    mid_w = min(ocean_w - 65.0, 125.0)
                    pygame.draw.rect(surface, (10, 97, 148), (water_edge_x + 65.0, y, mid_w, slice_h))
                    
                # Deep ocean
                if ocean_w > 190.0:
                    deep_w = ocean_w - 190.0
                    pygame.draw.rect(surface, COLOR_WATER_DEEP, (water_edge_x + 190.0, y, deep_w, slice_h))
                    
                # Swell 1
                swell1_x = water_edge_x + 75.0 + math.sin(wave_time * 1.8 + world_y * 0.02) * 22.0
                if swell1_x < (GAME_X + GAME_W) - 15.0:
                    pygame.draw.rect(surface, (46, 184, 209), (swell1_x, y, 22, slice_h))
                    pygame.draw.rect(surface, (224, 245, 255), (swell1_x + 1, y, 4, slice_h))
                    
                # Breaking surf foam
                foam_w = 9.0 + math.sin(wave_time * 2.8 + world_y * 0.04) * 4.0
                pygame.draw.rect(surface, (245, 252, 255), (water_edge_x - 2, y, foam_w, slice_h))
                
            # Asphalt
            pygame.draw.rect(surface, (61, 64, 69), (r_left, y, r_w, slice_h))
            
            # Dashed lanes
            lane_w = r_w / 4.0
            dash_cycle = (int(y + self.track_distance)) % 60
            if dash_cycle < 30:
                pygame.draw.rect(surface, (240, 240, 240), (r_left + lane_w - 1.5, y, 3, slice_h))
                pygame.draw.rect(surface, (240, 240, 240), (r_left + lane_w * 3.0 - 1.5, y, 3, slice_h))
                pygame.draw.rect(surface, (255, 215, 30), (r_left + lane_w * 2.0 - 2.0, y, 4, slice_h))
                
            # Curbs
            is_red = ((int(y + self.track_distance) // 16) % 2 == 0)
            curb_col = COLOR_BARRIER_RED if is_red else COLOR_WHITE
            pygame.draw.rect(surface, curb_col, (r_left - 8, y, 8, slice_h))
            pygame.draw.rect(surface, curb_col, (r_right, y, 8, slice_h))
            
        # Palm Trees
        for px, py in self.stage3_palms:
            scr_y = PLAYER_SCREEN_Y - (py - self.track_distance)
            if -120 <= scr_y <= SCREEN_HEIGHT + 120 and self.tex_palm_tree:
                surface.blit(pygame.transform.scale(self.tex_palm_tree, (72, 90)), (px - 36, scr_y - 90))

    def _render_stage4(self, surface: pygame.Surface):
        # Base rocky ground on shoulders
        self.draw_tiled_texture(surface, self.tex_rock_ground, (GAME_X, 0, ROAD_MARGIN + 30.0, SCREEN_HEIGHT))
        self.draw_tiled_texture(surface, self.tex_rock_ground, (GAME_X + GAME_W - ROAD_MARGIN - 30.0, 0, ROAD_MARGIN + 30.0, SCREEN_HEIGHT))
        
        slice_h = 6
        for y in range(0, SCREEN_HEIGHT, slice_h):
            world_y = self.track_distance + (PLAYER_SCREEN_Y - y)
            r_left, r_right = self.get_road_edges(4, world_y)
            r_w = r_right - r_left
            
            # Cliff Rock Walls on boundaries
            cliff_l = r_left - 24.0
            if cliff_l > GAME_X:
                pygame.draw.rect(surface, (46, 41, 38), (GAME_X, y, 40, slice_h))
                pygame.draw.rect(surface, (71, 64, 56), (GAME_X + 40, y, cliff_l - (GAME_X + 40), slice_h))
                if int(world_y * 0.1) % 14 < 3:
                    pygame.draw.rect(surface, (122, 112, 97), (GAME_X + 15, y, 18, slice_h))
                    
            cliff_r = r_right + 24.0
            if cliff_r < GAME_X + GAME_W:
                pygame.draw.rect(surface, (71, 64, 56), (cliff_r, y, (GAME_X + GAME_W - 40) - cliff_r, slice_h))
                pygame.draw.rect(surface, (46, 41, 38), (GAME_X + GAME_W - 40, y, 40, slice_h))
                if int(world_y * 0.1) % 14 < 3:
                    pygame.draw.rect(surface, (122, 112, 97), (GAME_X + GAME_W - 33, y, 18, slice_h))
                    
            # Gravel shoulders
            pygame.draw.rect(surface, (56, 51, 46), (r_left - 24, y, 16, slice_h))
            pygame.draw.rect(surface, (56, 51, 46), (r_right + 8, y, 16, slice_h))
            
            # Asphalt
            pygame.draw.rect(surface, (56, 56, 61), (r_left, y, r_w, slice_h))
            
            # Lane markings & Bottlenecks
            dash_cycle = (int(y + self.track_distance)) % 60
            if r_w < 520.0:
                # Narrow gorge bottleneck: 2-lane layout with yellow center line
                half_w = r_w * 0.5
                if dash_cycle < 30:
                    pygame.draw.rect(surface, (255, 215, 30), (r_left + half_w - 2.0, y, 4, slice_h))
                # Hazard stripes on shoulders
                if (int(world_y * 0.05) % 8) < 4:
                    pygame.draw.rect(surface, (255, 178, 25), (r_left - 18, y, 8, slice_h))
                    pygame.draw.rect(surface, (255, 178, 25), (r_right + 10, y, 8, slice_h))
            else:
                lane_w = r_w / 4.0
                if dash_cycle < 30:
                    pygame.draw.rect(surface, (235, 235, 235), (r_left + lane_w - 1.5, y, 3, slice_h))
                    pygame.draw.rect(surface, (235, 235, 235), (r_left + lane_w * 3.0 - 1.5, y, 3, slice_h))
                    pygame.draw.rect(surface, (255, 215, 30), (r_left + lane_w * 2.0 - 2.0, y, 4, slice_h))
                    
            # Curbs
            is_red = ((int(y + self.track_distance) // 16) % 2 == 0)
            curb_col = COLOR_BARRIER_RED if is_red else COLOR_WHITE
            pygame.draw.rect(surface, curb_col, (r_left - 8, y, 8, slice_h))
            pygame.draw.rect(surface, curb_col, (r_right, y, 8, slice_h))
            
            # Barrier posts
            if int(world_y) % 80 < 10:
                pygame.draw.rect(surface, (191, 199, 209), (r_left - 11, y, 3, slice_h))
                pygame.draw.rect(surface, (191, 199, 209), (r_right + 8, y, 3, slice_h))
                
        # Scenery: Pines & Boulders
        for item in self.stage4_scenery:
            px, py = item["pos"]
            is_pine = item["is_pine"]
            scr_y = PLAYER_SCREEN_Y - (py - self.track_distance)
            if -100 <= scr_y <= SCREEN_HEIGHT + 100:
                if is_pine and self.tex_pine_tree:
                    surface.blit(pygame.transform.scale(self.tex_pine_tree, (48, 64)), (px - 24, scr_y - 64))
                elif not is_pine and self.tex_boulder:
                    surface.blit(pygame.transform.scale(self.tex_boulder, (48, 36)), (px - 24, scr_y - 36))

    def _render_stage5(self, surface: pygame.Surface):
        # 1. Midnight / Twilight Night Sky Base
        pygame.draw.rect(surface, (10, 14, 24), (GAME_X, 0, GAME_W, SCREEN_HEIGHT))
        
        # 2. Elevated Expressway Concrete Deck on Verges
        self.draw_tiled_texture(surface, self.tex_concrete, (GAME_X, 0, ROAD_MARGIN, SCREEN_HEIGHT))
        self.draw_tiled_texture(surface, self.tex_concrete, (GAME_X + GAME_W - ROAD_MARGIN, 0, ROAD_MARGIN, SCREEN_HEIGHT))
        
        # Nighttime atmospheric shading on concrete
        night_shading = pygame.Surface((int(ROAD_MARGIN), SCREEN_HEIGHT), pygame.SRCALPHA)
        night_shading.fill((10, 14, 26, 185))
        surface.blit(night_shading, (GAME_X, 0))
        surface.blit(night_shading, (GAME_X + GAME_W - ROAD_MARGIN, 0))
        
        # 3. Skyscraper Silhouettes in Background Verges
        for b in self.stage5_buildings:
            bx, by, bw, bh = b["x"], b["y"], b["w"], b["h"]
            scr_y = PLAYER_SCREEN_Y - (by - self.track_distance)
            if -bh <= scr_y <= SCREEN_HEIGHT + 50:
                # Building facade
                b_rect = pygame.Rect(int(bx), int(scr_y), int(bw), int(bh))
                pygame.draw.rect(surface, b["col"], b_rect)
                pygame.draw.rect(surface, (12, 16, 26), b_rect, 1)
                
                # Rooftop beacon light
                if b["beacon"]:
                    is_blink = (int(self.frames // 18) % 2 == 0)
                    if is_blink:
                        pygame.draw.circle(surface, (255, 40, 40), (int(bx + bw * 0.5), int(scr_y - 2)), 3)
                        pygame.draw.circle(surface, (255, 140, 140), (int(bx + bw * 0.5), int(scr_y - 2)), 1)
                        
                # Window grid
                wins = b["windows"]
                for r_idx, row in enumerate(wins):
                    wy = scr_y + 16 + r_idx * 18
                    if 0 <= wy <= SCREEN_HEIGHT:
                        for c_idx, w_col in enumerate(row):
                            wx = bx + 8 + c_idx * 14
                            pygame.draw.rect(surface, w_col, (int(wx), int(wy), 8, 10))

        # 4. Slices: Roadway, Asphalt, Neon Curbs, and Reflective Markings
        slice_h = 6
        for y in range(0, SCREEN_HEIGHT, slice_h):
            world_y = self.track_distance + (PLAYER_SCREEN_Y - y)
            r_left, r_right = self.get_road_edges(5, world_y)
            r_w = r_right - r_left
            
            # Outer Elevated Railing Barrier
            guard_l = r_left - 18.0
            guard_r = r_right + 18.0
            pygame.draw.rect(surface, (25, 30, 42), (guard_l, y, 18, slice_h))
            pygame.draw.rect(surface, (25, 30, 42), (r_right, y, 18, slice_h))
            
            # Sleek Dark Midnight Asphalt
            pygame.draw.rect(surface, (36, 38, 44), (r_left, y, r_w, slice_h))
            
            # Dashed Lane Dividers (Bright Cool White)
            lane_w = r_w / 4.0
            dash_cycle = (int(y + self.track_distance)) % 60
            if dash_cycle < 30:
                pygame.draw.rect(surface, (235, 245, 255), (r_left + lane_w - 1.5, y, 3, slice_h))
                pygame.draw.rect(surface, (235, 245, 255), (r_left + lane_w * 3.0 - 1.5, y, 3, slice_h))
                # Double Amber Center Line
                pygame.draw.rect(surface, (255, 195, 25), (r_left + lane_w * 2.0 - 3.0, y, 2, slice_h))
                pygame.draw.rect(surface, (255, 195, 25), (r_left + lane_w * 2.0 + 1.0, y, 2, slice_h))
                
            # Neon Curbs (Alternating Electric Cyan & Vivid Amber)
            curb_cycle = (int(y + self.track_distance) // 20) % 2
            curb_col = COLOR_NEON_CYAN if curb_cycle == 0 else COLOR_NEON_AMBER
            pygame.draw.rect(surface, curb_col, (r_left - 8, y, 8, slice_h))
            pygame.draw.rect(surface, curb_col, (r_right, y, 8, slice_h))
            
            # Glowing Cat's-Eye Reflectors along Barriers every 50m
            if int(world_y) % 50 < 6:
                pygame.draw.rect(surface, (0, 240, 255), (r_left - 14, y + 1, 4, 4))
                pygame.draw.rect(surface, (0, 240, 255), (r_right + 10, y + 1, 4, 4))

        # 5. Street Light Lamp Posts along Highway Shoulders
        for ly in self.stage5_lamps:
            scr_y = PLAYER_SCREEN_Y - (ly - self.track_distance)
            if -80 <= scr_y <= SCREEN_HEIGHT + 80:
                r_l, r_r = self.get_road_edges(5, ly)
                
                # Left Lamp Post
                lp_lx = r_l - 22.0
                pygame.draw.rect(surface, (140, 150, 165), (lp_lx, scr_y - 45, 4, 45))
                pygame.draw.rect(surface, (170, 180, 195), (lp_lx, scr_y - 45, 16, 4)) # Arm pointing right
                pygame.draw.rect(surface, (255, 250, 210), (lp_lx + 12, scr_y - 43, 6, 5)) # Lamp head
                # Translucent light glow
                pygame.draw.circle(surface, (255, 245, 180), (int(lp_lx + 15), int(scr_y - 40)), 7)
                
                # Right Lamp Post
                lp_rx = r_r + 22.0
                pygame.draw.rect(surface, (140, 150, 165), (lp_rx - 4, scr_y - 45, 4, 45))
                pygame.draw.rect(surface, (170, 180, 195), (lp_rx - 16, scr_y - 45, 16, 4)) # Arm pointing left
                pygame.draw.rect(surface, (255, 250, 210), (lp_rx - 18, scr_y - 43, 6, 5)) # Lamp head
                # Translucent light glow
                pygame.draw.circle(surface, (255, 245, 180), (int(lp_rx - 15), int(scr_y - 40)), 7)

        # 6. Overhead Expressway Gantries
        for gy in self.stage5_gantries:
            scr_y = PLAYER_SCREEN_Y - (gy - self.track_distance)
            if -80 <= scr_y <= SCREEN_HEIGHT + 80:
                r_l, r_r = self.get_road_edges(5, gy)
                gw = (r_r - r_l) + 50.0
                gx = r_l - 25.0
                
                # Steel Truss Arch
                pygame.draw.rect(surface, (85, 95, 110), (gx, scr_y - 65, gw, 10))
                pygame.draw.rect(surface, (110, 120, 135), (gx, scr_y - 65, gw, 2))
                # Pillars
                pygame.draw.rect(surface, (70, 80, 95), (gx, scr_y - 65, 8, 65))
                pygame.draw.rect(surface, (70, 80, 95), (gx + gw - 8, scr_y - 65, 8, 65))
                
                # Highway Directional Signs (Japanese Green Highway Signs)
                sign_w = gw * 0.42
                sign_h = 32
                s1_x = gx + 20
                s2_x = gx + gw - sign_w - 20
                for sx, txt_code in [(s1_x, "C1 首都高 // SHUTO"), (s2_x, "湾岸線 // WANGAN")]:
                    pygame.draw.rect(surface, (16, 120, 68), (sx, scr_y - 60, sign_w, sign_h), border_radius=3)
                    pygame.draw.rect(surface, (240, 245, 250), (sx, scr_y - 60, sign_w, sign_h), 1, border_radius=3)
                    if hasattr(self, 'font_gantry') and self.font_gantry:
                        ts = self.font_gantry.render(txt_code, True, (255, 255, 255))
                        surface.blit(ts, ts.get_rect(center=(int(sx + sign_w * 0.5), int(scr_y - 44))))

    def _render_finish_line(self, surface: pygame.Surface):
        remaining = STAGE_TRACK_LENGTH - self.track_distance
        finish_y = PLAYER_SCREEN_Y - remaining
        if -80.0 <= finish_y <= SCREEN_HEIGHT + 80.0:
            r_left, r_right = self.get_road_edges(self.current_stage, STAGE_TRACK_LENGTH)
            r_w = r_right - r_left
            
            # Checkered Banner
            if self.tex_finish_banner:
                surface.blit(pygame.transform.scale(self.tex_finish_banner, (int(r_w), 40)), (r_left, finish_y - 20))
                
            # Goal Posts
            post_l = r_left - 18.0
            post_r = r_right + 2.0
            for side_x in [post_l, post_r]:
                for pr in range(4):
                    col = (230, 38, 38) if pr % 2 == 0 else (242, 242, 242)
                    pygame.draw.rect(surface, col, (side_x, finish_y - 16 + pr * 12, 16, 12))
                    pygame.draw.rect(surface, (0, 0, 0), (side_x, finish_y - 16 + pr * 12, 16, 12), 1)
