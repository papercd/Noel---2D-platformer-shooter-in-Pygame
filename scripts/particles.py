import pygame
import random 
import math 

class Particle: 
    def __init__(self,game, p_type, pos, source,velocity = [0,0], frame = 0):
        self.game = game 
        self.type = p_type
        self.pos = list(pos)
        self.velocity = velocity
        self.animation = self.game.assets['particle/' + p_type].copy()
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
    
    def render(self,surf, offset= (0,0)):
        img = self.animation.img()
        surf.blit(img, (self.pos[0]-offset[0]-img.get_width()//2,self.pos[1]- offset[1]-img.get_height()//2))



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
    
    def render(self,surf,offset = (0,0)):
        surf.blit(self.image,(self.pos[0]- offset[0],self.pos[1]-offset[1]))



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
    
    def render(self, surf, offset=(0, 0)):
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


    def render(self,surf,offset = (0,0)):
        pygame.draw.circle(surf,self.color,(self.pos[0]-offset[0],self.pos[1]-offset[1]),self.radius) 
    