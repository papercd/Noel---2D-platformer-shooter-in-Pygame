from pygame.math import Vector2 as vec2
from scripts.data import GRAVITY

class PhysicsEntity: 
    def __init__(self,name:str,size_in_pixels:tuple[int,int])->None: 
        self._size_in_pixels = size_in_pixels 
        self._name = name 

        self._on_ramp = False
        self._state = 'idle'
        self._flip = False

        self._collisions = {'up':False,'down':False,'left':False,'right':False}

        self._pos = vec2()
        self._velocity = vec2()
        self._acceleration = vec2(0,GRAVITY)

class Player(PhysicsEntity):
    def __init__(self)-> None:
        super().__init__('player', (16,16))