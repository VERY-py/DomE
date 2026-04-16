import pygame
from typing import Tuple, Dict, Optional, List, TYPE_CHECKING

import config

if TYPE_CHECKING:
    from system.physics_figure import PhysicFigure


class Player(pygame.sprite.Sprite):
    """Класс игрока"""

    def __init__(
            self,
            pos: Tuple[int, int],
            room_id: List[int],
            skin_path: str,
            keys: Optional[Dict[str, int]] = None,
            spawn_positions: Optional[Dict[Tuple[str, str], Tuple[int, int]]] = None
    ):
        super().__init__()
        self._init_pygame_once()

        self.keys = {
            'left': pygame.K_a, 'right': pygame.K_d, 'up': pygame.K_w, 'down': pygame.K_s,
            'shift': pygame.K_LSHIFT, 'ctrl': pygame.K_LCTRL, 'jump': pygame.K_SPACE
        }
        if keys:
            self.keys.update(keys)

        self.spawn_positions = spawn_positions or {
            ('room_11', 'room_21'): (125, 978),
            ('room_21', 'room_11'): (1700, 749),
            ('room_21', 'room_31'): (120, 849),
            ('room_31', 'room_21'): (1749, 978),
            ('room_31', 'room_30'): (447, 1044),
            ('room_30', 'room_31'): (1666, 34),
            ('room_12', 'room_11'): (76, 1003),
            ('room_11', 'room_12'): (16, 412),
        }

        self._create(pos, room_id, skin_path)

    def _init_pygame_once(self) -> None:
        """Инициализация Pygame"""
        if not hasattr(self, '_pygame_initialized'):
            pygame.init()
            self._pygame_initialized = True

    def _create(self, pos: Tuple[int, int], room: List[int], skin_path: str) -> None:
        """Создание игрока"""
        self.original_image = pygame.image.load(skin_path).convert_alpha()
        self.image = pygame.transform.scale(self.original_image, (config.PLAYER_SIZE, config.PLAYER_SIZE))
        self.rect = self.image.get_rect(topleft=pos)
        self.mask = pygame.mask.from_surface(self.image)

        self.vel = pygame.math.Vector2(0, 0)
        self.speed = config.PLAYER_SPEED
        self.jump_power = config.PLAYER_JUMP_POWER
        self.gravity = config.GRAVITY
        self.on_ground = False
        self.on_object = False
        self.can_wall_jump = False
        self.wall_jump_dir = 0
        self.wall_jump_timer = 0

        self.hp = 100
        self.st = 100
        self.fall_damage = 0
        self.bleeding = False
        self.brknthink = None

        self.room = room
        self.last_direction = 1

        self.coyote_time = 0

    def recreate(self, pos: Optional[Tuple[int, int]] = None,
                 skin_path: Optional[str] = None,
                 room: Optional[List[int]] = None) -> None:
        """Пересоздание игрока"""
        if pos:
            self.rect.topleft = pos
        if skin_path:
            self.original_image = pygame.image.load(skin_path).convert_alpha()
            self.image = pygame.transform.scale(self.original_image, (config.PLAYER_SIZE, config.PLAYER_SIZE))
            self.mask = pygame.mask.from_surface(self.image)
        if room:
            self.room = room

        self.vel = pygame.math.Vector2(0, 0)
        self.on_ground = False
        self.can_wall_jump = False
        self.wall_jump_timer = 0
        self.on_object = False
        self.hp = 100
        self.fall_damage = 0
        self.bleeding = False
        self.brknthink = None

    def _collide_x(self, level_mask: pygame.mask.Mask, doors: Optional[List] = None) -> None:
        """Коллизии по горизонтали"""
        step = 1 if self.vel.x > 0 else -1 if self.vel.x < 0 else 0
        self.can_wall_jump = False

        for _ in range(abs(int(self.vel.x))):
            self.rect.x += step

            if level_mask.overlap(self.mask, (self.rect.x, self.rect.y)):
                climbed = False
                for climb_height in range(1, config.MAX_CLIMB + 1):
                    self.rect.y -= 1
                    if not level_mask.overlap(self.mask, (self.rect.x, self.rect.y)):
                        climbed = True
                        break

                if not climbed:
                    self.rect.y += config.MAX_CLIMB
                    self.rect.x -= step
                    self.vel.x = 0
                    self.can_wall_jump = True
                    self.wall_jump_dir = -step
                    break

        if doors:
            for door in doors:
                if door.room == self.room and self.rect.colliderect(door.rect):
                    if self.vel.x > 0:
                        self.rect.right = door.rect.left
                    elif self.vel.x < 0:
                        self.rect.left = door.rect.right

    def _collide_y(self, level_mask: pygame.mask.Mask, doors: Optional[List] = None) -> None:
        """Коллизии по вертикали"""
        step = 1 if self.vel.y > 0 else -1 if self.vel.y < 0 else 0

        for _ in range(abs(int(self.vel.y))):
            self.rect.y += step

            if level_mask.overlap(self.mask, (self.rect.x, self.rect.y)):
                self.rect.y -= step
                if step > 0:
                    self.on_ground = True
                self.vel.y = 0
                break
        else:
            self.on_ground = False

        if doors:
            for door in doors:
                if door.room == self.room and self.rect.colliderect(door.rect):
                    if self.vel.y > 0:
                        self.rect.bottom = door.rect.top
                        self.on_ground = True
                    elif self.vel.y < 0:
                        self.rect.top = door.rect.bottom
                    self.vel.y = 0

    def _collide(self, level_mask: pygame.mask.Mask, doors: Optional[List] = None) -> None:
        """Обработка всех коллизий"""
        while level_mask.overlap(self.mask, (self.rect.x, self.rect.y)):
            self.rect.y -= 1

        self._collide_x(level_mask, doors)
        self._collide_y(level_mask, doors)

    def check_standing_on_objects(self, objects_list: List['PhysicFigure']) -> bool:
        """Проверка, стоит ли игрок на физическом объекте"""
        self.on_object = False

        for obj in objects_list:
            if obj.is_held:
                continue

            if (abs(self.rect.bottom - obj.rect.top) <= 8 and
                self.rect.right > obj.rect.left + 5 and
                self.rect.left < obj.rect.right - 5 and
                self.vel.y >= 0):

                self.rect.bottom = obj.rect.top
                self.on_ground = True
                self.on_object = True
                self.vel.y = 0
                return True

        return False

    def update(self, dt: float, level_mask: pygame.mask.Mask, level_surface: pygame.Surface,
               doors: Optional[List] = None, physics_objects: Optional[List['PhysicFigure']] = None) -> None:
        """Обновление состояния игрока"""
        keys = pygame.key.get_pressed()

        hp = self.hp
        if keys[pygame.K_LEFT]:
            hp -= 1
        elif keys[pygame.K_RIGHT]:
            hp += 1
        self.hp = min(100, max(0, hp))

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

        prev_on_ground = self.on_ground
        self._collide(level_mask, doors)

        on_object = False
        if physics_objects:
            on_object = self.check_standing_on_objects(physics_objects)

        if on_object:
            self.on_ground = True

        if self.on_ground or on_object:
            self.coyote_time = config.COYOTE_TIME_MAX
        elif prev_on_ground:
            self.coyote_time = config.COYOTE_TIME_MAX
        else:
            self.coyote_time = max(0, self.coyote_time - 1)

        if keys[self.keys['jump']] and (self.on_ground or on_object or self.coyote_time > 0) and self.vel.y >= 0:
            self.vel.y = -self.jump_power
            self.coyote_time = 0
            self.on_ground = False
            self.on_object = False

        if keys[self.keys['jump']] and self.can_wall_jump and not self.on_ground:
            self.vel.y = -self.jump_power
            self.vel.x = self.wall_jump_dir * self.speed * 1.5
            self.wall_jump_timer = config.WALL_JUMP_TIMER_MAX

        if self.on_ground or self.on_object:
            fall_damage = self.fall_damage // 180
            self.hp -= fall_damage
            self.fall_damage = 0
        else:
            self.fall_damage += 5

        scaled_image = pygame.transform.scale(self.original_image, (config.PLAYER_SIZE, config.PLAYER_SIZE))
        if self.last_direction == -1:
            self.image = pygame.transform.flip(scaled_image, True, False)
        else:
            self.image = scaled_image

    def xy(self) -> None:
        """Вывод координат (отладка)"""
        print(f'player: {self.rect.x}, {self.rect.y}')

    def new_room(self, room_x: int, room_y: int) -> Tuple[int, int, str]:
        """Обработка перехода в новую комнату"""
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

        new_room = f'room_{new_room_x}{new_room_y}'
        pos_key = (old_room, new_room)

        self.room = [new_room_x, new_room_y]

        if pos_key in self.spawn_positions:
            self.rect.x, self.rect.y = self.spawn_positions[pos_key]

        return new_room_x, new_room_y, new_room