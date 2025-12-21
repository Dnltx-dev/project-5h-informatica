import pygame
import sys
import random
import math

pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
TILE_SIZE = 32

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SKY_BLUE = (135, 206, 235)
BROWN = (139, 69, 19)
GREEN = (34, 139, 34)
DARK_GREEN = (0, 100, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
BLUE = (0, 0, 255)
PURPLE = (128, 0, 128)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
GOLD = (255, 215, 0)
PINK = (255, 192, 203)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Super Daniel Jaccosy")
clock = pygame.time.Clock()

class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, entity):
        return entity.rect.move(self.camera.topleft)

    def apply_rect(self, rect):
        return rect.move(self.camera.topleft)

    def update(self, target):
        x = -target.rect.centerx + SCREEN_WIDTH // 2
        y = -target.rect.centery + SCREEN_HEIGHT // 2
        x = min(0, x)
        y = min(0, y)
        x = max(-(self.width - SCREEN_WIDTH), x)
        y = max(-(self.height - SCREEN_HEIGHT), y)
        self.camera = pygame.Rect(x, y, self.width, self.height)

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.width = 24
        self.height = 32
        self.image = self.create_sprite()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.vel_x = 0
        self.vel_y = 0
        self.speed = 5
        self.jump_power = -15
        self.gravity = 0.8
        self.on_ground = False
        self.facing_right = True
        self.can_double_jump = False
        self.has_double_jumped = False
        self.speed_boost = False
        self.speed_boost_timer = 0
        self.invincible = False
        self.invincible_timer = 0
        self.animation_frame = 0
        self.animation_timer = 0

    def create_sprite(self):
        surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(surface, (255, 200, 150), (4, 0, 16, 10))
        pygame.draw.rect(surface, (100, 50, 0), (4, 0, 16, 6))
        pygame.draw.rect(surface, BLACK, (8, 6, 3, 3))
        pygame.draw.rect(surface, BLACK, (14, 6, 3, 3))
        pygame.draw.rect(surface, RED, (0, 10, 24, 14))
        pygame.draw.rect(surface, BLUE, (4, 24, 16, 8))
        pygame.draw.rect(surface, BROWN, (4, 28, 6, 4))
        pygame.draw.rect(surface, BROWN, (14, 28, 6, 4))
        return surface

    def update(self, platforms, enemies, powerups, coins, flag):
        keys = pygame.key.get_pressed()
        
        base_speed = self.speed
        if self.speed_boost:
            base_speed = self.speed * 1.5
            self.speed_boost_timer -= 1
            if self.speed_boost_timer <= 0:
                self.speed_boost = False

        if self.invincible:
            self.invincible_timer -= 1
            if self.invincible_timer <= 0:
                self.invincible = False

        self.vel_x = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel_x = -base_speed
            self.facing_right = False
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel_x = base_speed
            self.facing_right = True

        self.vel_y += self.gravity
        if self.vel_y > 15:
            self.vel_y = 15

        self.rect.x += self.vel_x
        self.check_collision_x(platforms)

        self.rect.y += self.vel_y
        self.on_ground = False
        self.check_collision_y(platforms)

        if self.on_ground:
            self.has_double_jumped = False

        if self.rect.y > 800:
            return "died"

        for enemy in enemies:
            if self.rect.colliderect(enemy.rect):
                if self.vel_y > 0 and self.rect.bottom <= enemy.rect.top + 20:
                    if enemy.enemy_type == "spike":
                        if not self.invincible:
                            return "hit"
                    else:
                        enemy.kill()
                        self.vel_y = self.jump_power * 0.6
                        return "enemy_killed"
                elif not self.invincible:
                    return "hit"

        for powerup in powerups:
            if self.rect.colliderect(powerup.rect):
                effect = powerup.collect()
                powerup.kill()
                return effect

        for coin in coins:
            if self.rect.colliderect(coin.rect):
                coin.kill()
                return "coin_collected"

        if flag and self.rect.colliderect(flag.rect):
            return "level_complete"

        return None

    def jump(self):
        if self.on_ground:
            self.vel_y = self.jump_power
            self.on_ground = False
        elif self.can_double_jump and not self.has_double_jumped:
            self.vel_y = self.jump_power
            self.has_double_jumped = True

    def check_collision_x(self, platforms):
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.vel_x > 0:
                    self.rect.right = platform.rect.left
                elif self.vel_x < 0:
                    self.rect.left = platform.rect.right

    def check_collision_y(self, platforms):
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.vel_y > 0:
                    self.rect.bottom = platform.rect.top
                    self.vel_y = 0
                    self.on_ground = True
                elif self.vel_y < 0:
                    self.rect.top = platform.rect.bottom
                    self.vel_y = 0

    def draw(self, surface, camera):
        if self.invincible and (self.invincible_timer // 5) % 2 == 0:
            return
        pos = camera.apply(self)
        if self.facing_right:
            surface.blit(self.image, pos)
        else:
            surface.blit(pygame.transform.flip(self.image, True, False), pos)

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, platform_type="ground"):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.platform_type = platform_type
        self.draw_platform()

    def draw_platform(self):
        if self.platform_type == "ground":
            self.image.fill(BROWN)
            pygame.draw.rect(self.image, GREEN, (0, 0, self.rect.width, 8))
            for i in range(0, self.rect.width, 16):
                pygame.draw.rect(self.image, DARK_GREEN, (i + 4, 2, 8, 4))
        elif self.platform_type == "brick":
            self.image.fill((180, 100, 50))
            for row in range(0, self.rect.height, 16):
                offset = 16 if (row // 16) % 2 else 0
                for col in range(-offset, self.rect.width, 32):
                    pygame.draw.rect(self.image, (140, 70, 30), (col, row, 30, 14))
                    pygame.draw.rect(self.image, (200, 120, 70), (col + 2, row + 2, 26, 2))
        elif self.platform_type == "stone":
            self.image.fill(GRAY)
            for i in range(0, self.rect.width, 32):
                for j in range(0, self.rect.height, 32):
                    pygame.draw.rect(self.image, DARK_GRAY, (i, j, 30, 30))
                    pygame.draw.rect(self.image, (180, 180, 180), (i + 2, j + 2, 26, 2))

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, enemy_type="goomba"):
        super().__init__()
        self.enemy_type = enemy_type
        self.width = 28
        self.height = 28
        self.image = self.create_sprite()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.vel_x = 2
        self.vel_y = 0
        self.gravity = 0.5
        self.direction = 1
        self.patrol_start = x - 100
        self.patrol_end = x + 100
        self.animation_timer = 0

    def create_sprite(self):
        surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        if self.enemy_type == "goomba":
            pygame.draw.ellipse(surface, (139, 90, 43), (2, 0, 24, 16))
            pygame.draw.ellipse(surface, (180, 120, 60), (4, 2, 20, 12))
            pygame.draw.rect(surface, (139, 90, 43), (4, 12, 20, 12))
            pygame.draw.circle(surface, WHITE, (9, 10), 4)
            pygame.draw.circle(surface, WHITE, (19, 10), 4)
            pygame.draw.circle(surface, BLACK, (10, 11), 2)
            pygame.draw.circle(surface, BLACK, (20, 11), 2)
            pygame.draw.ellipse(surface, (100, 60, 30), (2, 22, 10, 6))
            pygame.draw.ellipse(surface, (100, 60, 30), (16, 22, 10, 6))
        elif self.enemy_type == "spike":
            pygame.draw.rect(surface, GRAY, (4, 14, 20, 14))
            pygame.draw.polygon(surface, GRAY, [(4, 14), (14, 0), (24, 14)])
            pygame.draw.polygon(surface, RED, [(8, 14), (14, 4), (20, 14)])
        elif self.enemy_type == "flying":
            pygame.draw.ellipse(surface, PURPLE, (4, 8, 20, 16))
            pygame.draw.polygon(surface, PURPLE, [(0, 12), (8, 8), (8, 16)])
            pygame.draw.polygon(surface, PURPLE, [(28, 12), (20, 8), (20, 16)])
            pygame.draw.circle(surface, WHITE, (10, 14), 3)
            pygame.draw.circle(surface, WHITE, (18, 14), 3)
            pygame.draw.circle(surface, RED, (10, 14), 1)
            pygame.draw.circle(surface, RED, (18, 14), 1)
        return surface

    def update(self, platforms):
        self.vel_y += self.gravity
        if self.vel_y > 10:
            self.vel_y = 10

        if self.enemy_type != "spike":
            self.rect.x += self.vel_x * self.direction

            if self.rect.x <= self.patrol_start or self.rect.x >= self.patrol_end:
                self.direction *= -1

        self.rect.y += self.vel_y
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.vel_y > 0:
                    self.rect.bottom = platform.rect.top
                    self.vel_y = 0

