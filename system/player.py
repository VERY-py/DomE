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
        if not hasattr(self, '_pygame_initialized'):
            pygame.init()
            self._pygame_initialized = True

    def _create(self, pos: Tuple[int, int], room: List[int], skin_path: str) -> None:
        self.original_image = pygame.image.load(skin_path).convert_alpha()
        self.image = pygame.transform.scale(self.original_image, (config.PLAYER_SIZE, config.PLAYER_SIZE))
        self.rect = self.image.get_rect(topleft=pos)
        self.mask = pygame.mask.from_surface(self.image)

        self.base_speed = getattr(config, 'PLAYER_SPEED', 500)          # 500 px/сек
        self.run_multiplier = getattr(config, 'RUN_SPEED_MULTIPLIER', 1.8)
        self.jump_power = getattr(config, 'PLAYER_JUMP_POWER', -600)    # px/сек
        self.gravity = getattr(config, 'GRAVITY', 2000)                 # px/сек²

        self.st_max = getattr(config, 'STAMINA_MAX', 100)
        self.st = self.st_max
        self.stamina_drain_rate = getattr(config, 'STAMINA_DRAIN_RATE', 100)   
        self.stamina_regen_rate = getattr(config, 'STAMINA_REGEN_RATE', 50)

        self.vel = pygame.math.Vector2(0, 0)
        self.on_ground = False
        self.on_object = False
        self.can_wall_jump = False
        self.wall_jump_dir = 0
        self.wall_jump_timer = 0.0        
        self.coyote_time = 0.0             

        self.max_fall_speed = 0.0           

        self.hp = 100
        self.bleeding = False
        self.brknthink = None

        self.room = room
        self.last_direction = 1

        self.wall_jump_cooldown = getattr(config, 'WALL_JUMP_COOLDOWN', 0.2)

    def recreate(self, pos: Optional[Tuple[int, int]] = None,
                 skin_path: Optional[str] = None,
                 room: Optional[List[int]] = None) -> None:
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
        self.wall_jump_timer = 0.0
        self.on_object = False
        self.hp = 100
        self.max_fall_speed = 0.0
        self.bleeding = False
        self.brknthink = None
        self.st = self.st_mask

    def _collide_x(self, dx: float, level_mask: pygame.mask.Mask, doors: Optional[List] = None) -> None:
        """Перемещение по X"""
        if dx == 0:
            return

        self.rect.x += dx
        self.can_wall_jump = False

        if level_mask.overlap(self.mask, (self.rect.x, self.rect.y)):
            climbed = False
            for climb_height in range(1, getattr(config, 'MAX_CLIMB', 10) + 1):
                self.rect.y -= 1
                if not level_mask.overlap(self.mask, (self.rect.x, self.rect.y)):
                    climbed = True
                    break
            if not climbed:
                self.rect.x -= dx
                self.vel.x = 0
            else:
                if not self.on_ground:
                    self.can_wall_jump = True
                    self.wall_jump_dir = -1 if dx > 0 else 1

        if doors:
            for door in doors:
                if door.room == self.room and self.rect.colliderect(door.rect):
                    if dx > 0:
                        self.rect.right = door.rect.left
                        self.vel.x = 0
                    elif dx < 0:
                        self.rect.left = door.rect.right
                        self.vel.x = 0

    def _collide_y(self, dy: float, level_mask: pygame.mask.Mask, doors: Optional[List] = None) -> None:
        """Перемещение по Y"""
        if dy == 0:
            return

        self.rect.y += dy
        self.on_ground = False

        if level_mask.overlap(self.mask, (self.rect.x, self.rect.y)):
            self.rect.y -= dy
            self.vel.y = 0
            if dy > 0:
                self.on_ground = True

        if doors:
            for door in doors:
                if door.room == self.room and self.rect.colliderect(door.rect):
                    if dy > 0:
                        self.rect.bottom = door.rect.top
                        self.on_ground = True
                        self.vel.y = 0
                    elif dy < 0:
                        self.rect.top = door.rect.bottom
                        self.vel.y = 0

    def _move(self, dt: float, level_mask: pygame.mask.Mask, doors: Optional[List] = None) -> None:
        """Полное перемещение за кадр с учётом dt"""
        self._collide_x(self.vel.x * dt, level_mask, doors)
        self._collide_y(self.vel.y * dt, level_mask, doors)

    def check_standing_on_objects(self, objects_list: List['PhysicFigure']) -> bool:
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
        keys = pygame.key.get_pressed()

        hp = self.hp
        if keys[pygame.K_LEFT]:
            hp -= 1
        elif keys[pygame.K_RIGHT]:
            hp += 1
        self.hp = min(100, max(0, hp))

        target_speed = 0.0
        is_running = False
        run_key = self.keys.get('shift', pygame.K_LSHIFT)

        if self.wall_jump_timer <= 0:
            if keys[self.keys['left']]:
                target_speed = -self.base_speed
                self.last_direction = -1
            elif keys[self.keys['right']]:
                target_speed = self.base_speed
                self.last_direction = 1

            if target_speed != 0 and keys[run_key] and self.st > 0 and (self.on_ground or self.on_object):
                is_running = True
                target_speed *= self.run_multiplier
                self.st -= self.stamina_drain_rate * dt
                if self.st < 0:
                    self.st = 0
            else:
                if self.st < self.st_max:
                    self.st += self.stamina_regen_rate * dt
                    if self.st > self.st_max:
                        self.st = self.st_max

        self.vel.x = target_speed

        self.vel.y += self.gravity * dt

        self._move(dt, level_mask, doors)


        on_phys_object = False
        if physics_objects:
            on_phys_object = self.check_standing_on_objects(physics_objects)

        if self.on_ground or on_phys_object:
            self.coyote_time = getattr(config, 'COYOTE_TIME_SECONDS', 0.1)
        else:
            self.coyote_time -= dt
            if self.coyote_time < 0:
                self.coyote_time = 0

        jump_key = self.keys.get('jump', pygame.K_SPACE)
        if keys[jump_key] and (self.on_ground or on_phys_object or self.coyote_time > 0) and self.vel.y >= 0:
            self.vel.y = self.jump_power
            self.coyote_time = 0
            self.on_ground = False
            self.on_object = False

        if keys[jump_key] and self.can_wall_jump and not self.on_ground and self.wall_jump_timer <= 0:
            self.vel.y = self.jump_power
            self.vel.x = self.wall_jump_dir * self.base_speed * 1.5
            self.wall_jump_timer = self.wall_jump_cooldown

            self.can_wall_jump = False

        if self.wall_jump_timer > 0:
            self.wall_jump_timer -= dt

        if self.on_ground or on_phys_object:
            fall_speed = abs(self.max_fall_speed)
            threshold = getattr(config, 'FALL_DAMAGE_THRESHOLD', 500)   # px/сек
            factor = getattr(config, 'FALL_DAMAGE_FACTOR', 0.002)
            if fall_speed > threshold:
                damage = int((fall_speed - threshold) * factor)
                if damage > 0:
                    self.hp -= damage
                    if self.hp < 0:
                        self.hp = 0
            self.max_fall_speed = 0.0
        else:
            if abs(self.vel.y) > self.max_fall_speed:
                self.max_fall_speed = abs(self.vel.y)

        scaled_image = pygame.transform.scale(self.original_image, (config.PLAYER_SIZE, config.PLAYER_SIZE))
        if self.last_direction == -1:
            self.image = pygame.transform.flip(scaled_image, True, False)
        else:
            self.image = scaled_image

 
    def xy(self) -> None:
        print(f'player: {self.rect.x}, {self.rect.y}')

    def new_room(self, room_x: int, room_y: int) -> Tuple[int, int, str]:
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