import pygame
from typing import Optional, List, TYPE_CHECKING
from physics_figure import PhysicFigure

if TYPE_CHECKING:
    from system.player import Player


class Door:
    def __init__(self, rect, room, color=(110, 40, 0)):
        self.is_rect = rect
        self.open = False
        self.rect = self.is_rect.copy()
        self.color = color
        self.room = room

    def on_off(self, pl_rect):
        r = pygame.Rect(pl_rect.x - 20, pl_rect.y, pl_rect.width + 40, pl_rect.height)
        if r.colliderect(self.is_rect):
            self.open = not self.open

    def draw(self, screen):
        target_width = 0 if self.open else self.is_rect.width

        if self.rect.width < target_width:
            self.rect.width += 1
        elif self.rect.width > target_width:
            self.rect.width -= 1

        pygame.draw.rect(screen, self.color, self.rect)


class PhysikSq(PhysicFigure):
    """Квадрат с физикой - наследник PhysicFigure."""

    def __init__(self, rect, room, color=(76, 76, 76), level_mask=None, mass=1.0):
        """
        Инициализация физического квадрата.

        Args:
            rect: прямоугольник квадрата
            room: комната (room_rect, room_coords)
            color: цвет квадрата
            level_mask: маска уровня
            mass: масса квадрата
        """
        super().__init__(
            rect=rect,
            room=room,
            level_mask=level_mask,
            color=color,
            gravity=0.3,
            max_speed_x=15,
            max_speed_y=20,
            bounce=0.3,
            friction_air=0.98,
            friction_ground=0.92,
            friction_ground_min_speed=0.5,
            mass=mass
        )

    def update(self, player: Optional['Player'] = None, all_objects: List['PhysicFigure'] = None) -> None:
        """
        Обновляет физику квадрата.

        Args:
            player: объект игрока (опционально)
            all_objects: список всех физических объектов
        """
        super().update(player, all_objects)

    def get_mask(self) -> pygame.mask.Mask:
        """Возвращает маску квадрата."""
        return self.mask

    def draw(self, screen, current_player_room):
        """Отрисовывает квадрат."""
        super().draw(screen, current_player_room)