class Boss(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.width = 64
        self.height = 80
        self.image = self.create_sprite()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.health = 5
        self.max_health = 5
        self.vel_x = 3
        self.vel_y = 0
        self.gravity = 0.5
        self.direction = -1
        self.attack_timer = 0
        self.attack_cooldown = 120
        self.phase = 1
        self.projectiles = pygame.sprite.Group()
        self.invincible = False
        self.invincible_timer = 0
        self.patrol_start = x - 200
        self.patrol_end = x + 100

    def create_sprite(self):
        surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(surface, (80, 0, 0), (8, 20, 48, 50))
        pygame.draw.rect(surface, (120, 0, 0), (12, 24, 40, 42))
        pygame.draw.ellipse(surface, (60, 0, 0), (8, 0, 48, 30))
        pygame.draw.polygon(surface, (40, 0, 0), [(12, 5), (20, 0), (24, 10)])
        pygame.draw.polygon(surface, (40, 0, 0), [(40, 5), (44, 0), (52, 10)])
        pygame.draw.circle(surface, YELLOW, (22, 18), 6)
        pygame.draw.circle(surface, YELLOW, (42, 18), 6)
        pygame.draw.circle(surface, RED, (22, 18), 3)
        pygame.draw.circle(surface, RED, (42, 18), 3)
        pygame.draw.rect(surface, (60, 0, 0), (0, 35, 12, 30))
        pygame.draw.rect(surface, (60, 0, 0), (52, 35, 12, 30))
        pygame.draw.rect(surface, (40, 0, 0), (12, 65, 16, 15))
        pygame.draw.rect(surface, (40, 0, 0), (36, 65, 16, 15))
        return surface

    def update(self, platforms, player):
        if self.invincible:
            self.invincible_timer -= 1
            if self.invincible_timer <= 0:
                self.invincible = False

        self.vel_y += self.gravity
        if self.vel_y > 10:
            self.vel_y = 10

        speed = self.vel_x * (1.5 if self.phase == 2 else 1)
        self.rect.x += speed * self.direction

        if self.rect.x <= self.patrol_start or self.rect.x >= self.patrol_end:
            self.direction *= -1

        self.rect.y += self.vel_y
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.vel_y > 0:
                    self.rect.bottom = platform.rect.top
                    self.vel_y = 0

        self.attack_timer += 1
        cooldown = self.attack_cooldown if self.phase == 1 else self.attack_cooldown // 2
        if self.attack_timer >= cooldown:
            self.attack_timer = 0
            self.shoot_projectile(player)

        self.projectiles.update()
        
        if self.health <= self.max_health // 2:
            self.phase = 2

    def shoot_projectile(self, player):
        direction = 1 if player.rect.x > self.rect.x else -1
        proj = Projectile(self.rect.centerx, self.rect.centery, direction)
        self.projectiles.add(proj)

    def take_damage(self):
        if not self.invincible:
            self.health -= 1
            self.invincible = True
            self.invincible_timer = 60
            return True
        return False

    def draw(self, surface, camera):
        if self.invincible and (self.invincible_timer // 3) % 2 == 0:
            return
        pos = camera.apply(self)
        surface.blit(self.image, pos)
        health_bar_width = 60
        health_ratio = self.health / self.max_health
        pygame.draw.rect(surface, RED, (pos.x + 2, pos.y - 15, health_bar_width, 8))
        pygame.draw.rect(surface, GREEN, (pos.x + 2, pos.y - 15, health_bar_width * health_ratio, 8))
        pygame.draw.rect(surface, BLACK, (pos.x + 2, pos.y - 15, health_bar_width, 8), 2)

class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        super().__init__()
        self.image = pygame.Surface((16, 16), pygame.SRCALPHA)
        pygame.draw.circle(self.image, RED, (8, 8), 8)
        pygame.draw.circle(self.image, ORANGE, (8, 8), 5)
        pygame.draw.circle(self.image, YELLOW, (8, 8), 2)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.vel_x = 6 * direction
        self.lifetime = 180

    def update(self):
        self.rect.x += self.vel_x
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.kill()

class Powerup(pygame.sprite.Sprite):
    def __init__(self, x, y, powerup_type):
        super().__init__()
        self.powerup_type = powerup_type
        self.image = pygame.Surface((24, 24), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.bob_offset = 0
        self.bob_direction = 1
        self.draw_powerup()

    def draw_powerup(self):
        if self.powerup_type == "double_jump":
            pygame.draw.rect(self.image, BLUE, (4, 4, 16, 16))
            pygame.draw.polygon(self.image, WHITE, [(12, 6), (18, 14), (12, 11), (6, 14)])
            pygame.draw.polygon(self.image, WHITE, [(12, 10), (18, 18), (12, 15), (6, 18)])
        elif self.powerup_type == "extra_life":
            pygame.draw.circle(self.image, RED, (12, 12), 10)
            pygame.draw.circle(self.image, PINK, (9, 9), 4)
            pygame.draw.circle(self.image, PINK, (15, 9), 4)
            pygame.draw.polygon(self.image, RED, [(12, 20), (4, 12), (12, 14), (20, 12)])
        elif self.powerup_type == "speed":
            pygame.draw.rect(self.image, YELLOW, (4, 4, 16, 16))
            pygame.draw.polygon(self.image, ORANGE, [(8, 4), (16, 12), (8, 12), (12, 20), (4, 12), (8, 12)])

    def update(self):
        self.bob_offset += 0.1 * self.bob_direction
        if abs(self.bob_offset) > 3:
            self.bob_direction *= -1
        self.rect.y += self.bob_direction * 0.5

    def collect(self):
        return self.powerup_type

class Flag(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((32, 128), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        pygame.draw.rect(self.image, (80, 80, 80), (14, 0, 4, 128))
        pygame.draw.polygon(self.image, GREEN, [(18, 10), (18, 50), (0, 30)])
        pygame.draw.polygon(self.image, DARK_GREEN, [(18, 15), (18, 45), (5, 30)])
        pygame.draw.circle(self.image, GOLD, (16, 5), 5)

class Coin(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((16, 16), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.animation_frame = 0
        self.draw_coin()

    def draw_coin(self):
        pygame.draw.circle(self.image, GOLD, (8, 8), 7)
        pygame.draw.circle(self.image, YELLOW, (8, 8), 5)
        pygame.draw.circle(self.image, GOLD, (8, 8), 3)

    def update(self):
        self.animation_frame += 1

class Game:
    def __init__(self):
        self.state = "menu"
        self.lives = 5
        self.score = 0
        self.current_level = 1
        self.total_levels = 6
        self.font = pygame.font.Font(None, 36)
        self.title_font = pygame.font.Font(None, 72)
        self.reset_level()

    def reset_level(self):
        self.platforms = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.coins = pygame.sprite.Group()
        self.flag = None
        self.boss = None
        self.level_width = 2400
        self.level_height = 600
        
        self.load_level(self.current_level)
        self.camera = Camera(self.level_width, self.level_height)

    def reset_game(self):
        self.lives = 5
        self.score = 0
        self.current_level = 1
        self.reset_level()

    def load_level(self, level_num):
        self.platforms.empty()
        self.enemies.empty()
        self.powerups.empty()
        self.coins.empty()
        self.boss = None

        if level_num == 1:
            self.level_width = 2400
            self.create_level_1()
        elif level_num == 2:
            self.level_width = 2800
            self.create_level_2()
        elif level_num == 3:
            self.level_width = 3200
            self.create_level_3()
        elif level_num == 4:
            self.level_width = 3600
            self.create_level_4()
        elif level_num == 5:
            self.level_width = 4000
            self.create_level_5()
        elif level_num == 6:
            self.level_width = 2000
            self.create_level_6()

        self.player = Player(100, 400)

    def create_level_1(self):
        self.platforms.add(Platform(0, 550, 600, 50, "ground"))
        self.platforms.add(Platform(700, 550, 400, 50, "ground"))
        self.platforms.add(Platform(1200, 550, 600, 50, "ground"))
        self.platforms.add(Platform(1900, 550, 500, 50, "ground"))

        self.platforms.add(Platform(300, 450, 100, 20, "brick"))
        self.platforms.add(Platform(500, 380, 100, 20, "brick"))
        self.platforms.add(Platform(750, 420, 80, 20, "brick"))
        self.platforms.add(Platform(900, 350, 100, 20, "brick"))
        self.platforms.add(Platform(1100, 280, 80, 20, "brick"))
        self.platforms.add(Platform(1350, 400, 120, 20, "brick"))
        self.platforms.add(Platform(1550, 320, 100, 20, "brick"))
        self.platforms.add(Platform(1750, 400, 100, 20, "brick"))

        self.enemies.add(Enemy(400, 520, "goomba"))
        self.enemies.add(Enemy(800, 520, "goomba"))
        self.enemies.add(Enemy(1400, 520, "goomba"))

        self.powerups.add(Powerup(350, 410, "double_jump"))
        self.powerups.add(Powerup(1150, 240, "extra_life"))

        for x in [320, 520, 920, 1380, 1580]:
            self.coins.add(Coin(x, 300))

        self.flag = Flag(2200, 422)

    def create_level_2(self):
        self.platforms.add(Platform(0, 550, 400, 50, "ground"))
        self.platforms.add(Platform(500, 550, 300, 50, "ground"))
        self.platforms.add(Platform(900, 550, 400, 50, "ground"))
        self.platforms.add(Platform(1400, 550, 300, 50, "ground"))
        self.platforms.add(Platform(1800, 550, 400, 50, "ground"))
        self.platforms.add(Platform(2300, 550, 500, 50, "ground"))

        self.platforms.add(Platform(200, 450, 80, 20, "stone"))
        self.platforms.add(Platform(350, 380, 80, 20, "stone"))
        self.platforms.add(Platform(550, 320, 100, 20, "stone"))
        self.platforms.add(Platform(750, 380, 80, 20, "stone"))
        self.platforms.add(Platform(950, 300, 100, 20, "stone"))
        self.platforms.add(Platform(1150, 250, 80, 20, "stone"))
        self.platforms.add(Platform(1350, 350, 100, 20, "stone"))
        self.platforms.add(Platform(1500, 280, 80, 20, "stone"))
        self.platforms.add(Platform(1700, 400, 100, 20, "stone"))
        self.platforms.add(Platform(1950, 320, 120, 20, "stone"))
        self.platforms.add(Platform(2150, 380, 100, 20, "stone"))

        self.enemies.add(Enemy(300, 520, "goomba"))
        self.enemies.add(Enemy(600, 520, "goomba"))
        self.enemies.add(Enemy(1000, 520, "goomba"))
        self.enemies.add(Enemy(1500, 520, "spike"))
        self.enemies.add(Enemy(2000, 520, "goomba"))

        self.powerups.add(Powerup(580, 280, "speed"))
        self.powerups.add(Powerup(1180, 210, "double_jump"))
        self.powerups.add(Powerup(2180, 340, "extra_life"))

        self.flag = Flag(2600, 422)

    def create_level_3(self):
        self.platforms.add(Platform(0, 550, 300, 50, "ground"))
        self.platforms.add(Platform(400, 550, 200, 50, "ground"))
        self.platforms.add(Platform(700, 550, 300, 50, "ground"))
        self.platforms.add(Platform(1100, 550, 200, 50, "ground"))
        self.platforms.add(Platform(1400, 550, 300, 50, "ground"))
        self.platforms.add(Platform(1800, 550, 200, 50, "ground"))
        self.platforms.add(Platform(2100, 550, 300, 50, "ground"))
        self.platforms.add(Platform(2500, 550, 200, 50, "ground"))
        self.platforms.add(Platform(2800, 550, 400, 50, "ground"))

        self.platforms.add(Platform(150, 470, 60, 20, "brick"))
        self.platforms.add(Platform(280, 400, 60, 20, "brick"))
        self.platforms.add(Platform(450, 330, 60, 20, "brick"))
        self.platforms.add(Platform(600, 400, 60, 20, "brick"))
        self.platforms.add(Platform(800, 450, 80, 20, "brick"))
        self.platforms.add(Platform(950, 370, 60, 20, "brick"))
        self.platforms.add(Platform(1050, 300, 60, 20, "brick"))
        self.platforms.add(Platform(1200, 400, 80, 20, "brick"))
        self.platforms.add(Platform(1450, 350, 60, 20, "brick"))
        self.platforms.add(Platform(1600, 280, 60, 20, "brick"))
        self.platforms.add(Platform(1750, 350, 60, 20, "brick"))
        self.platforms.add(Platform(1900, 420, 80, 20, "brick"))
        self.platforms.add(Platform(2150, 350, 60, 20, "brick"))
        self.platforms.add(Platform(2300, 280, 60, 20, "brick"))
        self.platforms.add(Platform(2450, 350, 60, 20, "brick"))
        self.platforms.add(Platform(2600, 420, 80, 20, "brick"))

        for x in [200, 500, 900, 1250, 1550, 1950, 2350, 2650]:
            self.enemies.add(Enemy(x, 520, "goomba"))
        for x in [700, 1100, 1800, 2500]:
            self.enemies.add(Enemy(x, 520, "spike"))

        self.powerups.add(Powerup(480, 290, "double_jump"))
        self.powerups.add(Powerup(1080, 260, "speed"))
        self.powerups.add(Powerup(1630, 240, "extra_life"))
        self.powerups.add(Powerup(2330, 240, "double_jump"))

        self.flag = Flag(3000, 422)

    def create_level_4(self):
        self.platforms.add(Platform(0, 550, 250, 50, "ground"))
        for i in range(8):
            self.platforms.add(Platform(350 + i * 400, 550, 150, 50, "ground"))
        self.platforms.add(Platform(3400, 550, 200, 50, "ground"))

        heights = [480, 420, 360, 300, 360, 420, 360, 300, 250, 300, 360, 420]
        for i, h in enumerate(heights):
            self.platforms.add(Platform(200 + i * 260, h, 50, 20, "stone"))

        self.platforms.add(Platform(1000, 200, 100, 20, "stone"))
        self.platforms.add(Platform(1800, 180, 100, 20, "stone"))
        self.platforms.add(Platform(2600, 200, 100, 20, "stone"))

        for x in [400, 750, 1150, 1550, 1950, 2350, 2750]:
            self.enemies.add(Enemy(x, 520, "goomba"))
        for x in [600, 1000, 1400, 1800, 2200, 2600, 3000]:
            e = Enemy(x, 300, "flying")
            e.gravity = 0
            self.enemies.add(e)

        self.powerups.add(Powerup(1030, 160, "double_jump"))
        self.powerups.add(Powerup(1830, 140, "extra_life"))
        self.powerups.add(Powerup(2630, 160, "speed"))

        self.flag = Flag(3450, 422)

    def create_level_5(self):
        self.platforms.add(Platform(0, 550, 200, 50, "ground"))
        for i in range(10):
            self.platforms.add(Platform(300 + i * 370, 550, 120, 50, "ground"))
        self.platforms.add(Platform(3800, 550, 200, 50, "ground"))

        tower_positions = [400, 900, 1500, 2100, 2700, 3300]
        for pos in tower_positions:
            for h in range(3):
                self.platforms.add(Platform(pos, 450 - h * 80, 80, 20, "brick"))
            self.platforms.add(Platform(pos - 60, 250, 200, 20, "brick"))

        for x in [350, 700, 1100, 1550, 1900, 2200, 2600, 2900, 3200, 3600]:
            self.enemies.add(Enemy(x, 520, "goomba"))
        for x in [500, 1000, 1600, 2200, 2800, 3400]:
            self.enemies.add(Enemy(x, 520, "spike"))
        for x in [600, 1200, 1800, 2400, 3000]:
            e = Enemy(x, 250, "flying")
            e.gravity = 0
            self.enemies.add(e)

        self.powerups.add(Powerup(440, 200, "double_jump"))
        self.powerups.add(Powerup(1540, 200, "extra_life"))
        self.powerups.add(Powerup(2140, 200, "speed"))
        self.powerups.add(Powerup(2740, 200, "extra_life"))
        self.powerups.add(Powerup(3340, 200, "double_jump"))

        self.flag = Flag(3900, 422)

    def create_level_6(self):
        self.platforms.add(Platform(0, 550, 2000, 50, "stone"))
        
        self.platforms.add(Platform(100, 450, 150, 20, "brick"))
        self.platforms.add(Platform(350, 380, 100, 20, "brick"))
        self.platforms.add(Platform(550, 320, 100, 20, "brick"))
        self.platforms.add(Platform(750, 400, 100, 20, "brick"))
        self.platforms.add(Platform(1000, 350, 150, 20, "brick"))
        self.platforms.add(Platform(1250, 420, 100, 20, "brick"))
        self.platforms.add(Platform(1450, 350, 150, 20, "brick"))
        self.platforms.add(Platform(1700, 400, 100, 20, "brick"))

        self.boss = Boss(1600, 470)
        self.boss.patrol_start = 1200
        self.boss.patrol_end = 1800

        self.powerups.add(Powerup(130, 410, "double_jump"))
        self.powerups.add(Powerup(580, 280, "extra_life"))
        self.powerups.add(Powerup(1030, 310, "speed"))

        self.enemies.add(Enemy(400, 520, "goomba"))
        self.enemies.add(Enemy(700, 520, "spike"))
        self.enemies.add(Enemy(1100, 520, "goomba"))

        self.flag = Flag(1900, 422)

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if self.state == "menu":
                        if event.key == pygame.K_RETURN:
                            self.state = "playing"
                    elif self.state == "playing":
                        if event.key == pygame.K_SPACE or event.key == pygame.K_UP or event.key == pygame.K_w:
                            self.player.jump()
                    elif self.state == "game_over":
                        if event.key == pygame.K_RETURN:
                            self.reset_game()
                            self.state = "playing"
                    elif self.state == "victory":
                        if event.key == pygame.K_RETURN:
                            self.reset_game()
                            self.state = "menu"

            if self.state == "menu":
                self.draw_menu()
            elif self.state == "playing":
                self.update()
                self.draw()
            elif self.state == "game_over":
                self.draw_game_over()
            elif self.state == "victory":
                self.draw_victory()

            pygame.display.flip()
            clock.tick(FPS)

        pygame.quit()
        sys.exit()

    def update(self):
        result = self.player.update(self.platforms, self.enemies, self.powerups, self.coins, self.flag)

        if result == "double_jump":
            self.player.can_double_jump = True
        elif result == "extra_life":
            self.lives += 1
            self.score += 500
        elif result == "speed":
            self.player.speed_boost = True
            self.player.speed_boost_timer = 300
        elif result == "enemy_killed":
            self.score += 100
        elif result == "coin_collected":
            self.score += 50
        elif result == "hit" or result == "died":
            self.lives -= 1
            self.score = max(0, self.score - 500)
            if self.lives <= 0:
                self.state = "game_over"
            else:
                self.reset_level()
                self.player.invincible = True
                self.player.invincible_timer = 120
                return
        elif result == "level_complete":
            if self.current_level == 6 and self.boss is not None:
                pass  # Do not complete level if boss is still alive in level 6
            else:
                self.score += 1000
                self.current_level += 1
                if self.current_level > self.total_levels:
                    self.state = "victory"
                else:
                    self.reset_level()
                    return

        for enemy in self.enemies:
            enemy.update(self.platforms)

        for coin in self.coins:
            coin.update()

        if self.boss:
            self.boss.update(self.platforms, self.player)

            for proj in list(self.boss.projectiles):
                if self.player.rect.colliderect(proj.rect) and not self.player.invincible:
                    proj.kill()
                    self.lives -= 1
                    self.score = max(0, self.score - 500)
                    if self.lives <= 0:
                        self.state = "game_over"
                    else:
                        self.reset_level()
                        self.player.invincible = True
                        self.player.invincible_timer = 120
                        return

            if self.player.rect.colliderect(self.boss.rect):
                if self.player.vel_y > 0 and self.player.rect.bottom < self.boss.rect.centery:
                    if self.boss.take_damage():
                        self.player.vel_y = self.player.jump_power
                        self.score += 200
                        if self.boss.health <= 0:
                            self.boss = None
                            self.score += 2000
                elif not self.player.invincible:
                    self.lives -= 1
                    self.score = max(0, self.score - 500)
                    if self.lives <= 0:
                        self.state = "game_over"
                    else:
                        self.reset_level()
                        self.player.invincible = True
                        self.player.invincible_timer = 120
                        return

        for powerup in self.powerups:
            powerup.update()

        self.camera.update(self.player)

    def draw(self):
        screen.fill(SKY_BLUE)

        for i in range(0, SCREEN_WIDTH, 64):
            cloud_x = (i - self.camera.camera.x // 4) % (SCREEN_WIDTH + 100) - 50
            pygame.draw.ellipse(screen, WHITE, (cloud_x, 50, 60, 30))
            pygame.draw.ellipse(screen, WHITE, (cloud_x + 20, 35, 50, 35))
            pygame.draw.ellipse(screen, WHITE, (cloud_x + 40, 50, 60, 30))

        for platform in self.platforms:
            screen.blit(platform.image, self.camera.apply(platform))

        for coin in self.coins:
            screen.blit(coin.image, self.camera.apply(coin))

        for powerup in self.powerups:
            screen.blit(powerup.image, self.camera.apply(powerup))

        for enemy in self.enemies:
            screen.blit(enemy.image, self.camera.apply(enemy))

        if self.flag:
            screen.blit(self.flag.image, self.camera.apply(self.flag))

        if self.boss:
            self.boss.draw(screen, self.camera)
            for proj in self.boss.projectiles:
                screen.blit(proj.image, self.camera.apply(proj))

        self.player.draw(screen, self.camera)

        self.draw_hud()

    def draw_hud(self):
        pygame.draw.rect(screen, (0, 0, 0, 128), (0, 0, SCREEN_WIDTH, 40))
        
        lives_text = self.font.render(f"Lives: {self.lives}", True, WHITE)
        screen.blit(lives_text, (20, 10))

        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        screen.blit(score_text, (200, 10))

        level_text = self.font.render(f"Level: {self.current_level}/{self.total_levels}", True, WHITE)
        screen.blit(level_text, (400, 10))

        if self.player.can_double_jump:
            pygame.draw.rect(screen, BLUE, (600, 8, 24, 24))
            dj_text = self.font.render("2J", True, WHITE)
            screen.blit(dj_text, (603, 10))

        if self.player.speed_boost:
            pygame.draw.rect(screen, YELLOW, (640, 8, 24, 24))
            sp_text = self.font.render("S", True, BLACK)
            screen.blit(sp_text, (648, 10))

    def draw_menu(self):
        screen.fill((50, 50, 100))

        title = self.title_font.render("SUPER DANIEL JACCOSY", True, GOLD)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 150))
        screen.blit(title, title_rect)

        subtitle = self.font.render("A Pixel Adventure", True, WHITE)
        sub_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 220))
        screen.blit(subtitle, sub_rect)

        player_preview = Player(SCREEN_WIDTH // 2 - 12, 280)
        screen.blit(player_preview.image, (player_preview.rect.x, player_preview.rect.y))

        instructions = [
            "Arrow Keys / WASD - Move",
            "Space / Up / W - Jump",
            "",
            "Collect powerups for abilities!",
            "Stomp on enemies to defeat them!",
            "Reach the flag to complete each level!",
            "",
            "Press ENTER to Start"
        ]

        for i, line in enumerate(instructions):
            text = self.font.render(line, True, WHITE)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, 350 + i * 30))
            screen.blit(text, text_rect)

    def draw_game_over(self):
        screen.fill((100, 0, 0))

        title = self.title_font.render("GAME OVER", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 200))
        screen.blit(title, title_rect)

        score_text = self.font.render(f"Final Score: {self.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 300))
        screen.blit(score_text, score_rect)

        level_text = self.font.render(f"Reached Level: {self.current_level}", True, WHITE)
        level_rect = level_text.get_rect(center=(SCREEN_WIDTH // 2, 350))
        screen.blit(level_text, level_rect)

        restart = self.font.render("Press ENTER to Try Again", True, YELLOW)
        restart_rect = restart.get_rect(center=(SCREEN_WIDTH // 2, 450))
        screen.blit(restart, restart_rect)

    def draw_victory(self):
        screen.fill((0, 100, 0))

        title = self.title_font.render("VICTORY!", True, GOLD)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 150))
        screen.blit(title, title_rect)

        congrats = self.font.render("Congratulations, Daniel Jaccosy!", True, WHITE)
        congrats_rect = congrats.get_rect(center=(SCREEN_WIDTH // 2, 250))
        screen.blit(congrats, congrats_rect)

        score_text = self.font.render(f"Final Score: {self.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 320))
        screen.blit(score_text, score_rect)

        complete = self.font.render("You defeated the boss and saved the day!", True, WHITE)
        complete_rect = complete.get_rect(center=(SCREEN_WIDTH // 2, 380))
        screen.blit(complete, complete_rect)

        restart = self.font.render("Press ENTER to Play Again", True, YELLOW)
        restart_rect = restart.get_rect(center=(SCREEN_WIDTH // 2, 480))
        screen.blit(restart, restart_rect)


if __name__ == "__main__":
    game = Game()
    game.run()
