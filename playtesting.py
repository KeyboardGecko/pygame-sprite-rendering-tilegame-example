import pygame
import random
import time
from pathfinding import *

RESOLUTION = (640,480)
FPS = 60
PURPLE = (255, 0, 255)
TILESIZE = 32

class Sprite(pygame.sprite.DirtySprite):
    def __init__(self, images = None, entity = None):
        pygame.sprite.Sprite.__init__(self)
        self.size = TILESIZE
        self.entity = entity
        self.images = images.convert() # this is our spritesheet of frames.
        self.images.set_colorkey(PURPLE)

        self.framescount = (self.images.get_rect().size[0] // self.size) - 1 # the amount of frames in our spritesheet
        self.current_frame = random.randint(0, self.framescount) # number of current frame - for start picks at random

        self.image = self.images.subsurface(pygame.Rect([self.size * self.current_frame, 0],[self.size, self.size]))
        self.rect = self.image.get_rect()

    def set_image(self, current_frame):
        #function for setting current frame
        self.image = self.images.subsurface(pygame.Rect([self.size * self.current_frame, 0],[self.size, self.size]))

    def play_animation(self):
        if self.current_frame >= self.framescount:
            self.current_frame = 0
        else:
            self.current_frame += 1
        self.set_image(self.current_frame)


    def update(self, entity, movespeed):
        if entity.tile[0] * TILESIZE < self.rect.x:
            self.rect.x -= movespeed
        elif entity.tile[0] * TILESIZE > self.rect.x:
            self.rect.x += movespeed
        if entity.tile[1] * TILESIZE < self.rect.y:
            self.rect.y -= movespeed
        elif entity.tile[1] * TILESIZE > self.rect.y:
            self.rect.y += movespeed


class Tile:
    def __init__(self, tile = None, type = 'Floor', walkable = True):
        #tile.tile[0]. tile.tile[1] = tile.x, tile.y
        self.tile = tile
        self.walkable = walkable
        self.type = type


class Map:
    def __init__(self, size):
        self.size = size
        self.tiles = self.generate()

    def generate(self):
        #pretty simple random map generation.
        #I decided to make tiles a dict - can use key as tile coordinates
        tiles = {}
        for i in range(self.size):
            for j in range(self.size):
                x = random.randint(0, 6)
                if x == 1:
                    tile = Tile(tile =[i, j], walkable = False, type = 'Wall')
                else:
                    tile = Tile(tile =[i, j], walkable = True, type = 'Floor')
                tiles[i, j] = tile
        return tiles


class Action:
    def __init__(self, creature = None, key = None):
        #look into gameloop for details, what action is.
        if creature.AP >= creature.speed:
            creature.AP -= creature.speed
            self.perform(creature, key)
            if creature.actionQueue != []:
                creature.actionQueue.remove(creature.actionQueue[0])

    def perform(self, creature = None, key = None):
        return True


class MoveAction(Action):
    def perform(self, creature, key = None):
        map = creature.currentMap
        dx, dy = 0, 0
        if key == 'down': dx, dy = 0, 1
        elif key == 'up': dx, dy = 0, -1
        elif key == 'left': dx, dy = -1, 0
        elif key == 'right': dx, dy = 1, 0
        tile = next((t for t in map.tiles if map.tiles[t].tile == [creature.tile[0] + dx, creature.tile[1] + dy]), None)
        if tile != None and map.tiles[tile].walkable is True:
            creature.tile[0] += dx
            creature.tile[1] += dy
        return True


class Creature:
    def __init__(self, map = None, tile = None, type = 'Mob'):
        self.currentMap = map
        self.tile = tile
        self.type = type
        self.moving = False
        self.actionQueue = [] #mostly for player - stores list of movements
        self.set_AP()

    def set_AP(self):
        #defines the speed of the mob or player
        self.AP_max = 9
        self.AP_increment = 3
        self.AP = 9
        self.speed = 2


    def gainAP(self):
        self.AP += self.AP_increment
        if self.AP > self.AP_max: self.AP = self.AP_max

    def takeTurn(self, action = None):
        return action


    def move(self, map, dx = 0, dy = 0):
        tile = next((t for t in map.tiles if map.tiles[t].tile == [self.tile[0] + dx, self.tile[1] + dy]), None)
        if tile != None and map.tiles[tile].walkable is True:
            self.tile[0] += dx
            self.tile[1] += dy


    def set_path_to_goal(self, map, goaltile):
        self.actionQueue = astar(map, self.tile, goaltile)
        if self.actionQueue != []:
            self.actionQueue.remove(self.actionQueue[0])
            self.moving = True


class Player(Creature):

    def set_AP(self):
        self.AP_max = 9
        self.AP_increment = 3
        self.AP = 9
        self.speed = 3

    def takeTurn(self, key = None):
        if self.actionQueue != []:
            action = [self.actionQueue[0][0] - self.tile[0], self.actionQueue[0][1] - self.tile[1]]
            if action == [1, 0]: key = 'right'
            elif action == [-1, 0]: key = 'left'
            elif action == [0, 1]: key = 'down'
            elif action == [0, -1]: key = 'up'

            action = MoveAction(self, key = key)
            super().takeTurn(action = action)


class Monster(Creature):
    #monsters just move randomly
    def takeTurn(self, key = None):
        key = random.choice(['up', 'down', 'left', 'right'])
        a = MoveAction(self, key = key)
        super().takeTurn(action = a)


def generate_mobs(map, amount, sprites, img):
    mobs = []
    for a in range(amount):
        mob = Monster(map = map, tile = None, type = 'Mob')
        mobs.append(mob)

    for mob in mobs:
        t = random.choice(list(map.tiles.items()))
        mob.tile = [t[0][0], t[0][1]]
        s = Sprite(img, mob)
        s.rect.x = mob.tile[0] * TILESIZE
        s.rect.y = mob.tile[1] * TILESIZE
        sprites.append(s)

    return mobs

def play_animation(sprites):
    for sprite in sprites:
        if sprite.current_frame >= sprite.framescount:
            sprite.current_frame = 0
        else:
            sprite.current_frame += 1
        sprite.set_image(sprite.current_frame)

def gameloop(player, mobs):
    #so, every creature has a stack of actions
    #if it's not empty, we pop one from it and execute it
    #for every creature in order (player - creatures)
    #if stack is empty, it waits for input.
    if player.actionQueue != []:
        player.gainAP()
        playerTurn = player.takeTurn()
        for m in mobs:
            m.gainAP()
            m.takeTurn()


def run():
    # Initialize Pygame stuff
    pygame.init()
    window = pygame.display.set_mode(RESOLUTION)
    pygame.display.set_caption("Some testing")
    clock = pygame.time.Clock()
    pygame.key.set_repeat(1, 1)

    #some pygame stuff

    floorimg = pygame.image.load('floor.png').convert()
    wallimg = pygame.image.load('wall.png').convert()
    mobimg = pygame.image.load('mob.png').convert()
    playerimg = pygame.image.load('player.png').convert()
    pointerimg = pygame.image.load('pointer.png').convert()

    floorimg = pygame.transform.scale2x(floorimg)
    wallimg = pygame.transform.scale2x(wallimg)
    mobimg = pygame.transform.scale2x(mobimg)
    playerimg = pygame.transform.scale2x(playerimg)
    pointerimg = pygame.transform.scale2x(pointerimg)

    floorimg.set_colorkey((255,0,255))
    wallimg.set_colorkey((255,0,255))
    mobimg.set_colorkey((255,0,255))
    playerimg.set_colorkey((255,0,255))
    pointerimg.set_colorkey((255,0,255))

    #init map and player, spawn player randomly
    map = Map(40)
    player = Player(map = map, tile = [random.randint(0, map.size-1), random.randint(0, map.size-1)], type = 'Player')

    floorsprite = Sprite(images = floorimg)
    wallsprite = Sprite(images = wallimg)
    pointersprite = Sprite(images = pointerimg)
    playersprite = Sprite(images = playerimg, entity = player)

    playersprite.rect.x = player.tile[0] * TILESIZE
    playersprite.rect.y = player.tile[1] * TILESIZE

    #generate player
    sprites = []
    mobs = generate_mobs(map, 90, sprites, mobimg)
    sprites.append(playersprite)

    running = True
    start = time.time() +0.08

    view = 13
    while running:
        window.fill((0, 0, 0))
        x1, y1, x2, y2 = player.tile[0] - view, player.tile[1] - view, player.tile[0] + view, player.tile[1] + view

        ### THIS LITTLE STUFF HERE IS DOING ANIMATIONS ##
        tick = time.time()
        if tick > start:

            #for m in mobs:
            #    m.update(map)
            #player.update(map)
            gameloop(player, mobs)

            start = time.time() + 0.08
            play_animation(sprites)

        #################################################
        ## Drawing map ##

        for i in range(x1, x2):
            for j in range(y1, y2):
                if (i, j) in map.tiles:
                    tile = map.tiles[i, j]
                    x = tile.tile[0] * TILESIZE
                    y = tile.tile[1] * TILESIZE
                    if tile.type == 'Wall':
                        window.blit(wallsprite.image, (x -playersprite.rect.x +RESOLUTION[0]//2, y - playersprite.rect.y +RESOLUTION[1]//2))
                    else:
                        window.blit(floorsprite.image, (x -playersprite.rect.x +RESOLUTION[0]//2, y - playersprite.rect.y +RESOLUTION[1]//2))

        for s in sprites:
            x = s.rect.x
            y = s.rect.y
            if (x1 < x//32 < x2) and (y1 < y//32 < y2):
                window.blit(s.image, (x -playersprite.rect.x +RESOLUTION[0]//2, y - playersprite.rect.y +RESOLUTION[1]//2))
            s.update(s.entity, 8)

        for t in player.actionQueue:
            x = t[0] * 32
            y = t[1] * 32
            window.blit(pointersprite.image, (x -playersprite.rect.x +RESOLUTION[0]//2, y - playersprite.rect.y +RESOLUTION[1]//2))


        pygame.display.flip()
        #FPS = clock.tick()
        #pygame.display.set_caption(str(FPS))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONUP:
              pos = pygame.mouse.get_pos()
              clickx = (RESOLUTION[0] // 2 - pos[0] + TILESIZE) // TILESIZE
              clicky = (RESOLUTION[1] // 2 - pos[1] + TILESIZE) // TILESIZE

              goaltile = [player.tile[0] - clickx, player.tile[1] - clicky]
              player.set_path_to_goal(map, goaltile)

            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_ESCAPE:
                    running = False

        clock.tick(FPS)


if __name__ == "__main__":
    run()
    pygame.quit()
