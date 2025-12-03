import pygame, sys, random

# ------------------
# SETTINGS
# ------------------
SCREEN_WIDTH = 960
SCREEN_HEIGHT = 640
FPS = 60
BLOCK = 32

PLAYER_WIDTH = BLOCK
PLAYER_HEIGHT = BLOCK*2
GRAVITY = 1.2
MOVE_SPEED = 5
JUMP_SPEED = 18
COYOTE_TIME = 0.12
MAX_LIVES = 10
LEVELS_COUNT = 4
TIME_PER_LEVEL = 100  # seconden
POWERUP_DURATION = 10  # seconden

# ------------------
# COLORS
# ------------------
WHITE = (255,255,255)
BLACK = (0,0,0)
BLUE = (100, 149, 237)
RED = (255,0,0)
YELLOW = (255,255,0)
GREEN = (0,255,0)
GRAY = (100,100,100)
PURPLE = (160,32,240)
ORANGE = (255,165,0)
CYAN = (0,255,255)
MAGENTA = (255,0,255)

# ------------------
# CLASSES
# ------------------
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((PLAYER_WIDTH, PLAYER_HEIGHT))
        self.image.fill(BLUE)
        self.rect = self.image.get_rect(topleft=(x,y))
        self.vel_y = 0
        self.on_ground = False
        self.coyote_timer = 0
        self.double_jump_active = False
        self.double_jump_available = False

    def update(self, keys, platforms):
        dx = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -MOVE_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = MOVE_SPEED

        self.vel_y += GRAVITY
        if self.vel_y > 25:
            self.vel_y = 25
        dy = self.vel_y

        # Horizontal collision
        self.rect.x += dx
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if dx > 0:
                    self.rect.right = platform.rect.left
                elif dx < 0:
                    self.rect.left = platform.rect.right

        # Vertical collision
        self.rect.y += dy
        self.on_ground = False
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if dy > 0:
                    self.rect.bottom = platform.rect.top
                    self.vel_y = 0
                    self.on_ground = True
                    self.coyote_timer = COYOTE_TIME
                elif dy < 0:
                    self.rect.top = platform.rect.bottom
                    self.vel_y = 0

        if not self.on_ground:
            self.coyote_timer -= 1/FPS
        else:
            self.coyote_timer = COYOTE_TIME

    def jump(self):
        if self.on_ground or self.coyote_timer > 0:
            self.vel_y = -JUMP_SPEED
        elif self.double_jump_active and self.double_jump_available:
            self.vel_y = -JUMP_SPEED
            self.double_jump_available = False

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, speed=2):
        super().__init__()
        self.image = pygame.Surface((BLOCK,BLOCK))
        self.image.fill(RED)
        self.rect = self.image.get_rect(topleft=(x,y))
        self.speed = speed
        self.direction = -1

    def update(self, player, platforms):
        dist = abs(self.rect.centerx - player.rect.centerx)
        if dist < 200:
            self.direction = -1 if player.rect.centerx < self.rect.centerx else 1
        self.rect.x += self.direction * self.speed
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.direction > 0:
                    self.rect.right = platform.rect.left
                    self.direction *= -1
                elif self.direction < 0:
                    self.rect.left = platform.rect.right
                    self.direction *= -1

class Boss(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((BLOCK*3,BLOCK*3))
        self.image.fill(PURPLE)
        self.rect = self.image.get_rect(topleft=(x,y))
        self.speed = 3
        self.direction = 1
        self.health = 3

    def update(self, player, platforms):
        self.rect.x += self.direction*self.speed
        for p in platforms:
            if self.rect.colliderect(p.rect):
                if self.direction>0:
                    self.rect.right=p.rect.left
                    self.direction*=-1
                elif self.direction<0:
                    self.rect.left=p.rect.right
                    self.direction*=-1

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, w=BLOCK, h=BLOCK):
        super().__init__()
        self.image = pygame.Surface((w,h))
        self.image.fill(GRAY)
        self.rect = self.image.get_rect(topleft=(x,y))

