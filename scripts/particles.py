import pygame
from my_pygame_light2d.engine import Layer_,LightingEngine
import random 
import math 

class Particle: 
    def __init__(self,game, p_type, pos, source,velocity = [0,0], frame = 0):
        self.game = game 
        self.type = p_type
        self.pos = list(pos)
        self.velocity = velocity
        self.animation = self.game.general_sprites['particle/' + p_type].copy()
        self.animation.frame = frame
        self.source = source 

  
            

    def update(self):
        kill = False 
        if self.animation.done: 
            kill = True 
        
        self.pos[0] += self.velocity[0]
        self.pos[1] += self.velocity[1]

        self.animation.update()

        return kill 
    
    def render(self,render_engine_ref:LightingEngine, offset= (0,0)):
        tex = self.animation.curr_tex()
        render_engine_ref.render_texture(
            tex,Layer_.BACKGROUND,
            dest = pygame.Rect(self.pos[0]-offset[0]-tex.width//2,self.pos[1]- offset[1]-tex.height//2,tex.width,tex.height),
            source = pygame.Rect(0,0,tex.width,tex.height)
        )
        #surf.blit(img, (self.pos[0]-offset[0]-img.get_width()//2,self.pos[1]- offset[1]-img.get_height()//2))

class glass():
    def __init__(self,pos,size,speed,angle,idle_time):
        self.random_seed = random.random()
        self.size = size * self.random_seed 
        self.buffer_surf = pygame.Surface((self.size[0] * 2, self.size[1] * 2),pygame.SRCALPHA)
        self.pos =self.center = pos
        self.angle =angle 
        self.speed =speed * self.random_seed 
        self.num_vertices = random.randint(4,7)
        self._create_vertice_data()
        self.velocity = self.calculate_initial_velocity() 
        self.dead = False 
        self.frames_flown = 0
        self.idle_time = idle_time
        self.rot_angle = 0

    def _create_vertice_data(self):
        self.vertice_data = []
        for i in range(self.num_vertices): 
            angle = 2 * (i+1)* math.pi / self.num_vertices
            randomized_dist_from_pos = self.size * random.random()
            self.vertice_data.append((randomized_dist_from_pos,angle))


    def velocity_adjust(self):
        friction = random.uniform(0.44,0.46)
        self.velocity[0] *= friction  
            
    def calculate_initial_velocity(self):
        return [math.cos(self.angle) * self.speed , math.sin(self.angle) * self.speed ]


    def update(self,tilemap,dt):
        if math.sqrt(self.velocity[0] ** 2 + self.velocity[0] **2) >  dt:
            self.rot_angle = math.atan2(self.velocity[1],self.velocity[0])
        else: 
            self.idle_time -= 1
        if self.idle_time <= 0 :
            self.dead = True 
            return True 
        self.frames_flown += 1
        if self.frames_flown > 600: 
            self.dead = True 
            return True 
        
        self.pos[0] += self.velocity[0] 
        tile_loc = (int(self.pos[0])//tilemap.tile_size,int(self.pos[1])//tilemap.tile_size)
        key = f"{tile_loc[0]};{tile_loc[1]}" 
        if  key in tilemap.tilemap:
            
            tile = tilemap.tilemap[key]
            if tile.type == 'lights':
                pass
            elif tile.type.split('_')[1] == 'stairs' and tile.variant.split(';')[0] in ['0', '1']:
                check_rects = [pygame.Rect(tile_loc[0], tile_loc[1] + tilemap.tile_size - 4, tilemap.tile_size, 4),
                                pygame.Rect(tile_loc[0] + 12, tile_loc[1], 4, 12),
                                pygame.Rect(tile_loc[0] + 6, tile_loc[1] + 6, 6, 6)] if tile.variant.split(';')[0] == '0' else \
                                [pygame.Rect(tile_loc[0], tile_loc[1] + tilemap.tile_size - 4, tilemap.tile_size, 4),
                                pygame.Rect(tile_loc[0], tile_loc[1], 4, 12),
                                pygame.Rect(tile_loc[0] + 4, tile_loc[1] + 6, 6, 6)]
                for check_rect in check_rects:
                    if check_rect.collidepoint(self.pos): 
                        if self.velocity[0] <0 :
                            self.pos[0] =  check_rect.right
                        else:
                            self.pos[0] =  check_rect.left
                        self.velocity[0] = - self.velocity[0] * 0.25 

                        #self.dead = True 
                        #return True
            else: 
                if self.velocity[0] <0 :
                    self.pos[0] =  tile_loc[0] * tilemap.tile_size + tilemap.tile_size
                else:
                    self.pos[0] =  tile_loc[0] * tilemap.tile_size - 1
                self.velocity[0] = - self.velocity[0] *0.25
                #self.dead = True 
                #return True
        
        self.velocity[1] = min(12,self.velocity[1] +0.44)
        self.pos[1] += self.velocity[1] 
        tile_loc = (int(self.pos[0])//tilemap.tile_size,int(self.pos[1])//tilemap.tile_size)
        key = f"{tile_loc[0]};{tile_loc[1]}" 
        
        if  key in tilemap.tilemap:
            tile = tilemap.tilemap[key]
            if tile.type == 'lights':
                pass
            elif tile.type.split('_')[1] == 'stairs' and tile.variant.split(';')[0] in ['0', '1']:
                check_rects = [pygame.Rect(tile_loc[0], tile_loc[1] + tilemap.tile_size - 4, tilemap.tile_size, 4),
                                pygame.Rect(tile_loc[0] + 12, tile_loc[1], 4, 12),
                                pygame.Rect(tile_loc[0] + 6, tile_loc[1] + 6, 6, 6)] if tile.variant.split(';')[0] == '0' else \
                                [pygame.Rect(tile_loc[0], tile_loc[1] + tilemap.tile_size - 4, tilemap.tile_size, 4),
                                pygame.Rect(tile_loc[0], tile_loc[1], 4, 12),
                                pygame.Rect(tile_loc[0] + 4, tile_loc[1] + 6, 6, 6)]
                for check_rect in check_rects:
                    if check_rect.collidepoint(self.pos): 
                        if self.velocity[1] <0 :
                            self.pos[1] =  check_rect.bottom
                        else:
                            self.pos[1] =  check_rect.top
                        self.velocity_adjust()
                        self.velocity[1] = -self.velocity[1] * 0.25
                    
            else:
                if self.velocity[1] <0 :
                    self.pos[1] =  tile_loc[1]* tilemap.tile_size + tilemap.tile_size
                else:
                    self.pos[1] =  tile_loc[1]* tilemap.tile_size - 1
                self.velocity[1] = - self.velocity[1] * 0.25
                self.velocity_adjust()
       







    def render(self, render_engine_ref:LightingEngine, offset=(0, 0)):
        points = []
        self.buffer_surf.fill((0,0,0,0))
        center = (self.size,self.size)
        for distance, angle in self.vertice_data:
            self.vertice_data[i] = (int(center[0] + distance * math.cos(angle+self.rot_angle)),int(center[1] + distance * math.sin(angle+self.rot_angle)))
            points.append(
                (int(center[0] + distance * math.cos(angle+self.rot_angle)),int(center[1] + distance * math.sin(angle+self.rot_angle)))
            ) 
               
        pygame.draw.polygon(self.buffer_surf,(255,255,255),points)

        tex = render_engine_ref.surface_to_texture(self.buffer_surf)
        render_engine_ref.render_texture(
            tex, Layer_.BACKGROUND,
            dest = pygame.Rect(self.pos[0] - self.size- offset[0], self.pos[1]- self.size - offset[1], tex.width,tex.height),
            source=  pygame.Rect(0,0,tex.width,tex.height),
        )
                                


            
class non_animated_particle():
    def __init__(self,pos,color,velocity,tilemap,life = 60):
        self.time = 0
        self.pos = pos
        self.color = color
        self.tilemap = tilemap
        self.velocity = velocity
        self.life = life 
        self.create_surf()
    
    #the default non-animated particle is a circle. 
    def create_surf(self):
        self.image = pygame.Surface((1,1)).convert_alpha()
        self.image.set_colorkey("black")
        pygame.draw.rect(self.image,self.color, pygame.Rect(0,0,1,1))
        self.rect  = self.image.get_rect()
    
   
    def update(self,dt):
        self.time +=1
        for rect_tile in self.tilemap.physics_rects_around(self.pos,(1,1)):
            if self.rect.colliderect(rect_tile[0]):
                if rect_tile[1].type == 'stairs' and  rect_tile[1].variant.split(';')[0] in ['0','1']:
                    if rect_tile[1].variant.split(';')[0] == '0':
                        #left stairs
                        #this part where check rects are created is not dynamic, so if tilesize changes this part needs to be changed manually. maybe figure out a mathematical 
                        #way to create rects. 
                        check_rects = [pygame.Rect(rect_tile[0].left,rect_tile[0].bottom + 4,rect_tile[0].width,4),
                                       pygame.Rect(rect_tile[0].left + 12,rect_tile[0].top,4,12),
                                       pygame.Rect(rect_tile[0].left + 6,rect_tile[0].top + 6,6,6)
                                       ]
                        for check_rect in check_rects:
                            if self.rect.colliderect(check_rect):
                                return True
                    else: 
                        check_rects = [pygame.Rect(rect_tile[0].left,rect_tile[0].bottom + 4,rect_tile[0].width,4),
                                       pygame.Rect(rect_tile[0].left,rect_tile[0].top,4,12),
                                       pygame.Rect(rect_tile[0].left + 4,rect_tile[0].top + 6,6,6)
                                       ]
                        for check_rect in check_rects:
                            if self.rect.colliderect(check_rect):
                                return True 
                else: 

                    return True 
        if self.time > self.life:
            return True 
       
        self.pos[0] += self.velocity[0] * dt 
        self.pos[1] += self.velocity[1] * dt 
        self.rect.topleft = self.pos 
        return False 
    
    def render(self, render_engine_ref,offset = (0,0)):
        tex = render_engine_ref.surface_to_texture(self.buffer_surf)
        render_engine_ref.render_texture(
            tex, Layer_.BACKGROUND,
            dest = pygame.Rect(self.pos[0] - self.size- offset[0], self.pos[1]- self.size - offset[1], tex.width,tex.height),
            source=  pygame.Rect(0,0,tex.width,tex.height),
        )
                                


        #surf.blit(self.image,(self.pos[0]- offset[0],self.pos[1]-offset[1]))



class bullet_collide_particle:
    def __init__(self,size, pos, angle, speed,color,tilemap,life = 60,gravity_factor = 1):
        self.pos = list(pos)
        self.angle = angle
        self.speed = speed
        self.color = color 
        self.tilemap = tilemap
        self.time = 0
        self.velocity = [0,0]
        self.life = life
        self.size = size 
        
        self.gravity_factor= gravity_factor
        self.create_surf()
    
    def create_surf(self):
        self.image = pygame.Surface(self.size).convert_alpha()
        self.image.set_colorkey("black")
        pygame.draw.rect(self.image,self.color, pygame.Rect(0,0,self.size[0],self.size[1]))
        self.rect  = self.image.get_rect()
    

    def update(self,dt):
        self.time +=1
        self.velocity[1] = min(5,self.velocity[1] +0.20 / self.gravity_factor)

        for rect_tile in self.tilemap.physics_rects_around(self.pos,(1,1)):
            if self.rect.colliderect(rect_tile[0]):
                if rect_tile[1].type == 'stairs' and  rect_tile[1].variant.split(';')[0] in ['0','1']:
                    if rect_tile[1].variant.split(';')[0] == '0':
                        #left stairs
                        #this part where check rects are created is not dynamic, so if tilesize changes this part needs to be changed manually. maybe figure out a mathematical 
                        #way to create rects. 
                        check_rects = [pygame.Rect(rect_tile[0].left,rect_tile[0].bottom + 4,rect_tile[0].width,4),
                                       pygame.Rect(rect_tile[0].left + 12,rect_tile[0].top,4,12),
                                       pygame.Rect(rect_tile[0].left + 6,rect_tile[0].top + 6,6,6)
                                       ]
                        for check_rect in check_rects:
                            if self.rect.colliderect(check_rect):
                                return True
                    else: 
                        check_rects = [pygame.Rect(rect_tile[0].left,rect_tile[0].bottom + 4,rect_tile[0].width,4),
                                       pygame.Rect(rect_tile[0].left,rect_tile[0].top,4,12),
                                       pygame.Rect(rect_tile[0].left + 4,rect_tile[0].top + 6,6,6)
                                       ]
                        for check_rect in check_rects:
                            if self.rect.colliderect(check_rect):
                                return True 
                else: 
                    return True 
        if self.time > self.life:
            return True 
        self.pos[0] += math.cos(math.radians(self.angle)) * self.speed
        self.pos[1] += math.sin(math.radians(self.angle)) * self.speed

        self.pos[1] += self.velocity[1]

        self.rect.topleft = self.pos 
        
        self.speed = max(0, self.speed - 0.1)
        return False 
    
    def render(self,render_engine_ref , offset=(0, 0)):
        return 
        surf.blit(self.image,(self.pos[0]- offset[0],self.pos[1]-offset[1]))

class bullet_trail_particle_wheelbot:
    def __init__(self,radius,decay_rate,pos,color):
        self.radius  = radius
        self.decay_rate = decay_rate
        self.pos = pos #center position 
        self.color = color
        #and there won't be a velocity. 

        
    def update(self,dt):
        self.radius -=  self.decay_rate 
        return self.radius <= 0  


    def render(self,render_engine_ref,offset = (0,0)):
        return 
        pygame.draw.circle(surf,self.color,(self.pos[0]-offset[0],self.pos[1]-offset[1]),self.radius) 
    