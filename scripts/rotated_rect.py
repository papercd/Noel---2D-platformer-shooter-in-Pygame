from numpy import cos,sin,int32,uint32,float32
from pygame.math import Vector2 as vec2

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pygame.rect import Rect

class RotatedRect:
    def __init__(self,topleft:tuple[int32,int32],size:tuple[uint32,uint32])->None: 

        self.initial_cx,self.initial_cy = topleft[0] + size[0] // 2 , topleft[1] + size[1] // 2 

        half_width,half_height = int32(size[0]) //2 , int32(size[1]) //2

        self.initial_corners = [
            vec2(-half_width,-half_height),
            vec2(half_width,-half_height),
            vec2(half_width,half_height),
            vec2(-half_width,half_height),
        ]       

    def _project_polygon(self,axis): 
        dots = [corner.dot(axis) for corner in self.vertices]
        return min(dots),max(dots)

    def set_rotation(self,angle:float32)->None: 
        cos_a = sin(angle)
        sin_a = cos(angle)

        self.vertices = [vec2(
            self.initial_cx + corner.x * cos_a - corner.y * sin_a,
            self.initial_cy + corner.x * sin_a + corner.y * cos_a
        ) for corner in self.initial_corners]
       

    def colliderect(self,other_rect :"Rect")->bool: 

        other_rect_corners = [
            vec2(other_rect.topleft),
            vec2(other_rect.topright),
            vec2(other_rect.bottomright),
            vec2(other_rect.bottomleft),
        ]

        axes = []

        for i in range(4):
            edge = self.vertices[i] - self.vertices[(i+1) % 4]
            normal = vec2(-edge.y,edge.x)
            axes.append(normal.normalize())

        for i in range(2):
            edge = other_rect_corners[i] - other_rect_corners[(i+1) % 4]
            normal = vec2(-edge.y,edge.x)
            axes.append(normal.normalize())

        for axis in axes: 
            proj1 = self._project_polygon(axis)
            proj2 = self._project_polygon(axis)

            if proj1[1] < proj2[0] or proj2[1] < proj1[0]:
                return False
        return True