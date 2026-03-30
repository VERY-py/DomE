import pygame
import sys
import json
from datetime import datetime
from typing import Optional, Dict, Tuple

from system.player import Player
from system.client import Client
from system.GUI import GUI
from system.objects import Door, PhysikSq
import config


class GameResources:
    """Кэш для игровых ресурсов"""
    _room_cache: Dict[str, Tuple[pygame.mask.Mask, pygame.Surface, Optional[pygame.Surface]]] = {}
    _skin_cache: Dict[str, pygame.Surface] = {}
    _custom_cursor: Optional[pygame.Surface] = None

    @classmethod
    def load_room_assets(cls, room_name: str) -> Tuple[Optional[pygame.mask.Mask], Optional[pygame.Surface], Optional[pygame.Surface]]:
        """Загружает ресурсы комнаты с кэшированием"""
        if room_name in cls._room_cache:
            return cls._room_cache[room_name]

        try:
            mask_path = config.HB_DIR / f"{room_name}.png"
            bg_path = config.BG_DIR / f"{room_name}_bg.png"
            on_bg_path = config.ON_BG_DIR / f"{room_name}_bg.png"

            level_mask = pygame.mask.from_surface(pygame.image.load(str(mask_path)).convert_alpha())
            level_img = pygame.image.load(str(bg_path)).convert_alpha()
            on_level_img = pygame.image.load(str(on_bg_path)).convert_alpha() if on_bg_path.exists() else None

            assets = (level_mask, level_img, on_level_img)
            cls._room_cache[room_name] = assets
            return assets
        except FileNotFoundError as e:
            print(f"Ошибка загрузки комнаты {room_name}: {e}")
            return None, None, None

    @classmethod
    def get_skin(cls, skin_path: str, size: Tuple[int, int] = (config.PLAYER_SIZE, config.PLAYER_SIZE)) -> pygame.Surface:
        """Загружает и масштабирует скин с кэшированием"""
        cache_key = f"{skin_path}_{size[0]}_{size[1]}"
        if cache_key in cls._skin_cache:
            return cls._skin_cache[cache_key].copy()

        try:
            original = pygame.image.load(str(config.PR_DIR / skin_path)).convert_alpha()
            scaled = pygame.transform.scale(original, size)
            cls._skin_cache[cache_key] = scaled
            return scaled.copy()
        except FileNotFoundError:
            default_path = str(config.SKINS_DIR / "player_st.png")
            original = pygame.image.load(default_path).convert_alpha()
            scaled = pygame.transform.scale(original, size)
            cls._skin_cache[cache_key] = scaled
            return scaled.copy()

    @classmethod
    def load_custom_cursor(cls) -> Optional[pygame.Surface]:
        """Загружает пользовательский курсор"""
        if cls._custom_cursor is not None:
            return cls._custom_cursor

        cursor_path = config.ASSETS_DIR / "cursor.png"
        try:
            cursor_img = pygame.image.load(str(cursor_path)).convert_alpha()
            cls._custom_cursor = pygame.transform.scale(cursor_img, (24, 24))
            return cls._custom_cursor
        except FileNotFoundError:
            return None

    @classmethod
    def clear_cache(cls):
        """Очищает кэш (использовать при смене уровня)"""
        cls._room_cache.clear()


def load_json(filename: str, default: Dict) -> Dict:
    """Безопасная загрузка JSON с обработкой ошибок"""
    filepath = config.JSON_DIR / filename
    try:
        if filepath.exists() and filepath.stat().st_size > 0:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
    except (json.JSONDecodeError, OSError):
        pass

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(default, f, indent=2, ensure_ascii=False)
    return default.copy()


def save_json(filename: str, data: Dict) -> None:
    """Безопасное сохранение JSON"""
    filepath = config.JSON_DIR / filename
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except OSError as e:
        print(f"Ошибка сохранения {filename}: {e}")


def draw_nick(screen: pygame.Surface, font: pygame.font.Font, nick: str,
              rect: pygame.Rect, color=(255, 255, 255), bg_color=None, padding=5) -> None:
    """Отрисовка ника над игроком"""
    text_surface = font.render(nick, True, color)
    text_rect = text_surface.get_rect(centerx=rect.centerx, bottom=rect.top - padding)

    if bg_color:
        bg_rect = pygame.Rect(text_rect.x - 2, text_rect.y - 2,
                              text_rect.width + 4, text_rect.height + 4)
        pygame.draw.rect(screen, bg_color, bg_rect)

    screen.blit(text_surface, text_rect)


