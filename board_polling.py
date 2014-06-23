#! /usr/bin/env python 
import sys
import drawdbot
import pygame
from pygame.locals import *


LEFT = 1

running = 1
screen = pygame.display.set_mode((320, 200))

while running:
    event = pygame.event.poll()
    x=0
    y=0
    if event.type == pygame.QUIT:
        running = 0
    elif event.type == pygame.KEYDOWN:
        keys = pygame.key.get_pressed() 

        if (keys[K_w] or keys[K_s] or keys[K_a] or keys[K_d]):
            # Jog Keys ASWD
            if (keys[K_UP]):
                print "up"
                y = 1
            if (keys[K_DOWN]):
                print "down"
                y = -1
            if (keys[K_LEFT]):
                print "left"
                x = -1
            if (keys[K_RIGHT]):
                print "right"
                x = 1
        elif:
            



#        if (key[K_8]):
#            drawbot.drawSymbol(1)
#        elif (key[K_h]):
#            drawbot.drawSymbol(2)
#        elif (key[K_KP_EQUALS]):
#            drawbot.drawSymbol(3)
#        elif (key[K_6]):
#            drawbot.drawSymbol(4)
#         elif (key[K_k]):
#            drawbot.drawSymbol(5)           
#        elif (key[K_l]):
#            drawbot.drawSymbol(6)
#        elif (key[K_BACKSLASH]):
#            drawbot.drawSymbol(7)
#        elif (key[K_SEMICOLON]):
#            drawbot.drawSymbol(8)
#        elif (key[K_RIGHTBRACKET]):
#            drawbot.drawSymbol(9)
#        elif (key[K_CAPSLOCK]):
#            drawbot.drawSymbol(10)
#        elif (key[K_TAB]):
#            drawbot.drawSymbol(11)
#        elif (key[K_LEFTBRACKET]):
#            drawbot.drawSymbol(12)
#        elif (key[K_y]):
#            drawbot.drawSymbol(13)
#        elif (key[K_i]):
#            drawbot.drawSymbol(14)
#        elif (key[K_e]):
#            drawbot.drawSymbol(1)
#        elif (key[]):
#            drawbot.drawSymbol()
#        elif (key[]):
#            drawbot.drawSymbol()



#    drawbot.jog((x,y))
    screen.fill( 0, 0, 0))
    pygame.display.flip()
