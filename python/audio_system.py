"""
audio_system.py
Sound and volume management using Pygame Mixer for Hiragana Road Fighter.
"""

import os
import pygame
from game_config import get_asset_path

class AudioSystem:
    def __init__(self):
        self.master_volume = 0.40
        self.engine_volume = 0.70
        self.sfx_volume = 0.90
        
        self.duck_timer = 0.0
        self.is_initialized = False
        self.is_paused = False
        
        self.snd_engine = None
        self.snd_turbo = None
        self.snd_match = None
        self.snd_crash = None
        self.snd_fanfare = None
        self.snd_pause = None
        
        self.channel_engine = None
        self.channel_turbo = None
        self.channel_sfx = None
        
        self._init_audio()

    def _init_audio(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
            
            pygame.mixer.set_num_channels(16)
            self.channel_engine = pygame.mixer.Channel(0)
            self.channel_turbo = pygame.mixer.Channel(1)
            self.channel_sfx = pygame.mixer.Channel(2)
            
            # Load sounds
            eng_path = get_asset_path("audio/engine.wav")
            trb_path = get_asset_path("audio/turbo.wav")
            mtc_path = get_asset_path("audio/match.wav")
            crs_path = get_asset_path("audio/crash.wav")
            fan_path = get_asset_path("audio/fanfare.wav")
            pse_path = get_asset_path("audio/pause.wav")
            
            if os.path.exists(eng_path): self.snd_engine = pygame.mixer.Sound(eng_path)
            if os.path.exists(trb_path): self.snd_turbo = pygame.mixer.Sound(trb_path)
            if os.path.exists(mtc_path): self.snd_match = pygame.mixer.Sound(mtc_path)
            if os.path.exists(crs_path): self.snd_crash = pygame.mixer.Sound(crs_path)
            if os.path.exists(fan_path): self.snd_fanfare = pygame.mixer.Sound(fan_path)
            if os.path.exists(pse_path): self.snd_pause = pygame.mixer.Sound(pse_path)
            
            self.is_initialized = True
            self.apply_volumes()
        except Exception as e:
            print(f"Warning: Audio initialization failed: {e}")
            self.is_initialized = False

    def set_master_volume(self, val: float):
        self.master_volume = max(0.0, min(1.0, val))
        self.apply_volumes()

    def set_engine_volume(self, val: float):
        self.engine_volume = max(0.0, min(1.0, val))
        self.apply_volumes()

    def set_sfx_volume(self, val: float):
        self.sfx_volume = max(0.0, min(1.0, val))
        self.apply_volumes()

    def apply_volumes(self):
        if not self.is_initialized:
            return
        
        # Engine Channel
        eff_eng = self.master_volume * self.engine_volume
        if self.channel_engine:
            self.channel_engine.set_volume(eff_eng * 0.45)
            
        # Turbo Channel
        if self.channel_turbo:
            self.channel_turbo.set_volume(eff_eng * 0.55)
            
        # SFX Sounds
        eff_sfx = self.master_volume * self.sfx_volume
        for snd in [self.snd_match, self.snd_crash, self.snd_fanfare, self.snd_pause]:
            if snd:
                snd.set_volume(eff_sfx)

    def start_engine(self):
        if not self.is_initialized or self.is_paused:
            return
        if self.snd_engine and self.channel_engine and not self.channel_engine.get_busy():
            self.channel_engine.play(self.snd_engine, loops=-1)
        if self.snd_turbo and self.channel_turbo and not self.channel_turbo.get_busy():
            self.channel_turbo.play(self.snd_turbo, loops=-1)
            self.channel_turbo.set_volume(0.0)

    def stop_all(self):
        if not self.is_initialized:
            return
        if self.channel_engine: self.channel_engine.stop()
        if self.channel_turbo: self.channel_turbo.stop()
        if self.channel_sfx: self.channel_sfx.stop()
        try:
            pygame.mixer.stop()
        except Exception:
            pass

    def pause_all(self):
        """Pause all sounds, channels, and music when game is paused."""
        if not self.is_initialized:
            return
        self.is_paused = True
        if self.channel_engine:
            self.channel_engine.pause()
        if self.channel_turbo:
            self.channel_turbo.pause()
        if self.channel_sfx:
            self.channel_sfx.pause()
        try:
            pygame.mixer.pause()
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.pause()
        except Exception:
            pass

    def unpause_all(self):
        """Resume all audio channels upon unpausing."""
        if not self.is_initialized:
            return
        self.is_paused = False
        try:
            pygame.mixer.unpause()
            if pygame.mixer.music.get_pos() >= 0:
                pygame.mixer.music.unpause()
        except Exception:
            pass
        if self.channel_engine:
            self.channel_engine.unpause()
        if self.channel_turbo:
            self.channel_turbo.unpause()
        if self.channel_sfx:
            self.channel_sfx.unpause()

    def update_engine(self, speed_kmh: float, is_turbo: bool):
        if not self.is_initialized or self.is_paused:
            return
        
        # Ensure engine is playing
        if self.snd_engine and self.channel_engine and not self.channel_engine.get_busy():
            self.channel_engine.play(self.snd_engine, loops=-1)
        if self.snd_turbo and self.channel_turbo and not self.channel_turbo.get_busy():
            self.channel_turbo.play(self.snd_turbo, loops=-1)
            
        duck_mult = 0.55 if self.duck_timer > 0.0 else 1.0
        eff_eng = self.master_volume * self.engine_volume * duck_mult
        
        if speed_kmh <= 1.0:
            # Gentle stationary idle
            if self.channel_engine:
                self.channel_engine.set_volume(eff_eng * 0.25)
            if self.channel_turbo:
                self.channel_turbo.set_volume(0.0)
            return

        # Cruise volume scales with speed
        vol_factor = 0.3 + 0.35 * min(1.0, speed_kmh / 160.0)
        if self.channel_engine:
            self.channel_engine.set_volume(eff_eng * vol_factor)
            
        # Turbo sound
        if is_turbo and speed_kmh > 60.0:
            trb_factor = 0.45 * min(1.0, (speed_kmh - 60.0) / 100.0)
            if self.channel_turbo:
                self.channel_turbo.set_volume(eff_eng * trb_factor)
        else:
            if self.channel_turbo:
                self.channel_turbo.set_volume(0.0)

    def play_match(self):
        if not self.is_initialized or not self.snd_match:
            return
        self.duck_timer = 0.6
        self.snd_match.play()

    def play_crash(self):
        if not self.is_initialized or not self.snd_crash:
            return
        self.duck_timer = 0.5
        self.snd_crash.play()

    def play_fanfare(self):
        if not self.is_initialized or not self.snd_fanfare:
            return
        self.duck_timer = 3.0
        self.snd_fanfare.play()

    def play_pause(self):
        if not self.is_initialized or not self.snd_pause:
            return
        self.snd_pause.play()

    def update(self, delta: float):
        if self.duck_timer > 0.0:
            self.duck_timer = max(0.0, self.duck_timer - delta)
