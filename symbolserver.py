import pygame
from pygame.locals import *
import os
import fnmatch

symbolLibrary = dict()
symbolList = list()
symbolIndex = 0


def loadSymbols(directory):
    dirpath = os.getcwd() + '/' + directory 
    for file in os.listdir(dirpath):
        if fnmatch.fnmatch(file, '*.gcode'):
            with open(dirpath+'/'+file,'r') as f:
                symbolList.append(f.read())
                f.close

def getSymbol(key):
    if (len(symbolList)<1):
        return None
    if (key in symbolLibrary):
        return symbolLibrary[key]
    else:
        symbolLibrary.update({key:symbolList[symbolIndex]})
        return symbolLibrary[key]
        symbolIndex += 1