def save_screenshot(screen: pygame.Surface) -> None:
    """Сохранение скриншота"""
    config.SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = config.SCREENSHOTS_DIR / f"screenshot_{timestamp}.png"
    pygame.image.save(screen, str(filename))
    print(f"Скриншот сохранён: {filename}")


def draw_remote_player(screen: pygame.Surface, font: pygame.font.Font, nick: str,
                       data: Dict, skin_scaled: pygame.Surface, current_room: int) -> None:
    """Отрисовка удалённого игрока"""
    if data.get("room") != current_room:
        return

    rect = pygame.Rect(data["x"], data["y"], config.PLAYER_SIZE, config.PLAYER_SIZE)
    screen.blit(skin_scaled, rect)
    draw_nick(screen, font, nick, rect)


def create_physics_square(rect_coords: pygame.Rect, room_coords: list,
                          width: int, height: int, mass: float = 1.0) -> PhysikSq:
    """Создание физического квадрата с правильной маской"""
    room_str = f'room_{room_coords[0]}{room_coords[1]}'
    level_mask, _, _ = GameResources.load_room_assets(room_str)

    if level_mask is None:
        level_mask = pygame.mask.Mask((width, height), fill=False)

    room_rect = pygame.Rect(0, 0, width, height)
    return PhysikSq(rect_coords, (room_rect, room_coords), color=(255, 0, 0),
                    level_mask=level_mask, mass=mass)


