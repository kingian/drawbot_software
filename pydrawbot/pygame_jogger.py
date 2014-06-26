#! /usr/bin/env python
import sys
import pygame
from pygame.locals import *
from pydrawbot import *
from time import sleep

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

STAMPS = list(id for row in GRID for id in row if not id == START)

running = 1
pygame.init()
screen = pygame.display.set_mode((320, 200))

font = pygame.font.SysFont("monospace", 15)

# render text
d = Drawbot()

message_y = 0
def message(text):
    global message_y
    for line in text.splitlines():
        screen.blit(font.render(line, 1, (0,0,0)), (0, message_y))
        message_y += 15

while running:
    message_y = 0
    screen.fill((255, 255, 255))
    event = pygame.event.poll()

    if event.type == pygame.QUIT:
        running = 0
        break

    keys = pygame.key.get_pressed()

    if keys[K_ESCAPE]:
        running = 0
        break

    try:
        if d.is_connected():
            message("MPos:{}\nWPos:{}\nState:{}\nQsize={}".format(d._machine_position, d._work_position, d._state, d.send_queue.qsize()))
            if d.is_idle() or d.is_jogging():
                x, y = 0, 0
                if (keys[UP] or keys[K_UP]):
                    y = 1
                elif (keys[DOWN] or keys[K_DOWN]):
                    y = -1
                if (keys[LEFT] or keys[K_LEFT]):
                    x = -1
                elif (keys[RIGHT] or keys[K_RIGHT]):
                    x = 1
                d.jog((x, y))

            if event.type == pygame.KEYDOWN and (event.key == 92 or event.key == K_SPACE):
                print event.key
                if d.is_pen_down():
                    d.pen_down()
                else:
                    d.pen_up()

            if keys[270]:
                d.draw('beard')

            if keys[296]:
                d.draw('simple_chicken')
        elif event.type == pygame.KEYDOWN and event.key == K_SPACE and serial_device_name:
            d.connect(serial_device_name)
        else:
            serial_device_name = sniff_arduino()
            if not serial_device_name:
                message("no arduino found!\ncheck your connections\n(I'll keep looking for it)")
            else:
                message("not connected!\nzero the machine\npress space to try connecting")

    except Exception as e:
        print e

    sleep(0.01)
    pygame.display.flip()

d.queue('G1 X0 Y0 Z0')
d.wait_for_idle()
