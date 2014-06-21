# -*- coding: utf-8 -*-
import os
import fnmatch

# Since the usb serial connection seems to show different
# for each computer this sniffer method should find it on
# most OS X machines
def findArduinoName():
    for file in os.listdir('/dev/'):
        if fnmatch.fnmatch(file, 'tty.usbmodem*'):
        # Debug line, since the usb bluetooth files seem to always be there
        #if fnmatch.fnmatch(file, 'tty.Blue*'):
            return file