class GameState:
    """Управление состоянием игры"""
    def __init__(self, gui: GUI):
        self.gui = gui
        self.running = True
        self.paused = False

        info = pygame.display.Info()
        self.screen_width = info.current_w
        self.screen_height = info.current_h
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.NOFRAME)
        pygame.display.set_caption("CUBE")

        self.custom_cursor = GameResources.load_custom_cursor()
        pygame.mouse.set_visible(self.custom_cursor is None)

        self.font_big = pygame.font.Font(None, 50)
        self.font_small = pygame.font.Font(None, 30)

        self.pause_text = self.font_big.render("TAB - продолжить. ESC - выход.", True, (255, 255, 255))

        self.player = Player(
            (735, 749),
            [1, 1],
            str(config.PR_DIR / gui.image_path1)
        )

        self.remote_skin_scaled = GameResources.get_skin(gui.image_path2, (config.PLAYER_SIZE, config.PLAYER_SIZE))

        self.client = None
        if gui.multiplayer:
            save_json('input_info.json', {gui.name: {"x": 0, "y": 0, "room": 0}})
            self.client = Client(gui.host, int(gui.port))
            try:
                self.client.connect()
            except ConnectionRefusedError:
                print("Не удалось подключиться к серверу")
                gui.multiplayer = False
                self.client = None

        self.room_id = [1, 1]
        self.current_room_name = f'room_{self.room_id[0]}{self.room_id[1]}'
        self.output_room = int(self.current_room_name[5:])

        self.level_mask, self.level_img, self.on_level_img = GameResources.load_room_assets(self.current_room_name)

        self.squares = []
        squares_data = [
            (pygame.Rect(70, 30, 30, 30), [1, 1]),
            (pygame.Rect(370, 30, 30, 30), [1, 1]),
            (pygame.Rect(250, 70, 30, 30), [1, 1])
        ]
        for rect_coords, room_coords in squares_data:
            sq = create_physics_square(rect_coords, room_coords, self.screen_width, self.screen_height)
            self.squares.append(sq)

        self.doors = []
        doors_data = [
            [(717, 520, 10, 79), [2, 1]], [(912, 520, 10, 79), [2, 1]],
            [(1143, 520, 10, 79), [2, 1]], [(1426, 546, 10, 53), [2, 1]],
            [(1495, 547, 10, 52), [2, 1]], [(1425, 470, 10, 40), [2, 1]],
            [(1425, 381, 10, 47), [2, 1]], [(1425, 301, 10, 48), [2, 1]],
        ]
        for door_rect, room in doors_data:
            self.doors.append(Door(pygame.Rect(door_rect), room))

        self.held_square = None

    def handle_events(self) -> bool:
        """Обработка событий"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F2:
                    save_screenshot(self.screen)
                elif event.key == pygame.K_ESCAPE and self.paused:
                    return False
                elif event.key == pygame.K_TAB and self.paused:
                    self.paused = False
                elif event.key == pygame.K_ESCAPE:
                    self.paused = True
                elif event.key == pygame.K_f and not self.paused:
                    self._handle_pickup_throw()

            if event.type == pygame.MOUSEBUTTONDOWN and not self.paused and self.held_square is not None:
                self._handle_throw(event.button)

        return True

    def _handle_pickup_throw(self) -> None:
        """Поднятие/бросок предмета"""
        if self.held_square is not None:
            self.held_square.drop(self.player, throw=False)
            self.held_square = None
        else:
            closest_sq = None
            min_distance = 50
            for sq in self.squares:
                if not sq.is_held:
                    distance = sq.get_distance_to_player(self.player)
                    if distance < min_distance:
                        min_distance = distance
                        closest_sq = sq
            if closest_sq:
                closest_sq.pick_up(self.player)
                self.held_square = closest_sq

    def _handle_throw(self, button: int) -> None:
        """Бросок предмета"""
        mouse_x, mouse_y = pygame.mouse.get_pos()
        dx = mouse_x - self.player.rect.centerx
        dy = mouse_y - self.player.rect.centery
        length = (dx**2 + dy**2)**0.5

        if length == 0:
            dx, dy = 1, 0
            length = 1

        norm_dx = dx / length
        norm_dy = dy / length
        force = 7 if button == 1 else 3 if button == 3 else None

        if force:
            vel_x = norm_dx * force
            vel_y = norm_dy * force
            self.held_square.drop(self.player, throw_velocity=(vel_x, vel_y))
            self.held_square = None

    def update_room(self) -> None:
        """Обновление комнаты при переходе"""
        room_x, room_y, new_room = self.player.new_room(self.room_id[0], self.room_id[1])

        if new_room != self.current_room_name:
            assets = GameResources.load_room_assets(new_room)
            if assets[0] is None:
                self.running = False
                return

            self.level_mask, self.level_img, self.on_level_img = assets
            self.room_id = [room_x, room_y]
            self.current_room_name = new_room
            self.output_room = int(f"{self.room_id[0]}{self.room_id[1]}")

    def update_physics(self, dt: float) -> None:
        """Обновление физики"""
        self.player.update(dt, self.level_mask, self.level_img, self.doors, physics_objects=self.squares)

        for sq in self.squares:
            sq.update(self.player, self.squares)
            if not sq.is_held:
                sq.resolve_collision_with_player(self.player)

    def update_network(self) -> Optional[Dict]:
        """Обновление сетевого взаимодействия"""
        if not self.client:
            return None

        output = {
            self.gui.name: {
                "x": self.player.rect.x,
                "y": self.player.rect.y,
                "room": self.output_room,
            }
        }
        save_json('output_info.json', output)

        if self.client.send_to_file(str(config.JSON_DIR / 'output_info.json')):
            self.running = False
            return None

        return load_json('input_info.json', {})

    def draw(self, input_data: Optional[Dict] = None) -> None:
        """Отрисовка игрового мира"""
        self.screen.fill((100, 100, 100))
        self.screen.blit(self.level_img, (0, 0))

        if input_data:
            for nick, data in input_data.items():
                if nick != self.gui.name:
                    draw_remote_player(self.screen, self.font_small, nick, data,
                                      self.remote_skin_scaled, self.output_room)

        self.screen.blit(self.player.image, self.player.rect)

        for sq in self.squares:
            sq.draw(self.screen, self.player.room)

        for door in self.doors:
            if door.room == self.room_id:
                door.draw(self.screen)

        if self.on_level_img:
            self.screen.blit(self.on_level_img, (0, 0))

        draw_nick(self.screen, self.font_small, self.gui.name, self.player.rect)

        if self.custom_cursor:
            self.screen.blit(self.custom_cursor, pygame.mouse.get_pos())

    def draw_paused(self, input_data: Optional[Dict] = None) -> None:
        """Отрисовка в режиме паузы"""
        self.draw(input_data)

        text_rect = self.pause_text.get_rect(center=(self.screen_width // 2, self.screen_height - 100))
        self.screen.blit(self.pause_text, text_rect)

    def run(self) -> bool:
        """Главный игровой цикл"""
        clock = pygame.time.Clock()

        while self.running:
            dt = clock.tick(config.FPS) / 1000.0

            if not self.handle_events():
                break

            if not self.paused:
                self.update_room()
                if not self.running:
                    break

                self.update_physics(dt)

                input_data = self.update_network()
                if not self.running:
                    break

                self.draw(input_data)
            else:
                input_data = load_json('input_info.json', {}) if self.client else None
                self.draw_paused(input_data)

            pygame.display.flip()

        return True


def main() -> int:
    """Точка входа в игру"""
    gui = GUI()
    if gui.run():
        return 0

    pygame.init()
    try:
        game = GameState(gui)
        game.run()
    finally:
        pygame.mouse.set_visible(True)
        pygame.quit()

    return 0


if __name__ == '__main__':
    sys.exit(main())