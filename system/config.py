from pathlib import Path
import pygame

PR_DIR = Path(__file__).parent.parent
ASSETS_DIR = PR_DIR / "assets"
SKINS_DIR = ASSETS_DIR / "skins"
BG_DIR = ASSETS_DIR / "bg"
HB_DIR = ASSETS_DIR / "hb"
ON_BG_DIR = ASSETS_DIR / "on_bg"
JSON_DIR = PR_DIR / "json"
SCREENSHOTS_DIR = PR_DIR / "screenshots"

pygame.init()
info = pygame.display.Info()
SCREEN_WIDTH = info.current_w
SCREEN_HEIGHT = info.current_h
pygame.quit()
FPS = 60

GRAVITY = 0.7
PLAYER_SPEED = 5
PLAYER_JUMP_POWER = 12

PLAYER_SIZE = 30
OBJECT_SIZE = 30

COYOTE_TIME_MAX = 4
WALL_JUMP_TIMER_MAX = 14
MAX_CLIMB = 30

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 12345
SOCKET_TIMEOUT = 5.0

SKINS = {
    "Пон": "assets/skins/player_st.png",
    "НЕКлоун": "assets/skins/player_cln.png",
    "КиберНет": "assets/skins/player_cp.png",
    "Против0газ": "assets/skins/player_prt.png",
    "???": "assets/skins/player_tank.png",
}

for dir_path in [JSON_DIR, SCREENSHOTS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)