#! /usr/bin/env python 
import sys
import pygame
from pygame.locals import *

LEFT = 1

running = 1
screen = pygame.display.set_mode((320, 200))

while running:
    event = pygame.event.poll()
    if event.type == pygame.QUIT:
        running = 0
    elif event.type == pygame.KEYDOWN:
        keys = pygame.key.get_pressed() 
        #print keys
        if (keys[K_UP]):
           print "up" 
        if (keys[K_DOWN]):
            print "down"
        if (keys[K_LEFT]):
            print "left"
        if (keys[K_RIGHT]):
            print "right"

    screen.fill((0, 0, 0))
    pygame.display.flip()
