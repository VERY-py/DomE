import pygame

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
