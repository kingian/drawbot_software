from grbl import Grbl
from ConfigParser import ConfigParser

import logging
logging.basicConfig(level='DEBUG')
log = logging.getLogger('pydrawbot')

from svg.path import parse_path, Path, Line, QuadraticBezier

import arduinosniffer
import xml.etree.ElementTree as ET

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

def min_max_points(points):
    min_point = max_point = points[0]
    for point in points[1:]:
        min_point = min(min_point.real, point.real) + min(min_point.imag, point.imag) * 1j
        max_point = max(max_point.real, point.real) + max(max_point.imag, point.imag) * 1j
    return min_point, max_point

def segments(n, path):
    return [path.point(float(t) / n) for t in range(0, n)]

def path_bounds(path):
    steps = 100
    return min_max_points(segments(steps, path))

def bounding_box(paths):
    return min_max_points([point for path in paths for point in path_bounds(path)])

def gcode_move_to(x, y):
    return "G1 X{} Y{}".format(round(x, 5), round(y, 5))

def gcode_pen_up():
    return "G1 Z{}".format(0)

def gcode_pen_down():
    return "G1 Z{}".format(15)

def gcode_move_to_point(point, scale=1+1j, offset=0):
    return gcode_move_to((point.real + offset.real) * scale.real,
                         (point.imag + offset.imag) * scale.imag)

def gcodify_path(path, scale=1+1j, offset=0):
    steps = int(round(path.length() / 2 * min(scale.imag, scale.real)) + 1)
    points = segments(steps, path)
    return [
        gcode_pen_up(),
        gcode_move_to_point(points[0], scale, offset),
        gcode_pen_down(),
    ] + [gcode_move_to_point(point, scale, offset) for point in points]

def gcodify(paths, scale=1+1j, offset=0):
    return (command for path in paths for command in gcodify_path(path, scale, offset))

config = ConfigParser()
config.read('drawbot.ini')

if config.getboolean('svg', 'build_gcode'):
    svg = ET.parse(config.get('svg', 'file'))
    svg_tag = svg.getroot()
    paths = svg.findall('.//{http://www.w3.org/2000/svg}path')
    path_strings = (path.attrib['d'] for path in paths)

    desired_size = config.getfloat('svg', 'draw_size')
    size = float(svg_tag.attrib['width']) + float(svg_tag.attrib['height']) * 1j
    max_dimension = max(size.real, size.imag)
    scale = desired_size / max_dimension
    gcode = list(gcodify(paths, scale + scale * 1j, -0.5 * size))

if config.getboolean('grbl', 'sniff_arduino'):
    serial_device_name = arduinosniffer.findArduinoName()
    log.info('autodetected arduino at {}'.format(serial_device_name))
else:
    serial_device_name = config.get('grbl', 'serial_device_name')

with open('chicken.gcode', 'r') as f:
    gcode = f.read()

grbl = Grbl(serial_device_name)
