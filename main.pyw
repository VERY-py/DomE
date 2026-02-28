import pygame
import sys
import os
import json
from datetime import datetime
from system.player import Player
from system.client import Client
from system.GUI import GUI


def get_player_rect(size_state):
    match size_state:
        case 1:
            return 45, 15
        case 2:
            return 15, 45
        case _:
            return 30, 30


def load_json(filename, default):
    if not os.path.exists(filename) or os.path.getsize(filename) == 0:
        data = default.copy()
        os.makedirs(os.path.dirname(filename) or '.', exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return data

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        data = default.copy()
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return data


def draw_nick(screen, font, nick, rect, color=(255, 255, 255), bg_color=None, padding=5):
    text_surface = font.render(nick, True, color)
    text_rect = text_surface.get_rect(centerx=rect.centerx, bottom=rect.top - padding)

    if bg_color:
        bg_rect = pygame.Rect(text_rect.x - 2, text_rect.y - 2, text_rect.width + 4, text_rect.height + 4)
        pygame.draw.rect(screen, bg_color, bg_rect)

    screen.blit(text_surface, text_rect)


def save_screen(screen):
    os.makedirs(str(GUI.pr_dir / "screenshots"), exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = str(GUI.pr_dir / f"screenshots/screenshot_{now}.png")
    pygame.image.save(screen, filename)


def load_level(image_path):
    img = pygame.image.load(image_path).convert_alpha()
    return pygame.mask.from_surface(img)


def load_room_assets(room):
    try:
        level_mask = load_level(str(GUI.pr_dir / f'assets/hb/{room}.png'))
        level_img = pygame.image.load(str(GUI.pr_dir / f'assets/bg/{room}_bg.png')).convert_alpha()
        on_img_path = str(GUI.pr_dir / f'assets/on_bg/{room}_bg.png')
        on_level_img = pygame.image.load(on_img_path).convert_alpha() if os.path.exists(on_img_path) else None
        return level_mask, level_img, on_level_img
    except FileNotFoundError:
        return None, None, None


def draw_remote_player(screen, font, nick, data, skin_image, output_room):
    """Отрисовка удаленного игрока только по координатам"""
    if data.get("room") == output_room:
        x, y = data["x"], data["y"]
        size_state = data.get("pl", 0)
        width, height = get_player_rect(size_state)
        rect = pygame.Rect(x, y, width, height)

        scaled_skin = pygame.transform.scale(skin_image, (width, height))
        screen.blit(scaled_skin, rect)
        draw_nick(screen, font, nick, rect)


def main():
    spawn_points = {
        "Вход в подземки": [(1, 1), (735, 749)],
        "Гора": [(3, 0), (1124, 807)],
    }

    gui = GUI(spawn_points)
    exit_code = gui.run()
    if exit_code:
        return 0
    pygame.init()

    info = pygame.display.Info()
    WIDTH, HEIGHT = info.current_w, info.current_h

    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.NOFRAME)
    pygame.display.set_caption("DomE")
    pygame.display.set_icon(pygame.image.load(str(GUI.pr_dir / 'assets/logo_dome.ico')))

    font = pygame.font.Font(None, 50)
    font_small = pygame.font.Font(None, 30)
    clock = pygame.time.Clock()
    pause_text = font.render("E - продолжить. TAB - выход.", True, (255, 255, 255))

    room_id = [1, 1]
    coords = (735, 749)
    input_data = None

    player1 = Player(coords, str(GUI.pr_dir / gui.image_path1))

    remote_skin = pygame.image.load(str(GUI.pr_dir / gui.image_path2))

    client = None
    if gui.multiplayer:
        st = {gui.name: {"x": 0, "y": 0, "room": 0, "pl": 0}}
        with open(str(GUI.pr_dir / 'json/input_info.json'), 'w', encoding='utf-8') as f:
            json.dump(st, f, indent=4, ensure_ascii=False)
        client = Client(gui.host, int(gui.port))
        try:
            client.connect()
        except ConnectionRefusedError:
            gui.multiplayer = False

    level_mask, level_img, on_level_img = load_room_assets(f'room_{room_id[0]}{room_id[1]}')
    output_room = int(f"{room_id[0]}{room_id[1]}")

    running = True
    paused = False

    while running:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if client:
                    client.send_to_server(str(GUI.pr_dir / 'json/end.json'))
                return 0
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    player1.xy()
                if event.key == pygame.K_F2:
                    save_screen(screen)

        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            paused = True
        if keys[pygame.K_TAB] and paused:
            if client:
                client.send_to_server(str(GUI.pr_dir / 'json/end.json'))
            return 0
        if keys[pygame.K_e] and paused:
            paused = False

        if not paused:
            room_x, room_y, new_room = player1.new_room(room_id[0], room_id[1])
            if new_room != f'room_{room_id[0]}{room_id[1]}':
                assets = load_room_assets(new_room)
                if assets[0] is None:
                    running = False
                    break
                level_mask, level_img, on_level_img = assets
                room_id = [room_x, room_y]
                output_room = int(f"{room_id[0]}{room_id[1]}")

            player1.update(level_mask, level_img)

            if gui.multiplayer:
                output = {
                    gui.name: {
                        "x": player1.rect.x,
                        "y": player1.rect.y,
                        "room": output_room,
                        "pl": player1.size_state,
                    }
                }
                with open(str(GUI.pr_dir / 'json/output_info.json'), 'w', encoding='utf-8') as f:
                    json.dump(output, f, indent=4, ensure_ascii=False)

                if client.send_to_server(str(GUI.pr_dir / 'json/output_info.json')):
                    running = False
                    break

                input_data = load_json(str(GUI.pr_dir / 'json/input_info.json'), {})
            else:
                input_data = None

            screen.fill((100, 100, 100))
            screen.blit(level_img, (0, 0))

            if input_data:
                for nick, data in input_data.items():
                    if nick != gui.name:
                        draw_remote_player(screen, font_small, nick, data, remote_skin, output_room)

            screen.blit(player1.image, player1.rect)
            draw_nick(screen, font_small, gui.name, player1.rect)

            if on_level_img:
                screen.blit(on_level_img, (0, 0))

        else:
            screen.fill((60, 60, 60))
            screen.blit(level_img, (0, 0))

            if input_data:
                for nick, data in input_data.items():
                    if nick != gui.name:
                        draw_remote_player(screen, font_small, nick, data, remote_skin, output_room)

            screen.blit(player1.image, player1.rect)
            draw_nick(screen, font_small, gui.name, player1.rect)

            if on_level_img:
                screen.blit(on_level_img, (0, 0))

            text_rect = pause_text.get_rect(center=(WIDTH // 2, HEIGHT - 100))
            screen.blit(pause_text, text_rect)

        pygame.display.flip()

    pygame.quit()
    return 0


if __name__ == '__main__':
    sys.exit(main())