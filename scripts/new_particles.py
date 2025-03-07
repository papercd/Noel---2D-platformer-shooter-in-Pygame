from random import choice ,randint,uniform
from pygame import Surface
from pygame.math import Vector2 as vec2 
from pygame import Rect
from math import cos,sin,radians,sqrt,degrees,atan2
from scripts.data import CollideParticleData,FireParticleData,AnimationParticleData,Animation,SparkData
from scripts.data import PARTICLE_ANIMATION_DATA
from concurrent.futures import ThreadPoolExecutor
import numpy as np 

from typing import TYPE_CHECKING

if TYPE_CHECKING: 
    from scripts.new_grass import GrassManager
    from scripts.new_tilemap import Tilemap
    from my_pygame_light2d.light import PointLight


class ParticleSystem:
    _instance = None 
    
    @staticmethod
    def get_instance()-> "ParticleSystem":
        if ParticleSystem._instance is None: 
            ParticleSystem._instance = ParticleSystem()
        return ParticleSystem._instance

    def __init__(self) -> None:
        # can have at most 300 collide particles (when landing, when a bullet collides with a wall)
        self._max_collide_particle_count = 300
        self._collide_particle_pool_index = 299
        self._collide_particles = [] 

        # Creating new fire particle system 

        self._max_fire_particle_count = 600
        self._fire_particle_pool_index = 599
        self._fire_particles = []

        # testing new fire particle system to utilize compute shader
        #self._max_fire_particle_count = 600 
        #self._fire_particle_pool_index = 599 
        
        """ particle data attributes
        
        damage , life, dead, i, position(vec2) , velocity(vec2) , 
        sin , sinr , spread , rise_normal(vec2) , rise , rise_angle , r , 0's (vec2), alpha 
        
        """

        #self._fire_particle_data = np.zeros((self._max_fire_particle_count,20),dtype= np.float32) 

        # can have at most 300 animated particles (jump, dash, ...)
        self._max_animation_particle_count = 300
        self._animation_particle_pool_index = 299        
        self._animation_particles = []


        # can have at most 300 sparks 
        self._max_sparks_count = 300
        self._sparks_pool_index = 299
        self._sparks = []

        self._active_collide_particles = set( )
        self._active_animation_particles = set( )
        self._active_fire_particles = set()
        self._active_sparks = set()

        # create particle pools
        self._initialize_particle_containers()




    def _initialize_particle_containers(self):
        for i in range(self._max_collide_particle_count):
            particle_data = CollideParticleData((1,1),[float('-inf'),float('inf')],0,0,(255,255,255,255),60,1)
            self._collide_particles.append(PhysicalParticle(particle_data))

        # Creating new fire particle system 
        
        for i in range(self._max_fire_particle_count):
            particle_data = FireParticleData(0,0,0,0,0,0,0,0,0)
            self._fire_particles.append(FireParticle(particle_data))
        

        for i in range(self._max_animation_particle_count):
            animation = Animation(0,0,False,False)
            particle_data = AnimationParticleData("None",[0,0],[0,0],0,False,None)
            self._animation_particles.append(AnimatedParticle(particle_data,animation))

        for i in range(self._max_sparks_count):
            spark_data = SparkData([float('-inf'),float('inf')],1,0,1,1,(255,255,255),1)
            self._sparks.append(Spark(spark_data))



    def add_particle(self,particle_data,light:"PointLight" =None):
        if isinstance(particle_data,CollideParticleData):
            particle =self._collide_particles[self._collide_particle_pool_index]
            particle._active = True 
            particle.set_new_data(particle_data)
            self._active_collide_particles.add(particle)
            self._collide_particle_pool_index = (self._collide_particle_pool_index -1) % self._max_collide_particle_count 
            # creating new fire particle system 
            
        elif isinstance(particle_data,FireParticleData):
            particle = self._fire_particles[self._fire_particle_pool_index]
            particle._active = True 
            particle.set_new_data(particle_data)
            if light: 
                light.illuminator = particle 
            self._active_fire_particles.add(particle)
            self._fire_particle_pool_index = (self._fire_particle_pool_index -1) % self._max_fire_particle_count 
            
            """
        elif isinstance(particle_data,FireParticleData):
            queried_particle_data = self._fire_particle_data[self._fire_particle_pool_index]
            if self._active_fire_particle_indices[self._fire_particle_pool_index] == 0 :
                self._active_fire_particle_indices[self._fire_particle_pool_index] = 1
                self._active_fire_particle_count += 1
                self._set_fire_particle_data(queried_particle_data,particle_data)
                self._fire_particle_pool_index = (self._fire_particle_pool_index -1) % self._max_fire_particle_count
            """

        elif isinstance(particle_data,SparkData):
            particle = self._sparks[self._sparks_pool_index]
            particle._active = True 
            particle.set_new_data(particle_data)
            if light: 
                light.illuminator = particle
            self._active_sparks.add(particle)
            self._sparks_pool_index = (self._sparks_pool_index-1) % self._max_sparks_count
        elif isinstance(particle_data,AnimationParticleData):
            particle =self._animation_particles[self._animation_particle_pool_index]
            particle._active = True 
            particle.set_new_data(particle_data)

            self._active_animation_particles.add(particle)
            self._animation_particle_pool_index = (self._animation_particle_pool_index -1) % self._max_animation_particle_count 

    
    def _set_fire_particle_data(self,queried_particle_container,particle_data)->None: 
        queried_particle_container[0] = particle_data.damage
        life = randint(particle_data.size *5,particle_data.size*10)
        queried_particle_container[1] = life
        queried_particle_container[2] = life
        queried_particle_container[3] = 0
        queried_particle_container[4] = 0
        # position
        queried_particle_container[5] = particle_data.x
        queried_particle_container[6] = particle_data.y
        # velocity
        queried_particle_container[7] = 0
        queried_particle_container[8] = 0

        queried_particle_container[8] = randint(-10,10)/7
        queried_particle_container[10] = randint(5,10) 
        queried_particle_container[11] = particle_data.spread
        rise_vec = vec2(cos(radians(particle_data.rise_angle)),sin(radians(particle_data.rise_angle)))
        rise_normal = rise_vec.rotate(90).normalize()

        # rise normal 
        queried_particle_container[12] = rise_normal.x
        queried_particle_container[13] = rise_normal.y

        queried_particle_container[14] = particle_data.rise * 1.3
        queried_particle_container[15] = particle_data.rise_angle

        queried_particle_container[16] = randint(1,2)
        
        # Os
        queried_particle_container[17] = randint(-1,1)
        queried_particle_container[18] = randint(-1,1)

        # alpha
        queried_particle_container[19] = 255  

    
    def _update_particle_group(self, particles, update_function, *args):
        particles_to_remove = set()
        for particle in particles:
            if update_function(particle, *args):
                particles_to_remove.add(particle)
        return particles_to_remove



    def update(self, tilemap, grass_manager, dt):

            groups = [
                (self._active_collide_particles, lambda p: p.update(tilemap, dt)),
                (self._active_animation_particles, lambda p: p.update(dt)),
                (self._active_fire_particles,lambda p:p.update(tilemap,grass_manager,dt)),
                (self._active_sparks, lambda p: p.update(tilemap, dt)),
            ]

            # Thread-safe removal and processing
            with ThreadPoolExecutor() as executor:

              
                futures = {
                    executor.submit(self._update_particle_group, group[0], group[1]): group[0]
                    for group in groups
                }

                for future in futures:
                    particles_to_remove = future.result()
                    futures[future] -= particles_to_remove

