import pygame
from pygame.math import Vector2
from scripts.range import *

class QuadTree:
    def __init__(self, capacity, boundary):
        self.capacity = capacity
        self.boundary = boundary
        self.entities = []
        self.color = (255, 255, 255)

        self.northWest = None
        self.northEast = None
        self.southWest = None
        self.southEast = None

    def subdivide(self):
        parent = self.boundary

        boundary_nw = Rectangle(
                Vector2(
                parent.position.x ,
                parent.position.y
                ),
            parent.scale/2
            )
        boundary_ne = Rectangle(
                Vector2(
                parent.position.x + parent.scale.x/2,
                parent.position.y
                ),
                parent.scale/2
            )
        boundary_sw = Rectangle(
                Vector2(
                parent.position.x,
                parent.position.y + parent.scale.y/2
                ),
                parent.scale/2
            )
        boundary_se = Rectangle(
                Vector2(
                parent.position.x + parent.scale.x/2,
                parent.position.y + parent.scale.y/2
                ),
                parent.scale/2
            )

        self.northWest = QuadTree(self.capacity, boundary_nw)
        self.northEast = QuadTree(self.capacity, boundary_ne)
        self.southWest = QuadTree(self.capacity, boundary_sw)
        self.southEast = QuadTree(self.capacity, boundary_se)

        for i in range(len(self.entities)):
            self.northWest.insert(self.entities[i])
            self.northEast.insert(self.entities[i])
            self.southWest.insert(self.entities[i])
            self.southEast.insert(self.entities[i])
    def insert(self, entity):
        if self.boundary.containsEntity(entity) == False:
            return False

        if len(self.entities) < self.capacity and self.northWest == None:
            self.entities.append(entity)
            return True
        else:
            if self.northWest == None:
                self.subdivide()

            if self.northWest.insert(entity):
                return True
            if self.northEast.insert(entity):
                return True
            if self.southWest.insert(entity):
                return True
            if self.southEast.insert(entity):
                return True
            return False

    def queryRange(self, _range , e_type = None):
        entitiesInRange = []
        
        if type(_range) == Circle:
            if _range.intersects(self.boundary)==False:
                return entitiesInRange
        elif type(_range) == Rectangle:
            if _range.intersects(self.boundary)==True:
                return entitiesInRange

        for entity in self.entities:
            if e_type == None: 
                if _range.containsEntity(entity):
                    entitiesInRange.append(entity)
            else: 
                if entity.e_type == e_type and _range.containsEntity(entity):
                    entitiesInRange.append(entity) 
                
        if self.northWest != None:
            entitiesInRange += self.northWest.queryRange(_range,e_type)
            entitiesInRange += self.northEast.queryRange(_range,e_type)
            entitiesInRange += self.southWest.queryRange(_range,e_type)
            entitiesInRange += self.southEast.queryRange(_range,e_type)

        # if self.boundary.intersects(_range):
        #     return elementsInRange
        # else:
        #     for element in self.elements:
        #         if _range.containselement(element):
        #             elementsInRange.append(element)
        #
        #     if self.northWest != None:
        #         elementsInRange += self.northWest.queryRange(_range)
        #         elementsInRange += self.northEast.queryRange(_range)
        #         elementsInRange += self.southWest.queryRange(_range)
        #         elementsInRange += self.southEast.queryRange(_range)
        #
        #     return elementsInRange
        return entitiesInRange

    def Show(self, screen):
        self.boundary.Draw(screen)
        if self.northWest != None:
            self.northWest.Show(screen)
            self.northEast.Show(screen)
            self.southWest.Show(screen)
            self.southEast.Show(screen)
