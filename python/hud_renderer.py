"""
hud_renderer.py
Renders the Left GPS Radar, Right Command Deck, NES Title Screen, Volume Menu, and Game Overlays.
"""

import math
import time
import pygame
from game_config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TOTAL_STAGES, STAGE_NAMES, STAGE_ENV_NOTES,
    COLOR_PANEL_BG, COLOR_PANEL_BORDER, COLOR_GOLD, COLOR_CYAN, COLOR_WHITE,
    get_asset_path
)

class HudRenderer:
    def __init__(self, font_latin: pygame.font.Font, font_cjk: pygame.font.Font):
        self.font_latin = font_latin
        self.font_cjk = font_cjk
        
        # Load carbon texture
        self.tex_carbon = None
        c_path = get_asset_path("textures/carbon.png")
        try:
            raw = pygame.image.load(c_path).convert_alpha()
            self.tex_carbon = raw
        except Exception as e:
            print(f"Warning: Failed to load carbon texture: {e}")

        # Scaled fonts
        self.font_title = pygame.font.Font(get_asset_path("fonts/DejaVuSans-Bold.ttf"), 54)
        self.font_kana_title = pygame.font.Font(get_asset_path("fonts/NotoSansCJK-Bold.ttc"), 32)
        self.font_menu = pygame.font.Font(get_asset_path("fonts/DejaVuSans-Bold.ttf"), 28)
        self.font_large_kana = pygame.font.Font(get_asset_path("fonts/NotoSansCJK-Bold.ttc"), 88)
        self.font_speed = pygame.font.Font(get_asset_path("fonts/DejaVuSans-Bold.ttf"), 48)
        self.font_sub = pygame.font.Font(get_asset_path("fonts/DejaVuSans-Bold.ttf"), 15)
        self.font_tiny = pygame.font.Font(get_asset_path("fonts/DejaVuSans-Bold.ttf"), 11)

    def draw_tiled_carbon(self, surface: pygame.Surface, rect: tuple[int, int, int, int]):
        rx, ry, rw, rh = rect
        if self.tex_carbon:
            tw, th = self.tex_carbon.get_size()
            surface.set_clip(pygame.Rect(rx, ry, rw, rh))
            for x in range(rx, rx + rw, tw):
                for y in range(ry, ry + rh, th):
                    surface.blit(self.tex_carbon, (x, y))
            surface.set_clip(None)
        else:
            pygame.draw.rect(surface, COLOR_PANEL_BG, (rx, ry, rw, rh))

    def render_left_panel(self, surface: pygame.Surface, stage: int, track_dist: float, max_dist: float):
        # 0 to 280 px
        self.draw_tiled_carbon(surface, (0, 0, 280, SCREEN_HEIGHT))
        pygame.draw.line(surface, COLOR_PANEL_BORDER, (280, 0), (280, SCREEN_HEIGHT), 2)
        
        # Stage Header
        st_rect = pygame.Rect(16, 16, 248, 85)
        pygame.draw.rect(surface, (10, 20, 36), st_rect, border_radius=6)
        pygame.draw.rect(surface, COLOR_GOLD, st_rect, 2, border_radius=6)
        
        txt_st = self.font_menu.render(f"STAGE 0{stage}", True, COLOR_GOLD)
        surface.blit(txt_st, (28, 24))
        
        st_name = STAGE_NAMES.get(stage, "HIGHWAY")
        txt_name = self.font_sub.render(st_name, True, COLOR_CYAN)
        surface.blit(txt_name, (28, 52))
        
        txt_tele = self.font_tiny.render("GPS TRACK TELEMETRY", True, (150, 180, 210))
        surface.blit(txt_tele, (28, 74))
        
        # Vertical Mini-Map Track
        track_x = 140
        track_top = 148
        track_bot = 840
        track_len = track_bot - track_top
        
        # Goal Badge
        goal_rect = pygame.Rect(95, track_top - 24, 90, 20)
        pygame.draw.rect(surface, (10, 20, 36), goal_rect, border_radius=4)
        pygame.draw.rect(surface, COLOR_GOLD, goal_rect, 1, border_radius=4)
        txt_goal = self.font_sub.render("★ GOAL ★", True, COLOR_GOLD)
        surface.blit(txt_goal, (104, track_top - 22))
        
        # Center line
        pygame.draw.line(surface, (75, 100, 130), (track_x, track_top), (track_x, track_bot), 3)
        
        # Milestone markers (25%, 50%, 75%)
        for q in [0.25, 0.5, 0.75]:
            qy = int(track_bot - (track_len * q))
            pygame.draw.line(surface, COLOR_CYAN, (track_x - 16, qy), (track_x + 16, qy), 2)
            txt_q = self.font_tiny.render(f"{int(q * 100)}%", True, (160, 190, 220))
            surface.blit(txt_q, (32, qy - 12))
            q_dist = int((max_dist * (1.0 - q)) * 0.1)
            txt_qd = self.font_tiny.render(f"{q_dist}m", True, (110, 140, 170))
            surface.blit(txt_qd, (32, qy + 2))
            
        # Start Badge
        start_rect = pygame.Rect(105, track_bot + 6, 70, 20)
        pygame.draw.rect(surface, (10, 20, 36), start_rect, border_radius=4)
        pygame.draw.rect(surface, COLOR_CYAN, start_rect, 1, border_radius=4)
        txt_start = self.font_tiny.render("START", True, COLOR_CYAN)
        surface.blit(txt_start, (116, track_bot + 9))
        
        # Player Cursor (Sports car beacon)
        progress = max(0.0, min(1.0, track_dist / max_dist))
        cur_y = int(track_bot - (track_len * progress))
        # Beacon pulse ring
        pygame.draw.rect(surface, (0, 200, 255), (track_x - 12, cur_y - 12, 24, 24), 1, border_radius=3)
        # Car icon
        pygame.draw.rect(surface, (220, 35, 35), (track_x - 7, cur_y - 9, 14, 18), border_radius=3)
        pygame.draw.rect(surface, (255, 255, 255), (track_x - 4, cur_y - 6, 8, 8), border_radius=2)
        # 'YOU' label
        you_rect = pygame.Rect(track_x + 16, cur_y - 8, 38, 16)
        pygame.draw.rect(surface, COLOR_GOLD, you_rect, border_radius=3)
        txt_you = self.font_tiny.render("YOU", True, (0, 0, 0))
        surface.blit(txt_you, (track_x + 23, cur_y - 6))

        # Dedicated Bottom Distance Telemetry Card (Occupies y: 885 to 1060)
        card_x = 16
        card_y = 885
        card_w = 248
        card_h = 175
        card_rect = pygame.Rect(card_x, card_y, card_w, card_h)
        pygame.draw.rect(surface, (8, 16, 28), card_rect, border_radius=8)
        pygame.draw.rect(surface, COLOR_PANEL_BORDER, card_rect, 2, border_radius=8)

        txt_dh = self.font_tiny.render("REMAINING DISTANCE", True, (150, 185, 220))
        surface.blit(txt_dh, txt_dh.get_rect(center=(card_x + card_w // 2, card_y + 20)))

        remaining_m = int(max(0.0, (max_dist - track_dist) * 0.1))
        txt_m = self.font_speed.render(f"{remaining_m:,} M", True, COLOR_GOLD)
        surface.blit(txt_m, txt_m.get_rect(center=(card_x + card_w // 2, card_y + 60)))

        pct_val = int(round(progress * 100))
        txt_pct = self.font_sub.render(f"{pct_val}% COMPLETED", True, COLOR_CYAN)
        surface.blit(txt_pct, txt_pct.get_rect(center=(card_x + card_w // 2, card_y + 105)))

        # Progress bar
        bar_bx = card_x + 18
        bar_by = card_y + 135
        bar_bw = card_w - 36
        bar_bh = 18
        pygame.draw.rect(surface, (16, 26, 42), (bar_bx, bar_by, bar_bw, bar_bh), border_radius=4)
        p_fill = int(bar_bw * progress)
        if p_fill > 0:
            pygame.draw.rect(surface, (0, 217, 255), (bar_bx, bar_by, p_fill, bar_bh), border_radius=4)
        pygame.draw.rect(surface, (60, 90, 130), (bar_bx, bar_by, bar_bw, bar_bh), 1, border_radius=4)

    def render_right_panel(self, surface: pygame.Surface, stage: int, target_kana: str, target_romaji: str,
                           speed_kmh: float, is_turbo: bool, is_braking: bool, fuel: float, score: float, match_timer: float):
        # 1240 to 1920 px (width 680)
        self.draw_tiled_carbon(surface, (1240, 0, 680, SCREEN_HEIGHT))
        pygame.draw.line(surface, COLOR_PANEL_BORDER, (1240, 0), (1240, SCREEN_HEIGHT), 2)
        
        rx = 1260
        rw = 640
        
        # 1. Target Kana Holographic Chamber
        box_y = 20
        box_h = 240
        chamber_rect = pygame.Rect(rx, box_y, rw, box_h)
        pygame.draw.rect(surface, (8, 16, 28), chamber_rect)
        border_col = COLOR_GOLD if match_timer > 0.0 else COLOR_CYAN
        pygame.draw.rect(surface, border_col, chamber_rect, 2)
        
        # Header text
        txt_tgt_h = self.font_sub.render("TARGET KANA INTERCEPT TARGET", True, COLOR_CYAN)
        surface.blit(txt_tgt_h, (rx + 20, box_y + 12))
        
        # Huge Kana character
        if self.font_large_kana and target_kana:
            k_surf = self.font_large_kana.render(target_kana, True, COLOR_GOLD if match_timer > 0.0 else COLOR_WHITE)
            kr = k_surf.get_rect(center=(rx + rw // 2, box_y + 105))
            surface.blit(k_surf, kr)
            
        # Romaji pronunciation guide (high-contrast pill plate)
        ro_box = pygame.Rect(rx + rw // 2 - 100, box_y + 166, 200, 40)
        pygame.draw.rect(surface, (12, 22, 38), ro_box, border_radius=6)
        pygame.draw.rect(surface, COLOR_CYAN, ro_box, 2, border_radius=6)
        txt_ro = self.font_menu.render(f"[ {target_romaji.upper()} ]", True, COLOR_GOLD)
        surface.blit(txt_ro, txt_ro.get_rect(center=ro_box.center))
        
        # Subtitle instruction
        txt_sub = self.font_tiny.render("MATCH TRAFFIC ROOF ROMAJI TO REFUEL +30%", True, (160, 190, 220))
        sub_r = txt_sub.get_rect(center=(rx + rw // 2, box_y + 218))
        surface.blit(txt_sub, sub_r)
        
        # 2. Speedometer
        spd_y = 280
        spd_rect = pygame.Rect(rx, spd_y, rw, 150)
        pygame.draw.rect(surface, (8, 16, 28), spd_rect)
        pygame.draw.rect(surface, COLOR_PANEL_BORDER, spd_rect, 1)
        
        txt_spd_h = self.font_sub.render("VELOCITY TELEMETRY", True, (160, 190, 220))
        surface.blit(txt_spd_h, (rx + 20, spd_y + 12))
        
        # Speed readout
        s_val = int(speed_kmh)
        txt_s_val = self.font_speed.render(f"{s_val:03d}", True, COLOR_GOLD if is_turbo else COLOR_WHITE)
        surface.blit(txt_s_val, (rx + 24, spd_y + 40))
        txt_unit = self.font_menu.render("KM/H", True, COLOR_CYAN)
        surface.blit(txt_unit, (rx + 140, spd_y + 55))
        
        # State Badge
        if is_braking:
            badge_text = "BRAKING"
            badge_col = (255, 60, 60)
        elif is_turbo:
            badge_text = "TURBO BOOST"
            badge_col = COLOR_GOLD
        else:
            badge_text = "CRUISE DRIVE"
            badge_col = COLOR_CYAN
            
        txt_badge = self.font_sub.render(badge_text, True, badge_col)
        surface.blit(txt_badge, (rx + rw - 180, spd_y + 55))
        
        # Speed Segment Bar (160 cruise / 240 max turbo)
        bar_x = rx + 24
        bar_y = spd_y + 105
        bar_w = rw - 48
        bar_h = 22
        pygame.draw.rect(surface, (16, 26, 42), (bar_x, bar_y, bar_w, bar_h))
        
        fill_ratio = min(1.0, speed_kmh / 240.0)
        fill_w = int(bar_w * fill_ratio)
        if fill_w > 0:
            b_col = COLOR_GOLD if is_turbo else (0, 190, 240)
            pygame.draw.rect(surface, b_col, (bar_x, bar_y, fill_w, bar_h))
        pygame.draw.rect(surface, (80, 120, 160), (bar_x, bar_y, bar_w, bar_h), 1)
        
        # 3. Battery / Fuel Level
        fuel_y = 450
        fuel_rect = pygame.Rect(rx, fuel_y, rw, 150)
        pygame.draw.rect(surface, (8, 16, 28), fuel_rect)
        pygame.draw.rect(surface, COLOR_PANEL_BORDER, fuel_rect, 1)
        
        txt_f_h = self.font_sub.render("FUEL ENERGY CELL (WRONG CAR: -15%)", True, (160, 190, 220))
        surface.blit(txt_f_h, (rx + 20, fuel_y + 12))
        
        # Fuel %
        f_int = int(fuel)
        if fuel > 50.0:
            f_col = (46, 204, 113)
        elif fuel > 25.0:
            f_col = COLOR_GOLD
        else:
            f_col = (235, 45, 45)
            
        txt_f_val = self.font_speed.render(f"{f_int}%", True, f_col)
        surface.blit(txt_f_val, (rx + 24, fuel_y + 40))
        
        # 10 Fuel Battery Blocks
        bx_start = rx + 24
        by = fuel_y + 105
        total_cells = 10
        gap = 6
        cell_w = int((rw - 48 - (gap * (total_cells - 1))) / total_cells)
        active_cells = int(round((fuel / 100.0) * total_cells))
        
        for c in range(total_cells):
            cx = bx_start + c * (cell_w + gap)
            is_active = (c < active_cells)
            cell_col = f_col if is_active else (25, 35, 50)
            pygame.draw.rect(surface, cell_col, (cx, by, cell_w, 24), border_radius=3)
            pygame.draw.rect(surface, (60, 85, 115), (cx, by, cell_w, 24), 1, border_radius=3)
            
        # 4. Mission Telemetry / Score
        score_y = 620
        sc_rect = pygame.Rect(rx, score_y, rw, 140)
        pygame.draw.rect(surface, (8, 16, 28), sc_rect)
        pygame.draw.rect(surface, COLOR_PANEL_BORDER, sc_rect, 1)
        
        txt_sc_h = self.font_sub.render("TACTICAL SCORE TELEMETRY", True, (160, 190, 220))
        surface.blit(txt_sc_h, (rx + 20, score_y + 12))
        
        txt_sc_val = self.font_speed.render(f"{int(score):06d}", True, COLOR_GOLD)
        surface.blit(txt_sc_val, (rx + 24, score_y + 45))
        
        env_note = STAGE_ENV_NOTES.get(stage, "")
        txt_env = self.font_tiny.render(env_note, True, (130, 160, 190))
        surface.blit(txt_env, (rx + 24, score_y + 108))
        
        # 5. Controls Guide Deck
        ctrl_y = 780
        c_rect = pygame.Rect(rx, ctrl_y, rw, 270)
        pygame.draw.rect(surface, (8, 16, 28), c_rect)
        pygame.draw.rect(surface, COLOR_PANEL_BORDER, c_rect, 1)
        
        txt_c_h = self.font_sub.render("FLIGHT CONTROLS & COMMANDS", True, COLOR_CYAN)
        surface.blit(txt_c_h, (rx + 20, ctrl_y + 14))
        
        lines = [
            "STEER: [A / D] or [LEFT / RIGHT] or GAMEPAD D-PAD / STICK",
            "TURBO BOOST: [W] / [UP] / [SPACE] or GAMEPAD [A] / [RT]",
            "BRAKE / SLOW: [S] / [DOWN] or GAMEPAD [X] / [LT]",
            "AUDIO / SETTINGS: [ESC] / [ENTER] or GAMEPAD [START]",
            "QUICK PAUSE: [P] or GAMEPAD [SELECT]",
            "QUIT TO DESKTOP: GAMEPAD [SELECT + START]",
            "TARGET GOAL: 36,000 METERS ALL 5 STAGES"
        ]
        for idx, line in enumerate(lines):
            txt_l = self.font_tiny.render(line, True, (180, 205, 230))
            surface.blit(txt_l, (rx + 20, ctrl_y + 48 + idx * 34))

    def render_title_screen(self, surface: pygame.Surface, menu_index: int, selected_stage: int):
        # Solid dark arcade canvas
        surface.fill((8, 12, 22))
        
        # 1. Romanji Title with multi-layered retro shadow
        title_text = "HIRAGANA ROAD FIGHTER"
        title_y = 310
        
        # Shadow 1: Black
        t_b = self.font_title.render(title_text, True, (0, 0, 0))
        surface.blit(t_b, t_b.get_rect(center=(SCREEN_WIDTH // 2, title_y + 4)))
        # Shadow 2: Crimson
        t_r = self.font_title.render(title_text, True, (215, 38, 38))
        surface.blit(t_r, t_r.get_rect(center=(SCREEN_WIDTH // 2, title_y + 2)))
        # Face: Vibrant Gold
        t_g = self.font_title.render(title_text, True, COLOR_GOLD)
        surface.blit(t_g, t_g.get_rect(center=(SCREEN_WIDTH // 2, title_y)))
        
        # 2. Hiragana Title below Romanji
        kana_text = "ひらがな  ロードファイター"
        kana_y = title_y + 68
        t_k = self.font_kana_title.render(kana_text, True, COLOR_CYAN)
        surface.blit(t_k, t_k.get_rect(center=(SCREEN_WIDTH // 2, kana_y)))
        
        # Divider line
        pygame.draw.line(surface, (0, 130, 205), (660, kana_y + 45), (1260, kana_y + 45), 2)
        
        # 3. Menu Items with 200ms NES Blinking
        is_blink = (int(time.time() * 1000) // 200) % 2 == 0
        menu_y_start = 540
        spacing = 75
        
        # Item 0: START
        is_sel_0 = (menu_index == 0)
        col0 = COLOR_WHITE if (is_sel_0 and is_blink) else (COLOR_GOLD if is_sel_0 else (190, 210, 230))
        txt_0 = self.font_menu.render("START", True, col0)
        r0 = txt_0.get_rect(center=(SCREEN_WIDTH // 2, menu_y_start))
        if is_sel_0 and is_blink:
            arrow = self.font_menu.render("►", True, COLOR_GOLD)
            surface.blit(arrow, (r0.left - 40, r0.top))
        surface.blit(txt_0, r0)
        
        # Item 1: STAGE SELECT
        is_sel_1 = (menu_index == 1)
        col1 = COLOR_WHITE if (is_sel_1 and is_blink) else (COLOR_GOLD if is_sel_1 else (190, 210, 230))
        st_name = STAGE_NAMES.get(selected_stage, "STAGE 01")
        st_str = f"STAGE SELECT   ◄  STAGE 0{selected_stage} : {st_name}  ►" if is_sel_1 else f"STAGE SELECT   < STAGE 0{selected_stage} >"
        txt_1 = self.font_menu.render(st_str, True, col1)
        r1 = txt_1.get_rect(center=(SCREEN_WIDTH // 2, menu_y_start + spacing))
        if is_sel_1 and is_blink:
            arrow = self.font_menu.render("►", True, COLOR_GOLD)
            surface.blit(arrow, (r1.left - 40, r1.top))
        surface.blit(txt_1, r1)
        
        # Item 2: OPTIONS
        is_sel_2 = (menu_index == 2)
        col2 = COLOR_WHITE if (is_sel_2 and is_blink) else (COLOR_GOLD if is_sel_2 else (190, 210, 230))
        txt_2 = self.font_menu.render("OPTIONS", True, col2)
        r2 = txt_2.get_rect(center=(SCREEN_WIDTH // 2, menu_y_start + spacing * 2))
        if is_sel_2 and is_blink:
            arrow = self.font_menu.render("►", True, COLOR_GOLD)
            surface.blit(arrow, (r2.left - 40, r2.top))
        surface.blit(txt_2, r2)
        
        # Footer
        txt_foot = self.font_tiny.render("▲/▼ NAVIGATE   ◀/▶ STAGE SELECT   [ENTER] / [A] / [START]: BEGIN   [SELECT + START]: QUIT", True, (140, 175, 210))
        surface.blit(txt_foot, txt_foot.get_rect(center=(SCREEN_WIDTH // 2, 980)))

    def render_volume_menu(self, surface: pygame.Surface, is_title_screen: bool, selected_idx: int,
                           master_vol: float, engine_vol: float, sfx_vol: float):
        # Modal dialog centered
        w = 640
        h = 470
        cx = SCREEN_WIDTH // 2 if is_title_screen else 760
        cy = SCREEN_HEIGHT // 2
        x = cx - (w // 2)
        y = cy - (h // 2)
        
        # Semi-transparent dark backing
        modal_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        modal_surf.fill((10, 18, 32, 245))
        surface.blit(modal_surf, (x, y))
        
        # Cyber gold/cyan border
        pygame.draw.rect(surface, (0, 160, 240), (x, y, w, h), 3, border_radius=12)
        pygame.draw.rect(surface, (15, 30, 50), (x + 3, y + 3, w - 6, h - 6), 1, border_radius=10)
        
        # Header title
        title_str = "AUDIO VOLUME CONFIGURATION"
        txt_title = self.font_menu.render(title_str, True, COLOR_GOLD)
        surface.blit(txt_title, txt_title.get_rect(center=(cx, y + 42)))
        pygame.draw.line(surface, (0, 120, 190), (x + 30, y + 75), (x + w - 30, y + 75), 2)
        
        # Sliders: 0: Master, 1: Engine, 2: SFX, 3: Back Button
        items = [
            ("MASTER VOLUME", master_vol, 0),
            ("ENGINE VOLUME", engine_vol, 1),
            ("SFX VOLUME", sfx_vol, 2)
        ]
        
        start_sy = y + 110
        spacing_s = 85
        
        for name, vol, idx in items:
            sy = start_sy + idx * spacing_s
            is_sel = (selected_idx == idx)
            
            # Label
            lbl_col = COLOR_GOLD if is_sel else (180, 205, 230)
            prefix = "► " if is_sel else "  "
            txt_lbl = self.font_sub.render(prefix + name, True, lbl_col)
            surface.blit(txt_lbl, (x + 40, sy))
            
            # Value %
            pct = int(round(vol * 100))
            txt_pct = self.font_sub.render(f"{pct}%", True, COLOR_CYAN if is_sel else (150, 180, 210))
            surface.blit(txt_pct, (x + w - 120, sy))
            
            # Slider Track
            bx = x + 40
            by = sy + 32
            bw = w - 80
            bh = 18
            pygame.draw.rect(surface, (15, 25, 42), (bx, by, bw, bh), border_radius=4)
            fill_w = int(bw * max(0.0, min(1.0, vol)))
            if fill_w > 0:
                bar_col = (0, 217, 255) if is_sel else (0, 140, 190)
                pygame.draw.rect(surface, bar_col, (bx, by, fill_w, bh), border_radius=4)
            pygame.draw.rect(surface, (50, 85, 125), (bx, by, bw, bh), 1, border_radius=4)
            
            # Slider thumb knob
            kx = bx + fill_w
            pygame.draw.circle(surface, COLOR_GOLD if is_sel else COLOR_WHITE, (kx, by + bh // 2), 10)
            pygame.draw.circle(surface, (20, 30, 45), (kx, by + bh // 2), 10, 2)
            
        # Item 3: Return / Close Button
        btn_y = y + 365
        btn_is_sel = (selected_idx == 3)
        btn_bg = (0, 110, 180) if btn_is_sel else (20, 35, 55)
        btn_rect = pygame.Rect(cx - 150, btn_y, 300, 42)
        pygame.draw.rect(surface, btn_bg, btn_rect, border_radius=6)
        pygame.draw.rect(surface, COLOR_GOLD if btn_is_sel else (40, 80, 120), btn_rect, 2, border_radius=6)
        
        btn_lbl = "◄ RETURN TO GAME ►" if not is_title_screen else "◄ RETURN TO TITLE ►"
        txt_b = self.font_sub.render(btn_lbl, True, COLOR_WHITE if btn_is_sel else (180, 205, 230))
        surface.blit(txt_b, txt_b.get_rect(center=btn_rect.center))
        
        # Navigation footer
        pygame.draw.line(surface, (0, 90, 150), (x + 20, y + 418), (x + w - 20, y + 418), 1)
        foot_str = "▲/▼ SELECT   ◀/▶ ADJUST   [ENTER] / [A]: CONFIRM   [B] / [START]: RESUME"
        txt_foot = self.font_tiny.render(foot_str, True, (140, 170, 200))
        surface.blit(txt_foot, txt_foot.get_rect(center=(cx, y + 440)))

    def render_pause_overlay(self, surface: pygame.Surface):
        is_blink = (int(time.time() * 1000) // 350) % 2 == 0
        cx = 760
        cy = 500
        
        # Semi-transparent dark curtain across the road viewport
        dim_surf = pygame.Surface((960, 1080), pygame.SRCALPHA)
        dim_surf.fill((0, 0, 0, 100))
        surface.blit(dim_surf, (280, 0))
        
        # Pause badge box
        box_w = 460
        box_h = 130
        bg_rect = pygame.Rect(cx - box_w // 2, cy - box_h // 2, box_w, box_h)
        pygame.draw.rect(surface, (10, 15, 26), bg_rect, border_radius=8)
        pygame.draw.rect(surface, COLOR_GOLD, bg_rect, 2, border_radius=8)
        
        col_p = COLOR_GOLD if is_blink else (160, 140, 20)
        txt_p = self.font_title.render("PAUSE", True, col_p)
        surface.blit(txt_p, txt_p.get_rect(center=(cx, cy - 20)))
        
        txt_sub = self.font_tiny.render("SELECT / START: RESUME   |   SELECT + START: QUIT", True, (210, 230, 255))
        surface.blit(txt_sub, txt_sub.get_rect(center=(cx, cy + 34)))

    def render_stage_clear_overlay(self, surface: pygame.Surface, stage: int):
        cx = 760
        cy = 480
        
        if stage == TOTAL_STAGES:
            # All 4 stages cleared!
            box_w = 680
            box_h = 240
            r_box = pygame.Rect(cx - box_w // 2, cy - box_h // 2, box_w, box_h)
            pygame.draw.rect(surface, (10, 20, 36), r_box)
            pygame.draw.rect(surface, COLOR_GOLD, r_box, 3)
            
            txt_h = self.font_title.render("ALL STAGES CLEARED!", True, COLOR_GOLD)
            surface.blit(txt_h, txt_h.get_rect(center=(cx, cy - 50)))
            
            txt_m = self.font_menu.render("YOU MASTERED ALL HIRAGANA!", True, COLOR_CYAN)
            surface.blit(txt_m, txt_m.get_rect(center=(cx, cy + 10)))
            
            txt_f = self.font_sub.render("RETURNING TO TITLE SCREEN...", True, COLOR_WHITE)
            surface.blit(txt_f, txt_f.get_rect(center=(cx, cy + 65)))
        else:
            box_w = 640
            box_h = 200
            r_box = pygame.Rect(cx - box_w // 2, cy - box_h // 2, box_w, box_h)
            pygame.draw.rect(surface, (10, 20, 36), r_box)
            pygame.draw.rect(surface, COLOR_GOLD, r_box, 2)
            
            txt_h = self.font_title.render(f"STAGE 0{stage} CLEARED!", True, COLOR_GOLD)
            surface.blit(txt_h, txt_h.get_rect(center=(cx, cy - 35)))
            
            txt_f = self.font_sub.render("PRESS [SPACE] / [ENTER] / GAMEPAD [A] FOR NEXT STAGE", True, COLOR_CYAN)
            surface.blit(txt_f, txt_f.get_rect(center=(cx, cy + 35)))

    def render_game_over_overlay(self, surface: pygame.Surface):
        cx = 760
        cy = 480
        box_w = 580
        box_h = 200
        r_box = pygame.Rect(cx - box_w // 2, cy - box_h // 2, box_w, box_h)
        pygame.draw.rect(surface, (25, 10, 10), r_box)
        pygame.draw.rect(surface, (240, 40, 40), r_box, 2)
        
        txt_h = self.font_title.render("OUT OF FUEL", True, (255, 60, 60))
        surface.blit(txt_h, txt_h.get_rect(center=(cx, cy - 35)))
        
        txt_f = self.font_sub.render("PRESS [SPACE] / [ENTER] TO RETRY  |  [ESC]: TITLE", True, COLOR_WHITE)
        surface.blit(txt_f, txt_f.get_rect(center=(cx, cy + 35)))
