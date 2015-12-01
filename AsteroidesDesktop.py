import random
import math
import os, sys
import Timer
import pygame
from pygame.locals import *

pygame.init()
pygame.mixer.init()
# globals for user interface
WIDTH = 800
HEIGHT = 600
score = 0
# lives = 3
time = 0
pressed_left = False
pressed_right = False
wait_for_stop_game = .0

screen = pygame.display.set_mode((WIDTH, HEIGHT))
canvas = screen.convert_alpha()
pygame.display.set_caption(("Asteroides."))


class ImageInfo:
    def __init__(self, center, size, radius=0, lifespan=None, animated=False):
        self.center = center
        self.size = size
        self.radius = radius
        if lifespan:
            self.lifespan = lifespan
        else:
            self.lifespan = float('inf')
        self.animated = animated

    def get_center(self):
        return self.center

    def get_size(self):
        return self.size

    def get_radius(self):
        return self.radius

    def get_lifespan(self):
        return self.lifespan

    def get_animated(self):
        return self.animated


# art assets created by Kim Lathrop, may be freely re-used in non-commercial projects, please credit Kim
# debris images - debris1_brown.png, debris2_brown.png, debris3_brown.png, debris4_brown.png
#                 debris1_blue.png, debris2_blue.png, debris3_blue.png, debris4_blue.png, debris_blend.png
debris_info = ImageInfo([320, 240], [640, 480])
debris_image = pygame.image.load(os.path.join('data', 'debris2_blue.png')).convert_alpha()

# nebula images - nebula_brown.png, nebula_blue.png
nebula_info = ImageInfo([400, 300], [800, 600])
nebula_image = pygame.image.load(os.path.join('data', 'nebula_blue.f2014.png')).convert_alpha()

# splash image
splash_info = ImageInfo([200, 150], [400, 300])
splash_image = pygame.image.load(os.path.join('data', 'splash.png')).convert_alpha()

# ship image
ship_info = ImageInfo([45, 45], [90, 90], 35)
ship_image = pygame.image.load(os.path.join('data', 'double_ship.png')).convert_alpha()

# missile image - shot1.png, shot2.png, shot3.png
missile_info = ImageInfo([5, 5], [10, 10], 3, 50)
missile_image = pygame.image.load(os.path.join('data', 'shot2.png')).convert_alpha()

# asteroid images - asteroid_blue.png, asteroid_brown.png, asteroid_blend.png
asteroid_info = ImageInfo([45, 45], [90, 90], 40)
asteroid_image = []
asteroid_image.append(pygame.image.load(os.path.join('data', 'asteroid_blue.png')).convert_alpha())
asteroid_image.append(pygame.image.load(os.path.join('data', 'asteroid_brown.png')).convert_alpha())
asteroid_image.append(pygame.image.load(os.path.join('data', 'asteroid_blend.png')).convert_alpha())


# animated explosion - explosion_orange.png, explosion_blue.png, explosion_blue2.png, explosion_alpha.png
explosion_info = ImageInfo([64, 64], [128, 128], 17, 24, True)  # 24
explosion_image = []
explosion_image.append(pygame.image.load(os.path.join('data', 'explosion_orange.png')).convert_alpha())
explosion_image.append(pygame.image.load(os.path.join('data', 'explosion_blue.png')).convert_alpha())
explosion_image.append(pygame.image.load(os.path.join('data', 'explosion_blue2.png')).convert_alpha())
explosion_image.append(pygame.image.load(os.path.join('data', 'explosion_alpha.png')).convert_alpha())

# sound assets purchased from sounddogs.com, please do not redistribute
soundtrack = pygame.mixer.music.load(os.path.join('data', 'soundtrack.mp3'))
pygame.mixer.music.set_volume(.3)
missile_sound = pygame.mixer.Sound(os.path.join('data', 'missile.mp3.wav'))
missile_sound.set_volume(.5)
ship_thrust_sound = pygame.mixer.Sound(os.path.join('data', 'thrust.mp3.wav'))
explosion_sound = pygame.mixer.Sound(os.path.join('data', 'explosion.mp3.wav'))


# helper functions to handle transformations
def angle_to_vector(ang):
    return [math.cos(ang), -math.sin(ang)]


