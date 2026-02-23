import pymunk
import pygame

class Square:
    MAX_SPEED = 800.0
    REST_THRESHOLD = 50.0

    def __init__(self, width, height, mass, pos=(0, 0), space=None):
        self.body = pymunk.Body(mass, pymunk.moment_for_box(mass, (width, height)))
        self.body.position = pos
        self.body.angle = 0
        self.body.torque = 0
        self.shape = pymunk.Poly.create_box(self.body, (width, height))
        self.shape.friction = 1.2
        self.shape.elasticity = 0.0
        self.shape.collision_type = 1  # Для коллизий со стенами
        if space:
            space.add(self.body, self.shape)
        self.width = width
        self.height = height
        self.on_ground = False

    def update(self, level_mask):
        vel_length = self.body.velocity.length
        if vel_length > self.MAX_SPEED:
            scale = self.MAX_SPEED / vel_length
            self.body.velocity = self.body.velocity * scale

        # ✅ ДОПОЛНИТЕЛЬНАЯ проверка маски (только если нужно)
        self.on_ground = self._check_ground(level_mask)

        # ✅ ФИКСИРУЕМ вращение
        self.body.angle = 0
        self.body.angular_velocity = 0
        self.body.torque = 0

        # ✅ АДАПТИВНЫЙ демпфинг
        if self.on_ground and vel_length < self.REST_THRESHOLD:
            self.body.velocity *= 0.88
            if vel_length < 25:
                self.body.velocity *= 0.75
        else:
            self.body.velocity *= 0.985

    def _check_ground(self, level_mask):
        """Только проверка земли"""
        rect = pygame.Rect(
            self.body.position.x - self.width / 2,
            self.body.position.y - self.height / 2,
            self.width, self.height
        )

        bottom_points = [
            (rect.left + self.width * 0.25, rect.bottom - 1),
            (rect.centerx, rect.bottom - 1),
            (rect.right - self.width * 0.25, rect.bottom - 1)
        ]

        mask_size = level_mask.get_size()
        contacts = 0

        for px, py in bottom_points:
            ix, iy = int(px), int(py)
            if (0 <= ix < mask_size[0] and 0 <= iy < mask_size[1] and
                    level_mask.get_at((ix, iy))):
                contacts += 1

        return contacts >= 2

    def get_draw_vertices(self):
        center = self.body.position
        verts = [
            (center.x - self.width / 2, center.y - self.height / 2),
            (center.x + self.width / 2, center.y - self.height / 2),
            (center.x + self.width / 2, center.y + self.height / 2),
            (center.x - self.width / 2, center.y + self.height / 2)
        ]
        return verts