from random import choice ,randint
from scripts.new_tilemap import Tilemap
from pygame.math import Vector2 as vec2 
from pygame import Rect
from math import cos,sin,radians,sqrt,degrees,atan2
from scripts.custom_data_types import CollideParticleData,FireParticleData,AnimationParticleData,Animation

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

        # create particle pools
        self._initialize_particle_containers()

     
    def _initialize_particle_containers(self):
        for i in range(self._max_collide_particle_count):
            particle_data = CollideParticleData((1,1),[float('-inf'),float('inf')],0,0,(255,255,255,255),60,1)
            self._collide_particles.append(PhysicalParticle(particle_data))

        for i in range(self._max_fire_particle_count):
            particle_data = FireParticleData(0,0,0,0,0,0,0,0,0)
            self._fire_particles.append(FireParticle(particle_data))

        for i in range(self._max_animation_particle_count):
            particle_data = AnimationParticleData("None",[0,0],[0,0],None)
            self._animation_particles.append(AnimatedParticle(None,particle_data))



    def add_particle(self,particle_data,animation:Animation =None):
        if isinstance(particle_data,CollideParticleData):
            self._collide_particles[self._collide_particle_pool_index]._active = True 
            self._collide_particles[self._collide_particle_pool_index].set_new_data(particle_data)
            self._collide_particle_pool_index = (self._collide_particle_pool_index -1) % self._max_collide_particle_count 
        elif isinstance(particle_data,FireParticleData):
            self._fire_particles[self._fire_particle_pool_index]._active = True 
            self._fire_particles[self._fire_particle_pool_index].set_new_data(particle_data)
            self._fire_particle_pool_index = (self._fire_particle_pool_index -1) % self._max_fire_particle_count 
        elif isinstance(particle_data,AnimationParticleData):
            self._animation_particles[self._animation_particle_pool_index]._active = True 
            self._animation_particles[self._animation_particle_pool_index].set_new_data(particle_data,animation)
            self._animation_particle_pool_index = (self._animation_particle_pool_index -1) % self._max_animation_particle_count 


    def update(self,tilemap:Tilemap,grass_manager):
        for particle in self._collide_particles:
            if not particle._active:
                continue 
            kill =particle.update(tilemap)
            if kill: 
                particle._active = False 

        for particle in self._fire_particles:
            if not particle._active:
                continue 
            kill = particle.update(tilemap,grass_manager)
            if kill: 
                particle._active = False 
        
        for particle in self._animation_particles:
            if not particle._active:
                continue 
            kill = particle.update()
            if kill: 
                particle._active = False 

class PhysicalParticle: 
    def __init__(self,particle_data:CollideParticleData):
        self._size = particle_data.size 
        self._pos = particle_data.pos
        self._angle  =particle_data.angle 
        self._speed = particle_data.speed
        self._life = particle_data.life 
        self._color = particle_data.color
        self._gravity_factor = particle_data.gravity_factor
        self._active = False 

    def set_new_data(self,particle_data:CollideParticleData):
        self._size = particle_data.size 
        self._pos = particle_data.pos
        self._angle  =particle_data.angle 
        self._speed = particle_data.speed
        self._life = particle_data.life 
        self._color = particle_data.color
        self._gravity_factor = particle_data.gravity_factor

    def update(self,tilemap:Tilemap):
        # testing 
        return False 
    
