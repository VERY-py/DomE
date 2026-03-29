import pygame
import sys
import os
import json
from datetime import datetime
from system.player import Player
from system.client import Client
from system.GUI import GUI, FPS
from system.objects import Door, PhysikSq
from system.anim_player import Animation


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


def create_square(rect_coords, room_coords, width, height):
    """Создает квадрат с правильной маской для его комнаты"""
    wrect = pygame.Rect(0, 0, width, height)
    rooma = (wrect, room_coords)

    room_str = f'room_{room_coords[0]}{room_coords[1]}'
    sq_level_mask, _, _ = load_room_assets(room_str)

    if sq_level_mask is None:
        sq_level_mask = pygame.mask.Mask((width, height), fill=False)

    return PhysikSq(rect_coords, rooma, color=(255, 0, 0), level_mask=sq_level_mask)

def load_custom_cursor():
    """Загружает пользовательский курсор из файла."""
    cursor_path = str(GUI.pr_dir / 'assets/cursor.png')
    try:
        cursor_img = pygame.image.load(cursor_path).convert_alpha()
        cursor_img = pygame.transform.scale(cursor_img, (24, 24))
        return cursor_img
    except FileNotFoundError:
        return None

def main():
    gui = GUI()
    exit_code = gui.run()
    if exit_code:
        return 0
    pygame.init()

    info = pygame.display.Info()
    WIDTH, HEIGHT = info.current_w, info.current_h

    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.NOFRAME)
    pygame.display.set_caption("DomE")
    pygame.display.set_icon(pygame.image.load(str(GUI.pr_dir / 'assets/logo_dome.ico')))

    custom_cursor = load_custom_cursor()
    if custom_cursor:
        pygame.mouse.set_visible(False)
    else:
        pygame.mouse.set_visible(True)

    font = pygame.font.Font(None, 50)
    font_small = pygame.font.Font(None, 30)
    clock = pygame.time.Clock()
    pause_text = font.render("TAB - продолжить. ESC - выход.", True, (255, 255, 255))

    room_id = [1, 1]
    coords = (735, 749)
    input_data = None

    heart_anim = Animation(str(GUI.pr_dir / 'assets/anim/heart'), fps=5)

    player1 = Player(coords, room_id, str(GUI.pr_dir / gui.image_path1))

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

    squares_data = [
        (pygame.Rect(70, 30, 30, 30), [1, 1]),
        (pygame.Rect(370, 30, 30, 30), [1, 1])
    ]

    sqs = []
    for rect_coords, room_coords in squares_data:
        sq = create_square(rect_coords, room_coords, WIDTH, HEIGHT)
        sqs.append(sq)

    pos_doors = [
        [(717, 520, 10, 79), [2, 1]],
        [(912, 520, 10, 79), [2, 1]],
        [(1143, 520, 10, 79), [2, 1]],
        [(1426, 546, 10, 53), [2, 1]],
        [(1495, 547, 10, 52), [2, 1]],
        [(1425, 470, 10, 40), [2, 1]],
        [(1425, 381, 10, 47), [2, 1]],
        [(1425, 301, 10, 48), [2, 1]],
    ]
    doors = []
    for door in pos_doors:
        doors.append(Door(pygame.Rect(door[0]), door[1]))

    held_square = None

    running = True
    paused = False


    while running:
        dt = clock.tick(FPS) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if client:
                    client.send_to_server(str(GUI.pr_dir / 'json/end.json'))
                return 0
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    player1.xy()
                    print(f"mouse: {pygame.mouse.get_pos()}")
                if event.key == pygame.K_F2:
                    save_screen(screen)
                if event.key == pygame.K_f and not paused:
                    if held_square is not None:
                        held_square.drop(player1, throw=False)
                        held_square = None
                    else:
                        closest_sq = None
                        min_distance = 50
                        for sq in sqs:
                            if not sq.is_held:
                                distance = sq.get_distance_to_player(player1)
                                if distance < min_distance:
                                    min_distance = distance
                                    closest_sq = sq
                        if closest_sq:
                            closest_sq.pick_up(player1)
                            held_square = closest_sq
                if event.key == pygame.K_ESCAPE and paused:
                    if client:
                        client.send_to_server(str(GUI.pr_dir / 'json/end.json'))
                    return 0
                elif event.key == pygame.K_TAB and paused:
                    paused = False
                elif event.key == pygame.K_ESCAPE:
                    paused = True

            if event.type == pygame.MOUSEBUTTONDOWN and not paused:
                if held_square is not None:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    dx = mouse_x - player1.rect.centerx
                    dy = mouse_y - player1.rect.centery
                    length = (dx**2 + dy**2)**0.5
                    if length == 0:
                        dx, dy = 1, 0
                        length = 1

                    norm_dx = dx / length
                    norm_dy = dy / length

                    if event.button == 1:
                        force = 7
                    elif event.button == 3:
                        force = 3
                    else:
                        continue

                    vel_x = norm_dx * force
                    vel_y = norm_dy * force

                    held_square.drop(player1, throw_velocity=(vel_x, vel_y))
                    held_square = None

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

                for sq in sqs:
                    sq.level_mask = level_mask

            player1.update(level_mask, level_img, doors, physics_objects=sqs)

            for sq in sqs:
                sq.update(player1, all_objects=sqs)
                if not sq.is_held:
                    sq.resolve_collision_with_player(player1)

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

            if heart_anim.update(dt):
                heart_anim.play(screen, (int(player1.rect.x + 10), int(player1.rect.y + 10)))

            for sq in sqs:
                sq.draw(screen, player1.room)

            for door in doors:
                if door.room == room_id:
                    door.draw(screen)

            if on_level_img:
                screen.blit(on_level_img, (0, 0))

            draw_nick(screen, font_small, gui.name, player1.rect)

            if custom_cursor:
                mouse_pos = pygame.mouse.get_pos()
                screen.blit(custom_cursor, mouse_pos)

        else:
            screen.fill((60, 60, 60))
            screen.blit(level_img, (0, 0))

            if input_data:
                for nick, data in input_data.items():
                    if nick != gui.name:
                        draw_remote_player(screen, font_small, nick, data, remote_skin, output_room)

            screen.blit(player1.image, player1.rect)

            if heart_anim.update(dt):
                heart_anim.play(screen, (int(player1.rect.x + 10), int(player1.rect.y + 10)))

            for sq in sqs:
                sq.draw(screen, player1.room)

            draw_nick(screen, font_small, gui.name, player1.rect)

            if on_level_img:
                screen.blit(on_level_img, (0, 0))

            for door in doors:
                if door.room == room_id:
                    door.draw(screen)

            text_rect = pause_text.get_rect(center=(WIDTH // 2, HEIGHT - 100))
            screen.blit(pause_text, text_rect)

            if custom_cursor:
                mouse_pos = pygame.mouse.get_pos()
                screen.blit(custom_cursor, mouse_pos)

        pygame.display.flip()

    pygame.mouse.set_visible(True)
    pygame.quit()
    return 0


if __name__ == '__main__':
    sys.exit(main())