from grbl import Grbl
from ConfigParser import ConfigParser

import logging
logging.basicConfig(level='DEBUG')
log = logging.getLogger('pydrawbot')

import arduinosniffer

from serial import Serial
from time import sleep

RX_BUFFER_SIZE = 128

def grbl_init():
    try:
        arduinoName = arduinosniffer.findArduinoName()
        s = Serial(arduinoName, 9600)
        s.write("\r\r")
        sleep(2)
        s.flushInput()
        return s
    except ConnectionError as e:
        print "An error has occured.\n Check the arduino connection and the arduino.\n"


#def grbl_init():
#    s = Serial('/dev/tty.usbmodem1411', 9600)
#    s.write("\r\r")
#    sleep(2)
#    s.flushInput()
#    return s

def grbl_send_gcode(serial, gcode):
    buffered_command_sizes = []
    for command_to_send in gcode:
        while sum(buffered_command_sizes) + len(command_to_send) + 1 >= RX_BUFFER_SIZE-1 | serial.inWaiting():
            response = serial.readline().strip()
            if response.find('error') >= 0:
                raise response
            elif response.find('ok') >= 0:
                del buffered_command_sizes[0]
            else:
                print response
        serial.write(command_to_send + "\r")
        buffered_command_sizes.append(len(command_to_send) + 1)

config = ConfigParser()
config.read('drawbot.ini')

if config.getboolean('grbl', 'sniff_arduino'):
    serial_device_name = arduinosniffer.findArduinoName()
    log.info('autodetected arduino at {}'.format(serial_device_name))
else:
    serial_device_name = config.get('grbl', 'serial_device_name')

with open('chicken.gcode', 'r') as f:
    gcode = f.read()

grbl = Grbl(serial_device_name)
