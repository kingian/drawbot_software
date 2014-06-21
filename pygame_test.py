#! /usr/bin/env python
import pygame
import serial
import time


LEFT = 1

running = 1
screen = pygame.display.set_mode((320, 200))

s = serial.Serial('/dev/tty.usbmodemfa141', 9600)
xaxis = 0
yaxis = 0
pygame.key.set_repeat(250,250)
while running:
    event = pygame.event.poll()
    if event.type == pygame.QUIT:
        s.close()
        running = 0
    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == LEFT:
        print "You pressed the left mouse button at (%d, %d)" % event.pos
    elif event.type == pygame.MOUSEBUTTONUP and event.button == LEFT:
        print "You released the left mouse button at (%d, %d)" % event.pos
    elif event.type == pygame.KEYDOWN and event.key == 276:
        yaxis = yaxis-10
        temp = "G0 Y%d\n" % yaxis
        print "Left" + temp
        s.write(temp) 
    elif event.type == pygame.KEYDOWN and event.key == 275:
        yaxis = yaxis+10
        temp = "G0 Y%d\n" % yaxis
        print "Right" + temp
        s.write(temp) 
    elif event.type == pygame.KEYDOWN and event.key == 273:
        xaxis = xaxis+10
        temp = "G0 X%d\n" % xaxis
        print "Up" + temp
        s.write(temp)
    elif event.type == pygame.KEYDOWN and event.key == 274:
        xaxis = xaxis-10
        temp = "G0 X%d\n" % xaxis
        print "Down" + temp
        s.write(temp)

screen.fill((0, 0, 0))
pygame.display.flip()

# LEFT = 276
# RIGHT = 275
# UP = 273
# DOWN = 274

