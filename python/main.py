"""
main.py
Entry point for Hiragana Road Fighter (Python Edition).
"""

import os
import sys
import argparse
import pygame
from game_config import SCREEN_WIDTH, SCREEN_HEIGHT

def main():
    parser = argparse.ArgumentParser(description="Hiragana Road Fighter (Python Edition)")
    parser.add_argument("--stage", type=int, default=None, help="Stage to start on (1-4)")
    parser.add_argument("--trackdist", type=float, default=0.0, help="Initial track distance")
    parser.add_argument("--title", action="store_true", help="Force title screen")
    parser.add_argument("--titlemenu", type=int, default=0, help="Title screen menu index")
    parser.add_argument("--menu", action="store_true", help="Open audio settings menu immediately")
    parser.add_argument("--pause", action="store_true", help="Start game paused")
    parser.add_argument("--stageclear", action="store_true", help="Start with stage clear banner")
    parser.add_argument("--screenshot", type=str, default="", help="Save screenshot to path after 30 frames and exit")
    parser.add_argument("--windowed", action="store_true", help="Run in windowed mode instead of fullscreen")
    parser.add_argument("--headless", action="store_true", help="Run without graphical display")
    args = parser.parse_args()

    if args.headless:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ["SDL_AUDIODRIVER"] = "dummy"

    pygame.init()
    pygame.display.set_caption("Hiragana Road Fighter - ひらがな ロードファイター")

    flags = pygame.DOUBLEBUF | pygame.HWSURFACE
    if not args.windowed and not args.headless:
        flags |= pygame.FULLSCREEN

    # Fallback to windowed if fullscreen fails
    try:
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
    except Exception as e:
        print(f"Fullscreen mode init note: {e}, falling back to windowed mode")
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.DOUBLEBUF)

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
        start_stageclear=args.stageclear
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