class PhysicalParticle: 
    def __init__(self,particle_data:CollideParticleData):
        self._size = particle_data.size 
        self._pos = particle_data.pos
        self._angle  =particle_data.angle 
        self._speed = particle_data.speed
        self._velocity = [0,0]
        self._life = particle_data.life 
        self._color = particle_data.color
        self._gravity_factor = particle_data.gravity_factor
        self._rect = Rect(self._pos[0],self._pos[1],self._size[0],self._size[1])
        self._buffer_surf = Surface(self._size).convert_alpha()
        self._active = False 

    def set_new_data(self,particle_data:CollideParticleData):
        # size is not changed as it is predetermined 

        self._pos = particle_data.pos
        self._angle  =particle_data.angle 
        self._speed = particle_data.speed
        self._life = particle_data.life 
        self._color = particle_data.color
        self._gravity_factor = particle_data.gravity_factor
        self._velocity = [0,0]
        self._buffer_surf.fill(self._color)
        self._rect = Rect(self._pos[0],self._pos[1],self._size[0],self._size[1])

    def update(self,tilemap:"Tilemap",dt):
        scaled_dt = dt * 60

        # testing 
        self._life -= scaled_dt 
        if self._life <= 0:
            return True
        gravity = 0.23
        self._velocity[1] = min(6,self._velocity[1] + gravity* self._gravity_factor * scaled_dt)

        for rect_tile in tilemap.phy_rects_around(self._pos,self._size):
            if self._rect.colliderect(rect_tile[0]):
                rel_pos,variant = map(int,rect_tile[1].variant.split(';'))
                if rect_tile[1].type == 'stairs' and rel_pos in [0,1]:
                    if rel_pos == 0:
                        check_rects = [Rect(rect_tile[0].left,rect_tile[0].bottom + 4,rect_tile[0].width,4),
                                       Rect(rect_tile[0].left + 12,rect_tile[0].top,4,12),
                                       Rect(rect_tile[0].left + 6,rect_tile[0].top + 6,6,6)
                                       ]
                        for check_rect in check_rects:
                            if self._rect.colliderect(check_rect):
                                return True 
                    else:
                        check_rects = [Rect(rect_tile[0].left,rect_tile[0].bottom + 4,rect_tile[0].width,4),
                                       Rect(rect_tile[0].left,rect_tile[0].top,4,12),
                                       Rect(rect_tile[0].left + 4,rect_tile[0].top + 6,6,6)
                                       ]
                        for check_rect in check_rects:
                            if self._rect.colliderect(check_rect):
                                return True 
                else: 
                    return True 
        self._pos[0] += cos(radians(self._angle)) * self._speed * scaled_dt   
        self._pos[1] += sin(radians(self._angle)) * self._speed * scaled_dt 
        self._pos[1] += self._velocity[1] *scaled_dt 
        self._rect.topleft = self._pos

        self._speed = max(0,self._speed -0.1 * scaled_dt)

        return False 
    

