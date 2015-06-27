#! /usr/bin/env python
import sys
import os
from fnmatch import fnmatch
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
    [92, 122, 99, 46, 19],
    [112, 113, 101, 111, 270],
    [45, 96, 283, 289, 278],
    [59, 97, 100, 108, 271],
    [48, 49, 51, 57, 279]
]

STAMPS = list(id for row in GRID for id in row if not id == START)
files = []
for path in os.listdir(os.getcwd() + '/' + 'gcode'):
    if fnmatch(path, '*.gcode'):
        files.append(os.path.splitext(path)[0])

key_files = {}
for i, key in enumerate(STAMPS):
    key_files[key] = files[i % len(files)]

running = 1
pygame.init()
screen = pygame.display.set_mode((640, 480))
pygame.display.set_caption("Drawbot!")

font = pygame.font.SysFont("monospace", 24)

# render text
d = Drawbot()

settings = """$N0=
$N1=
$0=5 (step pulse, usec)
$1=25 (step idle delay, msec)
$2=192 (step port invert mask:11000000)
$3=0 (dir port invert mask:00000000)
$4=0 (step enable invert, bool)
$5=1 (limit pins invert, bool)
$6=0 (probe pin invert, bool)
$10=3 (status report mask:00000011)
$11=0.020 (junction deviation, mm)
$12=0.002 (arc tolerance, mm)
$13=0 (report inches, bool)
$20=0 (soft limits, bool)
$21=0 (hard limits, bool)
$22=0 (homing cycle, bool)
$23=0 (homing dir invert mask:00000000)
$24=25.000 (homing feed, mm/min)
$25=500.000 (homing seek, mm/min)
$26=250 (homing debounce, msec)
$27=1.000 (homing pull-off, mm)
$100=40.000 (x, step/mm)
$101=40.000 (y, step/mm)
$102=320.000 (z, step/mm)
$110=25000.000 (x max rate, mm/min)
$111=25000.000 (y max rate, mm/min)
$112=500.000 (z max rate, mm/min)
$120=1500.000 (x accel, mm/sec^2)
$121=1500.000 (y accel, mm/sec^2)
$122=30.000 (z accel, mm/sec^2)
$130=700.000 (x max travel, mm)
$131=700.000 (y max travel, mm)
$132=100.000 (z max travel, mm)
"""

old_settings = """$N0=
$N1=
$0=40.000 (x, step/mm)
$1=40.000 (y, step/mm)
$2=320.000 (z, step/mm)
$3=25000.000 (x v_max, mm/min)
$4=25000.000 (y v_max, mm/min)
$5=500.000 (z v_max, mm/min)
$6=1500.000 (x accel, mm/sec^2)
$7=1500.000 (y accel, mm/sec^2)
$8=30.000 (z accel, mm/sec^2)
$9=5 (step pulse, usec)
$10=40000.000 (default feed, mm/min)
$11=192 (step port invert mask, int:11000000)
$12=25 (step idle delay, msec)
$13=0.050 (junction deviation, mm)
$14=0.005 (arc tolerance, mm)
$15=3 (n-decimals, int)
$16=0 (report inches, bool)
$17=1 (auto start, bool)
$18=0 (invert step enable, bool)
$19=0 (hard limits, bool)
$20=0 (homing cycle, bool)
$21=0 (homing dir invert mask, int:00000000)
$22=25.000 (homing feed, mm/min)
$23=250.000 (homing seek, mm/min)
$24=100 (homing debounce, msec)
$25=1.000 (homing pull-off, mm)"""

message_y = 0
def message(text):
    global message_y
    for line in text.splitlines():
        screen.blit(font.render(line, 1, (0,0,0)), (0, message_y))
        message_y += 15

center = False
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
            #d.queue(settings)
            if center:
                center = False
                d.queue("G1 X350 Y350 F10000")
            message("MPos:{}\nWPos:{}\nState:{}\nQsize={}".format(d._machine_position, d._work_position, d._state, d.send_queue.qsize()))
            if False and d.is_idle() or d.is_jogging():
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

            if False and event.type == pygame.KEYDOWN and (event.key == 92 or event.key == K_SPACE):
                print event.key
                if d.is_pen_down():
                    d.pen_up()
                else:
                    d.pen_down()

            if event.type == pygame.KEYDOWN and key_files.has_key(event.key):
                d.draw(key_files[event.key])

            #if key_files[270]:
            #    d.draw('beard')
            #if keys[296]:
            #    d.draw('simple_chicken')
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

#d.queue('G1 X0 Y0 Z0 F10000')
#d.wait_for_idle()
