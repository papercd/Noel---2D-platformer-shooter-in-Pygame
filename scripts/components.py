from dataclasses import dataclass as component 
from dataclasses import field
from moderngl import Texture
from pygame import FRect
from pygame.math import Vector2 as vec2
from scripts.data import GRAVITY
import numpy as np


@component 
class PhysicsComponent: 
    size :     tuple[int,int] 
    flip :     bool = False
    position : vec2  = field(default_factory= lambda:vec2(0,0))         # world coordinates of entity. 
    rotation : float = 0                                                # rotation angle in radians 
    scale :    vec2  = field(default_factory= lambda:vec2(1.0,1.0))     #  (1.0,1.0)
    origin :   vec2  = field(default_factory= lambda:vec2(0,0))         # local origin coordinates (0,0) is topleft. 
    velocity:  vec2  = field(default_factory= lambda:vec2(0,0))
    acceleration: vec2 = field(default_factory= lambda:vec2(0,GRAVITY))
    
    collision_rect : FRect = field(default_factory= lambda:FRect(0,0,1,1))

    @property 
    def transform(self)->np.array: 
        cos_a = np.cos(self.rotation)
        sin_a = np.sin(self.rotation)

        tx = self.position[0] - self.origin[0] * self.scale[0]
        ty = self.position[1] - self.origin[1] * self.scale[1]

        return np.array([
            [cos_a * self.scale[0], -sin_a * self.scale[1], tx],
            [sin_a * self.scale[0], cos_a  * self.scale[1], ty],
            [0,0,1]
        ])



@component 
class RenderComponent:
    ref_texture_atlass : Texture
    texcoords: np.array 
    vertices : np.array = field(default_factory= lambda: np.zeros(6))

