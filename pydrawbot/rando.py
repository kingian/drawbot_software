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
position = [0.0, 0.0, 0.0]
limit = [1400.0, 700.0, 17.0]
d.queue("G1 X{} Y{}".format(position[0], limit[1]))
d.queue("G1 X{} Y{}".format(limit[0], limit[1]))
d.queue("G1 X{} Y{}".format(limit[0], position[1]))
d.queue("G1 X{} Y{}".format(position[0], position[1]))
lines = 0
while not tried_quit:
  print "({} {})".format(position[0], position[1])
  position[0] = random() * limit[0]
  position[1] = random() * limit[1]
  d.queue("G1 X{} Y{} Z{}".format(position[0], position[1], position[2]))
  position[2] = random() * limit[2]
  lines += 1
  #if not drawing:
  #  drawing = True
  #  d.queue('G1 Z15')

  if lines >= 5:
    lines = 0
    d.wait_for_idle()
d.wait_for_idle()
