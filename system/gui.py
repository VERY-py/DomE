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
