#! /usr/bin/env python
import sys
import pygame
from pygame.locals import *
from pydrawbot import *

d = Drawbot(serial_device_name)
d.connect()

UP = 256 # Numpad [0]
DOWN = 267 # Numpad[/]
LEFT = 275 # right
RIGHT = 261 # Numpad [5]
START = 92 # \
GRID = [
    [92, 122, 99, 46, None],
    [59, 113, 102, 121, 270],
    [45, 96, 283, 289, 278],
    [111, 97, 115, 105, 271],
    [48, 49, 51, 57, 279]
]

running = 1
screen = pygame.display.set_mode((320, 200))

while running:
    event = pygame.event.poll()
    if event.type == pygame.QUIT:
        running = 0
    elif event.type == pygame.KEYDOWN or event.type == pygame.KEYUP:
        keys = pygame.key.get_pressed()
        x, y = 0, 0
        if (keys[UP] or keys[K_UP]):
            x = -1
        if (keys[DOWN] or keys[K_DOWN]):
            x = 1
        if (keys[LEFT] or keys[K_LEFT]):
            y = 1
        if (keys[RIGHT] or keys[K_RIGHT]):
            y = -1
        try:
            d.jog((x, y))
        except Exception:
            pass

    screen.fill((0, 0, 0))
    pygame.display.flip()
