import pygame # needed in order for the load image functions to work
from config import *

def images():
    return {

        'planet' : [load_image('planet.png')],
        'obstacle' : [load_image('obstacle.png')],
        'goal' : [load_image('goal.png')],
        'player_spawn' : [load_image('player_spawn.png')],
        'stars' : load_images('bg', 5)
    }

def sounds():
    return {
        
        'hit' : pygame.mixer.Sound("data/sounds/impact.wav"),
        'explosion' : pygame.mixer.Sound("data/sounds/explosion.wav"),
        'jump' : pygame.mixer.Sound("data/sounds/jump.wav"),
        'levelup' : pygame.mixer.Sound("data/sounds/jump.wav"),
        'blackhole' : pygame.mixer.Sound('data/sounds/blackhole.wav'),
        'music' : pygame.mixer.Sound('data/sounds/music.wav')
    }