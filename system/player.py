import pygame
from typing import Tuple, Dict, Optional


class Player(pygame.sprite.Sprite):
    def __init__(
            self,
            pos: Tuple[int, int],
            skin_path: str,
            keys: Dict[str, int] = None,
            spawn_positions: Optional[Dict[Tuple[str, str], Tuple[int, int]]] = None
    ):
        super().__init__()
        self._init_pygame_once()

        default_keys = {
            'left': pygame.K_a, 'right': pygame.K_d, 'up': pygame.K_w, 'down': pygame.K_s,
            'size_small': pygame.K_e, 'shift': pygame.K_LSHIFT, 'ctrl': pygame.K_LCTRL,
            'jump': pygame.K_SPACE
        }
        self.keys = default_keys.copy()
        if keys:
            self.keys.update(keys)

        self.spawn_positions = {
            ('room_11', 'room_21'): (125, 978),
            ('room_21', 'room_11'): (1700, 749),
            ('room_21', 'room_31'): (120, 849),
            ('room_31', 'room_21'): (1749, 978),
            ('room_31', 'room_30'): (447, 1044),
            ('room_30', 'room_31'): (1666, 34),
            ('room_12', 'room_11'): (76, 1003),
            ('room_11', 'room_12'): (16, 412),
        }

        self.create(pos, skin_path)

    def _init_pygame_once(self):
        """Инициализация Pygame только один раз для всех игроков"""
        if not hasattr(self, '_pygame_initialized'):
            pygame.init()
            self._pygame_initialized = True

    def create(self, pos: Tuple[int, int], skin_path: str):
        """Основной метод создания игрока"""
        self.original_image = pygame.image.load(skin_path)
        self.image = pygame.transform.scale(self.original_image, (30, 30))
        self.rect = self.image.get_rect(topleft=pos)
        self.mask = pygame.mask.from_surface(self.image)

        self.vel = pygame.math.Vector2(0, 0)
        self.speed = 5
        self.jump_power = 12
        self.gravity = 0.7
        self.on_ground = False
        self.can_wall_jump = False
        self.wall_jump_dir = 0
        self.wall_jump_timer = 0
        self.wall_jump_timer_max = 14

        self.coyote_time = 0
        self.coyote_time_max = 4 # Длительность Coyote Time (кадров)
        self.was_on_ground = False

        self.size_state = 0
        self.prev_keys = {}
        self.last_direction = 1

        self.health = 100
        self.max_health = 100
        self.fall_height = 0
        self.shoot_cooldown = 0
        self.projectiles = []
        self.damage_cooldown = 0

    @classmethod
    def from_preset(cls, preset_name: str, pos: Tuple[int, int], skin_path: str):
        """Создание игрока с предустановленными настройками"""
        presets = {
            'default': {},
            'hardcore': {'jump_power': 10, 'speed': 4},
            'speedrunner': {'speed': 8, 'jump_power': 14}
        }

        preset_keys = presets.get(preset_name, {})
        return cls(pos, skin_path, keys=preset_keys)

    def recreate(self, pos: Optional[Tuple[int, int]] = None, skin_path: Optional[str] = None):
        """Пересоздание игрока (респавн)"""
        if pos:
            self.rect.topleft = pos
        if skin_path:
            self.original_image = pygame.image.load(skin_path)

        self.vel = pygame.math.Vector2(0, 0)
        self.on_ground = False
        self.can_wall_jump = False
        self.wall_jump_timer = 0
        self.size_state = 0
        self.coyote_time = 0
        self.health = self.max_health
        self.image = pygame.transform.scale(self.original_image, (30, 30))
        self.mask = pygame.mask.from_surface(self.image)

    def toggle_size(self, key):
        if key == self.keys['down']:
            self.size_state = 1
        elif key == self.keys['up']:
            self.size_state = 2
        elif key == self.keys['size_small']:
            self.size_state = 0

    def move_and_collide(self, level_mask):
        step_x = 1 if self.vel.x > 0 else -1 if self.vel.x < 0 else 0
        self.can_wall_jump = False

        for _ in range(abs(int(self.vel.x))):
            self.rect.x += step_x
            if level_mask.overlap(self.mask, (self.rect.x, self.rect.y)):
                max_climb = 30
                climbed = False
                for climb_height in range(1, max_climb + 1):
                    self.rect.y -= 1
                    if not level_mask.overlap(self.mask, (self.rect.x, self.rect.y)):
                        climbed = True
                        break
                if not climbed:
                    self.rect.y += climb_height
                    self.rect.x -= step_x
                    self.vel.x = 0
                    self.can_wall_jump = True
                    self.wall_jump_dir = -step_x
                    break

        step_y = 1 if self.vel.y > 0 else -1 if self.vel.y < 0 else 0
        for _ in range(abs(int(self.vel.y))):
            self.rect.y += step_y
            if level_mask.overlap(self.mask, (self.rect.x, self.rect.y)):
                self.rect.y -= step_y
                if step_y > 0:
                    self.on_ground = True
                self.vel.y = 0
                break
        else:
            self.on_ground = False

    def new_pl_size(self, new_size):
        old_bottom = self.rect.bottom
        topleft = self.rect.topleft

        self.image = pygame.transform.scale(self.original_image, new_size)
        self.rect = self.image.get_rect()
        self.rect.topleft = topleft
        self.mask = pygame.mask.from_surface(self.image)
        self.rect.bottom = old_bottom

    def update(self, level_mask, level_surface):
        keys = pygame.key.get_pressed()

        for k in (self.keys['down'], self.keys['up'], self.keys['size_small']):
            if keys[k] and not self.prev_keys.get(k, False):
                self.toggle_size(k)

        for k in (self.keys['down'], self.keys['up'], self.keys['size_small']):
            self.prev_keys[k] = keys[k]

        if self.size_state == 1:
            new_size = (45, 15)
        elif self.size_state == 2:
            new_size = (15, 45)
        else:
            new_size = (30, 30)

        if self.image.get_size() != new_size:
            self.new_pl_size(new_size)

        while level_mask.overlap(self.mask, (self.rect.x, self.rect.y)):
            self.rect.y -= 1

        target_vel_x = 0
        if self.wall_jump_timer > 0:
            self.wall_jump_timer -= 1
        else:
            if keys[self.keys['left']]:
                target_vel_x = -self.speed
                self.last_direction = -1
            elif keys[self.keys['right']]:
                target_vel_x = self.speed
                self.last_direction = 1
            self.vel.x = target_vel_x

        self.vel.y += self.gravity

        # Обновляем состояние платформенности ПЕРЕД проверкой прыжка
        prev_on_ground = self.on_ground

        self.move_and_collide(level_mask)

        # Логика Coyote Time - обновляем только после move_and_collide
        if self.on_ground:
            self.coyote_time = self.coyote_time_max
        elif prev_on_ground:  # Только если только что покинули землю
            self.coyote_time = self.coyote_time_max  # Начинаем отсчет
        else:
            # Продолжаем уменьшать только если уже в воздухе
            self.coyote_time = max(0, self.coyote_time - 1)

        # Проверка прыжка
        if keys[self.keys['jump']] and (self.on_ground or self.coyote_time > 0) and self.vel.y >= 0:
            self.vel.y = -self.jump_power
            self.coyote_time = 0  # Сбрасываем сразу после прыжка
            self.on_ground = False

        if keys[self.keys['jump']] and self.can_wall_jump and not self.on_ground:
            self.vel.y = -self.jump_power
            self.vel.x = self.wall_jump_dir * self.speed * 1.5
            self.wall_jump_timer = self.wall_jump_timer_max

        image1 = pygame.transform.scale(self.original_image, new_size)
        if self.last_direction == -1:
            self.image = pygame.transform.flip(image1, True, False)
        else:
            self.image = image1.copy()

    def xy(self):
        print(f'{self.rect.x}, {self.rect.y} 1')

    def new_room(self, room_x, room_y):
        info = pygame.display.Info()
        old_room = f'room_{room_x}{room_y}'
        new_room_x, new_room_y = room_x, room_y

        if self.rect.x > info.current_w:
            new_room_x += 1
        elif self.rect.x < 0:
            new_room_x -= 1
        elif self.rect.y > info.current_h:
            new_room_y += 1
        elif self.rect.y < 0:
            new_room_y -= 1

        room = f'room_{new_room_x}{new_room_y}'
        pos_key = (old_room, room)

        if pos_key in self.spawn_positions:
            self.rect.x, self.rect.y = self.spawn_positions[pos_key]
        return new_room_x, new_room_y, room
