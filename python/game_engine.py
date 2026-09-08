"""
game_engine.py
Main arcade game loop, event management, physics, collision, and state transitions.
"""

import sys
import random
import pygame
from game_config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, VIRTUAL_WIDTH, VIRTUAL_HEIGHT, TARGET_FPS,
    GAME_X, GAME_W, ROAD_MARGIN, STAGE_TRACK_LENGTH, GAME_SPEED_SCALE,
    MAX_FUEL, FUEL_REWARD, FUEL_PENALTY, SCORE_REWARD, TOTAL_STAGES,
    STAGE_KANA, TRAFFIC_COLORS, COLOR_BG, COLOR_BEZEL,
    compute_aspect_ratio, get_asset_path, get_virtual_dimensions
)
from audio_system import AudioSystem
from road_renderer import RoadRenderer
from entities import PlayerCar, TrafficCar
from hud_renderer import HudRenderer
from update_manager import UpdateManager

class GameEngine:
    def __init__(self, start_stage: int = 1, skip_title: bool = False, custom_dist: float = 0.0,
                 start_paused: bool = False, start_menu: bool = False, start_stageclear: bool = False,
                 detected_res: tuple[int, int] | None = None, aspect_mode: str = "auto"):
        self.screen = pygame.display.get_surface()
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Display & Viewport Geometry
        win_size = self.screen.get_size() if self.screen else (VIRTUAL_WIDTH, VIRTUAL_HEIGHT)
        self.detected_res = detected_res if detected_res else win_size
        self.aspect_ratio_num, self.detected_aspect_label = compute_aspect_ratio(*self.detected_res)
        self.aspect_mode = aspect_mode # "auto" or "stretch"
        
        # Virtual Canvas (Dynamic aspect-adaptive high-definition internal resolution)
        self.virtual_width, self.virtual_height = get_virtual_dimensions(self.detected_res[0], self.detected_res[1], self.aspect_mode)
        self.virtual_screen = pygame.Surface((self.virtual_width, self.virtual_height))
        self.player_screen_y = self.virtual_height - 240.0
        
        self._last_win_w = 0
        self._last_win_h = 0
        self._last_aspect_mode = ""
        self.dst_rect = pygame.Rect(0, 0, self.virtual_width, self.virtual_height)
        self.scaled_surf = None
        
        # Audio & Renderers
        self.audio = AudioSystem()
        self.road = RoadRenderer()
        
        # Load system fonts
        latin_path = get_asset_path("fonts/DejaVuSans-Bold.ttf")
        cjk_path = get_asset_path("fonts/NotoSansCJK-Bold.ttc")
        
        self.font_latin = pygame.font.Font(latin_path, 20)
        self.font_cjk = pygame.font.Font(cjk_path, 26)
        
        self.hud = HudRenderer(self.font_latin, self.font_cjk)
        self.player = PlayerCar(self.font_cjk)
        self.player.y = self.player_screen_y
        
        # Gamepad setup
        pygame.joystick.init()
        self.joysticks = []
        for i in range(pygame.joystick.get_count()):
            try:
                joy = pygame.joystick.Joystick(i)
                joy.init()
                self.joysticks.append(joy)
                print(f"Controller {i} initialized: {joy.get_name()}")
            except Exception as e:
                print(f"Failed to init joystick {i}: {e}")
                
        self.stick_x_released = True
        self.stick_y_released = True
        self.gamepad_buttons_down = set()
            
        # Mouse auto-hide
        pygame.mouse.set_visible(False)
        self.mouse_idle_timer = 0.0
        
        # Game State
        self.current_stage = start_stage
        self.selected_stage = start_stage
        self.is_title_screen = not skip_title
        self.title_menu_index = 0
        self.is_volume_menu_open = start_menu
        self.volume_selected_index = 0
        self.is_paused = start_paused
        self.is_stage_clear = start_stageclear
        self.is_game_over = False
        
        # Auto-updater
        self.update_mgr = UpdateManager()
        self.is_update_dialog_open = False
        
        self.score = 0.0
        self.fuel = 100.0
        self.track_distance = custom_dist
        self.current_target_kana = {}
        self.match_timer = 0.0
        self.stage_clear_timer = 0.0
        self.spawn_timer = 0.0
        self.traffic_bump_sfx_timer = 0.0
        
        self.traffic_cars: list[TrafficCar] = []
        
        if self.is_title_screen:
            self.player.speed_kmh = 0.0
            self.audio.stop_all()
            self.audio.play_title_music()
        else:
            self.start_stage(self.current_stage, keep_fuel=False)
            if custom_dist > 0.0:
                self.track_distance = custom_dist
                self.road.track_distance = custom_dist
                self.traffic_cars.clear()
                for idx in range(3):
                    self._spawn_traffic_car(self.track_distance + 240.0 + (idx * 220.0))
            if start_stageclear:
                self.is_stage_clear = True
            if start_paused:
                self.is_paused = True
            if start_menu:
                self.is_volume_menu_open = True
            self.audio.start_engine()

    def check_quit_combo(self) -> bool:
        """Check if any connected controller has both SELECT and START pressed simultaneously."""
        for joy in self.joysticks:
            try:
                num = joy.get_numbuttons()
                # Direct pairs on the same controller:
                # Pair 1: Xbox / Steam Deck (6: Back/View, 7: Menu/Start)
                if 6 < num and 7 < num and joy.get_button(6) and joy.get_button(7):
                    return True
                # Pair 2: 8BitDo / Switch / PlayStation (8: Minus/Select/Share, 9: Plus/Start/Options)
                if 8 < num and 9 < num and joy.get_button(8) and joy.get_button(9):
                    return True
                # Pair 3: Generic / Arcade / D-Input (10: Select, 11: Start)
                if 10 < num and 11 < num and joy.get_button(10) and joy.get_button(11):
                    return True
                # Pair 4: Retro USB / SNES (4: Select, 6: Start)
                if 4 < num and 6 < num and joy.get_button(4) and joy.get_button(6):
                    return True
                # Cross-check on same controller:
                has_select = any(joy.get_button(b) for b in (4, 6, 8, 10) if b < num)
                has_start = any(joy.get_button(b) for b in (7, 9, 11) if b < num)
                if has_select and has_start:
                    return True
            except Exception:
                pass
        return False

    def start_stage(self, stage_num: int, keep_fuel: bool = False):
        self.audio.stop_title_music(fade_ms=350)
        self.current_stage = stage_num
        self.track_distance = 0.0
        self.is_stage_clear = False
        self.is_game_over = False
        self.is_paused = False
        self.stage_clear_timer = 0.0
        
        if not keep_fuel:
            self.fuel = 100.0
        else:
            self.fuel = min(100.0, self.fuel + 35.0)
            
        self.traffic_cars.clear()
        self.road.current_stage = self.current_stage
        self.road.track_distance = 0.0
        
        self.pick_new_target_kana()
        
        # Spawn initial traffic ahead
        for idx in range(3):
            self._spawn_traffic_car(self.track_distance + 280.0 + (idx * 240.0))
            
        self.player.x = 680.0
        self.player.y = self.player_screen_y
        self.player.speed_kmh = 80.0
        self.player.wobble_timer = 0.0

    def start_game_from_title(self):
        self.is_title_screen = False
        self.current_stage = self.selected_stage
        self.audio.stop_title_music(fade_ms=350)
        self.audio.play_fanfare()
        self.start_stage(self.selected_stage, keep_fuel=False)
        self.audio.start_engine()

    def return_to_title(self):
        self.is_title_screen = True
        self.is_paused = False
        self.is_volume_menu_open = False
        self.is_update_dialog_open = False
        self.is_stage_clear = False
        self.is_game_over = False
        self.stage_clear_timer = 0.0
        self.title_menu_index = 0
        self.audio.stop_all()
        self.audio.play_title_music()
        self.traffic_cars.clear()
        self.current_stage = self.selected_stage
        self.road.current_stage = self.selected_stage
        self.road.track_distance = 0.0
        self.player.x = 680.0
        self.player.y = self.player_screen_y
        self.player.speed_kmh = 0.0

    def pick_new_target_kana(self):
        pool = STAGE_KANA.get(self.current_stage, STAGE_KANA[1])
        available = [item for item in pool if item.get("kana") != self.current_target_kana.get("kana")]
        if not available:
            available = pool
        self.current_target_kana = random.choice(available)
        self.player.update_kana(self.current_target_kana["kana"])

    def toggle_volume_menu(self):
        self.is_volume_menu_open = not self.is_volume_menu_open
        self.audio.play_pause()
        if self.is_volume_menu_open:
            self.is_paused = False
            self.audio.update_engine(0.0, False)
            max_opts = 6 if not self.is_title_screen else 5
            if self.volume_selected_index >= max_opts:
                self.volume_selected_index = 0
        else:
            if not self.is_title_screen:
                self.audio.update_engine(self.player.speed_kmh, self.player.is_turbo)

    def toggle_pause(self):
        if self.is_volume_menu_open:
            self.is_volume_menu_open = False
            self.audio.update_engine(self.player.speed_kmh, self.player.is_turbo)
            return
        self.is_paused = not self.is_paused
        self.audio.play_pause()
        if self.is_paused:
            self.audio.pause_all()
        else:
            self.audio.unpause_all()
            self.audio.update_engine(self.player.speed_kmh, self.player.is_turbo)

    def adjust_volume(self, step: float):
        if self.volume_selected_index == 0:
            self.audio.set_master_volume(self.audio.master_volume + step)
        elif self.volume_selected_index == 1:
            self.audio.set_engine_volume(self.audio.engine_volume + step)
            self.audio.update_engine(0.0, False)
        elif self.volume_selected_index == 2:
            self.audio.set_sfx_volume(self.audio.sfx_volume + step)
            self.audio.play_match()

    def _spawn_traffic_car(self, custom_y: float = -1.0):
        pool = STAGE_KANA.get(self.current_stage, STAGE_KANA[1])
        if random.random() < 0.4:
            pick_romaji = self.current_target_kana.get("romaji", pool[0]["romaji"])
        else:
            pick_romaji = random.choice(pool)["romaji"]
            
        spawn_world_y = custom_y if custom_y > 0.0 else (self.track_distance + 1050.0)
        
        # Check occupied lanes near spawn_world_y to avoid overlap
        available_lanes = [0, 1, 2, 3]
        for car in self.traffic_cars:
            if car.is_active and abs(car.world_y - spawn_world_y) < 220.0:
                if car.lane_idx in available_lanes:
                    available_lanes.remove(car.lane_idx)
                    
        if available_lanes:
            lane_idx = random.choice(available_lanes)
        else:
            spawn_world_y += 240.0
            lane_idx = random.randint(0, 3)
            
        spd = random.uniform(70.0, 130.0)
        col = random.choice(TRAFFIC_COLORS)
        
        car = TrafficCar(pick_romaji, spawn_world_y, lane_idx, spd, col, self.font_latin)
        self.traffic_cars.append(car)

    def menu_up(self):
        if self.is_update_dialog_open:
            return
        if self.is_volume_menu_open:
            max_opts = 6 if not self.is_title_screen else 5
            self.volume_selected_index = (self.volume_selected_index - 1 + max_opts) % max_opts
            self.audio.play_pause()
        elif self.is_title_screen:
            self.title_menu_index = (self.title_menu_index - 1 + 4) % 4
            self.audio.play_pause()

    def menu_down(self):
        if self.is_update_dialog_open:
            return
        if self.is_volume_menu_open:
            max_opts = 6 if not self.is_title_screen else 5
            self.volume_selected_index = (self.volume_selected_index + 1) % max_opts
            self.audio.play_pause()
        elif self.is_title_screen:
            self.title_menu_index = (self.title_menu_index + 1) % 4
            self.audio.play_pause()

    def menu_left(self):
        if self.is_update_dialog_open:
            return
        if self.is_volume_menu_open:
            if self.volume_selected_index == 3:
                self.toggle_aspect_mode()
            elif self.volume_selected_index < 3:
                self.adjust_volume(-0.05)
        elif self.is_title_screen and self.title_menu_index == 1:
            self.selected_stage = (self.selected_stage - 2 + TOTAL_STAGES) % TOTAL_STAGES + 1
            self.current_stage = self.selected_stage
            self.road.current_stage = self.selected_stage
            self.audio.play_pause()

    def menu_right(self):
        if self.is_update_dialog_open:
            return
        if self.is_volume_menu_open:
            if self.volume_selected_index == 3:
                self.toggle_aspect_mode()
            elif self.volume_selected_index < 3:
                self.adjust_volume(0.05)
        elif self.is_title_screen and self.title_menu_index == 1:
            self.selected_stage = (self.selected_stage % TOTAL_STAGES) + 1
            self.current_stage = self.selected_stage
            self.road.current_stage = self.selected_stage
            self.audio.play_pause()

    def get_aspect_mode_label(self) -> str:
        if self.aspect_mode == "stretch":
            return "FULL (STRETCH)"
        if 1.50 <= self.aspect_ratio_num <= 1.65:
            return "AUTO (16:10 NATIVE)"
        return f"AUTO ({self.detected_aspect_label.split()[0]})"

    def toggle_aspect_mode(self):
        self.aspect_mode = "stretch" if self.aspect_mode == "auto" else "auto"
        self.audio.play_match()

    def _update_viewport_geometry(self):
        win_w, win_h = self.screen.get_size()
        if (win_w, win_h) == (self._last_win_w, self._last_win_h) and self._last_aspect_mode == self.aspect_mode:
            return

        self._last_win_w, self._last_win_h = win_w, win_h
        self._last_aspect_mode = self.aspect_mode

        # Ensure virtual canvas matches current window aspect ratio / mode
        new_vw, new_vh = get_virtual_dimensions(win_w, win_h, self.aspect_mode)
        if (new_vw, new_vh) != (self.virtual_width, self.virtual_height):
            self.virtual_width, self.virtual_height = new_vw, new_vh
            self.virtual_screen = pygame.Surface((self.virtual_width, self.virtual_height))
            self.player_screen_y = self.virtual_height - 240.0
            self.player.y = self.player_screen_y

        if self.aspect_mode == "stretch":
            draw_w, draw_h = win_w, win_h
            dst_x, dst_y = 0, 0
        else:
            # AUTO: preserve optimal aspect ratio based on virtual canvas
            target_ratio = self.virtual_width / self.virtual_height
            win_ratio = win_w / win_h
            if abs(win_ratio - target_ratio) < 0.01:
                # Direct match (e.g. 1920x1200 on 1280x800, or 1920x1080 on 1920x1080) -> ZERO black bars!
                draw_w, draw_h = win_w, win_h
                dst_x, dst_y = 0, 0
            elif win_ratio > target_ratio:
                # Wider (pillarbox)
                draw_h = win_h
                draw_w = int(win_h * target_ratio)
                dst_x = (win_w - draw_w) // 2
                dst_y = 0
            else:
                # Taller (letterbox)
                draw_w = win_w
                draw_h = int(win_w / target_ratio)
                dst_x = 0
                dst_y = (win_h - draw_h) // 2

        self.dst_rect = pygame.Rect(dst_x, dst_y, draw_w, draw_h)
        if (draw_w, draw_h) != (self.virtual_width, self.virtual_height):
            self.scaled_surf = pygame.Surface((draw_w, draw_h))
        else:
            self.scaled_surf = None

    def _present_to_screen(self):
        self._update_viewport_geometry()
        win_w, win_h = self.screen.get_size()

        if self.dst_rect.size == (self.virtual_width, self.virtual_height):
            if self.dst_rect.topleft == (0, 0):
                self.screen.blit(self.virtual_screen, (0, 0))
            else:
                self.screen.fill(COLOR_BEZEL)
                self.screen.blit(self.virtual_screen, (self.dst_rect.x, self.dst_rect.y))
        else:
            if self.dst_rect.x > 0 or self.dst_rect.y > 0 or self.dst_rect.w < win_w or self.dst_rect.h < win_h:
                self.screen.fill(COLOR_BEZEL)
            if self.scaled_surf is None or self.scaled_surf.get_size() != (self.dst_rect.w, self.dst_rect.h):
                self.scaled_surf = pygame.Surface((self.dst_rect.w, self.dst_rect.h))
            pygame.transform.scale(self.virtual_screen, (self.dst_rect.w, self.dst_rect.h), self.scaled_surf)
            self.screen.blit(self.scaled_surf, (self.dst_rect.x, self.dst_rect.y))

    def window_to_virtual_coords(self, mx: int, my: int) -> tuple[int, int]:
        if not hasattr(self, 'dst_rect') or self.dst_rect.w <= 0 or self.dst_rect.h <= 0:
            return mx, my
        rel_x = mx - self.dst_rect.x
        rel_y = my - self.dst_rect.y
        vx = int(rel_x * (self.virtual_width / self.dst_rect.w))
        vy = int(rel_y * (self.virtual_height / self.dst_rect.h))
        return vx, vy

    def open_update_dialog(self):
        self.is_update_dialog_open = True
        self.audio.play_match()
        self.update_mgr.check_for_updates()

    def close_update_dialog(self):
        if self.update_mgr.state != UpdateManager.STATE_DOWNLOADING:
            self.is_update_dialog_open = False
            self.audio.play_pause()

    def menu_confirm(self):
        if self.is_update_dialog_open:
            state = self.update_mgr.state
            if state == UpdateManager.STATE_UPDATE_AVAILABLE:
                self.audio.play_match()
                self.update_mgr.start_download()
            elif state == UpdateManager.STATE_SUCCESS:
                self.update_mgr.restart_game()
            elif state in (UpdateManager.STATE_UP_TO_DATE, UpdateManager.STATE_ERROR):
                self.close_update_dialog()
            return

        if self.is_volume_menu_open:
            if not self.is_title_screen:
                if self.volume_selected_index == 4:
                    self.toggle_volume_menu()
                elif self.volume_selected_index == 5:
                    self.return_to_title()
                elif self.volume_selected_index == 3:
                    self.toggle_aspect_mode()
                elif self.volume_selected_index < 3:
                    self.adjust_volume(0.05)
            else:
                if self.volume_selected_index == 4:
                    self.toggle_volume_menu()
                elif self.volume_selected_index == 3:
                    self.toggle_aspect_mode()
                elif self.volume_selected_index < 3:
                    self.adjust_volume(0.05)
            return
        elif self.is_title_screen:
            if self.title_menu_index == 0:
                self.start_game_from_title()
            elif self.title_menu_index == 1:
                self.selected_stage = (self.selected_stage % TOTAL_STAGES) + 1
                self.current_stage = self.selected_stage
                self.road.current_stage = self.selected_stage
                self.audio.play_pause()
            elif self.title_menu_index == 2:
                self.toggle_volume_menu()
            elif self.title_menu_index == 3:
                self.open_update_dialog()
        elif self.is_stage_clear:
            if self.current_stage == TOTAL_STAGES:
                self.return_to_title()
            else:
                self.start_stage(self.current_stage + 1, keep_fuel=True)
        elif self.is_game_over:
            self.start_stage(self.current_stage, keep_fuel=False)

    def menu_back(self):
        if self.is_update_dialog_open:
            self.close_update_dialog()
            return
        if self.is_volume_menu_open:
            self.toggle_volume_menu()
        elif self.is_title_screen:
            self.running = False
        elif self.is_stage_clear or self.is_game_over:
            self.return_to_title()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            # Controller Hotplugging
            if event.type == pygame.JOYDEVICEADDED:
                try:
                    joy = pygame.joystick.Joystick(event.device_index)
                    joy.init()
                    if not any(j.get_instance_id() == joy.get_instance_id() for j in self.joysticks):
                        self.joysticks.append(joy)
                        print(f"Gamepad attached: {joy.get_name()}")
                except Exception as e:
                    print(f"Error initializing attached gamepad: {e}")
            elif event.type == pygame.JOYDEVICEREMOVED:
                self.joysticks = [j for j in self.joysticks if j.get_instance_id() != event.instance_id]
                self.gamepad_buttons_down = {b for b in self.gamepad_buttons_down if b[0] != event.instance_id}
                print("Gamepad detached")

            # Mouse activity & 2-second countdown
            if event.type == pygame.MOUSEMOTION:
                dx, dy = event.rel
                # Filter out zero delta and micro-jitter from trackpads
                if abs(dx) >= 2 or abs(dy) >= 2:
                    if not pygame.mouse.get_visible():
                        pygame.mouse.set_visible(True)
                    self.mouse_idle_timer = 2.0
            elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
                if not pygame.mouse.get_visible():
                    pygame.mouse.set_visible(True)
                self.mouse_idle_timer = 2.0

            # Mouse clicks in menus
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = self.window_to_virtual_coords(*event.pos)
                if self.is_update_dialog_open:
                    cx, cy = self.virtual_width // 2, self.virtual_height // 2
                    modal_rect = pygame.Rect(cx - 490, cy - 280, 980, 560)
                    btn_rect = pygame.Rect(cx - 420, cy + 190, 840, 65)
                    if btn_rect.collidepoint(mx, my):
                        self.menu_confirm()
                    elif not modal_rect.collidepoint(mx, my):
                        self.close_update_dialog()
                elif self.is_title_screen and not self.is_volume_menu_open:
                    cx = self.virtual_width // 2
                    title_y = int(self.virtual_height * 0.285)
                    m_start = title_y + 205
                    sp = 65
                    if (m_start - 25) <= my <= (m_start + 25) and (cx - 360) <= mx <= (cx + 360):
                        self.start_game_from_title()
                    elif (m_start + sp - 25) <= my <= (m_start + sp + 25) and (cx - 540) <= mx <= (cx + 540):
                        if mx < cx:
                            self.menu_left()
                        else:
                            self.menu_right()
                    elif (m_start + sp * 2 - 25) <= my <= (m_start + sp * 2 + 25) and (cx - 360) <= mx <= (cx + 360):
                        self.toggle_volume_menu()
                    elif (m_start + sp * 3 - 25) <= my <= (m_start + sp * 3 + 25) and (cx - 360) <= mx <= (cx + 360):
                        self.open_update_dialog()
                elif self.is_volume_menu_open:
                    cx = self.virtual_width // 2 if self.is_title_screen else 760
                    cy = self.virtual_height // 2
                    w, h = 780, 600
                    x = cx - (w // 2)
                    y = cy - (h // 2)
                    start_sy = y + 92
                    spacing_s = 72
                    
                    bar_x = x + 45
                    bar_w = w - 90
                    click_val = max(0.0, min(1.0, (mx - bar_x) / bar_w))
                    
                    s0_y = start_sy
                    s1_y = start_sy + spacing_s
                    s2_y = start_sy + spacing_s * 2
                    ar_y = start_sy + spacing_s * 3
                    
                    if (s0_y - 10) <= my <= (s0_y + 55) and (x + 35) <= mx <= (x + w - 35):
                        self.volume_selected_index = 0
                        self.audio.set_master_volume(click_val)
                    elif (s1_y - 10) <= my <= (s1_y + 55) and (x + 35) <= mx <= (x + w - 35):
                        self.volume_selected_index = 1
                        self.audio.set_engine_volume(click_val)
                    elif (s2_y - 10) <= my <= (s2_y + 55) and (x + 35) <= mx <= (x + w - 35):
                        self.volume_selected_index = 2
                        self.audio.set_sfx_volume(click_val)
                        self.audio.play_match()
                    elif (ar_y - 10) <= my <= (ar_y + 65) and (x + 35) <= mx <= (x + w - 35):
                        self.volume_selected_index = 3
                        self.toggle_aspect_mode()
                    elif not self.is_title_screen:
                        btn1_y = y + 404
                        btn2_y = y + 462
                        if (btn1_y - 6) <= my <= (btn1_y + 52) and (cx - 215) <= mx <= (cx + 215):
                            self.volume_selected_index = 4
                            self.toggle_volume_menu()
                        elif (btn2_y - 6) <= my <= (btn2_y + 52) and (cx - 215) <= mx <= (cx + 215):
                            self.volume_selected_index = 5
                            self.return_to_title()
                    else:
                        btn_y = y + 430
                        if (btn_y - 6) <= my <= (btn_y + 56) and (cx - 215) <= mx <= (cx + 215):
                            self.volume_selected_index = 4
                            self.toggle_volume_menu()

            # Keyboard Input
            if event.type == pygame.KEYDOWN:
                # Quit shortcuts (Ctrl+Q or Ctrl+C, or Q when paused/gameover)
                if (event.key == pygame.K_q and (event.mod & pygame.KMOD_CTRL or self.is_paused or self.is_game_over)) or \
                   (event.key == pygame.K_c and (event.mod & pygame.KMOD_CTRL)):
                    self.running = False
                    return

                # Pause toggle on keyboard
                if event.key in (pygame.K_p, pygame.K_PAUSE):
                    if not self.is_title_screen and not self.is_volume_menu_open:
                        self.toggle_pause()
                    continue

                if self.is_paused:
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
                        self.toggle_pause()
                    continue

                if self.is_title_screen or self.is_volume_menu_open or self.is_update_dialog_open:
                    if event.key in (pygame.K_UP, pygame.K_w):
                        self.menu_up()
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        self.menu_down()
                    elif event.key in (pygame.K_LEFT, pygame.K_a):
                        self.menu_left()
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        self.menu_right()
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.menu_confirm()
                    elif event.key == pygame.K_ESCAPE:
                        self.menu_back()
                    continue

                # In-Game Keyboard commands
                if event.key == pygame.K_ESCAPE:
                    self.toggle_volume_menu()
                elif self.is_stage_clear:
                    if self.current_stage == TOTAL_STAGES:
                        self.return_to_title()
                    else:
                        if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_w, pygame.K_UP):
                            self.start_stage(self.current_stage + 1, keep_fuel=True)
                        elif event.key in (pygame.K_b, pygame.K_ESCAPE):
                            self.return_to_title()
                elif self.is_game_over:
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_w, pygame.K_UP):
                        self.start_stage(self.current_stage, keep_fuel=False)
                    elif event.key in (pygame.K_b, pygame.K_ESCAPE):
                        self.return_to_title()

            # Gamepad D-Pad (Hat motion)
            if event.type == pygame.JOYHATMOTION:
                hx, hy = event.value
                if hy == 1:
                    self.menu_up()
                elif hy == -1:
                    self.menu_down()
                if hx == -1:
                    self.menu_left()
                elif hx == 1:
                    self.menu_right()

            # Gamepad Analog Sticks in menus (with debounce threshold)
            if event.type == pygame.JOYAXISMOTION:
                if self.is_title_screen or self.is_volume_menu_open or self.is_update_dialog_open:
                    if event.axis == 1: # Left stick Y
                        if event.value < -0.55 and self.stick_y_released:
                            self.menu_up()
                            self.stick_y_released = False
                        elif event.value > 0.55 and self.stick_y_released:
                            self.menu_down()
                            self.stick_y_released = False
                        elif abs(event.value) < 0.25:
                            self.stick_y_released = True
                    elif event.axis == 0: # Left stick X
                        if event.value < -0.55 and self.stick_x_released:
                            self.menu_left()
                            self.stick_x_released = False
                        elif event.value > 0.55 and self.stick_x_released:
                            self.menu_right()
                            self.stick_x_released = False
                        elif abs(event.value) < 0.25:
                            self.stick_x_released = True

            # Gamepad Button Releases
            if event.type == pygame.JOYBUTTONUP:
                inst = getattr(event, 'instance_id', getattr(event, 'joy', 0))
                self.gamepad_buttons_down.discard((inst, event.button))

            # Gamepad Button Presses
            if event.type == pygame.JOYBUTTONDOWN:
                inst = getattr(event, 'instance_id', getattr(event, 'joy', 0))
                self.gamepad_buttons_down.add((inst, event.button))

                # Immediate check for simultaneous SELECT + START quit combination
                if self.check_quit_combo():
                    self.running = False
                    return

                btn = event.button
                # SELECT buttons: 4, 6, 8, 10
                # START buttons: 7, 9, 11
                # A: 0, B: 1, X: 2, Y: 3

                # SELECT Button: Pause / Unpause toggle or close modal
                if btn in (4, 6, 8, 10):
                    if self.is_update_dialog_open:
                        self.close_update_dialog()
                    elif self.is_volume_menu_open:
                        self.toggle_volume_menu()
                    elif self.is_paused:
                        self.toggle_pause() # Unpause
                    elif not self.is_title_screen:
                        self.toggle_pause() # Pause
                    continue

                # When paused, pressing START or any action button unpauses
                if self.is_paused:
                    if btn in (0, 1, 2, 3, 7, 9, 11):
                        self.toggle_pause()
                    continue

                # Menus (Title screen, Volume settings modal, Update modal)
                if self.is_title_screen or self.is_volume_menu_open or self.is_update_dialog_open:
                    if btn in (0, 7, 9, 11): # A or Start to Confirm
                        self.menu_confirm()
                    elif btn in (1, 2): # B or X to Back
                        self.menu_back()
                else:
                    # In-Game gameplay
                    if btn in (7, 9, 11): # In-Game Start opens volume menu
                        self.toggle_volume_menu()
                    elif self.is_stage_clear:
                        if self.current_stage == TOTAL_STAGES:
                            self.return_to_title()
                        elif btn in (0, 7, 9, 11):
                            self.start_stage(self.current_stage + 1, keep_fuel=True)
                        elif btn == 1:
                            self.return_to_title()
                    elif self.is_game_over:
                        if btn in (0, 7, 9, 11):
                            self.start_stage(self.current_stage, keep_fuel=False)
                        elif btn == 1:
                            self.return_to_title()

    def update(self, delta: float):
        # Continuous check for simultaneous SELECT + START quit combination
        if self.check_quit_combo():
            self.running = False
            return

        self.audio.update(delta)
        
        # Mouse auto-hide countdown (hides after 2 seconds idle)
        if pygame.mouse.get_visible():
            self.mouse_idle_timer -= delta
            if self.mouse_idle_timer <= 0.0:
                pygame.mouse.set_visible(False)
                self.mouse_idle_timer = 0.0

        if self.is_title_screen or self.is_volume_menu_open or self.is_paused or self.is_update_dialog_open:
            return

        if self.is_stage_clear:
            self.player.speed_kmh = max(0.0, self.player.speed_kmh - 80.0 * delta)
            self.audio.update_engine(self.player.speed_kmh, False)
            self.stage_clear_timer += delta
            if self.current_stage == TOTAL_STAGES and self.stage_clear_timer >= 4.0:
                self.return_to_title()
            return

        if self.is_game_over:
            self.player.speed_kmh = max(0.0, self.player.speed_kmh - 100.0 * delta)
            self.audio.update_engine(0.0, False)
            return

        # 1. Player Input (Polling Keyboard + ALL Connected Gamepads)
        keys = pygame.key.get_pressed()
        key_steer = 0.0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            key_steer -= 1.0
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            key_steer += 1.0
            
        key_turbo = keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_SPACE]
        key_brake = keys[pygame.K_DOWN] or keys[pygame.K_s]

        # Scan all connected gamepads
        joy_steer = 0.0
        joy_turbo = False
        joy_brake = False
        for joy in self.joysticks:
            inst_id = joy.get_instance_id() if hasattr(joy, 'get_instance_id') else 0

            # 1. Analog stick X (Axis 0)
            if joy.get_numaxes() > 0:
                ax0 = joy.get_axis(0)
                if abs(ax0) > 0.18:
                    joy_steer = ax0
                    
            # 2. D-Pad (Hats): Hat X for Steer, Hat Y for Gas/Brake
            for h in range(joy.get_numhats()):
                hx, hy = joy.get_hat(h)
                if abs(hx) > 0.2:
                    joy_steer = float(hx)
                if hy > 0.2:
                    joy_turbo = True
                elif hy < -0.2:
                    joy_brake = True

            # 3. Left Stick Y (Axis 1): UP = Turbo, DOWN = Brake
            if joy.get_numaxes() > 1:
                ay = joy.get_axis(1)
                if ay < -0.45: # Pushed UP
                    joy_turbo = True
                elif ay > 0.55: # Pushed DOWN
                    joy_brake = True
                    
            num_btns = joy.get_numbuttons()
            # Turbo buttons: A (0), Y (3), RB (5)
            if num_btns > 0 and (joy.get_button(0) or (inst_id, 0) in self.gamepad_buttons_down):
                joy_turbo = True
            if num_btns > 3 and (joy.get_button(3) or (inst_id, 3) in self.gamepad_buttons_down):
                joy_turbo = True
            if num_btns > 5 and (joy.get_button(5) or (inst_id, 5) in self.gamepad_buttons_down):
                joy_turbo = True
            
            # Brake buttons: X (2), LB (4)
            if num_btns > 2 and (joy.get_button(2) or (inst_id, 2) in self.gamepad_buttons_down):
                joy_brake = True
            if num_btns > 4 and (joy.get_button(4) or (inst_id, 4) in self.gamepad_buttons_down):
                joy_brake = True

            # D-pad buttons fallback (Buttons 11=Up, 12=Down, 13=Left, 14=Right)
            if num_btns > 14:
                if joy.get_button(13) or (inst_id, 13) in self.gamepad_buttons_down:
                    joy_steer = -1.0
                elif joy.get_button(14) or (inst_id, 14) in self.gamepad_buttons_down:
                    joy_steer = 1.0
                if joy.get_button(11) or (inst_id, 11) in self.gamepad_buttons_down:
                    joy_turbo = True
                elif joy.get_button(12) or (inst_id, 12) in self.gamepad_buttons_down:
                    joy_brake = True
            
            # Analog triggers (Strict threshold > 0.40 to reject idle/uncalibrated axes)
            num_axes = joy.get_numaxes()
            # Right Trigger: Axis 5 on Linux xpad / Xbox / Steam Deck
            if num_axes > 5 and joy.get_axis(5) > 0.40:
                joy_turbo = True
            # Left Trigger: Axis 2 on Linux xpad / Xbox / Steam Deck
            if num_axes > 2 and joy.get_axis(2) > 0.40:
                joy_brake = True

        steer = key_steer if abs(key_steer) > 0.01 else joy_steer
        steer = max(-1.0, min(1.0, steer))
        turbo_down = key_turbo or joy_turbo
        brake_down = key_brake or joy_brake
        
        # Gas / Turbo ALWAYS takes priority over brake to prevent phantom or stuck braking
        if turbo_down and brake_down:
            brake_down = False
            
        self.player.handle_input(steer, turbo_down, brake_down, delta)
        
        # 2. Track Progress
        dist_step = self.player.speed_kmh * 6.0 * GAME_SPEED_SCALE * delta
        self.track_distance += dist_step
        self.score += dist_step * 0.1
        
        # 3. Fuel Consumption
        fuel_drain = (self.player.speed_kmh / 120.0) * 1.8 * GAME_SPEED_SCALE * delta
        self.fuel = max(0.0, self.fuel - fuel_drain)
        if self.fuel <= 0.0:
            self.is_game_over = True
            self.audio.stop_all()
            
        # 4. Road Bounds Check
        road_edges = self.road.get_road_edges(self.current_stage, self.track_distance)
        self.player.check_road_bounds(road_edges)
        
        # 5. Check Finish Line
        if self.track_distance >= STAGE_TRACK_LENGTH:
            self.track_distance = STAGE_TRACK_LENGTH
            self.is_stage_clear = True
            self.audio.play_fanfare()
            
        # 6. Spawning Traffic
        if self.track_distance < STAGE_TRACK_LENGTH - 1200.0:
            self.spawn_timer += delta
            spawn_interval = 2.2 if self.player.speed_kmh > 120.0 else 3.5
            if self.spawn_timer >= spawn_interval:
                self.spawn_timer = 0.0
                self._spawn_traffic_car()
                
        # 7. Update Traffic Cars, Physics & Collisions
        if self.traffic_bump_sfx_timer > 0.0:
            self.traffic_bump_sfx_timer = max(0.0, self.traffic_bump_sfx_timer - delta)

        p_box = self.player.get_hitbox()
        
        # 7a. Individual Car Update & Screen Positioning
        for car in list(self.traffic_cars):
            car.update(delta)
            edges_at_car = self.road.get_road_edges(self.current_stage, car.world_y)
            car.update_screen_pos(self.track_distance, edges_at_car, player_screen_y=self.player_screen_y, screen_h=self.virtual_height)
            
            if car.to_remove:
                self.traffic_cars.remove(car)
                continue

        active_cars = [c for c in self.traffic_cars if c.is_active]

        # 7b. Longitudinal Anti-Ghosting & Arcade Traffic Avoidance (Traffic vs Traffic)
        active_cars.sort(key=lambda c: c.world_y, reverse=True)
        min_gap = TrafficCar.HEIGHT + 20.0
        
        for i in range(len(active_cars)):
            lead = active_cars[i]
            for j in range(i + 1, len(active_cars)):
                trail = active_cars[j]
                
                dx = abs(lead.x - trail.x)
                if dx < TrafficCar.WIDTH * 0.85:
                    gap_y = lead.world_y - trail.world_y
                    if TrafficCar.HEIGHT * 0.5 <= gap_y < min_gap:
                        trail.world_y = lead.world_y - min_gap
                        trail.speed_kmh = min(trail.speed_kmh, lead.speed_kmh)
                        edges_at_trail = self.road.get_road_edges(self.current_stage, trail.world_y)
                        trail.update_screen_pos(self.track_distance, edges_at_trail, player_screen_y=self.player_screen_y, screen_h=self.virtual_height)
                    elif min_gap <= gap_y < 220.0 and trail.speed_kmh > lead.speed_kmh and trail.lane_change_timer <= 0.0:
                        left_free = True
                        right_free = True
                        
                        target_left_lane = trail.lane_idx - 1
                        target_right_lane = trail.lane_idx + 1
                        
                        if target_left_lane < 0:
                            left_free = False
                        if target_right_lane > 3:
                            right_free = False
                            
                        for other in active_cars:
                            if other is trail:
                                continue
                            if abs(other.world_y - trail.world_y) < 220.0:
                                if other.lane_idx == target_left_lane or abs(other.lane_fraction - TrafficCar.LANE_FRACTIONS[max(0, target_left_lane)]) < 0.15:
                                    left_free = False
                                if other.lane_idx == target_right_lane or abs(other.lane_fraction - TrafficCar.LANE_FRACTIONS[min(3, target_right_lane)]) < 0.15:
                                    right_free = False
                                    
                        if left_free and right_free:
                            chosen_lane = target_left_lane if trail.lane_idx >= 2 else target_right_lane
                            trail.attempt_lane_change(chosen_lane)
                        elif left_free:
                            trail.attempt_lane_change(target_left_lane)
                        elif right_free:
                            trail.attempt_lane_change(target_right_lane)
                        else:
                            trail.speed_kmh = min(trail.speed_kmh, lead.speed_kmh)

        # 7c. Direct Hitbox Collisions (Traffic vs Traffic)
        for i in range(len(active_cars)):
            car_a = active_cars[i]
            box_a = car_a.get_hitbox()
            for j in range(i + 1, len(active_cars)):
                car_b = active_cars[j]
                box_b = car_b.get_hitbox()
                
                if box_a.colliderect(box_b):
                    dx = car_b.x - car_a.x
                    overlap_x = (box_a.width * 0.5 + box_b.width * 0.5) - abs(dx)
                    push = max(6.0, overlap_x * 0.5 + 4.0)
                    impulse = 260.0
                    
                    if car_a.x < car_b.x:
                        car_a.lateral_offset -= push
                        car_b.lateral_offset += push
                        car_a.apply_lateral_impulse(-impulse)
                        car_b.apply_lateral_impulse(impulse)
                    else:
                        car_a.lateral_offset += push
                        car_b.lateral_offset -= push
                        car_a.apply_lateral_impulse(impulse)
                        car_b.apply_lateral_impulse(-impulse)
                        
                    edges_a = self.road.get_road_edges(self.current_stage, car_a.world_y)
                    car_a.update_screen_pos(self.track_distance, edges_a, player_screen_y=self.player_screen_y, screen_h=self.virtual_height)
                    edges_b = self.road.get_road_edges(self.current_stage, car_b.world_y)
                    car_b.update_screen_pos(self.track_distance, edges_b, player_screen_y=self.player_screen_y, screen_h=self.virtual_height)
                    
                    car_a.trigger_wobble(0.4)
                    car_b.trigger_wobble(0.4)
                    
                    avg_speed = (car_a.speed_kmh + car_b.speed_kmh) * 0.5
                    car_a.speed_kmh = max(40.0, avg_speed * 0.95)
                    car_b.speed_kmh = max(40.0, avg_speed * 0.95)
                    
                    if self.traffic_bump_sfx_timer <= 0.0:
                        self.audio.play_crash()
                        self.traffic_bump_sfx_timer = 0.35

        # 7d. Player vs Traffic Car Collisions
        for car in active_cars:
            if car.is_active and p_box.colliderect(car.get_hitbox()):
                car_ro = car.romaji.strip().lower()
                target_ro = self.current_target_kana.get("romaji", "").strip().lower()
                
                # Support Hepburn / Kunrei romanization variants
                alt_matches = {
                    "si": ["si", "shi"],
                    "shi": ["si", "shi"],
                    "tu": ["tu", "tsu"],
                    "tsu": ["tu", "tsu"],
                    "ti": ["ti", "chi"],
                    "chi": ["ti", "chi"],
                    "fu": ["fu", "hu"],
                    "hu": ["fu", "hu"]
                }
                is_match = (car_ro == target_ro) or (target_ro in alt_matches and car_ro in alt_matches[target_ro])
                
                if is_match:
                    # MATCH! Refuel and reward
                    self.score += SCORE_REWARD
                    self.fuel = min(MAX_FUEL, self.fuel + FUEL_REWARD)
                    self.audio.play_match()
                    self.match_timer = 2.0
                    car.trigger_match()
                    self.pick_new_target_kana()
                else:
                    # MISMATCH CRASH! Spinout and 15% penalty
                    if self.player.wobble_timer <= 0.0:
                        self.player.trigger_wobble()
                        self.fuel = max(0.0, self.fuel - FUEL_PENALTY)
                        self.audio.play_crash()
                    
                    car.trigger_crash()
                    
                    # Classic arcade lateral bounce impulse applied to BOTH player and traffic car
                    bounce = 24.0
                    traffic_impulse = 380.0
                    if self.player.x < car.x:
                        self.player.x -= bounce
                        car.apply_lateral_impulse(traffic_impulse)
                    else:
                        self.player.x += bounce
                        car.apply_lateral_impulse(-traffic_impulse)

        if self.match_timer > 0.0:
            self.match_timer = max(0.0, self.match_timer - delta)

        # 8. Audio & Road Sync
        self.road.track_distance = self.track_distance
        self.audio.update_engine(self.player.speed_kmh, self.player.is_turbo)

    def render(self):
        self.virtual_screen.fill(COLOR_BG)
        
        # 1. Road & Environment
        self.road.render(self.virtual_screen, self.current_stage, self.track_distance, player_screen_y=self.player_screen_y)
        
        # 2. Traffic Cars
        for car in self.traffic_cars:
            car.render(self.virtual_screen)
            
        # 3. Player Car
        self.player.render(self.virtual_screen)
        
        # 4. HUD Panels
        self.hud.render_left_panel(self.virtual_screen, self.current_stage, self.track_distance, STAGE_TRACK_LENGTH)
        self.hud.render_right_panel(
            self.virtual_screen, self.current_stage,
            self.current_target_kana.get("kana", "あ"),
            self.current_target_kana.get("romaji", "a"),
            self.player.speed_kmh, self.player.is_turbo, self.player.is_braking,
            self.fuel, self.score, self.match_timer
        )
        
        # 5. Overlays
        if self.is_title_screen:
            disp_info = f"{self.detected_res[0]}x{self.detected_res[1]} [{self.detected_aspect_label.split()[0]}]"
            self.hud.render_title_screen(self.virtual_screen, self.title_menu_index, self.selected_stage, disp_info)
            if self.is_update_dialog_open:
                self.hud.render_update_modal(self.virtual_screen, self.update_mgr)
            
        if self.is_volume_menu_open:
            self.hud.render_volume_menu(
                self.virtual_screen, self.is_title_screen, self.volume_selected_index,
                self.audio.master_volume, self.audio.engine_volume, self.audio.sfx_volume,
                self.get_aspect_mode_label()
            )
        elif self.is_paused:
            self.hud.render_pause_overlay(self.virtual_screen)
        elif self.is_stage_clear:
            self.hud.render_stage_clear_overlay(self.virtual_screen, self.current_stage)
        elif self.is_game_over:
            self.hud.render_game_over_overlay(self.virtual_screen)

        # 6. Presentation with Aspect-Ratio Adaptive Scaling
        self._present_to_screen()
        pygame.display.flip()

    def run_frame(self, delta: float):
        self.handle_events()
        self.update(delta)
        self.render()

    def run(self):
        while self.running:
            delta = self.clock.tick(TARGET_FPS) / 1000.0
            # Cap delta to avoid physics explosions on lag spikes
            delta = min(0.05, max(0.001, delta))
            self.run_frame(delta)
        
        self.audio.stop_all()
        pygame.quit()
