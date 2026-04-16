from config import *

def get_bar(ed, size=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 20), color=(255, 80, 80), revers=True) -> pygame.Surface:
    surface = pygame.surface.Surface(size)
    rect = surface.get_rect()
    hp1 = rect.width // 100

    if ed == 0:
        a = 0
    else:
        a = 1
        while a <= ed:
            a += 1

    if revers:
        surface.fill(color)
        hp_rect = pygame.rect.Rect(0, 0, hp1 * a, rect.height)
        pygame.draw.rect(surface, (0, 0, 0), hp_rect)
    else:
        surface.fill((0, 0, 0))
        hp_rect = pygame.rect.Rect(0, 0, hp1 * a, rect.height)
        pygame.draw.rect(surface, color, hp_rect)


    return surface

class HPBar:
    def __init__(self, player) -> None:
        self.player = player
        pass

    def get_hpbar(self) -> pygame.Surface:
        return get_bar(self.player.hp, revers=True)

class StaminaBar:
    def __init__(self, player) -> None:
        self.player = player
        pass

    def get_stbar(self) -> pygame.Surface:
        return get_bar(self.player.st, color=(100, 100, 255))