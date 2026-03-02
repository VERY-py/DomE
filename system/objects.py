import pygame

def draw_dashed_rect(surface, color, rect, dash_length=10, gap_length=5, width=1):
    x, y, width_rect, height_rect = rect

    top_left = (x, y)
    top_right = (x + width_rect, y)
    bottom_right = (x + width_rect, y + height_rect)
    bottom_left = (x + width_rect, y + height_rect)

    draw_dashed_line(surface, color, top_left, top_right, dash_length, gap_length, width)
    draw_dashed_line(surface, color, top_right, bottom_right, dash_length, gap_length, width)
    draw_dashed_line(surface, color, bottom_right, bottom_left, dash_length, gap_length, width)
    draw_dashed_line(surface, color, bottom_left, top_left, dash_length, gap_length, width)


def draw_dashed_line(surface, color, start_pos, end_pos, dash_length, gap_length, width):
    x1, y1 = start_pos
    x2, y2 = end_pos

    dx = x2 - x1
    dy = y2 - y1
    distance = max(abs(dx), abs(dy))

    if distance == 0:
        return

    step_x = dx / distance
    step_y = dy / distance

    current_distance = 0
    is_drawing = True

    while current_distance < distance:
        if is_drawing:
            segment_length = min(dash_length, distance - current_distance)
        else:
            segment_length = min(gap_length, distance - current_distance)

        end_distance = current_distance + segment_length
        x_end = x1 + step_x * end_distance
        y_end = y1 + step_y * end_distance

        if is_drawing:
            pygame.draw.line(
                surface,
                color,
                (x1 + step_x * current_distance, y1 + step_y * current_distance),
                (x_end, y_end),
                width
            )

        current_distance = end_distance
        is_drawing = not is_drawing

class Door:
    def __init__(self, rect):
        self.is_rect = rect
        self.open = False
        self.rect = self.is_rect.copy()

    def on_off(self, pl_rect):
        r = pygame.rect.Rect(pl_rect.x - 20, pl_rect.y, pl_rect.width + 20, pl_rect.height)
        if r.colliderect(self.is_rect):
            if self.open:
                self.open = False
            else:
                self.open = True

    def draw(self, screen):
        if self.open:
            if self.rect.width > 0:
                self.rect = pygame.rect.Rect(self.rect.x, self.rect.y, self.rect.width - 1, self.rect.height)
                pygame.draw.rect(screen, (110, 40, 0), self.rect)
            else:
                draw_dashed_rect(screen, (0, 255, 0), self.is_rect)
        elif not self.open:
            if self.rect.width < self.is_rect.width:
                self.rect = pygame.rect.Rect(self.rect.x, self.rect.y, self.rect.width + 1, self.rect.height)
                draw_dashed_rect(screen, (0, 255, 0), self.is_rect)
            else:
                pygame.draw.rect(screen, (110, 40, 0), self.rect)