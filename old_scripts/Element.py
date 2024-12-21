import pygame
from math import sqrt
from pygame.math import Vector2
from random import uniform
from scripts.range import *
#this is just my entities class. 
class Element:
    def __init__(self, position = Vector2(0, 0), size=(10, 10), color=(255, 255, 255)):
        self.position = position
        self.color = color
        self.size = size
        self.highlighted = False
        self.HighlightColor = None

    def move(self):
        self.position.x += uniform(-2, 2)
        self.position.y += uniform(-2, 2)

    def collide(self, other):
    # Check for collision between two rectangles
        return (self.position.x < other.position.x + other.size[0] and
                self.position.x + self.size[0] > other.position.x and
                self.position.y < other.position.y + other.size[1] and
                self.position.y + self.size[1] > other.position.y)

    def Highlight(self, color=(0, 255, 255)):
        self.highlighted = True
        self.highlightColor = color

    def draw(self, screen, size=None):
        _size = self.size
        if size is not None:
            _size = size

        surface = pygame.Surface(_size,pygame.SRCALPHA,32)
       
        r, g, b = self.color
        if self.highlighted:
            r, g, b = self.highlightColor
        pygame.draw.rect(surface, (r, g, b, 100), (0, 0, _size[0], _size[1]))
        pygame.draw.rect(surface, (r, g, b, 255), (0, 0, _size[0], _size[1]), 1)

        screen.blit(surface, self.position)
        self.highlighted = False
def GetDistance(x1, y1, x2, y2):
    return sqrt( (x2 - x1) * (x2-x1) + (y2 - y1) * (y2 - y1) )