def dist(p, q):
    return math.sqrt((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2)


def process_sprite_group(sprite_group, canvas):
    for sprite in list(sprite_group):
        if (sprite.update()):
            sprite.draw(canvas)
        else:
            sprite_group.remove(sprite)


def group_collide(collection, other_object):
    """looks for collide between each object in collection and other_object
    until found a collide, remove the object from the collection and return True, False if
    not collide detected."""
    for obj in list(collection):
        if other_object.collide(obj):
            collection.discard(obj)
            explosion_group.add(
                Sprite(obj.get_position(), [0, 0], 0, 0, explosion_image[random.randrange(0, 3)], explosion_info,
                       explosion_sound))
            return True
    return False


def group_group_collide(group_destroyable, group_destroyer):
    counter = 0
    for obj in list(group_destroyer):
        if group_collide(group_destroyable, obj):
            counter += 1
            # comment out next line to have missiles that survive to asteroids
            group_destroyer.remove(obj)
    return counter


def draw_image(screen, image, center_to_show, image_size, pos, angle):
    """recibe screen, image, center_to_show centro de la porcion de imagen a mostrar,
    image_size=area a mostrar centrada en center_to_show, pos=donde poner la imagen
    angle=en radianes. pega la porcion de imagen rotada en screen.
    """
    posx = pos[0] - (image_size[0] / 2)
    posy = pos[1] - (image_size[1] / 2)

    angle = (180 * angle) / math.pi

    newimg = image.subsurface((center_to_show[0] - (image_size[0] / 2), center_to_show[1] - (image_size[1] / 2),
                               image_size[0], image_size[1]))

    oldrect = newimg.get_rect()
    newimg = pygame.transform.rotozoom(newimg, angle, 1)
    newrect = newimg.get_rect()

    posx += oldrect.centerx - newrect.centerx
    posy += oldrect.centery - newrect.centery

    screen.blit(newimg, (posx, posy))


# Ship class
class Ship:
    def __init__(self, pos, vel, angle, image, info, lives=3):
        self.pos = [pos[0], pos[1]]
        self.vel = [vel[0], vel[1]]
        self.thrust = False
        self.angle = angle
        self.angle_vel = 0
        self.image = image
        self.image_center = info.get_center()
        self.image_size = info.get_size()
        self.radius = info.get_radius()
        self.forward = [0, 0]
        self.exploded = False
        self.exploding = False
        self.lives = lives
        self.missiles = set([])

    def get_missiles(self):
        return self.missiles

    def get_lives(self):
        return self.lives

    def set_lives(self, lives):
        self.lives = lives

    def lose_live(self):
        self.lives -= 1

    def get_position(self):
        return self.pos

    def get_radius(self):
        return self.radius

    def collide(self, other_object):
        return (dist(self.pos, other_object.get_position())) <= (self.radius + other_object.get_radius())

    def draw(self, canvas):
        # canvas.draw_circle(self.pos, self.radius, 1, "White", "White")
        if self.lives <= 0:
            if self.exploded and not self.exploding:
                explosion_group.add(
                    Sprite(self.get_position(), [0, 0], 0, 0, explosion_image[3], explosion_info, explosion_sound))
                self.pos = [WIDTH * 2, HEIGHT * 2]
                self.exploding = True
            return

        center_to_show = list(self.image_center)
        if self.thrust:
            center_to_show[0] += self.image_size[0]
        draw_image(canvas, self.image, center_to_show, self.image_size, self.pos, self.angle)

    def update(self):
        self.pos[0] += self.vel[0]
        self.pos[1] += self.vel[1]
        self.angle += self.angle_vel
        self.forward = angle_to_vector(self.angle)

        if (self.thrust):
            self.vel[0] += (self.forward[0] * 0.05)
            self.vel[1] += (self.forward[1] * 0.05)
        else:
            self.vel[0] *= 0.99
            self.vel[1] *= 0.99

        if (self.pos[0] != 0):
            if (WIDTH % self.pos[0]) >= WIDTH:
                self.pos[0] = 0
            elif (WIDTH % self.pos[0]) < 0:
                self.pos[0] = WIDTH
        if (self.pos[1] != 0):
            if (HEIGHT % self.pos[1]) >= HEIGHT:
                self.pos[1] = 0
            elif (HEIGHT % self.pos[1]) < 0:
                self.pos[1] = HEIGHT

    def switch_thrusters(self):
        self.thrust = not self.thrust
        if self.thrust:
            ship_thrust_sound.play()
        else:
            ship_thrust_sound.stop()

    def set_angle_vel(self, angle_vel):
        self.angle_vel = angle_vel

    def get_angle_vel(self):
        return self.angle_vel

    def shoot(self):
        missile_vel = [0, 0]
        missile_start = [0, 0]

        missile_vel[0] = self.vel[0] + (self.forward[0] * 2.5)
        missile_vel[1] = self.vel[1] + (self.forward[1] * 2.5)

        missile_start[0] = self.pos[0] + (self.forward[0] * 40)
        missile_start[1] = self.pos[1] + (self.forward[1] * 40)

        self.missiles.add(Sprite(missile_start, missile_vel, 0, 0, missile_image, missile_info, missile_sound))


def draw_text(screen, text, font, fontsize, txtcolor, backcolor=None, pos=(0, 0), postipe="topleft",
              antialiasing=False):
    fontObj = pygame.font.Font(font, fontsize)
    txtSurface = fontObj.render(text, antialiasing, txtcolor)
    txtRect = txtSurface.get_rect()
    if postipe == "topleft":
        txtRect.topleft = pos
    elif postipe == "topright":
        txtRect.topright = pos
    elif postipe == "bottomright":
        txtRect.bottomright = pos
    elif postipe == "bottomleft":
        txtRect.bottomleft = pos

    screen.blit(txtSurface, txtRect)


# Sprite class
class Sprite:
    def __init__(self, pos, vel, ang, ang_vel, image, info, sound=None):
        self.pos = [pos[0], pos[1]]
        self.vel = [vel[0], vel[1]]
        self.angle = ang
        self.angle_vel = ang_vel
        self.image = image
        self.image_center = info.get_center()
        self.image_size = info.get_size()
        self.radius = info.get_radius()
        self.lifespan = info.get_lifespan()
        self.animated = info.get_animated()
        self.age = 0
        if self.animated:
            self.time = 0
        if sound:
            sound.play()

    def draw(self, canvas):
        # canvas.draw_circle(self.pos, self.radius, 1, "Red", "Red")
        if self.animated:
            self.time += 0.3
            idx = (time % 24) // 1
            image_center = self.image_center[0] + (self.image_size[0] * idx)
            draw_image(canvas, self.image, [image_center, self.image_center[1]], self.image_size, self.pos, self.angle)
        else:
            draw_image(canvas, self.image, self.image_center, self.image_size, self.pos, self.angle)

    def update(self):
        self.pos[0] += self.vel[0]
        self.pos[1] += self.vel[1]
        self.angle += self.angle_vel
        self.age += 1

        if (self.pos[0] != 0):
            if (WIDTH % self.pos[0]) >= WIDTH:
                self.pos[0] = 0
            elif (WIDTH % self.pos[0]) < 0:
                self.pos[0] = WIDTH
        if (self.pos[1] != 0):
            if (HEIGHT % self.pos[1]) >= HEIGHT:
                self.pos[1] = 0
            elif (HEIGHT % self.pos[1]) < 0:
                self.pos[1] = HEIGHT

        return (self.age < self.lifespan)

    def get_position(self):
        return self.pos

    def get_radius(self):
        return self.radius

    def collide(self, other_object):
        return (dist(self.pos, other_object.get_position())) <= (self.radius + other_object.get_radius())


def draw(canvas):
    global time, splash, score

    #canvas = canvas2.convert_alpha()

    if (splash):
        draw_image(canvas, splash_image, splash_info.get_center(), splash_info.get_size(), [WIDTH / 2, HEIGHT / 2], 0)
        message = "Score: " + str(score) + " Lives: " + str(my_ship.get_lives())
        draw_text(canvas, message, "freesansbold.ttf", 25, (255, 255, 0), None, (WIDTH - 5, 5), 'topright', True)
        return

    # animiate background
    time += 1
    wtime = (time / 4) % WIDTH
    center = debris_info.get_center()
    size = debris_info.get_size()
    draw_image(canvas, nebula_image, nebula_info.get_center(), nebula_info.get_size(), [WIDTH / 2, HEIGHT / 2], 0)
    draw_image(canvas, debris_image, center, size, (wtime - WIDTH / 2, HEIGHT / 2), 0)
    draw_image(canvas, debris_image, center, size, (wtime + WIDTH / 2, HEIGHT / 2), 0)

    # draw ship and sprites
    my_ship.draw(canvas)

    # update ship and sprites
    my_ship.update()

    # update and show rocks
    process_sprite_group(rock_group, canvas)
    process_sprite_group(missile_group, canvas)
    process_sprite_group(explosion_group, canvas)

    score += group_group_collide(rock_group, missile_group)

    if group_collide(rock_group, my_ship):
        if (my_ship.get_lives() > 0): my_ship.lose_live()

    if (my_ship.get_lives() == 0):
        my_ship.exploded = True
        timer_stop_game.start()

    message = "Score: " + str(score) + " Lives: " + str(my_ship.get_lives())
    draw_text(canvas, message, "freesansbold.ttf", 25, (255, 255, 0), None, (WIDTH - 5, 5), 'topright', True)
    # canvas.draw_text("ExpCount: "+str(len(explosion_group)), (5, 25), 25, 'yellow', 'monospace')


    #canvas2.blit(canvas, (0, 0))

# timer handler that spawns a rock    
def rock_spawner():
    if (len(rock_group) < 12):
        start_pos = [random.randrange(0, WIDTH), random.randrange(0, HEIGHT)]

        while dist(start_pos, my_ship.get_position()) < (asteroid_info.get_radius() + my_ship.get_radius() + 50):
            start_pos = [random.randrange(0, WIDTH), random.randrange(0, HEIGHT)]

        start_vel = [random.randrange(-3, 4), random.randrange(-3, 4)]
        if (start_vel[0] == 0 and start_vel[1] == 0):
            start_vel = [random.randrange(-3, 4), random.randrange(-3, 4)]
        angle_vel = random.randrange(-10, 10) / 60.0

        rock_group.add(
            Sprite(start_pos, start_vel, 0, angle_vel, asteroid_image[random.randrange(0, 3)], asteroid_info))


def key_down_handler(key_code):
    global my_ship, pressed_left, pressed_right
    if splash:
        return
    if (key_code == K_LEFT):
        pressed_left = True
        my_ship.set_angle_vel(0.05)
    elif (key_code == K_RIGHT):
        pressed_right = True
        my_ship.set_angle_vel(-0.05)
    elif (key_code == K_UP):
        my_ship.switch_thrusters()
    elif (key_code == K_SPACE):
        my_ship.shoot()


def key_up_handler(key_code):
    global my_ship, pressed_left, pressed_right
    if splash:
        return
    if (key_code == K_LEFT):
        pressed_left = False
        my_ship.set_angle_vel(0)
        if pressed_right:
            my_ship.set_angle_vel(-0.05)
    elif (key_code == K_RIGHT):
        pressed_right = False
        my_ship.set_angle_vel(0)
        if pressed_left:
            my_ship.set_angle_vel(0.05)
    elif (key_code == K_UP):
        my_ship.switch_thrusters()


def mouse_handler(position):
    if (splash):
        start_game()
    else:
        stop_game()


def stop_game():
    global splash, rock_group, missile_group, wait_for_stop_game, explosion_group

    timer_stop_game.stop()

    wait_for_stop_game = 0
    splash = True
    timer.stop()

    pygame.mixer.music.stop()
    missile_sound.stop()

    ship_thrust_sound.stop()
    rock_group = set([])
    missile_group = set([])
    explosion_group = set([])


def start_game():
    global splash, score, my_ship, rock_group, missile_group, explosion_group

    pygame.mixer.music.play(-1, 0.0)

    splash = False
    score = 0
    my_ship.set_lives(3)

    my_ship = Ship([WIDTH / 2, HEIGHT / 2], [0, 0], 0, ship_image, ship_info)
    my_ship.exploded = False
    my_ship.exploding = False
    rock_group = set([])
    missile_group = my_ship.get_missiles()
    explosion_group = set([])

    timer.start()


def delay_stop_game():
    global wait_for_stop_game
    wait_for_stop_game += 0.5
    if wait_for_stop_game >= 1.5:
        stop_game()


my_ship = Ship([WIDTH / 2, HEIGHT / 2], [0, 0], 0, ship_image, ship_info)
rock_group = set([])
missile_group = my_ship.get_missiles()
explosion_group = set([])

splash = True
timer = Timer.Timer(1000.0, rock_spawner)
timer_stop_game = Timer.Timer(500.0, delay_stop_game)

fpsClock = pygame.time.Clock()
while True:
    #draw(canvas)
    #screen.blit(canvas,(0,0))
    draw(screen)
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit(0)

        elif event.type == MOUSEBUTTONDOWN:
            mouse_handler(event.pos)

        elif event.type == KEYDOWN:
            key_down_handler(event.key)

        elif event.type == KEYUP:
            key_up_handler(event.key)

    pygame.display.update()
    fpsClock.tick(60)
