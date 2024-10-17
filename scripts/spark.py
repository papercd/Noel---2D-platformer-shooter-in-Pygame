#!/usr/bin/python3.4
# Setup Python ----------------------------------------------- #
import pygame, sys, math, random

# Setup pygame/window ---------------------------------------- #
mainClock = pygame.time.Clock()
from pygame.locals import *
pygame.init()
pygame.display.set_caption('game base')
screen = pygame.display.set_mode((500, 500), 0, 32)

sparks = []

class Spark():
    def __init__(self, loc, angle, speed, color, scale=1,speed_factor = 2):
        self.loc = loc
        self.center = self.loc
        self.angle = angle
        self.speed = speed
        self.scale = scale
        self.color = color
        self.movement = []
        self.dead = False
        self.speed_factor = speed_factor

    def point_towards(self, angle, rate):
        rotate_direction = ((angle - self.angle + math.pi * 3) % (math.pi * 2)) - math.pi
        try:
            rotate_sign = abs(rotate_direction) / rotate_direction
        except ZeroDivisionError:
            rotate_sing = 1
        if abs(rotate_direction) < rate:
            self.angle = angle
        else:
            self.angle += rate * rotate_sign

    def calculate_movement(self, dt):
        return [math.cos(self.angle) * self.speed * dt, math.sin(self.angle) * self.speed * dt]


    # gravity and friction
    def velocity_adjust(self, friction, force, terminal_velocity, dt):
        movement = self.calculate_movement(dt)
        movement[1] = min(terminal_velocity, movement[1] + force * dt)
        movement[0] *= friction
        self.angle = math.atan2(movement[1], movement[0])
        # if you want to get more realistic, the speed should be adjusted here

    def update(self, dt):
        self.movement = self.calculate_movement(dt)
        self.loc[0] += self.movement[0] * self.speed_factor
        self.loc[1] += self.movement[1] * self.speed_factor

        # a bunch of options to mess around with relating to angles...
        self.point_towards(math.pi / 2, 0.02)
        #self.velocity_adjust(0.975, 0.2, 8, dt)
        self.angle += 0.02

        self.speed -= 0.1

        if self.speed <= 0:
            self.dead = True
            return True 
        return False

    def render(self, surf, offset=[0, 0]):
        if not self.dead:
            points = [
                [self.loc[0] -offset[0]+ math.cos(self.angle) * self.speed * self.scale, self.loc[1]-offset[1] + math.sin(self.angle) * self.speed * self.scale],
                [self.loc[0] -offset[0]+ math.cos(self.angle + math.pi / 2) * self.speed * self.scale * 0.3, self.loc[1]-offset[1] + math.sin(self.angle + math.pi / 2) * self.speed * self.scale * 0.3],
                [self.loc[0] -offset[0]- math.cos(self.angle) * self.speed * self.scale * 3.5, self.loc[1] -offset[1]- math.sin(self.angle) * self.speed * self.scale * 3.5],
                [self.loc[0] -offset[0]+ math.cos(self.angle - math.pi / 2) * self.speed * self.scale * 0.3, self.loc[1]-offset[1] - math.sin(self.angle + math.pi / 2) * self.speed * self.scale * 0.3],
                ]
            pygame.draw.polygon(surf, self.color, points)
