# -*- coding: utf-8 -*-
import os
import fnmatch

class ConnectionError(Exception):
    def __init__(self,value):
        self.value = value
    def __str__(self):
        return repr(self.value)

# Since the usb serial connection seems to show different
# for each computer this sniffer method should find it on
# most OS X machines
def findArduinoName():
    for file in os.listdir('/dev/'):
        #if fnmatch.fnmatch(file, 'tty.usbmodem*'):
        if fnmatch.fnmatch(file, 'ttyACM*'):
        # Debug line, since the usb bluetooth files seem to always be there
        #if fnmatch.fnmatch(file, 'tty.Blue*'):
            return '/dev/' + file
