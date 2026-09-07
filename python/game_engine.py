"""
game_engine.py
Main arcade game loop, event management, physics, collision, and state transitions.
"""

import sys
import random
import pygame
from game_config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TARGET_FPS, GAME_X, GAME_W, ROAD_MARGIN,
    STAGE_TRACK_LENGTH, GAME_SPEED_SCALE, MAX_FUEL, FUEL_REWARD, FUEL_PENALTY,
    SCORE_REWARD, TOTAL_STAGES, STAGE_KANA, TRAFFIC_COLORS,
    COLOR_BG, get_asset_path
)
from audio_system import AudioSystem
from road_renderer import RoadRenderer
from entities import PlayerCar, TrafficCar
from hud_renderer import HudRenderer
from update_manager import UpdateManager

class GameEngine:
    def __init__(self, start_stage: int = 1, skip_title: bool = False, custom_dist: float = 0.0,
                 start_paused: bool = False, start_menu: bool = False, start_stageclear: bool = False):
        self.screen = pygame.display.get_surface()
        self.clock = pygame.time.Clock()
        self.running = True
        
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
        
        self.traffic_cars: list[TrafficCar] = []
        
        if self.is_title_screen:
            self.player.speed_kmh = 0.0
            self.audio.stop_all()
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
        self.player.y = 840.0
        self.player.speed_kmh = 80.0
        self.player.wobble_timer = 0.0

    def start_game_from_title(self):
        self.is_title_screen = False
        self.current_stage = self.selected_stage
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
        self.traffic_cars.clear()
        self.current_stage = self.selected_stage
        self.road.current_stage = self.selected_stage
        self.road.track_distance = 0.0
        self.player.x = 680.0
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
        lane_idx = random.randint(0, 3)
        spd = random.uniform(70.0, 130.0)
        col = random.choice(TRAFFIC_COLORS)
        
        car = TrafficCar(pick_romaji, spawn_world_y, lane_idx, spd, col, self.font_latin)
        self.traffic_cars.append(car)

    def menu_up(self):
        if self.is_update_dialog_open:
            return
        if self.is_volume_menu_open:
            self.volume_selected_index = (self.volume_selected_index - 1 + 4) % 4
            self.audio.play_pause()
        elif self.is_title_screen:
            self.title_menu_index = (self.title_menu_index - 1 + 4) % 4
            self.audio.play_pause()

    def menu_down(self):
        if self.is_update_dialog_open:
            return
        if self.is_volume_menu_open:
            self.volume_selected_index = (self.volume_selected_index + 1) % 4
            self.audio.play_pause()
        elif self.is_title_screen:
            self.title_menu_index = (self.title_menu_index + 1) % 4
            self.audio.play_pause()

    def menu_left(self):
        if self.is_update_dialog_open:
            return
        if self.is_volume_menu_open:
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
            self.adjust_volume(0.05)
        elif self.is_title_screen and self.title_menu_index == 1:
            self.selected_stage = (self.selected_stage % TOTAL_STAGES) + 1
            self.current_stage = self.selected_stage
            self.road.current_stage = self.selected_stage
            self.audio.play_pause()

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
            if self.volume_selected_index == 3:
                self.toggle_volume_menu()
            else:
                self.adjust_volume(0.05)
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
                    if joy not in self.joysticks:
                        self.joysticks.append(joy)
                        print(f"Gamepad attached: {joy.get_name()}")
                except Exception as e:
                    print(f"Error initializing attached gamepad: {e}")
            elif event.type == pygame.JOYDEVICEREMOVED:
                self.joysticks = [j for j in self.joysticks if j.get_instance_id() != event.instance_id]
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
                mx, my = event.pos
                if self.is_update_dialog_open:
                    cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
                    modal_rect = pygame.Rect(cx - 420, cy - 250, 840, 500)
                    btn_rect = pygame.Rect(cx - 300, cy + 190, 600, 55)
                    if btn_rect.collidepoint(mx, my):
                        self.menu_confirm()
                    elif not modal_rect.collidepoint(mx, my):
                        self.close_update_dialog()
                elif self.is_title_screen and not self.is_volume_menu_open:
                    if 495 <= my <= 545 and 600 <= mx <= 1320:
                        self.start_game_from_title()
                    elif 560 <= my <= 610 and 420 <= mx <= 1500:
                        if mx < 960:
                            self.menu_left()
                        else:
                            self.menu_right()
                    elif 625 <= my <= 675 and 600 <= mx <= 1320:
                        self.toggle_volume_menu()
                    elif 690 <= my <= 745 and 600 <= mx <= 1320:
                        self.open_update_dialog()
                elif self.is_volume_menu_open:
                    cx = 960 if self.is_title_screen else 760
                    bar_x = (cx - 320) + 32
                    bar_w = 576
                    click_val = max(0.0, min(1.0, (mx - bar_x) / bar_w))
                    
                    if 380 <= my <= 445:
                        self.volume_selected_index = 0
                        self.audio.set_master_volume(click_val)
                    elif 460 <= my <= 525:
                        self.volume_selected_index = 1
                        self.audio.set_engine_volume(click_val)
                    elif 540 <= my <= 605:
                        self.volume_selected_index = 2
                        self.audio.set_sfx_volume(click_val)
                        self.audio.play_match()
                    elif 645 <= my <= 695 and (cx - 160) <= mx <= (cx + 160):
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
                if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
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

            # Gamepad Button Presses
            if event.type == pygame.JOYBUTTONDOWN:
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
            # Analog stick X (Axis 0)
            if joy.get_numaxes() > 0:
                ax0 = joy.get_axis(0)
                if abs(ax0) > 0.15:
                    joy_steer = ax0
                    
            # D-Pad X (Hat 0)
            if joy.get_numhats() > 0:
                hx, _ = joy.get_hat(0)
                if hx != 0:
                    joy_steer = float(hx)
                    
            num_btns = joy.get_numbuttons()
            # Turbo buttons: A (0), Y (3), RB (5)
            if num_btns > 0 and joy.get_button(0): joy_turbo = True
            if num_btns > 3 and joy.get_button(3): joy_turbo = True
            if num_btns > 5 and joy.get_button(5): joy_turbo = True
            
            # Brake buttons: X (2), B (1), LB (4)
            if num_btns > 2 and joy.get_button(2): joy_brake = True
            if num_btns > 1 and joy.get_button(1): joy_brake = True
            if num_btns > 4 and joy.get_button(4): joy_brake = True
            
            # Analog triggers
            num_axes = joy.get_numaxes()
            # Right Trigger (Axis 5 on Xbox/Deck) for Turbo
            if num_axes > 5 and joy.get_axis(5) > 0.0:
                joy_turbo = True
            # Left Trigger (Axis 4 on Xbox/Deck or Axis 2) for Brake
            if num_axes > 4 and joy.get_axis(4) > 0.0:
                joy_brake = True

        steer = key_steer if key_steer != 0.0 else joy_steer
        turbo_down = key_turbo or joy_turbo
        brake_down = key_brake or joy_brake
            
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
                
        # 7. Update Traffic Cars & Collisions
        p_box = self.player.get_hitbox()
        for car in list(self.traffic_cars):
            car.update(delta)
            edges_at_car = self.road.get_road_edges(self.current_stage, car.world_y)
            car.update_screen_pos(self.track_distance, edges_at_car)
            
            if car.to_remove:
                self.traffic_cars.remove(car)
                continue
                
            # Responsive Collision Detection
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
                    "chi": ["ti", "chi"]
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
                    self.player.trigger_wobble()
                    self.fuel = max(0.0, self.fuel - FUEL_PENALTY)
                    self.audio.play_crash()
                    car.trigger_crash()
                    
                    # Classic arcade lateral bounce impulse
                    bounce = 24.0
                    if self.player.x < car.x:
                        self.player.x -= bounce
                        car.x += bounce
                    else:
                        self.player.x += bounce
                        car.x -= bounce

        if self.match_timer > 0.0:
            self.match_timer = max(0.0, self.match_timer - delta)

        # 8. Audio & Road Sync
        self.road.track_distance = self.track_distance
        self.audio.update_engine(self.player.speed_kmh, self.player.is_turbo)

    def render(self):
        self.screen.fill(COLOR_BG)
        
        # 1. Road & Environment
        self.road.render(self.screen, self.current_stage, self.track_distance)
        
        # 2. Traffic Cars
        for car in self.traffic_cars:
            car.render(self.screen)
            
        # 3. Player Car
        self.player.render(self.screen)
        
        # 4. HUD Panels
        self.hud.render_left_panel(self.screen, self.current_stage, self.track_distance, STAGE_TRACK_LENGTH)
        self.hud.render_right_panel(
            self.screen, self.current_stage,
            self.current_target_kana.get("kana", "あ"),
            self.current_target_kana.get("romaji", "a"),
            self.player.speed_kmh, self.player.is_turbo, self.player.is_braking,
            self.fuel, self.score, self.match_timer
        )
        
        # 5. Overlays
        if self.is_title_screen:
            self.hud.render_title_screen(self.screen, self.title_menu_index, self.selected_stage)
            if self.is_update_dialog_open:
                self.hud.render_update_modal(self.screen, self.update_mgr)
            
        if self.is_volume_menu_open:
            self.hud.render_volume_menu(
                self.screen, self.is_title_screen, self.volume_selected_index,
                self.audio.master_volume, self.audio.engine_volume, self.audio.sfx_volume
            )
        elif self.is_paused:
            self.hud.render_pause_overlay(self.screen)
        elif self.is_stage_clear:
            self.hud.render_stage_clear_overlay(self.screen, self.current_stage)
        elif self.is_game_over:
            self.hud.render_game_over_overlay(self.screen)

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
