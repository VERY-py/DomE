import pygame
import sys
import os
import json
from datetime import datetime
from system.player import Player
from system.client import Client
from system.GUI import GUI

def get_player_rect(size_state):
    """Возвращает pygame.Rect в зависимости от size_state"""
    if size_state == 1:
        return 45, 15
    elif size_state == 2:
        return 15, 45
    else:
        return 30, 30

def load_json(filename, default):
    """Возвращает данные или default, создает файл если нужно"""
    if not os.path.exists(filename) or os.path.getsize(filename) == 0:
        data = default.copy()
        os.makedirs(os.path.dirname(filename) or '.', exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"📝 Создан {filename}")
        return data

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError:
        print(f"🔧 Исправлен поврежденный {filename}")
        data = default.copy()
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return data

def draw_nick(screen, font, nick, rect, color=(255, 255, 255), bg_color=None, padding=5):
    """Рисует ник над квадратом"""
    text_surface = font.render(nick, True, color)
    text_rect = text_surface.get_rect()

    text_rect.centerx = rect.centerx

    text_rect.bottom = rect.top - padding

    if bg_color:
        bg_rect = pygame.Rect(
            text_rect.x - 2,
            text_rect.y - 2,
            text_rect.width + 4,
            text_rect.height + 4
        )
        pygame.draw.rect(screen, bg_color, bg_rect)

    screen.blit(text_surface, text_rect)

def save_screen(screen):
    os.makedirs("screenshots", exist_ok=True)

    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"screenshots/screenshot_{now}.png"

    pygame.image.save(screen, filename)
    print(f"Скриншот сохранён: {filename}")

def load_level(image_path):
    img = pygame.image.load(image_path).convert_alpha()
    level_mask = pygame.mask.from_surface(img)
    return level_mask

