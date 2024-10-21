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
    
    

    def calculate_bounce_angle(self, angle,axis):
        
        if axis == 'x':
            reflected_angle = math.pi - angle 
        else:
            #reflected_angle =  angle
            reflected_angle = -angle 

        return reflected_angle



    def update(self, tilemap, dt):
        if self.speed <= 0:
            self.dead = True
            return True
        self.movement = self.calculate_movement(dt)
        self.loc[0] += self.movement[0] * self.speed_factor
        tile_loc = (int(self.loc[0])//tilemap.tile_size,int(self.loc[1])//tilemap.tile_size)
        key = f"{tile_loc[0]};{tile_loc[1]}" 
        if  key in tilemap.tilemap:
            
            tile = tilemap.tilemap[key]
            if tile.type.split('_')[1] == 'stairs' and tile.variant.split(';')[0] in ['0', '1']:
                check_rects = [pygame.Rect(tile_loc[0], tile_loc[1] + tilemap.tile_size + 4, tilemap.tile_size, 4),
                                pygame.Rect(tile_loc[0] + 12, tile_loc[1], 4, 12),
                                pygame.Rect(tile_loc[0] + 6, tile_loc[1] + 6, 6, 6)] if tile.variant.split(';')[0] == '0' else \
                                [pygame.Rect(tile_loc[0], tile_loc[1] + tilemap.tile_size + 4, tilemap.tile_size, 4),
                                pygame.Rect(tile_loc[0], tile_loc[1], 4, 12),
                                pygame.Rect(tile_loc[0] + 4, tile_loc[1] + 6, 6, 6)]
                for check_rect in check_rects:
                    if check_rect.collidepoint(self.center): 
                        if self.movement[0] <0 :
                            self.loc[0] =  check_rect.right
                        else:
                            self.loc[0] =  check_rect.left

                        self.angle = self.calculate_bounce_angle(self.angle,'x')
                        self.speed *= 0.8  
                        #self.dead = True 
                        #return True
            else: 
                if self.movement[0] <0 :
                    self.loc[0] =  tile_loc[0] * tilemap.tile_size + tilemap.tile_size
                else:
                    self.loc[0] =  tile_loc[0] * tilemap.tile_size - 1
                self.angle = self.calculate_bounce_angle(self.angle,'x')
                self.speed *= 0.8  #
                #self.dead = True 
                #return True


        self.loc[1] += self.movement[1] * self.speed_factor
        tile_loc = (int(self.loc[0])//tilemap.tile_size,int(self.loc[1])//tilemap.tile_size)
        key = f"{tile_loc[0]};{tile_loc[1]}" 
        
        if  key in tilemap.tilemap:
            tile = tilemap.tilemap[key]
            if tile.type.split('_')[1] == 'stairs' and tile.variant.split(';')[0] in ['0', '1']:
                check_rects = [pygame.Rect(tile_loc[0], tile_loc[1] + tilemap.tile_size + 4, tilemap.tile_size, 4),
                                pygame.Rect(tile_loc[0] + 12, tile_loc[1], 4, 12),
                                pygame.Rect(tile_loc[0] + 6, tile_loc[1] + 6, 6, 6)] if tile.variant.split(';')[0] == '0' else \
                                [pygame.Rect(tile_loc[0], tile_loc[1] + tilemap.tile_size + 4, tilemap.tile_size, 4),
                                pygame.Rect(tile_loc[0], tile_loc[1], 4, 12),
                                pygame.Rect(tile_loc[0] + 4, tile_loc[1] + 6, 6, 6)]
                for check_rect in check_rects:
                    if check_rect.collidepoint(self.center): 
                        if self.movement[0] <0 :
                            self.loc[1] =  check_rect.bottom
                        else:
                            self.loc[1] =  check_rect.top
                            
                        self.angle = self.calculate_bounce_angle(self.angle,'y')
                        self.speed *= 0.8  
                        #self.dead = True 
                        #return True
                    
            else:
                if self.movement[1] <0 :
                    self.loc[1] =  tile_loc[1]* tilemap.tile_size + tilemap.tile_size
                else:
                    self.loc[1] =  tile_loc[1]* tilemap.tile_size - 1
                self.angle = self.calculate_bounce_angle(self.angle,'y')
                self.speed *= 0.8
                #self.dead = True 
                #return True
        
       


        
        # a bunch of options to mess around with relating to angles...
        self.point_towards(math.pi / 2, 0.02)
        self.velocity_adjust(0.975, 0.05, 8, dt)
        #self.angle += 0.02

        self.speed -= 0.1

         
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