class Spark: 
    def __init__(self,particle_data:SparkData)->None:
        self.pos = particle_data.pos
        self.decay_factor = particle_data.decay_factor
        self.center = self.pos
        self.angle = particle_data.angle
        self.scale = particle_data.scale
        self.color = particle_data.color
        self.speed = particle_data.speed
        self.velocity = [0,0]
        self.dead = False 
        self._active = False
        self.speed_factor = particle_data.speed_factor


    def _point_towards(self,angle,rate):
        rotate_direction = ((angle-self.angle + 180 * 3)% (180*2)) - 180
        try: 
            rotate_sign = abs(rotate_direction) / rotate_direction
        except ZeroDivisionError:
            rotate_sign = 1
        if abs(rotate_sign) < rate: 
            self.angle = angle 
        else: 
            self.angle += rate*rotate_sign

    def _velocity_adjust(self,friction,force,terminal_velocity,dt):
        friction += uniform(-0.01,0.01)
        force += uniform(-0.05,0.05)

        movement = self._calculate_movement(dt)
        movement[1] = min(terminal_velocity,movement[1] + force )
        movement[0] *= friction * dt
        self.angle = degrees(atan2(-movement[1],movement[0]))

    def _calculate_velocity(self)->list[float,float]:
        return [cos(radians(self.angle))*self.speed*self.speed_factor,
                -sin(radians(self.angle))*self.speed*self.speed_factor]

    
    def _calculate_bounce_angle(self,axis:str): 
        if axis == 'x':
            reflected_angle = 180 - self.angle
        else: 
            reflected_angle = -self.angle
        return reflected_angle
    

    def set_new_data(self,particle_data:SparkData)-> None: 
        self.pos = particle_data.pos
        self.decay_factor = particle_data.decay_factor
        self.center = self.pos
        self.angle = particle_data.angle
        self.scale = particle_data.scale
        self.color = particle_data.color 
        self.speed = particle_data.speed
        self.speed_factor = particle_data.speed_factor
        self.dead = False
    

    def update(self,tilemap:"Tilemap",dt)->None: 
        if self.speed < 0:
            self.dead = True
            return True 
        scaled_dt = dt * 60
        self.velocity = self._calculate_velocity()

        self.pos[0] += self.velocity[0] * scaled_dt
        key= (int(self.pos[0])//tilemap.tile_size,int(self.pos[1])//tilemap.tile_size)

        if key in tilemap.physical_tiles:
            tile = tilemap.physical_tiles[key][0]
            if tile.type == 'lights':
                pass 
            elif tile.type.endswith('stairs') and tile.variant.split(';')[0] in ('0','1'):
                pass 
            else: 
                if self.velocity[0] < 0 :
                    self.pos[0] = (key[0]+1) * tilemap.tile_size  
                else:
                    self.pos[0] = key[0] * tilemap.tile_size - 1
                self.angle = self._calculate_bounce_angle('x')
                self.speed *= 0.8

        self.pos[1] += self.velocity[1] *scaled_dt

        key= (int(self.pos[0])//tilemap.tile_size,int(self.pos[1])//tilemap.tile_size)
        if key in tilemap.physical_tiles:
            tile = tilemap.physical_tiles[key][0]
            if tile.type == 'lights':
                pass 
            elif tile.type.endswith('stairs') and tile.variant.split(';')[0] in ('0','1'):
                pass 
            else: 
                if self.velocity[1] < 0 :
                    self.pos[1] = (key[1]+1) * tilemap.tile_size 
                else:
                    self.pos[1] = key[1] * tilemap.tile_size - 1
                self.angle = self._calculate_bounce_angle('y')
                self.speed *= 0.8


        self._point_towards(90, 0.02)
        #self._velocity_adjust(0.975,0.05,6,dt)

        angle_jitter = uniform(-4,4)
        self.angle += angle_jitter * dt * 60
        self.speed -= 0.1*self.decay_factor*dt*110

        return False 
    

class FireParticle:
    def __init__(self,particle_data:FireParticleData):
       
        self.origin = (particle_data.x,particle_data.y) 
       
        # -------------   predetermined particle parameters 
        self.rise = particle_data.rise * 1.3
        self.spread = particle_data.spread
        self.rise_angle = particle_data.rise_angle
        self.damage = particle_data.damage
        self.max_damage =particle_data.damage
        #---------------
        
        self.rise_vec = vec2(cos(radians(self.rise_angle)), sin(radians(self.rise_angle)))
        self.rise_normal = self.rise_vec.rotate(90).normalize()

        self.x, self.y = particle_data.x, particle_data.y
        self.pos = [self.x,self.y]

        self.maxlife = randint( int(particle_data.size*5),   int(particle_data.size*10))
        self.life = self.maxlife
        self.dir = choice((-2, -1, 1, 2))
        self.sin = randint(-10, 10)/7
        self.sinr = randint(5, 10)
        self.r = randint(1,2)

        self.velocity = [0,0]
        self.center = [self.x + self.r,self.y+self.r]
        self.ren_x,self.ren_y = self.x,self.y

        self.ox = randint(-1, 1)
        self.oy = randint(-1, 1)
        self.palette = ((255, 255, 0),
            (255, 173, 51),
            (247, 117, 33),
            (191, 74, 46),
            (115, 61, 56),
            (61, 38, 48))[::-1]
        
        self.alpha = 255
        self.i = 0

        self.dead = False
        self._active = False 

        """
        attributes that change: 
        self.damage float 
        self.life   float
        self.dead   float
        self.i      float
        self.velocity   2 floats
        self.x,self.y    2 floats 
        self.ren_x,self.ren_y  2 floats
        self.center   2floats 
        self.alpha    1float
        """

    def set_new_data(self,particle_data:FireParticleData):
        self.origin = (particle_data.x,particle_data.y) 
       
        # -------------   predetermined particle parameters 
        self.rise = particle_data.rise * 1.3
        self.spread = particle_data.spread
        self.rise_angle = particle_data.rise_angle
        self.damage = particle_data.damage
        self.max_damage =particle_data.damage
        #---------------
        
        self.rise_vec = vec2(cos(radians(self.rise_angle)), sin(radians(self.rise_angle)))
        self.rise_normal = self.rise_vec.rotate(90).normalize()

        self.x, self.y = particle_data.x, particle_data.y
        self.pos = [self.x,self.y]

        self.maxlife = randint( int(particle_data.size*5),   int(particle_data.size*10))
        self.life = self.maxlife
        self.dir = choice((-2, -1, 1, 2))
        self.sin = randint(-10, 10)/7
        self.sinr = randint(5, 10)
        self.r = randint(1,2)

        self.center = [self.x + self.r,self.y+self.r]
        self.ren_x,self.ren_y = self.x,self.y

        self.ox = randint(-1, 1)
        self.oy = randint(-1, 1)
        self.alpha = 255
        self.i = 0

        self.dead = False


    def rect(self):
        return Rect(self.x-self.r,self.y-self.r,self.r * 2,self.r * 2)
    
    def point_circle_collision(self,point_x, point_y):
        """
        Check if a point is within the circle.
        """
        distance = sqrt((point_x - self.x)**2 + (point_y - self.y)**2)
        return distance <= self.r


    def check_collision_with_rect(self,other):
        """
        Check if a circle has collided with a rectangle and return collision information.
        """
        
        
        # Check if the circle's center is inside the rectangle
        if other.left <= self.x <= other.right and other.top <= self.y <= other.top + other.height:
            return "Center", True
        
        # Check if any of the rectangle's corners are within the circle
        corners = [other.topleft, other.topright, other.bottomleft, other.bottomright]
        for corner in corners:
            if self.point_circle_collision(corner[0], corner[1]):
                return "Corner",True 
        
        # Check if any of the rectangle's sides intersect with the circle
        if other.left <= self.x <= other.right:
            if abs(self.y - other.top) <= self.r:
                return  "Top", True 
            elif abs(self.y - other.bottom) <= self.r:
                return  "Bottom",True 
        if other.top <= self.y <= other.bottom:
            if abs(self.x - other.left) <= self.r:
                return  "Left", True 
            elif abs(self.x - other.right) <= self.r:
                return  "Right", True 
        
        # If none of the above conditions are met, there's no collision
        return False, None

    def collide(self, other):
        # Check for collision between a circle and a rectangle 
        #other is an entity object. 

        # complete boundbox of the rectangle
        rleft, rtop = other.collision_rect().left,other.collision_rect().top
        rright, rbottom = other.collision_rect().right ,other.collision_rect().bottom

        if rleft <= self.x <= rright and rtop <= self.y <= rbottom:
            return True
        
        # Check if any of the rectangle's corners are within the circle
        corners = [(rleft,rtop), (rright,rtop), (rleft,rbottom), (rright,rbottom)]
        for corner in corners:
            if self.point_circle_collision(corner[0], corner[1]):
                return True 
        
        # Check if any of the rectangle's sides intersect with the circle
        if rleft <= self.x <= rright:
            if abs(self.y - rtop) <= self.r:
                return   True 
            elif abs(self.y - (rbottom)) <= self.r:
                return  True 
        if rtop <= self.y <= rbottom:
            if abs(self.x - rleft) <= self.r:
                return   True 
            elif abs(self.x - (rright)) <= self.r:
                return   True 
        
        # If none of the above conditions are met, there's no collision
        return False

    def _calculate_bounce_angle(self,axis:str): 
        if axis == 'x':
            reflected_angle = 180 - self.rise_angle
        else: 
            reflected_angle = -self.rise_angle
        return reflected_angle


    def update(self,tilemap:"Tilemap",grass_manager:"GrassManager",dt:float):
        self.damage = max(2,int(self.damage * (self.life / self.maxlife)))
        scaled_dt = dt * 60

        self.life -= scaled_dt
        
        if self.life <= 0: 
            self.dead = True 
            return True 
        
        self.i = int((self.life/self.maxlife)*6)

        # TODO: don't oscillate particle if it has collided. 

        self.velocity= [
                ((self.sin * sin(self.life/(self.sinr)))/2)*self.spread * self.rise_normal.x    + self.rise * cos(radians(self.rise_angle)),
                (self.rise * sin(radians(self.rise_angle)) + self.rise_normal.y * self.spread * ((self.sin * sin(self.life/(self.sinr)))/2))
        ]
        """
        for rect_tile in tilemap.phy_rects_around((self.pos[0]-self.r,self.pos[1] - self.r),(self.r * 2, self.r * 2)):
            
            side_point, collided = self.check_collision_with_rect(rect_tile[0])
            
            if collided: 
                if not rect_tile[1].type == 'stairs':
                    if rect_tile[1].type =='live_grass':
                        loc = (rect_tile[1].pos[0]//16,rect_tile[1].pos[1]//16)
                        if loc in self.game.gm.grass_tiles:
                            self.game.gm.grass_tiles[loc].burning -= 0.3
                        #self.game.gm.burn_tile((rect_tile[1].pos[0]//16,rect_tile[1].pos[1]//16))
                    else:
                        incid_angle = degrees(atan2(self.pos[1] - self.origin[1],self.pos[0] - self.origin[0]))
                        if side_point == "Top" or side_point == "Bottom":
                            self.rise *= 0.7
                            #self.rise_angle = self._calculate_bounce_angle('x')
                        elif side_point == 'Left' or side_point == 'Right':
                            self.rise *= 0.7
                            #self.rise_angle = self._calculate_bounce_angle('y')
                        elif side_point == 'Center':
                            self.rise *= 0.3
                        else:
                            self.rise *= 0.7

                else: 
                    #collision with stairs 
                    incid_angle = degrees(atan2(self.pos[1] - self.origin[1],self.pos[0] - self.origin[0]))

                    if rect_tile[1].variant.split(';')[0] == '0' :
                        #left stairs
                        #this part where check rects are created is not dynamic, so if tilesize changes this part needs to be changed manually. maybe figure out an algorithmic 
                        #way to create rects for stairs. 
                        check_rects = [Rect(rect_tile[0].left,rect_tile[0].bottom + 4,rect_tile[0].width,4),
                                       Rect(rect_tile[0].left + 12,rect_tile[0].top,4,12),
                                       Rect(rect_tile[0].left + 6,rect_tile[0].top + 6,6,6)
                                       ]
                        for check_rect in check_rects:
                            side_point,collided = self.collide_with_rect(check_rect)
                            if collided: 
                                if side_point == "Top" or side_point == "Bottom":
                                    self.rise *= 0.7
                                    #self.rise_angle = self._calculate_bounce_angle('x')
                                elif side_point == 'Left' or side_point == 'Right':
                                    self.rise *= 0.7
                                    #self.rise_angle = self._calculate_bounce_angle('y')
                                elif side_point == 'Center':
                                    self.rise *= 0.3
                                else:
                                    self.rise *= 0.7
                                
                                break 
                        
                    elif rect_tile[1].variant.split(';')[0] == '1' :
                        #right stairs 
                        check_rects = [Rect(rect_tile[0].left,rect_tile[0].bottom + 4,rect_tile[0].width,4),
                                       Rect(rect_tile[0].left,rect_tile[0].top,4,12),
                                       Rect(rect_tile[0].left + 4,rect_tile[0].top + 6,6,6)
                                       ]
                        for check_rect in check_rects:
                            side_point,collided = self.collide_with_rect(check_rect)
                            if collided: 
                                if side_point == "Top" or side_point == "Bottom":
                                    self.rise *= 0.7
                                    #self.rise_angle = self._calculate_bounce_angle('x')
                                elif side_point == 'Left' or side_point == 'Right':
                                    self.rise *= 0.7
                                    #self.rise_angle  = self._calculate_bounce_angle('y')
                                elif side_point == 'Center':
                                    self.rise *= 0.3
                                else:
                                    self.rise *= 0.7
                                
                                break 
        """

        self.x += self.velocity[0] * scaled_dt
        self.y += self.velocity[1] * scaled_dt

        self.pos = [self.x,self.y]

        if not randint(0,5):
            self.r += 0.88 *scaled_dt 
        
        self.ren_x,self.ren_y = self.x,self.y
        self.ren_x += self.ox*(5-self.i) * scaled_dt
        self.ren_y += self.oy*(5-self.i) * scaled_dt

        self.center[0] = self.ren_x + self.r
        self.center[1] = self.ren_y + self.r
        
        if self.life < self.maxlife/4:
            self.alpha = int((self.life/self.maxlife)*255)

        return False 


    def update_pos(self,tilemap,j):
        self.damage = max(2,int(self.damage * (self.life/self.maxlife)))

        self.life -=1
        
      
        if self.life == 0:
            self.dead = True 
            del self 
            return True 
        
       
        self.i = int((self.life/self.maxlife)*6)
       
        

        frame_movement = [
                ((self.sin * sin(j/(self.sinr)))/2)*self.spread * self.rise_normal.x    + self.rise * cos(radians(self.rise_angle)),
                -(self.rise * sin(radians(self.rise_angle)) + self.rise_normal.y * self.spread * ((self.sin * sin(j/(self.sinr)))/2))
        ]



        self.x +=  frame_movement[0] 
        self.y += frame_movement[1] 
        
        grass_check = j % 11== 0

        for rect_tile in tilemap.physics_rects_around((self.pos[0] - self.r,self.pos[1] - self.r),(self.r * 2,self.r * 2),grass_check=grass_check):
              
             
            side_point,collided = self.collide_with_rect(rect_tile[0])
            if collided: 
                if not rect_tile[1].type == 'stairs':
                    if rect_tile[1].type =='live_grass':
                        loc = (rect_tile[1].pos[0]//16,rect_tile[1].pos[1]//16)
                        if loc in self.game.gm.grass_tiles:
                            self.game.gm.grass_tiles[loc].burning -= 0.3
                        #self.game.gm.burn_tile((rect_tile[1].pos[0]//16,rect_tile[1].pos[1]//16))
                    else:
                        incid_angle = degrees(atan2(self.pos[1] - self.origin[1],self.pos[0] - self.origin[0]))
                        if side_point == "Top" or side_point == "Bottom":
                            self.rise *= 0.7
                            #self.rise_angle = incid_angle
                        elif side_point == 'Left' or side_point == 'Right':
                            self.rise *= 0.7
                            #self.rise_angle = -180 + incid_angle
                        elif side_point == 'Center':
                            self.rise *= 0.3
                        else:
                            self.rise *= 0.7
                            #self.rise_angle += 180  
                else: 
                    #collision with stairs 
                    incid_angle = degrees(atan2(self.pos[1] - self.origin[1],self.pos[0] - self.origin[0]))

                    if rect_tile[1].variant.split(';')[0] == '0' :
                        #left stairs
                        #this part where check rects are created is not dynamic, so if tilesize changes this part needs to be changed manually. maybe figure out an algorithmic 
                        #way to create rects for stairs. 
                        check_rects = [Rect(rect_tile[0].left,rect_tile[0].bottom + 4,rect_tile[0].width,4),
                                       Rect(rect_tile[0].left + 12,rect_tile[0].top,4,12),
                                       Rect(rect_tile[0].left + 6,rect_tile[0].top + 6,6,6)
                                       ]
                        for check_rect in check_rects:
                            side_point,collided = self.collide_with_rect(check_rect)
                            if collided: 
                                if side_point == "Top" or side_point == "Bottom":
                                    self.rise *= 0.7
                                    #self.rise_angle = incid_angle
                                elif side_point == 'Left' or side_point == 'Right':
                                    self.rise *= 0.7
                                    #self.rise_angle = -180 + incid_angle
                                elif side_point == 'Center':
                                    self.rise *= 0.3
                                else:
                                    self.rise *= 0.7
                                    #self.rise_angle += 180  
                                
                                break 

                        
                        
                    elif rect_tile[1].variant.split(';')[0] == '1' :
                        #right stairs 
                        check_rects = [Rect(rect_tile[0].left,rect_tile[0].bottom + 4,rect_tile[0].width,4),
                                       Rect(rect_tile[0].left,rect_tile[0].top,4,12),
                                       Rect(rect_tile[0].left + 4,rect_tile[0].top + 6,6,6)
                                       ]
                        for check_rect in check_rects:
                            side_point,collided = self.collide_with_rect(check_rect)
                            if collided: 
                                if side_point == "Top" or side_point == "Bottom":
                                    self.rise *= 0.7
                                    self.rise_angle = incid_angle
                                elif side_point == 'Left' or side_point == 'Right':
                                    self.rise *= 0.7
                                    self.rise_angle = -180 + incid_angle
                                elif side_point == 'Center':
                                    self.rise *= 0.3
                                else:
                                    self.rise *= 0.7
                                    self.rise_angle += 180  
                                
                                break 

                        
                         
        self.pos = [self.x,self.y]

        if not randint(0, 5): 
            self.r += 0.88

        self.ren_x, self.ren_y = self.x, self.y
        self.ren_x += self.ox*(5-self.i)
        self.ren_y += self.oy*(5-self.i)

        self.center[0] = self.ren_x + self.r
        self.center[1] = self.ren_y + self.r
        
        if self.life < self.maxlife/4:
            self.alpha = int((self.life/self.maxlife)*255)

        return False 
    
    def render(self,bsurf,offset=(0,0)):
        pass 
        """
        pygame.draw.circle(bsurf,self.palette[self.i] + (self.alpha,), (self.x-offset[0], self.y-offset[1]), self.r, 0) 
        if self.i == 0:
            pygame.draw.circle(bsurf, (0, 0, 0, 0), (self.x+random.randint(-1, 1)-offset[0], self.y-4-offset[1]), self.r*(((self.maxlife-self.life)/self.maxlife)/0.88), 0)
            pass
        else:
            pygame.draw.circle(bsurf, self.palette[self.i-1] + (self.alpha,), (self.x+random.randint(-1, 1)-offset[0], self.y-3-offset[1]), self.r/1.5, 0)
        """
        """
        pygame.draw.circle(bsurf, self.palette[self.i] + (self.alpha,), (self.ren_x - offset[0], self.ren_y - offset[1]), self.r, 0)
            
        if self.i == 0:
            life_ratio = (self.maxlife - self.life) / self.maxlife
            pygame.draw.circle(bsurf, (0, 0, 0, 0), (self.ren_x + random.randint(-1, 1) - offset[0], self.ren_y - 4 - offset[1]), self.r * (life_ratio / 0.88), 0)
        else:
            pygame.draw.circle(bsurf, self.palette[self.i - 1] + (self.alpha,), (self.ren_x + random.randint(-1, 1) - offset[0], self.ren_y - 3 - offset[1]), self.r / 1.5, 0)
       
        """ 
        

    

class AnimatedParticle: 
    def __init__(self,particle_data:AnimationParticleData,animation:Animation) -> None:
        self.type= particle_data.type 
        self.pos = particle_data.pos 
        self.velocity = particle_data.velocity
        self.rotation_angle = particle_data.angle
        self.flipped = particle_data.flipped
        self.source = particle_data.source
        self.animation = animation 
        self._active = False 



        # TODO: ACCOUNT FOR ROTATION HERE 

    def set_new_data(self,particle_data:AnimationParticleData):
        self.type= particle_data.type 
        self.pos = particle_data.pos 
        self.velocity = particle_data.velocity
        self.rotation_angle = particle_data.angle
        self.flipped = particle_data.flipped
        self.source = particle_data.source
        self.animation.set_new_data(PARTICLE_ANIMATION_DATA[self.type])

    def update(self,dt:float):
        scaled_dt = dt * 60
        kill = False 
        if self.animation.done: 
            kill = True 
        self.pos[0] += self.velocity[0] *scaled_dt 
        self.pos[1] += self.velocity[1] *scaled_dt 

        self.animation.update(dt)
        return kill 



