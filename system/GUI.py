<<<<<<< HEAD
import pygame
from config import *


def get_bar(ed, size=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 20), color=(255, 80, 80), revers=True) -> pygame.Surface:
    surface = pygame.Surface(size, pygame.SRCALPHA)
    rect = surface.get_rect()
    surface.fill((0, 0, 0))
    filled_width = int(rect.width * (ed / 100.0))
    if filled_width <= 0:
        return surface
    if revers:
        x = rect.width - filled_width
    else:
        x = 0
    bar_rect = pygame.Rect(x, 0, filled_width, rect.height)
    pygame.draw.rect(surface, color, bar_rect)
    return surface


class HPBar:
    def __init__(self, player):
        self.player = player

    def get_hpbar(self) -> pygame.Surface:
        return get_bar(self.player.hp, revers=True)


class StaminaBar:
    def __init__(self, player):
        self.player = player

    def get_stbar(self) -> pygame.Surface:
        return get_bar(self.player.st, color=(100, 100, 255), revers=False)
=======
from config import *


class HPBar:
    def __init__(self, player) -> None:
        self.player = player
        pass

    def get_hpbar(self) -> pygame.Surface:
        surface = pygame.surface.Surface((SCREEN_WIDTH // 2, SCREEN_HEIGHT // 20))
        rect = surface.get_rect()
        hp1 = rect.width // 100

        if self.player.hp == 0:
            a = 0
        else:
            a = 1
            while a <= self.player.hp:
                a += 1

        hp_rect = pygame.rect.Rect(0, 0, hp1 * a, rect.height)
        pygame.draw.rect(surface, (255, 80, 80), hp_rect)

        return surface
>>>>>>> parent of 1599117 (0.9.1)
