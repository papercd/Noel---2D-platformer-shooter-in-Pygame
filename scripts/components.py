from dataclasses import dataclass as component 
from dataclasses import field
from pygame.rect import Rect
from scripts.frect import FRect
from pygame.math import Vector2 as vec2
from scripts.data import GRAVITY, AnimationDataCollection
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
    
    collision_rect : Rect = field(default_factory= lambda: Rect(0,0,1,1))
    displacement_buffer : vec2 = field(default_factory= lambda: vec2(0,0))
    
    prev_transform : np.array = field(default_factory= lambda: np.array([
        [1,0,0],                        
        [0,1,0],
        [0,0,1]
    ])) # previous transform matrix to integrate interpolation for rendering.


    @property 
    def transform(self)->np.array: 
        cos_a = np.cos(self.rotation)
        sin_a = np.sin(self.rotation)

        tx = self.position[0] - self.origin[0] * self.scale[0] 
        ty = self.position[1] - self.origin[1] * self.scale[1] 
        
        return np.array([
            [(-2*self.flip +1) *cos_a * self.scale[0], -sin_a * self.scale[1], tx],
            [sin_a * self.scale[0], cos_a  * self.scale[1], ty],
            [0,0,1]
        ])

    
        


@component
class StateInfoComponent:

    type : str = "default"
    curr_state : str = "idle"
    has_weapon : bool = False
    max_jump_count : int = 0
    jump_count : int = 0
    collide_left : bool = False
    collide_right : bool = False
    collide_top : bool = False
    collide_bottom : bool = False



@component 
class InputComponent: 
    left: bool = False
    right: bool = False 
    up : bool = False 
    down : bool = False 
    open_inventory: bool = False 
    interact : bool  = False
    shoot: bool = False


@component 
class RenderComponent:
    animation_data_collection : AnimationDataCollection
    vertices : np.array = field(default_factory= lambda: np.zeros(6))

