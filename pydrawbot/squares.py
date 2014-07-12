from sys import exit
from signal import signal, SIGINT
from pydrawbot import *
from random import random
from time import sleep

d = Drawbot(serial_device_name)
d.connect()

tried_quit = False
def handler(sig, frame):
  global tried_quit
  if tried_quit:
    print 'killing'
    exit(-1)
  tried_quit = True
  print 'zeroing'
  d.reset()
  sleep(2)
  d.queue('G1 G53 Z0')
  d.queue('G1 G53 X0 Y0 Z0')

signal(SIGINT, handler)
drawing = False
position = [0.0,0.0]
limit = [1400.0, 700.0]
d.queue('g1z15')

while not tried_quit:
  print "({} {})".format(position[0], position[1])
  # up
  position[1] += random() * (limit[1] - position[1])
  d.queue("G1 X{} Y{}".format(position[0], position[1]))

  print "({} {})".format(position[0], position[1])
  # right
  position[0] += random() * (limit[0] - position[0])
  d.queue("G1 X{} Y{}".format(position[0], position[1]))

  print "({} {})".format(position[0], position[1])
  # down
  position[1] += random() * (0.0 - position[1])
  d.queue("G1 X{} Y{}".format(position[0], position[1]))

  print "({} {})".format(position[0], position[1])
  # left
  position[0] += random() * (0.0 - position[0])
  d.queue("G1 X{} Y{}".format(position[0], position[1]))

  d.wait_for_idle()
d.wait_for_idle()
