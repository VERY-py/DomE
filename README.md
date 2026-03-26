# CUBE

Небольшой мультиплеерный платформер.
Перед запуском убедится о наличии Pygame, Pugame-gui, Python 3.12 и выше.
```
pip install pygame, pygame-gui
```

import pygame
import pymunk
from GUI import FPS

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

class PhysikSq:
    def __init__(self, rect, room, color=(76, 76, 76)):
        self.is_rect = rect
        self.rect = self.is_rect.copy()
        self.color = color
        self.room = room

        info = pygame.display.Info()
        WIDTH, HEIGHT = info.current_w, info.current_h

        self.space = pymunk.Space()
        self.space.gravity = (0, 900)

        walls = [pymunk.Segment(self.space.static_body, (0, 0), (0, HEIGHT), 1),
                 pymunk.Segment(self.space.static_body, (WIDTH, 0), (WIDTH, HEIGHT), 1),
                 pymunk.Segment(self.space.static_body, (0, 0), (WIDTH, 0), 1),
                 pymunk.Segment(self.space.static_body, (0, HEIGHT), (WIDTH, HEIGHT), 1)]

        for wall in walls:
            wall.elasticity = 0.8  # Элостичность стен
            self.space.add(wall)

        self._create(30, 30)

    def _create(self, x, y):
        body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        body.position = x, y

        poly = pymunk.Poly.create_box(body, (10, 10))
        poly.mass = 10
        poly.elasticity = 0.8

        self.space.add(body, poly)

    def update(self, player, running):
        self.space.step(1 / FPS)
    
    def draw(self, screen):
