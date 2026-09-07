"""
main.py
Entry point for Hiragana Road Fighter (Python Edition).
"""

import os
import sys
import argparse
import pygame
from game_config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, VIRTUAL_WIDTH, VIRTUAL_HEIGHT,
    detect_maximum_resolution, compute_aspect_ratio
)

def main():
    parser = argparse.ArgumentParser(description="Hiragana Road Fighter (Python Edition)")
    parser.add_argument("--stage", type=int, default=None, help="Stage to start on (1-5)")
    parser.add_argument("--trackdist", type=float, default=0.0, help="Initial track distance")
    parser.add_argument("--title", action="store_true", help="Force title screen")
    parser.add_argument("--titlemenu", type=int, default=0, help="Title screen menu index")
    parser.add_argument("--menu", action="store_true", help="Open audio settings menu immediately")
    parser.add_argument("--pause", action="store_true", help="Start game paused")
    parser.add_argument("--stageclear", action="store_true", help="Start with stage clear banner")
    parser.add_argument("--screenshot", type=str, default="", help="Save screenshot to path after frames and exit")
    parser.add_argument("--windowed", action="store_true", help="Run in windowed mode instead of fullscreen")
    parser.add_argument("--headless", action="store_true", help="Run without graphical display")
    parser.add_argument("--res", type=str, default="", help="Force resolution WIDTHxHEIGHT (e.g. 1920x1080, 1280x800)")
    parser.add_argument("--aspect", type=str, default="auto", choices=["auto", "stretch"], help="Aspect ratio mode ('auto' or 'stretch')")
    args = parser.parse_args()

    if args.headless:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ["SDL_AUDIODRIVER"] = "dummy"

    pygame.init()
    pygame.display.set_caption("Hiragana Road Fighter - ひらがな ロードファイター")

    # 1. Auto-detect maximum display resolution supported by system
    detected_max = detect_maximum_resolution()
    target_w, target_h = detected_max

    if args.res:
        try:
            parts = args.res.lower().split("x")
            target_w, target_h = int(parts[0]), int(parts[1])
        except Exception:
            print(f"[Display] Invalid --res format '{args.res}', using detected {target_w}x{target_h}")

    disp_ratio, aspect_label = compute_aspect_ratio(target_w, target_h)
    print(f"[Display] Detected Maximum Resolution: {target_w}x{target_h}")
    print(f"[Display] Auto Aspect Ratio: {aspect_label} ({disp_ratio:.3f})")

    flags = pygame.DOUBLEBUF | pygame.HWSURFACE
    if not args.windowed and not args.headless:
        flags |= pygame.FULLSCREEN

    # 2. Display mode initialization with graceful fallback chain
    screen = None
    if not args.windowed and not args.headless:
        try:
            # Try maximum detected resolution in fullscreen
            screen = pygame.display.set_mode((target_w, target_h), flags)
        except Exception as e1:
            print(f"[Display] Fullscreen mode ({target_w}x{target_h}) note: {e1}, attempting desktop fallback (0, 0)")
            try:
                # Try SDL desktop mode fallback (0, 0)
                screen = pygame.display.set_mode((0, 0), flags)
            except Exception as e2:
                print(f"[Display] Desktop mode (0,0) note: {e2}, falling back to windowed mode")
                screen = pygame.display.set_mode((min(target_w, 1920), min(target_h, 1080)), pygame.DOUBLEBUF)
    else:
        win_w = min(target_w, 1920) if not args.res else target_w
        win_h = min(target_h, 1080) if not args.res else target_h
        screen = pygame.display.set_mode((win_w, win_h), pygame.DOUBLEBUF)

    actual_w, actual_h = screen.get_size()
    print(f"[Display] Active Screen Resolution: {actual_w}x{actual_h}")

    stage_to_start = args.stage if args.stage is not None else 1
    skip_title = not args.title and (args.stage is not None or args.trackdist > 0.0 or args.pause or args.stageclear)

    # Import GameEngine after pygame.init() and display.set_mode()
    from game_engine import GameEngine

    engine = GameEngine(
        start_stage=stage_to_start,
        skip_title=skip_title,
        custom_dist=args.trackdist,
        start_paused=args.pause,
        start_menu=args.menu,
        start_stageclear=args.stageclear,
        detected_res=(actual_w, actual_h),
        aspect_mode=args.aspect
    )

    if args.titlemenu > 0:
        engine.title_menu_index = args.titlemenu

    if args.screenshot:
        # Run 25 frames to settle physics & textures, capture, then exit
        for _ in range(25):
            engine.run_frame(1.0 / 60.0)
        pygame.image.save(screen, args.screenshot)
        print(f"Screenshot successfully saved to: {args.screenshot}")
        pygame.quit()
        sys.exit(0)

    # Standard game loop
    engine.run()

if __name__ == "__main__":
    main()
