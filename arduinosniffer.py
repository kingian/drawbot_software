# -*- coding: utf-8 -*-
import os
import fnmatch


def findArduinoName():
    for file in os.listdir('/dev/'):
        if fnmatch.fnmatch(file, 'tty.usbmodem*'):
            return file
