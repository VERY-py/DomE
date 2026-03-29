# player.py
import pygame
from typing import Tuple, Dict, Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from system.physics_figure import PhysicFigure


class Player(pygame.sprite.Sprite):
    def __init__(
            self,
            pos: Tuple[int, int],
            room_id: list[int],
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

        self.max_climb = 30
        self.climbed = False

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

        self.create(pos, room_id, skin_path)

    def _init_pygame_once(self):
        if not hasattr(self, '_pygame_initialized'):
            pygame.init()
            self._pygame_initialized = True

    def create(self, pos: tuple[int, int], room: list[int], skin_path: str):
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

        self.room = room

        self.coyote_time = 0
        self.coyote_time_max = 4  # Длительность Coyote Time (кадров)
        self.was_on_ground = False

        self.size_state = 0
        self.prev_keys = {}
        self.last_direction = 1

        self.on_object = False

    def recreate(self, pos: Optional[Tuple[int, int]] = None, skin_path: Optional[str] = None,
                 room: Optional[list[int]] = None):
        if pos:
            self.rect.topleft = pos
        if skin_path:
            self.original_image = pygame.image.load(skin_path)
        if room:
            self.room = room

        self.vel = pygame.math.Vector2(0, 0)
        self.on_ground = False
        self.can_wall_jump = False
        self.wall_jump_timer = 0
        self.size_state = 0
        self.coyote_time = 0
        self.on_object = False
        self.image = pygame.transform.scale(self.original_image, (30, 30))
        self.mask = pygame.mask.from_surface(self.image)

    def toggle_size(self, key):
        if key == self.keys['down']:
            self.size_state = 1
        elif key == self.keys['up']:
            self.size_state = 2
        elif key == self.keys['size_small']:
            self.size_state = 0

    def collide(self, level_mask, doors: list = None):
        step_x = 1 if self.vel.x > 0 else -1 if self.vel.x < 0 else 0
        self.can_wall_jump = False

        for _ in range(abs(int(self.vel.x))):
            self.rect.x += step_x
            if level_mask.overlap(self.mask, (self.rect.x, self.rect.y)):
                max_climb = 30
                self.climbed = False
                for climb_height in range(1, max_climb + 1):
                    self.rect.y -= 1
                    if not level_mask.overlap(self.mask, (self.rect.x, self.rect.y)):
                        self.climbed = True
                        break
                if not self.climbed:
                    self.rect.y += climb_height
                    self.rect.x -= step_x
                    self.vel.x = 0
                    self.can_wall_jump = True
                    self.wall_jump_dir = -step_x
                    break

        if doors:
            for door in doors:
                if door.room == self.room:
                    if self.rect.colliderect(door.rect):
                        if self.vel.x > 0:
                            self.rect.right = door.rect.left
                        elif self.vel.x < 0:
                            self.rect.left = door.rect.right

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

        if doors:
            for door in doors:
                if door.room == self.room:
                    if self.rect.colliderect(door.rect):
                        if self.vel.y > 0:
                            self.rect.bottom = door.rect.top
                            self.on_ground = True
                        elif self.vel.y < 0:
                            self.rect.top = door.rect.bottom
                        self.vel.y = 0

    def new_pl_size(self, new_size):
        old_bottom = self.rect.bottom
        topleft = self.rect.topleft

        self.image = pygame.transform.scale(self.original_image, new_size)
        self.rect = self.image.get_rect()
        self.rect.topleft = topleft
        self.mask = pygame.mask.from_surface(self.image)
        self.rect.bottom = old_bottom

    def check_standing_on_objects(self, objects_list: List['PhysicFigure']) -> bool:
        """
        Проверяет, стоит ли игрок на каком-либо физическом объекте.

        Args:
            objects_list: список физических объектов (PhysicFigure)

        Returns:
            bool: True если игрок стоит на объекте
        """
        was_on_object = self.on_object
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

    def update(self, level_mask, level_surface, doors: list = None, physics_objects: List['PhysicFigure'] = None):
        """
        Обновление игрока с поддержкой физических объектов.

        Args:
            level_mask: маска уровня для коллизий
            level_surface: поверхность уровня (не используется)
            doors: список дверей
            physics_objects: список физических объектов (квадраты, ящики и т.д.)
        """
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

        prev_on_ground = self.on_ground

        self.collide(level_mask, doors)

        on_object = False
        if physics_objects:
            on_object = self.check_standing_on_objects(physics_objects)

        if on_object:
            self.on_ground = True

        if self.on_ground or on_object:
            self.coyote_time = self.coyote_time_max
        elif prev_on_ground:
            self.coyote_time = self.coyote_time_max
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
            self.wall_jump_timer = self.wall_jump_timer_max

        image1 = pygame.transform.scale(self.original_image, new_size)
        if self.last_direction == -1:
            self.image = pygame.transform.flip(image1, True, False)
        else:
            self.image = image1.copy()

    def xy(self):
        print(f'player: {self.rect.x, self.rect.y}')

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
        self.room = [new_room_x, new_room_y]

        if pos_key in self.spawn_positions:
            self.rect.x, self.rect.y = self.spawn_positions[pos_key]
        return new_room_x, new_room_y, room