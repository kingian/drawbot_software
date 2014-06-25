#! /usr/bin/env python
import sys
import pygame
from pygame.locals import *
from pydrawbot import *
from time import sleep

d = Drawbot(serial_device_name)
d.connect()

UP = 256 # Numpad [0]
DOWN = 267 # Numpad[/]
LEFT = 275 # right
RIGHT = 261 # Numpad [5]
START = 92 # \
GRID = [
    [92, 122, 99, 46, 296],
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
    keys = pygame.key.get_pressed()

    try:
        if True: #d.is_idle() or d.is_jogging():
            x, y = 0, 0
            if (keys[UP] or keys[K_UP]):
                x = -1
            elif (keys[DOWN] or keys[K_DOWN]):
                x = 1
            if (keys[LEFT] or keys[K_LEFT]):
                y = 1
            elif (keys[RIGHT] or keys[K_RIGHT]):
                y = -1
            d.jog((x, y))

        if event.type == pygame.KEYDOWN:
            if keys[92]:
                if d.is_pen_down():
                    d.pen_down()
                else:
                    d.pen_up()
            if keys[296]:
                d.draw('simple_chicken')
    except Exception as e:
        print e

    sleep(0.01)
    screen.fill((0, 0, 0))
    pygame.display.flip()

d.queue('G1 X0 Y0 Z0')
d.wait_for_idle()
