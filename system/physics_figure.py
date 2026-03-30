import pygame
import math
from abc import ABC, abstractmethod
from typing import Optional, Tuple, List, TYPE_CHECKING

if TYPE_CHECKING:
    from system.player import Player


class PhysicFigure(ABC):
    """Базовый класс для всех физических объектов в игре."""

    def __init__(
            self,
            rect: pygame.Rect,
            room: tuple,
            level_mask: Optional[pygame.mask.Mask] = None,
            color: Tuple[int, int, int] = (76, 76, 76),
            gravity: float = 0.6,
            max_speed_x: float = 500,
            max_speed_y: float = 1000,
            bounce: float = 0.3,
            friction_air: float = 0.99,
            friction_ground: float = 0.92,
            friction_ground_min_speed: float = 0.5,
            mass: float = 1.0
    ):
        """
        Инициализация физического объекта.
        """
        self.color = color
        self.level_mask = level_mask
        self.room = room

        self.width = rect.width
        self.height = rect.height
        self.rect = pygame.Rect(rect.x, rect.y, self.width, self.height)

        self.vel_x = 0.0
        self.vel_y = 0.0
        self.gravity = gravity
        self.max_speed_x = max_speed_x
        self.max_speed_y = max_speed_y
        self.bounce = bounce
        self.friction_air = friction_air
        self.friction_ground = friction_ground
        self.friction_ground_min_speed = friction_ground_min_speed
        self.mass = mass

        self.on_ground = False
        self.is_held = False
        self.hold_offset = (0, 100)

        self.mask = pygame.mask.Mask((self.width, self.height), fill=True)

        self.current_room = room[1] if room else None

        self.debug_collision = False

    @abstractmethod
    def get_mask(self) -> pygame.mask.Mask:
        """Возвращает маску объекта для коллизий."""
        return self.mask

    def update(self, player: Optional['Player'] = None, all_objects: List['PhysicFigure'] = None) -> None:
        """
        Обновляет физику объекта с учётом коллизий с другими объектами.
        """
        if self.is_held and player:
            self._update_held(player)
        elif player and getattr(player, 'room', None) == self.current_room:
            self._update_physics(all_objects)

    def _update_held(self, player: 'Player') -> None:
        """Обновляет состояние удерживаемого объекта."""
        self.rect.x = player.rect.x
        self.rect.y = player.rect.y - 33
        self.vel_x = 0
        self.vel_y = 0
        if hasattr(player, 'room'):
            self.current_room = player.room.copy() if hasattr(player.room, 'copy') else player.room

    def _update_physics(self, all_objects: List['PhysicFigure'] = None) -> None:
        """Обновляет физику объекта с коллизиями."""
        # Применяем гравитацию
        self.vel_y += self.gravity

        # Воздушное трение
        self.vel_x *= self.friction_air

        # Трение о землю
        if self.on_ground:
            if abs(self.vel_x) > self.friction_ground_min_speed:
                self.vel_x *= self.friction_ground
            else:
                self.vel_x = 0

        # Ограничение максимальной скорости
        self.vel_x = max(-self.max_speed_x, min(self.max_speed_x, self.vel_x))
        self.vel_y = max(-self.max_speed_y, min(self.max_speed_y, self.vel_y))

        # Гарантируем, что объект не находится внутри стены
        self._push_out_of_mask()

        # Движение по X
        self._move_until_collision_x(self.vel_x)

        # Движение по Y
        self._move_until_collision_y(self.vel_y)

        # Коллизии с другими объектами
        if all_objects:
            self._resolve_object_collisions_x(all_objects)
            self._resolve_object_collisions_y(all_objects)

        # Стабилизация на земле
        self.stabilize_on_ground()

        # Финальное выталкивание
        self._push_out_of_mask()

    def _push_out_of_mask(self) -> None:
        """
        Выталкивает объект из маски уровня, если он в ней находится.
        """
        if not self.level_mask or not self.room:
            return

        # Ограничим число итераций, чтобы не зациклиться
        for _ in range(5):
            if not self._check_mask_collision(self.rect):
                break

            # Ищем направление, в котором можно вытолкнуть объект
            best_dist = float('inf')
            best_vec = (0, 0)
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    test_rect = self.rect.move(dx, dy)
                    if not self._check_mask_collision(test_rect):
                        dist = dx * dx + dy * dy
                        if dist < best_dist:
                            best_dist = dist
                            best_vec = (dx, dy)

            if best_vec != (0, 0):
                self.rect.move_ip(*best_vec)
            else:
                # Если не нашли выхода, перемещаем вверх
                self.rect.y -= 1

    def _move_until_collision_x(self, dx: float) -> None:
        """
        Двигает объект по X до столкновения с маской.
        """
        if dx == 0:
            return

        step = 1 if dx > 0 else -1
        steps = int(abs(dx))

        for _ in range(steps):
            new_rect = self.rect.move(step, 0)
            if not self._check_mask_collision(new_rect):
                self.rect.move_ip(step, 0)
            else:
                self.vel_x = 0
                break

        # Обрабатываем дробную часть
        if abs(dx) - steps > 0:
            new_rect = self.rect.move(step, 0)
            if not self._check_mask_collision(new_rect):
                self.rect.move_ip(step, 0)
            else:
                self.vel_x = 0

    def _move_until_collision_y(self, dy: float) -> None:
        """
        Двигает объект по Y до столкновения с маской.
        """
        if dy == 0:
            return

        step = 1 if dy > 0 else -1
        steps = int(abs(dy))
        self.on_ground = False

        for _ in range(steps):
            new_rect = self.rect.move(0, step)
            if not self._check_mask_collision(new_rect):
                self.rect.move_ip(0, step)
            else:
                self.vel_y = 0
                if step > 0:
                    self.on_ground = True
                break

        # Обрабатываем дробную часть
        if abs(dy) - steps > 0:
            new_rect = self.rect.move(0, step)
            if not self._check_mask_collision(new_rect):
                self.rect.move_ip(0, step)
            else:
                self.vel_y = 0
                if step > 0:
                    self.on_ground = True

    def _check_mask_collision(self, rect: pygame.Rect) -> bool:
        """Проверяет пересечение прямоугольника с маской уровня."""
        if not self.level_mask:
            return False

        mask_rect = pygame.Rect(0, 0, self.level_mask.get_size()[0], self.level_mask.get_size()[1])
        if not rect.colliderect(mask_rect):
            return False

        points = [
            (rect.left, rect.top),
            (rect.right - 1, rect.top),
            (rect.left, rect.bottom - 1),
            (rect.right - 1, rect.bottom - 1),
            (rect.centerx, rect.centery)
        ]

        for x, y in points:
            if 0 <= x < self.level_mask.get_size()[0] and 0 <= y < self.level_mask.get_size()[1]:
                if self.level_mask.get_at((int(x), int(y))):
                    return True
        return False

    def _resolve_object_collisions_x(self, objects: List['PhysicFigure']) -> None:
        """Разрешает коллизии с другими объектами по горизонтали."""
        for obj in objects:
            if obj is self or obj.is_held:
                continue

            if self.rect.colliderect(obj.rect):
                overlap = self._calculate_overlap_x(obj)

                if overlap > 0:
                    # Определяем направление
                    if self.rect.centerx < obj.rect.centerx:
                        self.rect.right = obj.rect.left
                    else:
                        self.rect.left = obj.rect.right

                    # Обмениваемся импульсами
                    self._resolve_collision_impulse_x(obj)

    def _resolve_object_collisions_y(self, objects: List['PhysicFigure']) -> None:
        """Разрешает коллизии с другими объектами по вертикали."""
        for obj in objects:
            if obj is self or obj.is_held:
                continue

            if self.rect.colliderect(obj.rect):
                overlap = self._calculate_overlap_y(obj)

                if overlap > 0:
                    # Определяем направление
                    if self.rect.centery < obj.rect.centery:
                        self.rect.bottom = obj.rect.top
                        self.on_ground = True
                        self.vel_y = 0
                    else:
                        self.rect.top = obj.rect.bottom
                        if self.vel_y < 0:
                            self.vel_y = 0

                    # Обмениваемся импульсами
                    self._resolve_collision_impulse_y(obj)

    def _calculate_overlap_x(self, other: 'PhysicFigure') -> float:
        """Вычисляет перекрытие по горизонтали."""
        return min(self.rect.right - other.rect.left, other.rect.right - self.rect.left)

    def _calculate_overlap_y(self, other: 'PhysicFigure') -> float:
        """Вычисляет перекрытие по вертикали."""
        return min(self.rect.bottom - other.rect.top, other.rect.bottom - self.rect.top)

    def _resolve_collision_impulse_x(self, other: 'PhysicFigure') -> None:
        """
        Разрешает обмен импульсами при столкновении по горизонтали.
        Учитывает массы объектов.
        """
        total_mass = self.mass + other.mass
        if total_mass == 0:
            return

        # Относительная скорость
        rel_vel = self.vel_x - other.vel_x

        # Коэффициент восстановления (bounce)
        restitution = min(self.bounce, other.bounce)

        # Импульс
        impulse = (1 + restitution) * rel_vel / total_mass

        # Применяем изменение скорости
        self.vel_x -= impulse * other.mass
        other.vel_x += impulse * self.mass

        # Ограничиваем минимальную скорость
        if abs(self.vel_x) < 0.5 and abs(other.vel_x) < 0.5:
            self.vel_x = 0
            other.vel_x = 0

    def _resolve_collision_impulse_y(self, other: 'PhysicFigure') -> None:
        """
        Разрешает обмен импульсами при столкновении по вертикали.
        Учитывает массы объектов.
        """
        total_mass = self.mass + other.mass
        if total_mass == 0:
            return

        # Относительная скорость
        rel_vel = self.vel_y - other.vel_y

        # Коэффициент восстановления
        restitution = min(self.bounce, other.bounce)

        # Импульс
        impulse = (1 + restitution) * rel_vel / total_mass

        # Применяем изменение скорости
        self.vel_y -= impulse * other.mass
        other.vel_y += impulse * self.mass

        # Проверяем, стоит ли объект на другом
        if self.rect.bottom <= other.rect.top + 10 and self.vel_y >= 0:
            self.on_ground = True
            self.vel_y = 0

    def stabilize_on_ground(self) -> None:
        """Стабилизирует объект на земле/платформе."""
        if self.is_held or self.vel_y > 0:
            return

        test_rect = pygame.Rect(self.rect.x, self.rect.y + 1, self.width, self.height)
        if self._check_mask_collision(test_rect):
            self.vel_y = 0
            self.on_ground = True

            while self._check_mask_collision(self.rect):
                self.rect.y -= 1

            if self.room:
                while not self._check_mask_collision(
                        pygame.Rect(self.rect.x, self.rect.y + 1, self.width, self.height)):
                    if self.rect.y + 1 > self.room[0].bottom:
                        break
                    self.rect.y += 1
        else:
            self.on_ground = False

    def can_place(self, player: 'Player') -> bool:
        """Проверяет, можно ли положить объект в текущей позиции."""
        direction = 1 if player.last_direction == 1 else -1
        test_rect = pygame.Rect(
            player.rect.centerx + (35 * direction) - self.width // 2,
            player.rect.centery - 15 - self.height // 2,
            self.width, self.height
        )

        if self.level_mask and self._check_mask_collision(test_rect):
            return False

        if self.room:
            room_rect = self.room[0]
            if not room_rect.contains(test_rect):
                return False

        return True

    def pick_up(self, player: 'Player') -> None:
        """Поднимает объект."""
        if not self.is_held:
            self.is_held = True
            self.rect.x = player.rect.x
            self.rect.y = player.rect.y - 33
            self.vel_x = 0
            self.vel_y = 0
            if hasattr(player, 'room'):
                self.current_room = player.room.copy() if hasattr(player.room, 'copy') else player.room

    def drop(self, player: 'Player', throw: bool = False, throw_velocity: Optional[Tuple[float, float]] = None) -> None:
        """Отпускает объект."""
        if self.is_held:
            self.is_held = False
            if hasattr(player, 'room'):
                self.current_room = player.room.copy() if hasattr(player.room, 'copy') else player.room

            if throw_velocity is not None:
                self.vel_x, self.vel_y = throw_velocity
            elif throw:
                direction = 1 if player.last_direction == 1 else -1
                self.vel_x = 500 * direction
                self.vel_y = -100
            else:
                direction = 1 if player.last_direction == 1 else -1
                self.rect.centerx = player.rect.centerx + (35 * direction)
                self.rect.centery = player.rect.centery - 15

                if self.room:
                    room_rect = self.room[0]
                    if self.rect.left < room_rect.left:
                        self.rect.left = room_rect.left
                    elif self.rect.right > room_rect.right:
                        self.rect.right = room_rect.right
                    if self.rect.top < room_rect.top:
                        self.rect.top = room_rect.top
                    elif self.rect.bottom > room_rect.bottom:
                        self.rect.bottom = room_rect.bottom

                self.vel_x = 0
                self.vel_y = 0

    def get_distance_to_player(self, player: 'Player') -> float:
        """Возвращает расстояние от объекта до игрока."""
        dx = self.rect.centerx - player.rect.centerx
        dy = self.rect.centery - player.rect.centery
        return math.sqrt(dx * dx + dy * dy)

    def resolve_collision_with_player(self, player: 'Player') -> None:
        """Разрешает коллизию между объектом и игроком."""
        if self.is_held:
            return

        if not self.rect.colliderect(player.rect):
            return

        overlap_x = min(self.rect.right - player.rect.left, player.rect.right - self.rect.left)
        overlap_y = min(self.rect.bottom - player.rect.top, player.rect.bottom - self.rect.top)

        if overlap_x < overlap_y:
            if player.rect.centerx < self.rect.centerx:
                correction = overlap_x
                player_dx = -correction
                sq_dx = correction
            else:
                correction = overlap_x
                player_dx = correction
                sq_dx = -correction

            self.rect.x += sq_dx
            player.rect.x += player_dx
            if sq_dx != 0 and hasattr(player, 'vel'):
                player.vel.x = 0
        else:
            if player.rect.centery < self.rect.centery:
                correction = overlap_y
                player_dy = -correction
                sq_dy = correction
            else:
                correction = overlap_y
                player_dy = correction
                sq_dy = -correction

            self.rect.y += sq_dy
            player.rect.y += player_dy
            if player_dy > 0:
                player.on_ground = True
                if hasattr(player, 'vel'):
                    player.vel.y = 0
            elif player_dy < 0 and hasattr(player, 'vel'):
                player.vel.y = 0

    def set_level_mask(self, level_mask: pygame.mask.Mask) -> None:
        """Устанавливает новую маску уровня."""
        self.level_mask = level_mask

    def set_room(self, room_rect: pygame.Rect, room_coords) -> None:
        """Устанавливает новую комнату."""
        self.room = (room_rect, room_coords)
        self.current_room = room_coords

    @abstractmethod
    def draw(self, screen: pygame.Surface, current_player_room) -> None:
        """Отрисовывает объект."""
        if self.current_room == current_player_room:
            pygame.draw.rect(screen, self.color, self.rect)
            if self.debug_collision:
                pygame.draw.rect(screen, (255, 255, 0), self.rect, 2)