from grbl import Grbl
from ConfigParser import ConfigParser
from math import copysign

import logging
logging.basicConfig(level='INFO')
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

def sniff_arduino():
    name = arduinosniffer.findArduinoName()
    if name:
        log.info('autodetected arduino at {}'.format(name))
    return name

if config.getboolean('grbl', 'sniff_arduino'):
    serial_device_name = sniff_arduino()
else:
    serial_device_name = config.get('grbl', 'serial_device_name')

class Drawbot(Grbl):
    def __init__(self, serial_device_name=None):
        Grbl.__init__(self, serial_device_name)
        self.jog_direction = None
        self.last_jog_direction = None
        self.margin = 125
        self.x_limit = 1500 #700
        self.y_limit = 700 #1500
        self._is_pen_down = False

    def load_chicken(self):
        with open('chicken.gcode', 'r') as f:
            self.chicken = f.read()

    def jog(self, direction):
        if not self.is_jogging() and not self.is_idle():
            raise Exception("can't start jogging while moving")
        if direction[0] == 0 and direction[1] == 0:
            self.jog_direction = None
        else:
            self.jog_direction = direction

    def queue(self, script):
        if self.jog_direction:
            raise Exception("can't execute script while jogging")
        Grbl.queue(self, script)

    def is_pen_down(self):
        return self._is_pen_down

    def pen_down(self):
        if not self.ready_for_action():
            raise Exception("can't draw while moving")
        self.queue('G1 G53 Z15')
        sleep(1)
        self._is_pen_down = True
        self.wait_for_idle()

    def pen_up(self):
        if not self.ready_for_action():
            raise Exception("can't draw while moving")
        self.queue('G1 G53 Z0')
        sleep(1)
        self._is_pen_down = False
        self.wait_for_idle()

    def ready_for_action(self):
        return not self.is_jogging() and self.is_idle() and self.send_queue.empty()

    def is_jogging(self):
        return self.last_jog_direction or self.jog_direction

    def draw(self, filename):
        if not self.ready_for_action():
            raise Exception("can't draw while moving")
        with open("gcode/{}.gcode".format(filename), 'r') as f:
            gcode = f.read()
        self.queue(gcode)

    def _gcode_machine_position_move_to(self, position):
        "Generate command string to move to given XY position. Specifying None for a position skips that axis."
        if not any(p != None for p in position):
            return ""
        command = "G1 G53 "
        if position[0] != None:
            command += "X{}".format(position[0])
        if position[1] != None:
            command += "Y{}".format(position[1])
        return command

    def _jog_target(self, jog_direction):
        x_target = [None, self.x_limit - self.margin, self.margin][jog_direction[0]]
        y_target = [None, self.y_limit - self.margin, self.margin][jog_direction[1]]
        if x_target != None and y_target != None:
            # the hard case where x and y are being jogged
            # we have to adjust one of the targets
            x_offset = x_target - self._machine_position[0]
            y_offset = y_target - self._machine_position[1]
            # we only do 45-degree moves, so the target is equidistant in both axes
            # the target is limited by the shorter distance
            if abs(y_offset) < abs(x_offset):
                x_target = copysign(abs(y_offset), x_offset) + self._machine_position[0]
            else:
                y_target = copysign(abs(x_offset), y_offset) + self._machine_position[1]

        return (x_target, y_target)

    def _status_update(self):
        Grbl._status_update(self)
        if self.jog_direction != self.last_jog_direction:
            # we're changing jog direction, we need to come to a stop first
            if self._state == 'Run':
                self.hold() # start stopping
            elif self._state == 'Queue':
                self.reset() # done stopping, clear the command queue
            elif self._state == 'Idle':
                # ready for a new move command
                if self.jog_direction:
                    # move to the edge of the workspace in the jog direction
                    command = self._gcode_machine_position_move_to(self._jog_target(self.jog_direction))
                    if command:
                        self._execute(command)
                self.last_jog_direction = self.jog_direction