def main():
    global client, output, chat, GRAVITY, PRESETS_FILE, DEFAULT_DIR, nmb_scr
    err = 1
    GRAVITY = 0.7
    nmb_scr = 1
    spawn_points = {
        "Вход в подземки": [(1, 1), (735, 749)],
        "Гора": [(3, 0), (1124, 807)],
    }
    gui = GUI(spawn_points)
    exit = gui.run()
    if exit:
        return 0
    pygame.init()
    info = pygame.display.Info()
    WIDTH, HEIGHT = info.current_w, info.current_h
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.NOFRAME)
    pygame.display.set_caption("DomE")
    ico = pygame.image.load('assets/logo_dome.ico')
    PRESETS_FILE = "json/presets.json"
    DEFAULT_DIR = os.path.expanduser("~")
    pygame.display.set_icon(ico)
    font = pygame.font.Font(None, 50)
    font1 = pygame.font.Font(None, 30)
    clock = pygame.time.Clock()
    room_id = [1, 1]
    coords = [735, 749]
    player1 = Player(coords, gui.image_path1)
    player2 = Player(coords, gui.image_path2,
        A=pygame.K_KP4,
        D=pygame.K_KP6,
        W=pygame.K_KP8,
        S=pygame.K_KP5,
        E=pygame.K_KP9,
        SHIFT=pygame.K_UP,
        CTRL=pygame.K_LEFT,
        SPACE=pygame.K_KP_ENTER)
    room_x, room_y = room_id
    room = f'room_{room_x}{room_y}'
    level_mask = load_level(f'assets/hb/{room}.png')
    level_img = pygame.image.load(f'assets/bg/{room}_bg.png').convert_alpha()
    text = font.render("E - продолжить. TAB - выход.", True, (255, 255, 255))

    st = {
    "": {
        "x": 0,
        "y": 0,
        "room": 00,
        "pl": 0,
         }
    }

    if gui.multiplayer:
        with open('json/input_info.json', 'w', encoding='utf-8') as f:
            json.dump(st, f, indent=4, ensure_ascii=False)
        client = Client(gui.host, int(gui.port))
        try:
            client.connect()
        except ConnectionRefusedError:
            gui.multiplayer = False

    running = True
    stop = False
    abs_run = True
    while abs_run:
        while running:
            clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    client.send_to_server('json/end.json')
                    running = False
                    stop = False
                    abs_run = False
                    err = 0
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        player1.xy()
                        player2.xy()
                    if event.key == pygame.K_F2:
                        save_screen(screen)
            keys = pygame.key.get_pressed()
            if keys[pygame.K_ESCAPE]:
                running = False
                stop = True

            a = True
            room_x, room_y, new_room = player1.new_room(room_x, room_y)
            if new_room != room:
                a = False
                try:
                    room = new_room
                    level_mask = load_level(f'assets/hb/{new_room}.png')
                    level_img = pygame.image.load(f'assets/bg/{new_room}_bg.png').convert_alpha()
                    player2.rect.topleft = player1.rect.topleft
                except FileNotFoundError:
                    running = False
                    stop = True

            if a:
                room_x, room_y, new_room = player2.new_room(room_x, room_y)
                if new_room != room:
                    try:
                        room = new_room
                        level_mask = load_level(f'assets/hb/{new_room}.png')
                        level_img = pygame.image.load(f'assets/bg/{new_room}_bg.png').convert_alpha()
                        player2.rect.topleft = player1.rect.topleft
                    except FileNotFoundError:
                        running = False
                        stop = True

            player1.update(level_mask, level_img)
            player2.update(level_mask, level_img)

            screen.fill((100, 100, 100))
            screen.blit(level_img, (0, 0))

            if gui.multiplayer:
                output = {
                    f"{gui.name}": {
                        "x": player1.rect.x,
                        "y": player1.rect.y,
                        "room": int(f"{room_x}{room_y}"),
                        "pl" : player1.size_state,
                    }
                }
                with open('json/output_info.json', 'w', encoding='utf-8') as f:
                    json.dump(output, f, indent=4, ensure_ascii=False)

                c = client.send_to_server('json/output_info.json')
                if c:
                    running = False
                    stop = True
                input = load_json('json/input_info.json', {"nicks": {}})

                for nick in input.keys():
                    try:
                        if input[nick]["room"] == output[gui.name]["room"]:
                            crd = get_player_rect(input[nick]["pl"])
                            player2.new_pl_size(crd)
                            rect2 = pygame.Rect(input[nick]["x"],
                                                input[nick]["y"],
                                                player2.rect.width,
                                                player2.rect.height)
                            screen.blit(player2.image, rect2)
                            draw_nick(screen, font1, nick, rect2)
                        else:
                            screen.blit(player1.image, player1.rect)
                    except KeyError:
                        pass

                draw_nick(screen, font1, gui.name, player1.rect)
            else:
                screen.blit(player2.image, player2.rect)

            screen.blit(player1.image, player1.rect)

            pygame.display.flip()

        while stop:
            clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    stop = False
                    abs_run = False
                    client.send_to_server('json/end.json')
                    err = 0
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        player1.xy()
                        player2.xy()
            keys = pygame.key.get_pressed()
            if keys[pygame.K_TAB]:
                running = False
                stop = False
                abs_run = False
                client.send_to_server('json/end.json')
                err = 0
            elif keys[pygame.K_e]:
                running = True
                stop = False

            screen.fill((60, 60, 60))
            screen.blit(level_img, (0, 0))
            if gui.multiplayer:
                input = load_json('json/input_info.json', {"nicks": {}})

                for nick in input.keys():
                    try:
                        if input[nick]["room"] == output[gui.name]["room"]:
                            rect2 = pygame.Rect(input[nick]["x"], input[nick]["y"], 30, 30)
                            screen.blit(player2.image, (input[nick]["x"], input[nick]["y"]))
                            draw_nick(screen, font1, nick, rect2)
                        else:
                            screen.blit(player1.image, player1.rect)
                    except KeyError:
                        pass

                draw_nick(screen, font1, gui.name, player1.rect)
            else:
                screen.blit(player2.image, player2.rect)

            screen.blit(player1.image, player1.rect)

            screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT - 100))
            pygame.display.flip()

    pygame.quit()
    return err

if __name__ == '__main__':
    exit_code = main()
    print(f"Exit code {exit_code}")
    sys.exit()