class Coin(pygame.sprite.Sprite):
    def __init__(self,x,y):
        super().__init__()
        self.image = pygame.Surface((BLOCK//2,BLOCK//2))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect(center=(x,y))

class Powerup(pygame.sprite.Sprite):
    def __init__(self,x,y,kind='double_jump'):
        super().__init__()
        self.image = pygame.Surface((BLOCK//2,BLOCK//2))
        if kind=='double_jump': self.image.fill(GREEN)
        elif kind=='extra_life': self.image.fill(ORANGE)
        elif kind=='invincibility': self.image.fill(MAGENTA)
        elif kind=='high_jump': self.image.fill(CYAN)
        self.rect = self.image.get_rect(center=(x,y))
        self.kind = kind

class Spike(pygame.sprite.Sprite):
    def __init__(self,x,y):
        super().__init__()
        self.image = pygame.Surface((BLOCK,BLOCK//2))
        self.image.fill(RED)
        self.rect = self.image.get_rect(bottomleft=(x,y))

class Flag(pygame.sprite.Sprite):
    def __init__(self,x,y):
        super().__init__()
        self.image = pygame.Surface((BLOCK//2,BLOCK*1.5))
        self.image.fill(PURPLE)
        self.rect = self.image.get_rect(midbottom=(x,y))

# ------------------
# LEVEL GENERATOR
# ------------------
def generate_level(level_index):
    platforms = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    coins = pygame.sprite.Group()
    powerups = pygame.sprite.Group()
    spikes = pygame.sprite.Group()
    flags = pygame.sprite.Group()
    boss_group = pygame.sprite.Group()

    level_length = SCREEN_WIDTH*3 + level_index*BLOCK*20

    for x in range(0, level_length, BLOCK):
        platforms.add(Platform(x, SCREEN_HEIGHT-BLOCK))
        if random.random()<0.05+0.01*level_index:
            platforms.add(Platform(x, SCREEN_HEIGHT-BLOCK*3 - random.randint(0,3)*BLOCK))
        if random.random()<0.03+0.01*level_index:
            coins.add(Coin(x, SCREEN_HEIGHT-BLOCK*4 - random.randint(0,2)*BLOCK))
        if random.random()<0.01+0.005*level_index:
            spikes.add(Spike(x, SCREEN_HEIGHT-BLOCK))
        if random.random()<0.01+0.005*level_index:
            enemies.add(Enemy(x, SCREEN_HEIGHT-BLOCK*2))

    kinds = ['double_jump','extra_life','invincibility','high_jump']
    for kind in kinds:
        powerups.add(Powerup(random.randint(200, level_length-200), SCREEN_HEIGHT-BLOCK*4, kind))

    flags.add(Flag(level_length-100, SCREEN_HEIGHT-BLOCK))

    if level_index==3:
        boss_group.add(Boss(level_length-300, SCREEN_HEIGHT-BLOCK*4-BLOCK*3))

    return platforms, enemies, coins, powerups, spikes, flags, boss_group, level_length

# ------------------
# GAME LOOP
# ------------------
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Super Daniel Jaccosy")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("monospace", 24)

    level_index = 0
    lives = MAX_LIVES
    score = 0
    running = True

    player = Player(100, SCREEN_HEIGHT-PLAYER_HEIGHT-BLOCK)
    platforms, enemies, coins, powerups, spikes, flags, boss_group, level_length = generate_level(level_index)

    time_left = TIME_PER_LEVEL
    camera_x = 0
    powerup_text = ""
    powerup_timer = 0
    active_powerups = {}

    while running:
        dt = clock.tick(FPS)/1000
        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type==pygame.KEYDOWN:
                if event.key in [pygame.K_UP, pygame.K_w]:
                    player.jump()

        # Update
        player.update(keys, platforms)
        enemies.update(player, platforms)
        boss_group.update(player, platforms)

        # Coins
        for coin in coins:
            if player.rect.colliderect(coin.rect):
                score+=10
                coin.kill()

        # Powerups oppakken
        for pu in powerups:
            if player.rect.colliderect(pu.rect):
                powerup_text = f"{pu.kind.replace('_',' ').title()}"
                powerup_timer = 120

                if pu.kind=='double_jump':
                    player.double_jump_active = True
                    player.double_jump_available = True
                    active_powerups['double_jump'] = POWERUP_DURATION*FPS
                elif pu.kind=='high_jump':
                    global JUMP_SPEED
                    JUMP_SPEED = 25
                    active_powerups['high_jump'] = POWERUP_DURATION*FPS
                elif pu.kind=='invincibility':
                    active_powerups['invincibility'] = POWERUP_DURATION*FPS
                elif pu.kind=='extra_life':
                    lives += 1  # permanent

                pu.kill()

        # Powerup timers
        for key in list(active_powerups.keys()):
            active_powerups[key] -=1
            if active_powerups[key]<=0:
                if key=='double_jump':
                    player.double_jump_active = False
                    player.double_jump_available = False
                elif key=='high_jump':
                    JUMP_SPEED = 18
                del active_powerups[key]

        invincible = 'invincibility' in active_powerups

        # Spikes
        for spike in spikes:
            if player.rect.colliderect(spike.rect) and not invincible:
                lives-=1
                player.rect.topleft=(100, SCREEN_HEIGHT-PLAYER_HEIGHT-BLOCK)
                player.vel_y=0

        # Enemy collision
        for enemy in enemies:
            if player.rect.colliderect(enemy.rect):
                if player.vel_y>0:
                    enemy.kill()
                    player.vel_y=-JUMP_SPEED/2
                    score+=50
                else:
                    if not invincible:
                        lives-=1
                        player.rect.topleft=(100, SCREEN_HEIGHT-PLAYER_HEIGHT-BLOCK)
                        player.vel_y=0

        # Boss collision
        for b in boss_group:
            if player.rect.colliderect(b.rect):
                if player.vel_y>0:
                    b.health-=1
                    player.vel_y=-JUMP_SPEED/2
                    if b.health<=0:
                        boss_group.remove(b)
                else:
                    if not invincible:
                        lives-=1
                        player.rect.topleft=(100, SCREEN_HEIGHT-PLAYER_HEIGHT-BLOCK)
                        player.vel_y=0

        # Timer
        time_left -= dt
        if time_left<=0:
            lives-=1
            player.rect.topleft=(100, SCREEN_HEIGHT-PLAYER_HEIGHT-BLOCK)
            player.vel_y=0
            time_left=TIME_PER_LEVEL

        # Camera
        camera_x = player.rect.centerx - SCREEN_WIDTH//2
        camera_x = max(0, min(camera_x, level_length-SCREEN_WIDTH))

        # Check flag
        for flag in flags:
            if player.rect.colliderect(flag.rect):
                level_index+=1
                if level_index>=LEVELS_COUNT:
                    running=False
                    victory=True
                else:
                    platforms, enemies, coins, powerups, spikes, flags, boss_group, level_length = generate_level(level_index)
                    player.rect.topleft=(100, SCREEN_HEIGHT-PLAYER_HEIGHT-BLOCK)
                    time_left = TIME_PER_LEVEL
                    camera_x = 0
                    active_powerups.clear()
                    JUMP_SPEED = 18
                    player.double_jump_active=False
                    player.double_jump_available=False

        # Draw
        screen.fill(BLACK)
        for group in [platforms, coins, spikes, powerups, enemies, flags, boss_group]:
            for s in group:
                screen.blit(s.image, (s.rect.x-camera_x, s.rect.y))
        screen.blit(player.image, (player.rect.x-camera_x, player.rect.y))

        # HUD
        hud = font.render(f"Lives: {lives}  Score: {score}  Time: {int(time_left)}  Level: {level_index+1}", True, WHITE)
        screen.blit(hud, (10,10))
        # Powerup tekst rechtsboven
        if powerup_text:
            pt = font.render(powerup_text, True, ORANGE)
            screen.blit(pt, (SCREEN_WIDTH - pt.get_width() - 20, 10))

        pygame.display.flip()

        if lives<=0:
            running=False
            victory=False

    # End screen
    screen.fill(BLACK)
    msg = "VICTORY!" if 'victory' in locals() and victory else "GAME OVER"
    end_text = font.render(msg, True, RED)
    screen.blit(end_text, (SCREEN_WIDTH//2-80, SCREEN_HEIGHT//2))
    pygame.display.flip()
    pygame.time.wait(3000)
    pygame.quit()

if __name__=="__main__":
    main()
