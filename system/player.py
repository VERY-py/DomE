import pygame

class Player(pygame.sprite.Sprite):
    def __init__(
            self,
            pos,
            skin,
            A=pygame.K_a,
            D=pygame.K_d,
            W=pygame.K_w,
            S=pygame.K_s,
            E=pygame.K_e,
            SHIFT=pygame.K_LSHIFT,
            CTRL=pygame.K_LCTRL,
            SPACE=pygame.K_SPACE
    ):
        super().__init__()
        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
        self.image.fill((0, 200, 200))
        self.rect = self.image.get_rect(topleft=pos)
        self.mask = pygame.mask.from_surface(self.image)
        self.vel = pygame.math.Vector2(0, 0)
        self.speed = 5
        self.a = A
        self.d = D
        self.w = W
        self.s = S
        self.e = E
        self.shift = SHIFT
        self.ctrl = CTRL
        self.space = SPACE
        self.jump_power = 12
        self.on_ground = False
        self.gravity = 0.7
        self.can_wall_jump = False
        self.wall_jump_dir = 0
        self.wall_jump_timer = 0
        self.wall_jump_timer_max = 14
        self.original_image = pygame.image.load(skin).convert_alpha()
        self.image = pygame.transform.scale(self.original_image, (30, 30))
        self.rect = self.image.get_rect(topleft=pos)
        self.mask = pygame.mask.from_surface(self.image)
        self.size_state = 0
        self.prev_keys = {}
        self.spawn_positions = {
            ('room_11', 'room_21'): (125, 978),
            ('room_21', 'room_11'): (1700, 749),
            ('room_21', 'room_31'): (120, 849),
            ('room_31', 'room_21'): (1749, 978),
            ('room_31', 'room_30'): (447, 1044),
            ('room_30', 'room_31'): (1666, 34),
            ('room_12', 'room_11'): (76, 1003),
            ('room_11', 'room_12'): (16, 412),
        }
        self.health = 100
        self.max_health = 100
        self.fall_height = 0
        self.last_direction = 1
        self.shoot_cooldown = 0
        self.projectiles = []
        self.damage_cooldown = 0

    def toggle_size(self, key):
        if key == self.s:
            self.size_state = 1
        elif key == self.w:
            self.size_state = 2
        elif key == self.e:
            self.size_state = 0

    def move_and_collide(self, level_mask):
        step_x = 1 if self.vel.x > 0 else -1 if self.vel.x < 0 else 0
        self.can_wall_jump = False

        for _ in range(abs(int(self.vel.x))):
            self.rect.x += step_x
            if level_mask.overlap(self.mask, (self.rect.x, self.rect.y)):
                max_climb = 30
                climbed = False
                for climb_height in range(1, max_climb + 1):
                    self.rect.y -= 1
                    if not level_mask.overlap(self.mask, (self.rect.x, self.rect.y)):
                        climbed = True
                        break
                if not climbed:
                    self.rect.y += climb_height
                    self.rect.x -= step_x
                    self.vel.x = 0
                    self.can_wall_jump = True
                    self.wall_jump_dir = -step_x
                    break

        step_y = 1 if self.vel.y > 0 else -1 if self.vel.y < 0 else 0
        for _ in range(abs(int(self.vel.y))):
            self.rect.y += step_y
            if level_mask.overlap(self.mask, (self.rect.x, self.rect.y)):
                self.rect.y -= step_y
                if step_y > 0:
                    self.on_ground = True
                self.vel.y = 0
                break
        else:
            self.on_ground = False

    def new_pl_size(self, new_size):
        old_bottom = self.rect.bottom
        topleft = self.rect.topleft

        self.image = pygame.transform.scale(self.original_image, new_size)
        self.rect = self.image.get_rect()
        self.rect.topleft = topleft
        self.mask = pygame.mask.from_surface(self.image)
        self.rect.bottom = old_bottom

    def update(self, level_mask, level_surface):
        keys = pygame.key.get_pressed()

        for k in (self.s, self.w, self.e):
            if keys[k] and not self.prev_keys.get(k, False):
                self.toggle_size(k)

        for k in (self.s, self.w, self.e):
            self.prev_keys[k] = keys[k]

        if self.size_state == 1:
            new_size = (45, 15)
        elif self.size_state == 2:
            new_size = (15, 45)
        else:
            new_size = (30, 30)

        if self.image.get_size() != new_size:
            self.new_pl_size(new_size)

        while level_mask.overlap(self.mask, (self.rect.x, self.rect.y)):
            self.rect.y -= 1

        target_vel_x = 0
        if self.wall_jump_timer > 0:
            self.wall_jump_timer -= 1
        else:
            if keys[self.a]:
                target_vel_x = -self.speed
                self.last_direction = 1
            elif keys[self.d]:
                target_vel_x = self.speed
                self.last_direction = -1

            self.vel.x = target_vel_x

        self.vel.y += self.gravity
        self.move_and_collide(level_mask)

        if keys[self.space]:
            if self.on_ground:
                self.vel.y = -self.jump_power
            elif self.can_wall_jump and not self.on_ground:
                self.vel.y = -self.jump_power
                self.vel.x = self.wall_jump_dir * self.speed * 1.5
                self.wall_jump_timer = self.wall_jump_timer_max

        image1 = pygame.transform.scale(self.original_image, new_size)
        if self.last_direction == -1:
            self.image = pygame.transform.flip(image1, True, False)
        else:
            self.image = image1.copy()

    def xy(self):
        print(f'{self.rect.x}, {self.rect.y} 1')

    def new_room(self, room_x, room_y):
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

        room = f'room_{new_room_x}{new_room_y}'
        pos_key = (old_room, room)

        if pos_key in self.spawn_positions:
            self.rect.x, self.rect.y = self.spawn_positions[pos_key]
        return new_room_x, new_room_y, room
