from dataclasses import dataclass as component 
from dataclasses import field
from pygame.rect import Rect
from pygame.math import Vector2 as vec2
from scripts.data import GRAVITY, AnimationDataCollection
 
from numpy import cos,sin, float32,uint16,uint32,int32,array,zeros

@component 
class PhysicsComponent: 
    size :     tuple[uint32,uint32] 
    flip :     bool = False 
    position : array = field(default_factory= lambda:array([0,0],dtype=int32))
    rotation : array = field(default_factory= lambda:array([0],dtype=float32))
    scale : array = field(default_factory= lambda : array([1.0,1.0],dtype = float32))
    origin : array = field(default_factory= lambda: array([0,0],dtype=float32))
    velocity : array = field(default_factory= lambda : array([0,0],dtype=float32))
    acceleration : array = field(default_factory= lambda: array([0,GRAVITY],dtype= float32))

    collision_rect : Rect = field(default_factory= lambda: Rect(0,0,1,1))
    displacement_buffer : array = field(default_factory= lambda: array([0,0],dtype= float32))
    
    prev_transform : array = field(default_factory= lambda: array([
        [1,0,0],                        
        [0,1,0],
        [0,0,1]
    ],dtype=float32)) # previous transform matrix to integrate interpolation for rendering.


    @property 
    def transform(self)->array: 
        cos_a = cos(self.rotation[0])
        sin_a = sin(self.rotation[0])

        tx = self.position[0] - self.origin[0] * self.scale[0] 
        ty = self.position[1] - self.origin[1] * self.scale[1] 
        
        return array([
            [(-2*self.flip +1) *cos_a * self.scale[0], -sin_a * self.scale[1], tx],
            [sin_a * self.scale[0], cos_a  * self.scale[1], ty],
            [0,0,1]
        ],dtype= float32)




@component 
class WeaponHolderComponent: 
    size: tuple[int,int] = (1,1)
    flip: bool = False 
    rotation: float = 0
    scale : vec2 = field(default_factory= lambda: vec2(1.0,1.0)) 
    origin : vec2 = field(default_factory= lambda:vec2(0,0))

    @property
    def transform(self,position:vec2)->array: 
        cos_a = cos(self.rotation)
        sin_a = sin(self.rotation)

        tx = position[0] - self.origin[0] * self.scale[0]
        ty = position[1] - self.origin[1] * self.scale[1] 


        return array([
            [(-2*self.flip +1) *cos_a * self.scale[0], -sin_a * self.scale[1], tx],
            [sin_a * self.scale[0], cos_a  * self.scale[1], ty],
            [0,0,1]
        ])

@component
class StateInfoComponent:
    type : str = "default"
    curr_state : str = "idle"
    max_health : uint16 = uint16(100)
    health : array = field(default_factory= lambda: array([100],dtype = uint16))
    max_jump_count : uint16 = uint16(5)
    jump_count : array = field(default_factory= lambda: array([0],dtype = uint16))
    dynamic : bool = True
    collide_left : bool = False
    collide_right : bool = False
    collide_top : bool = False
    collide_bottom : bool = False
    mouse_hold : bool = False

@component 
class ItemInfoComponent: 
    type: str = "item"
    active_time : array = field(default_factory= lambda: array([0],dtype = float32))
    dynamic : bool = False 
    mouse_hold : bool = False
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
    interact : bool  = False
    shoot: bool = False
    shift : bool = False

@component 
class AnimatedRenderComponent:
    animation_data_collection : AnimationDataCollection
    vertices_bytes : bytes = field(default_factory= lambda: zeros(6).tobytes())

@component
class StaticRenderComponent: 
    vertices_bytes : bytes = field(default_factory= lambda: zeros(6).tobytes())

@component 
class ParticleEmiiterComponent: 
    pass 