class FireParticle:
    def __init__(self,particle_data:FireParticleData):
       
       #save opening pos for later collision detection 
        self.origin = (particle_data.x,particle_data.y) 
       
        # -------------   predetermined particle parameters 
        self.size = particle_data.size
        self.density = particle_data.density
        self.rise = particle_data.rise * 1.3
        self.spread = particle_data.spread
        self.wind = particle_data.wind
        self.rise_angle = particle_data.rise_angle
        self.damage = particle_data.damage
        self.max_damage =particle_data.damage
        #---------------
        
        self.rise_vec = vec2(cos(radians(self.rise_angle)), sin(radians(self.rise_angle)))
        self.rise_normal = self.rise_vec.rotate(90).normalize()

        self.x, self.y = particle_data.x, particle_data.y
        self.pos = [self.x,self.y]

        self.maxlife = randint( int(self.size*5),   int(self.size*10))
        self.life = self.maxlife
        self.dir = choice((-2, -1, 1, 2))
        self.sin = randint(-10, 10)/7
        self.sinr = randint(5, 10)
        self.r = randint(1,2)

        self.center = [self.x + self.r,self.y+self.r]

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

        self._active = False 

    def set_new_data(self,particle_data:FireParticleData):
        self.origin = (particle_data.x,particle_data.y) 
       
        # -------------   predetermined particle parameters 
        self.size = particle_data.size
        self.density = particle_data.density
        self.rise = particle_data.rise * 1.3
        self.spread = particle_data.spread
        self.wind = particle_data.wind
        self.rise_angle = particle_data.rise_angle
        self.damage = particle_data.damage
        self.max_damage =particle_data.damage
        #---------------
        
        self.rise_vec = vec2(cos(radians(self.rise_angle)), sin(radians(self.rise_angle)))
        self.rise_normal = self.rise_vec.rotate(90).normalize()

        self.x, self.y = particle_data.x, particle_data.y
        self.pos = [self.x,self.y]

        self.maxlife = randint( int(self.size*5),   int(self.size*10))
        self.life = self.maxlife
        self.dir = choice((-2, -1, 1, 2))
        self.sin = randint(-10, 10)/7
        self.sinr = randint(5, 10)
        self.r = randint(1,2)

        self.center = [self.x + self.r,self.y+self.r]

        self.ox = randint(-1, 1)
        self.oy = randint(-1, 1)
        self.alpha = 255
        self.i = 0


    def rect(self):
        return Rect(self.x-self.r,self.y-self.r,self.r * 2,self.r * 2)
    
    def point_circle_collision(self,point_x, point_y):
        """
        Check if a point is within the circle.
        """
        distance = sqrt((point_x - self.x)**2 + (point_y - self.y)**2)
        return distance <= self.r


    def collide_with_rect(self,other):
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

    def update(self,tilemap:Tilemap,grass_manager):
        # testing 
        return False 


    def update_pos(self,tilemap,j):
        #print(self.rise_normal.angle_to(pygame.math.Vector2(1,0)))
        self.damage = max(2,int(self.damage * (self.life/self.maxlife)))

        self.life -=1
        
      
        if self.life == 0:
            self.dead = True 
            del self 
            return True 
        
       
        self.i = int((self.life/self.maxlife)*6)
       
        #collision detection with tiles - make these ballistic particles. 
        #surround the particle with a rectangle with side length of twice its radius and check for rects 
        ##change the direction of the particle.



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
                #print(rect_tile[1].type)
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
                            self.rise_angle = incid_angle
                        elif side_point == 'Left' or side_point == 'Right':
                            self.rise *= 0.7
                            self.rise_angle = -180 + incid_angle
                        elif side_point == 'Center':
                            self.rise *= 0.3
                        else:
                            self.rise *= 0.7
                            self.rise_angle += 180  
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

                        

                     
                         

        """
        entity_rect = self.rect()
        for rect_tile in tilemap.physics_rects_around((self.pos[0] - self.r,self.pos[1] - self.r),(self.r * 2,self.r * 2)):
            if self.collide_with_rect(rect_tile[0]):
                if not rect_tile[1].type == 'stairs':
                    incid_angle = math.degrees(math.atan2(self.pos[1] - self.origin[1],self.pos[0] - self.origin[0]))
                    print(incid_angle,self.rise_angle)
                    self.rise_angle = -180 + incid_angle 
                    if frame_movement[0] > 0:
                        
                        self.x = rect_tile[0].left - self.r 
                 
                        pass
                    if frame_movement[0] < 0:
                        self.x = rect_tile[0].right + self.r 
                        #entity_rect.left = rect_tile[0].right 
                       
                        pass 
                    #self.x = entity_rect.x + self.r
        

        
        
        entity_rect = self.rect()
        for rect_tile in tilemap.physics_rects_around((self.pos[0] - self.r,self.pos[1] - self.r),(self.r * 2,self.r * 2)):
            if self.collide_with_rect(rect_tile[0]):
                if not rect_tile[1].type == 'stairs':
                    incid_angle = math.degrees(math.atan2(self.pos[1] - self.origin[1],self.pos[0] - self.origin[0]))
                    self.rise_angle = incid_angle
                    if frame_movement[1] > 0:
                        
                        self.y = rect_tile[0].top - self.r
                        #self.collisions['right'] = True
                        
              
                        #you need to push away the tile.
                        pass
                    if frame_movement[1] < 0:
                        self.y = rect_tile[0].bottom + self.r
                        #self.collisions['left'] = True
                     
                        pass 
                    #self.y = entity_rect.y + self.r
                else: 
                    pass 
                
        """
                

        

        """
        entity_rect = self.rect()
        for rect_tile in tilemap.physics_rects_around((self.pos[0] - self.r,self.pos[1] - self.r),(self.r * 2,self.r * 2)):
            if self.collide_with_rect(rect_tile[0]):
                if not rect_tile[1].type == 'stairs':
                    
                    if frame_movement[1] > 0: 
                        
                        entity_rect.bottom = rect_tile[0].top  
                        #self.collisions['right'] = True
                        pass 
                    if frame_movement[1] < 0: 
                        
                        entity_rect.top = rect_tile[0].bottom
                        #self.collisions['left'] = True
                        pass 
                    #self.y = entity_rect.y 
        """

        
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
    def __init__(self,animation:Animation,particle_data:AnimationParticleData) -> None:
        self.type= particle_data.type 
        self.pos = particle_data.pos 
        self.animation = animation
        self.velocity = particle_data.velocity
        self.source = particle_data.source
        self._active = False 

    def set_new_data(self,particle_data:AnimationParticleData,animation:Animation):
        self.type= particle_data.type 
        self.pos = particle_data.pos 
        self.animation = animation
        self.velocity = particle_data.velocity
        self.source = particle_data.source

    
    def update(self):
        # testing
        return False 


