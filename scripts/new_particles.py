from random import choice 
from scripts.new_tilemap import Tilemap




class ParticleSystem:
    def __init__(self) -> None:


        # can have at most 300 collide particles (when landing, when a bullet collides with a wall)
        self._max_collide_particle_count = 300
        self._collide_particle_pool_index = 299
        self._collide_particles = [] 

        # can have at most 700 fire particles 
        self._max_fire_particle_count = 700
        self._fire_particle_pool_index = 699
        self._fire_particles = []
        
        # can have at most 300 animated particles (jump, dash, ...)
        self._max_animation_particle_count = 300
        self._animation_particle_pool_index = 299        
        self._animation_particles = []

        self._initialize_particle_containers()

     
    def _initialize_particle_containers(self):
        for i in range(self._max_collide_particle_count):
            size = choice([(1,1),(2,1),(1,2),(3,1),(1,3),(2,2)])
            self._collide_particles.append(PhysicalParticle(size,[float('-inf'),float('inf')],0,0))

        for i in range(self._max_fire_particle_count):
            pass 

        for i in range(self._max_animation_particle_count):
            pass 


    def update(self,tilemap:Tilemap):
        pass 


class PhysicalParticle: 
    def __init__(self,size,pos:list[float,float],angle:float,speed,\
                color = (255,255,255,255),life = 60,gravity_factor =1):
        
        self._size = size 
        self._pos = pos
        self._angle  =angle 
        self._speed = speed
        self._life = life 
        self._color = color
        self._gravity_factor = gravity_factor
        self._active = False 


class FireParticle(PhysicalParticle):
    def __init__(self, size, pos: list[int], angle: float, speed, color, life=60, gravity_factor=1):
        super().__init__(size, pos, angle, speed, color, life, gravity_factor)



class AnimatedParticle: 
    def __init__(self) -> None:
        pass 