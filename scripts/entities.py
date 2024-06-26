#alright, so this is where I am going to implement physics for the objects 
#of my game. 
import random
import pygame 
import math
from scripts.particles import Particle,non_animated_particle,bullet_collide_particle,bullet_trail_particle_wheelbot
from scripts.health import HealthBar,StaminaBar
from scripts.indicator import indicator 
from scripts.tilemap import Node,Tile
from scripts.weapons import Wheelbot_weapon
from scripts.spark import Spark 
from scripts.Pygame_Lights import LIGHT,pixel_shader,global_light
from scripts.weapon_list import DoublyLinkedList


#a body class to implement a more accurate body with better physics that require rotation, 
#utilizing the pymunk module. 

class Accurate_Rect_Body():
    def __init__(self) -> None:
        pass

    def update(self):
        pass 

    def render(self,surf,offset= [0,0]):
        pass 

class PhysicsEntity:
   
    def __init__(self,game,e_type,pos,size):
        self.game = game 
        self.type = e_type 
        self.pos = list(pos)  #this list() ensures that the position variable that you pass to the constructor 
                              #becomes a list. This gives us flexibility with passing argumments here for example 
                              #when we pass a tuple, this allows us to actually manage the position variable, as tuples can't be modified after initialization.
        self.collisions = {'up' :False,'down' : False, 'left': False, 'right': False }
        self.size = size
        self.velocity = [0,0]
        self.state = ''
        self.anim_offset = (-0,-0)
        self.flip = False
        self.set_state('idle')
        self.cut_movement_input = False 
        self.on_ramp = 0
         
        


    def set_state(self,action):
        if action != self.state: 
            self.state = action 
            self.animation = self.game.assets[self.type + '/' + self.state].copy() 

    def collide(self, other):
    # Check for collision between two entities. 
        """
        return (self.pos[0] < other.pos[0] + other.size[0] and
                self.pos[0] + self.size[0] > other.pos[0] and
                self.pos[1] < other.pos[1] + other.size[1] and
                self.pos[1] + self.size[1] > other.pos[1])
        """
        return self.collision_rect().colliderect(other.collision_rect())

    def collision_rect(self):
        return pygame.Rect(self.pos[0],self.pos[1],self.size[0],self.size[1])

    def rect(self):
        
        return pygame.Rect(self.pos[0],self.pos[1],self.size[0],self.size[1])
    
    def update_pos(self, tile_map, movement = (0,0)):
        
        if movement[0] > 0:
            self.flip = False
        if movement[0] < 0 :
            self.flip = True 

        self.animation.update()
        
        self.collisions = {'up' :False,'down' : False, 'left': False, 'right': False }
        
        self.velocity[1] = min(5,self.velocity[1] +0.24)

        #this is decel 
        if self.velocity[0] < 0:
            self.velocity[0] = min(self.velocity[0]+0.21, 0)  
        if self.velocity[0] > 0:
            self.velocity[0] = max(self.velocity[0] -0.21,0)

         

        if self.cut_movement_input:
            frame_movement = (self.velocity[0],self.velocity[1])
        else: 
            frame_movement =  (movement[0] + self.velocity[0], movement[1] + self.velocity[1])

    
        self.pos[0] += frame_movement[0]
        entity_rect = self.rect() 
        for rect_tile in tile_map.physics_rects_around(self.pos,self.size):
            if entity_rect.colliderect(rect_tile[0]):
                if not rect_tile[1].type == 'stairs':
                
                    if frame_movement[0] > 0: 
                        self.collisions['right'] = True
                        entity_rect.right = rect_tile[0].left 
                    if frame_movement[0] < 0: 
                        self.collisions['left'] = True
                        entity_rect.left = rect_tile[0].right 
                    self.pos[0] = entity_rect.x 
                

       

        self.pos[1] += frame_movement[1]
        entity_rect = self.rect() 
        for rect_tile in tile_map.physics_rects_around(self.pos,self.size):
            if entity_rect.colliderect(rect_tile[0]):
                
                if not rect_tile[1].type == 'stairs':
                    
                    if frame_movement[1] > 0: 
                        self.collisions['down'] = True
                        self.on_ramp =0 
                        entity_rect.bottom = rect_tile[0].top  
                    if frame_movement[1] < 0:  
                        self.collisions['up'] = True
                        entity_rect.top = rect_tile[0].bottom
                    self.velocity[1] = 0 
                    self.pos[1] = entity_rect.y 
                else: 
                    pos_height = 0 

                    if rect_tile[1].variant.split(';')[0] == '0' :
                        #if you are on the left ramp 
                        #then you compare the right edge. 
                        #and cap this at -16. 
                        
                        rel_x = rect_tile[0].x - entity_rect.right
                        if rel_x >= -16 and rel_x < 0: 
                            pos_height =  max(0,-rel_x -self.size[0]//4) 
                        
                    elif rect_tile[1].variant.split(';')[0] == '2': 
                        
                        rel_x = rect_tile[0].x - entity_rect.right
                        if rel_x < 0: 
                            pos_height = min(tile_map.tile_size,-rel_x  +(tile_map.tile_size-self.size[0]//4))
                        
                    elif rect_tile[1].variant.split(';')[0] == '1':
                        rel_x = rect_tile[0].right - entity_rect.left
                        if rel_x > 0 :
                            pos_height = max(0,rel_x - self.size[0] //4)
                    elif rect_tile[1].variant.split(';')[0] == '3':
                        rel_x = rect_tile[0].right - entity_rect.left
                        if rel_x > 0 and rel_x <= tile_map.tile_size:
                            pos_height = min(tile_map.tile_size,rel_x + (tile_map.tile_size - self.size[0]//4))
                    
                    target_y = rect_tile[0].y + tile_map.tile_size - pos_height
                    if entity_rect.bottom > target_y: 
                    
                        self.on_ramp = 1 if rect_tile[1].variant.split(';')[0] == '0' else -1
                        entity_rect.bottom = target_y
                        self.pos[1] = entity_rect.y
                            
                        self.collisions['down'] = True
                    """
                    rel_x = entity_rect.x + (self.size[0]-tile_map.tile_size) - rect_tile[0].x

                    

                    pos_height= 0

                    if rect_tile[1].variant.split(';')[0] == '0' :
                        #left stairs 

                        pos_height = min(0,rel_x - 4) + rect_tile[0].width 
                    elif rect_tile[1].variant.split(';')[0] == '1':
                        #right stairs 
                        
                        pos_height = min(0,12 - rel_x)

                    elif rect_tile[1].variant.split(';')[0] == '2':
                        pos_height = rel_x + 12 
                    elif rect_tile[1].variant.split(';')[0] == '3':
                        
                        pos_height = max(tile_map.tile_size,28 - rel_x) 
                    
                   

                    pos_height = min(pos_height,tile_map.tile_size)
                    pos_height = max(pos_height,0)

                    target_y = rect_tile[0].y + tile_map.tile_size - pos_height

                    if entity_rect.bottom > target_y: 
                    
                        self.on_ramp = 1 if rect_tile[1].variant.split(';')[0] == '0' else -1
                        entity_rect.bottom = target_y
                        self.pos[1] = entity_rect.y
                         
                        self.collisions['down'] = True
                    """
                

                    
                        

                    
                    
       

        

       



    def render(self,surf,offset):
        surf.blit(pygame.transform.flip(self.animation.img(),self.flip, False),(self.pos[0]-offset[0]+self.anim_offset[0] ,self.pos[1]-offset[1]+self.anim_offset[1]))
        


class Enemy(PhysicsEntity):

    def __init__(self,game,pos,size,variant,hp):
        super().__init__(game,variant,pos,size)
        self.walking = 0
        self.air_time =0
        self.aggro = False 
        self.aggro_timer = 0 
        self.hit_mask = None
        self.first_hit = False
        self.alertted = False 
        self.hp = hp 
        self.hit_mask = None 

    def set_state(self,action):
        if action != self.state: 
            self.state = action 
            self.animation = self.game.enemies[self.type + '/' + self.state].copy() 


    def render(self,surf,offset= (0,0),shake = 0):
        #if the position of the thing is within the screen, render it 
        x_min = offset[0] - self.size[0]
        x_max = offset[0] + surf.get_width() + self.size[0]

        y_min = offset[1] -self.size[1]
        y_max = offset[1] +surf.get_height() + self.size[1]

        if (self.pos[0] > x_min and self.pos[0] < x_max) and (self.pos[1] > y_min and self.pos[1] < y_max):
            self.outline = pygame.mask.from_surface(self.animation.img() if not self.flip else pygame.transform.flip(self.animation.img(),True,False))
            for offset_ in [(-1,0),(1,0),(0,-1),(0,1)]:
                surf.blit(self.outline.to_surface(unsetcolor=(255,255,255,0),setcolor=(0,0,0,255)),(self.pos[0] - offset[0]+offset_[0],self.pos[1]-offset[1]+offset_[1]))
            super().render(surf,offset=offset)
            
            if self.hit_mask:
                for offset_ in [(-1,0),(1,0),(0,-1),(0,1)]:
                    surf.blit(self.hit_mask.to_surface(unsetcolor=(0,0,0,0),setcolor=(255,255,255,255)),(self.pos[0] - offset[0]+offset_[0],self.pos[1]-offset[1]+offset_[1]))
                self.hit_mask = None

    def hit(self,hit_damage):
        if self.hp > 0 :
            self.hp -= hit_damage
            self.first_hit = True 
            self.hurt = True 
            self.hit_mask = pygame.mask.from_surface(self.animation.img() if not self.flip else pygame.transform.flip(self.animation.img(),True,False))

class Sabre(Enemy):
    def __init__(self,game,pos,size):
        super().__init__(game,pos,size,'sabre',230)
        self.wake = False 
        self.hurt = False 
        self.attack_choice = False 
        self.hit_mask = None 
        self.health_bar = HealthBar(self.pos[0] + 3, self.pos[1] -5, 16,2,self.hp)

    
    def update(self,tilemap,player_pos,dt,movement = (0,0)):
        if  math.dist(self.pos,player_pos) > 20*tilemap.tile_size:
            #self.alertted = False 
            self.aggro_timer = 0 
            self.aggro = False 
            self.first_hit = False 

        if self.hp >0 and self.wake:
            if self.walking : 
                if self.aggro: 
                    self.aggro_timer += self.aggro
                    #then you are going to charge up an attack, and shoot. 
                    #the attack is going to be a lazer. that expands then shrinks. 
                    #I need to change the charging animation so that the gun that the bots hold will change angle depending on where you are. 
                    #it is the same mechanism as the player's gun rotation 
                    
                   
                   
                   
                     
                else: 

                    
                    #this needs to be fixed. 


                    if tilemap.solid_check((self.pos[0]+ (-8 if self.flip else 8+self.size[0]),self.pos[1]+8)):
                        if tilemap.solid_check((self.pos[0] + (-8 if self.flip else 8+self.size[0]),self.pos[1]+8-tilemap.tile_size)):
                            if tilemap.solid_check((self.pos[0]+ (-8 if self.flip else 8+self.size[0] ),self.pos[1]+8-tilemap.tile_size*2)):
                                self.flip = not self.flip 
                            else: 
                                self.velocity[1] = -5
                                movement = (movement[0] - 1.5 if self.flip else movement[0] + 1.5, movement[1])
                        else: 
                            
                            self.velocity[1] = -3.3
                            movement = (movement[0] - 1.5 if self.flip else movement[0] + 1.5, movement[1])
                    else:
                        if tilemap.solid_check((self.pos[0]+ (-8 if self.flip else 8+self.size[0]),self.pos[1]+8-tilemap.tile_size)):
                            if not tilemap.solid_check((self.pos[0]+ (-8 if self.flip else 8+self.size[0]),self.pos[1]+8-tilemap.tile_size*2)):
                                
                                self.velocity[1] = -5
                                movement = (movement[0] - 1.5 if self.flip else 1.5, movement[1])
                            else: 
                                self.flip = not self.flip 
                                movement = (movement[0] - 1.5 if self.flip else 1.5, movement[1])
                        else: 
                            if not tilemap.solid_check((self.pos[0]+ (-8 if self.flip else 8+self.size[0]),self.pos[1]+8+tilemap.tile_size)):
                                if not tilemap.solid_check((self.pos[0]+ (-8 if self.flip else 8+self.size[0]),self.pos[1]+8+tilemap.tile_size*2)):
                                    if not tilemap.solid_check((self.pos[0]+ (-8 if self.flip else 8+self.size[0]),self.pos[1]+8+tilemap.tile_size*3)):
                                        if not tilemap.solid_check((self.pos[0]+ (-8 if self.flip else 8+self.size[0]),self.pos[1]+8+tilemap.tile_size*4)):
                                            if not tilemap.solid_check((self.pos[0]+ (-8 if self.flip else 8+self.size[0]),self.pos[1]+8+tilemap.tile_size*5)):
                                                self.flip = not self.flip 
                                            else: 
                                                movement = (movement[0] - 1.5 if self.flip else 1.5, movement[1])
                                        else: 
                                            movement = (movement[0] - 1.5 if self.flip else 1.5, movement[1])
                                    else: 
                                        movement = (movement[0] - 1.5 if self.flip else 1.5, movement[1])
                                else: 
                                    movement = (movement[0] - 1.5 if self.flip else 1.5, movement[1])
                            else: 
                                movement = (movement[0] - 1.5 if self.flip else 1.5, movement[1])
                            
                    self.walking = max(0, self.walking - 1)
                
            elif random.random() < 0.01:
                #things to do when you aren't walking 
                
                self.walking = random.randint(30,120) 
                #if the wheel bot woke up, then you move around.
        else:
            #if the wheel bot is dormant, it stays in the dormant state and does not move. 
            pass 
        
        self.health_bar.x = self.pos[0] + 1
        self.health_bar.y = self.pos[1] -6
        self.health_bar.cur_resource = self.hp

        super().update_pos(tilemap,movement=movement)

        if self.hp <= 0:
            self.set_state('death')
            if self.animation.done: 
                del self 
                return True 
        else: 
            if not self.wake: 
                #if you are dormant 
                if math.dist(self.pos,player_pos) < 4*tilemap.tile_size or self.first_hit:
                    self.set_state('wake')
                    if self.animation.done == True: 
                        self.wake = True 
                else: 
                    self.set_state('dormant')
                return False 
            else: 
                if math.dist(self.pos,player_pos) < 12*tilemap.tile_size or self.first_hit:
                    self.aggro = True 
                if self.collisions['down']:
                    self.air_time = 0
                            
                    if movement[0] != 0:
                        self.set_state('move')    
                    else: 
                        self.set_state('idle') 
                        
                        
                return False 

    def render(self,surf,offset):
        super().render(surf,offset=offset)
        



class Wheel_bot(Enemy):
    def __init__(self,game,pos,size):
        super().__init__(game,pos,size,'Wheel_bot',200)
        self.weapon = self.game.weapons['laser_weapon'].copy()
        self.weapon.equip(self)
        self.wake = False 
        self.charge_time = 0
        self.shooting = False 
        self.hurt = False 
       

        self.hit_mask = None
        self.health_bar = HealthBar(self.pos[0]+3,self.pos[1]-5,16,2,self.hp,True)

        

    def collision_rect(self):
        return pygame.Rect(self.pos[0]+3,self.pos[1]+1,14,20)

    def update(self,tilemap,player_pos,dt,movement = (0,0)):
        
        #print(self.on_ramp)
        """
        if self.aggro_timer >= 1200 and math.dist(self.pos,player_pos) > 12*tilemap.tile_size:
            self.aggro_timer = 0
            self.aggro = False 
            self.first_hit = False 
            self.alertted = False
        """

        if  math.dist(self.pos,player_pos) > 20*tilemap.tile_size:
            #self.alertted = False 
            self.aggro_timer = 0 
            self.aggro = False 
            self.charge_time = 0
            self.first_hit = False 
            self.shooting = False  
            


        
        if self.hp >0 and self.wake:
            if self.walking : 
                if self.aggro: 
                    self.aggro_timer += self.aggro
                    #then you are going to charge up an attack, and shoot. 
                    #the attack is going to be a lazer. that expands then shrinks. 
                    #I need to change the charging animation so that the gun that the bots hold will change angle depending on where you are. 
                    #it is the same mechanism as the player's gun rotation 
                    
                   
                   
                   
                     
                else: 
                    if self.on_ramp != 0 :
                        #if the wheelbot in on a ramp, just move. 
                        movement = (movement[0] - 1.5 if self.flip else movement[0] + 1.5, movement[1])
                       
                    else: 

                        if tilemap.solid_check((self.pos[0]+ (-8 if self.flip else 8+self.size[0]),self.pos[1]+8)):
                            if tilemap.solid_check((self.pos[0] + (-8 if self.flip else 8+self.size[0]),self.pos[1]+8-tilemap.tile_size)):
                                if tilemap.solid_check((self.pos[0]+ (-8 if self.flip else 8+self.size[0] ),self.pos[1]+8-tilemap.tile_size*2)):
                                    self.flip = not self.flip 
                                else: 
                                    print("first")
                                    self.velocity[1] = -5
                                    movement = (movement[0] - 1.5 if self.flip else movement[0] + 1.5, movement[1])
                            else: 
                                
                                tile = tilemap.return_tile(None,(self.pos[0]+ (-8 if self.flip else 8+self.size[0]),self.pos[1]+8))
                                if tile == None or (tile != None and tile.type == 'stairs'):
                                    movement = (movement[0] - 1.5 if self.flip else movement[0] + 1.5, movement[1])
                                else: 
                                    self.velocity[1] = -3.3
                                    movement = (movement[0] - 1.5 if self.flip else movement[0] + 1.5, movement[1])
                                
                                
                        else:
                            if tilemap.solid_check((self.pos[0]+ (-8 if self.flip else 8+self.size[0]),self.pos[1]+8-tilemap.tile_size)):
                                if not tilemap.solid_check((self.pos[0]+ (-8 if self.flip else 8+self.size[0]),self.pos[1]+8-tilemap.tile_size*2)):
                                    print("third")
                                    self.velocity[1] = -5
                                    movement = (movement[0] - 1.5 if self.flip else 1.5, movement[1])
                                else: 
                                    self.flip = not self.flip 
                                    movement = (movement[0] - 1.5 if self.flip else 1.5, movement[1])
                            else: 
                                #fix this to optimize 
                                
                                if not tilemap.solid_check((self.pos[0]+ (-8 if self.flip else 8+self.size[0]),self.pos[1]+8+tilemap.tile_size)):
                                    if not tilemap.solid_check((self.pos[0]+ (-8 if self.flip else 8+self.size[0]),self.pos[1]+8+tilemap.tile_size*2)):
                                        if not tilemap.solid_check((self.pos[0]+ (-8 if self.flip else 8+self.size[0]),self.pos[1]+8+tilemap.tile_size*3)):
                                            if not tilemap.solid_check((self.pos[0]+ (-8 if self.flip else 8+self.size[0]),self.pos[1]+8+tilemap.tile_size*4)):
                                                if not tilemap.solid_check((self.pos[0]+ (-8 if self.flip else 8+self.size[0]),self.pos[1]+8+tilemap.tile_size*5)):
                                                    self.flip = not self.flip 
                                                else: 
                                                    movement = (movement[0] - 1.5 if self.flip else 1.5, movement[1])
                                            else: 
                                                movement = (movement[0] - 1.5 if self.flip else 1.5, movement[1])
                                        else: 
                                            movement = (movement[0] - 1.5 if self.flip else 1.5, movement[1])
                                    else: 
                                        movement = (movement[0] - 1.5 if self.flip else 1.5, movement[1])
                                else: 
                                    movement = (movement[0] - 1.5 if self.flip else 1.5, movement[1])
                                
                                
                    self.walking = max(0, self.walking - 1)
                
            elif random.random() < 0.01:
                #things to do when you aren't walking 
                
                self.walking = random.randint(30,120) 
                #if the wheel bot woke up, then you move around.
        else:
            #if the wheel bot is dormant, it stays in the dormant state and does not move. 
            pass 
        
        
        self.health_bar.x = self.pos[0] + 1
        self.health_bar.y = self.pos[1] -6
        self.health_bar.update(self.hp)

        
        super().update_pos(tilemap,movement=movement)
        
      

        if self.hp <= 0:
            self.set_state('death')
            
            if self.animation.done: 
                del self 
                return True 
        else: 
            if not self.wake: 
                #if you are dormant 
                if math.dist(self.pos,player_pos) < 4*tilemap.tile_size or self.first_hit:
                    self.set_state('wake')
                    if self.animation.done == True: 
                        self.wake = True 
                else: 
                    self.set_state('dormant')
                return False 
            else: 
                if math.dist(self.pos,player_pos) < 12*tilemap.tile_size or self.first_hit:
                    self.aggro = True 
                if self.hurt:
                    self.shooting = False
                    self.charge_time +=0.1
                    self.set_state('hit')
                    
                    self.weapon.update(player_pos) 
                    if self.animation.done == True: 
                        self.hurt = False
                        self.alertted = True 
                else: 

                    if not self.aggro: 
                        self.charge_time = 0
                        if self.collisions['down']:
                            self.air_time = 0
                            
                        if movement[0] != 0:
                            self.set_state('move')    
                        else: 
                            self.set_state('idle') 
                    else: 
                        dir = player_pos[0] - self.pos[0]
                        if dir >= 0:
                            self.flip = False
                        else: 
                            self.flip = True  
                        
                        if not self.alertted:
                            self.set_state('alert')
                            if self.animation.done == True: 
                                self.charge_time = 0
                                self.alertted = True 
                        else:
                            self.weapon.update(player_pos) 
                            if not self.shooting:
                                if self.charge_time < 100: 
                                    self.charge_time += 1
                                    self.set_state('new_charge')
                                    
                                else: 
                                    self.shooting = True 
                                    self.charge_time = 0
                            else: 
                                self.set_state('shoot')
                                if self.animation.frame/self.animation.img_dur == 0 :
                                    
                                    #shoot the gun at the beginning of the shooting animation 
                                    
                                    self.weapon.load(Wheelbot_bullet(self.game,self.game.bullets['laser_weapon'].copy(),[0,0],self.game.bullets['laser_weapon'].images[0].get_size(),'laser_weapon'))
                                    self.weapon.shoot() 
                                if self.animation.done == True: 
                                    self.shooting= False 
                        
                    
                    return False 
    
    def hit(self,hit_damage):
        if self.hp > 0 :
            self.hp -= hit_damage
            self.first_hit = True 
            self.hurt = True 
            self.hit_mask = pygame.mask.from_surface(self.animation.img() if not self.flip else pygame.transform.flip(self.animation.img(),True,False))



    def render(self,surf,offset):
        if self.alertted:
            self.health_bar.render(surf,offset)
        """
        self.outline = pygame.mask.from_surface(self.animation.img() if not self.flip else pygame.transform.flip(self.animation.img(),True,False))
        for offset_ in [(-1,0),(1,0),(0,-1),(0,1)]:
            surf.blit(self.outline.to_surface(unsetcolor=(255,255,255,0),setcolor=(0,0,0,255)),(self.pos[0] - offset[0]+offset_[0],self.pos[1]-offset[1]+offset_[1]))
        super().render(surf,offset=offset)

        if self.hit_mask:
            for offset_ in [(-1,0),(1,0),(0,-1),(0,1)]:
                surf.blit(self.hit_mask.to_surface(unsetcolor=(0,0,0,0),setcolor=(255,255,255,255)),(self.pos[0] - offset[0]+offset_[0],self.pos[1]-offset[1]+offset_[1]))
            self.hit_mask = None
        """


        super().render(surf,(offset[0] - self.weapon.knockback[0]/4, offset[1] - self.weapon.knockback[1]/4))

        if self.state == 'new_charge' or self.state == 'shoot' or self.state == 'hit':
            """
            lights_display = pygame.Surface(surf.get_size())
            self.light.main([],lights_display,self.pos[0]+ self.size[0]//2, self.pos[1]+self.size[1]//2,offset)
            surf.blit(lights_display,(0,0),special_flags = pygame.BLEND_RGB_MULT)
            """
            self.weapon.render(surf,offset)

        #render the outline as well. 

        
        

class Canine(Enemy):
    def __init__(self,game,pos,size,color):
        self.color = color 
        #self.aggro = False 
        #self.aggro_timer = 0 
        #self.hit_mask = None
        #self.first_hit = False
        self.jump_count =1

        super().__init__(game,pos,size,'Canine',253)

        self.health_bar = HealthBar(self.pos[0]+5,self.pos[1]-5,20,2,self.hp)
    
    def collision_rect(self):
        return pygame.Rect(self.pos[0]+3,self.pos[1]+4,self.size[0]-6,self.size[1]-8)


    def set_state(self,action):
        if action != self.state: 
            self.state = action 
            self.animation = self.game.enemies[self.type + '/' + self.color  + '/'+ self.state].copy() 

    def update(self,tilemap,player_pos,dt,movement = (0,0)):
     
        #self.path = tilemap.graph_between_ent_player(self.pos,player_pos)
        self.path  = None 
        #now I want to make the AI of the enemies a bit better 
        
        self.air_time +=1

        if self.collisions['down']:
            self.jump_count =1
            self.air_time = 0
            

        if math.dist(self.pos,player_pos) < 12*tilemap.tile_size or self.first_hit:
            self.aggro = True 
            
        if self.aggro_timer >= 1200:
            self.aggro_timer  = 0
            self.aggro = False 
            self.first_hit = False 

        if self.hp >= 0: 
            if self.aggro : 
                self.aggro_timer += self.aggro
                
                dir = player_pos[0] + 8 - (self.pos[0] + self.size[0]/2)
                if dir >= 0:
                    self.path = tilemap.Astar_pathfinding((self.pos[0]+32,self.pos[1]+16),player_pos)
                else: 
                    self.path = tilemap.Astar_pathfinding((self.pos[0],self.pos[1]+16),player_pos)
                
                
                if self.path:
                    
                    #testing pathtaking.
                    if len(self.path) >1:
                        current_node = self.path[0]
                        if current_node.left and current_node.left == self.path[1]:
                            #then you go left. 
                            movement = (movement[0] -1.5,movement[1])
                        elif current_node.right and current_node.right == self.path[1]:
                            movement = (movement[0] +1.5,movement[1])
                        elif current_node.up and current_node.up == self.path[1]:
                            #here you are going to measure the power of the jump that is needed. 
                            
                            if len(self.path) > 3:
                                x_offset = current_node.pos[0]
                                for node in self.path: 
                                    if x_offset < node.pos[0]:
                                        self.flip = False 
                                        break
                                    elif x_offset > node.pos[0]:
                                        self.flip = True 
                                        break

                                movement = (movement[0] -1.5 if self.flip else movement[0] + 1.5,movement[1] )

                            next_node = current_node.up 
                            
                            if isinstance(current_node.down,Tile) :
                                
                               #something's off... 
                                count = 2
                                power = 2.8
                                while next_node: 
                                    if next_node.up and len(self.path) > count and next_node.up == self.path[count]:
                                        count += 1 
                                    power += 3*dt *14
                                    next_node = next_node.up 
                                    
                                #if self.state != 'jump_up' or self.state != 'jump_down':
                            
                                self.jump(power)

                                
                        elif current_node.down and current_node.down == self.path[1]: 
                            #find the temporary dir. 
                            #traverse through the path until you find a node that is to the left or right. then that becomes the dir. 
                            if len(self.path) > 3:
                                x_offset = current_node.pos[0]
                                for node in self.path: 
                                    if x_offset < node.pos[0]:
                                        self.flip = False 
                                        break
                                    elif x_offset > node.pos[0]:
                                        self.flip = True 
                                        break

                                movement = (movement[0] -1.5 if self.flip else movement[0] + 1.5,movement[1] )
                            
                           
                else: 
                    pass 


                    """
                    
                    if dir > 0:
                        current_node = self.path[0]
                        if current_node.right and isinstance(current_node.right,Node):
                            movement = (movement[0] +0.2,movement[1])
                        if current_node.up and isinstance(current_node.up,Node):
                            self.jump()
                            movement = (movement[0] +0.2,movement[1] )
                        if current_node.down and isinstance(current_node.down,Node):
                            movement = (movement[0] +0.2,movement[1] )

                    elif dir < 0:
                        current_node = self.path[0]
                        if current_node.left and isinstance(current_node.left,Node):
                            movement = (movement[0] -0.2,movement[1])
                        if current_node.up and isinstance(current_node.up,Node):
                            self.jump()
                            movement = (movement[0] -0.2,movement[1] )
                        if current_node.down and isinstance(current_node.down,Node):
                            movement = (movement[0] -0.2,movement[1] )
                    """
        

            else: 
                
                if self.walking :
                    
                    if tilemap.solid_check((self.pos[0]+ (-8 if self.flip else 8+self.size[0]),self.pos[1]+8)):
                        if tilemap.solid_check((self.pos[0] + (-8 if self.flip else 8+self.size[0]),self.pos[1]+8-tilemap.tile_size)):
                            if tilemap.solid_check((self.pos[0]+ (-8 if self.flip else 8+self.size[0] ),self.pos[1]+8-tilemap.tile_size*2)):
                                self.flip = not self.flip 
                            else: 
                                self.velocity[1] = -5
                                movement = (movement[0] - 1.5 if self.flip else movement[0] + 1.5, movement[1])
                        else: 
                            
                            self.velocity[1] = -3.3
                            movement = (movement[0] - 1.5 if self.flip else movement[0] + 1.5, movement[1])
                    else:
                        if tilemap.solid_check((self.pos[0]+ (-8 if self.flip else 8+self.size[0]),self.pos[1]+8-tilemap.tile_size)):
                            if not tilemap.solid_check((self.pos[0]+ (-8 if self.flip else 8+self.size[0]),self.pos[1]+8-tilemap.tile_size*2)):
                                
                                self.velocity[1] = -5
                                movement = (movement[0] - 1.5 if self.flip else 1.5, movement[1])
                            else: 
                                self.flip = not self.flip 
                                movement = (movement[0] - 1.5 if self.flip else 1.5, movement[1])
                        else: 
                            
                            if not tilemap.solid_check((self.pos[0]+ (-8 if self.flip else 8+self.size[0]),self.pos[1]+8+tilemap.tile_size)):
                                if not tilemap.solid_check((self.pos[0]+ (-8 if self.flip else 8+self.size[0]),self.pos[1]+8+tilemap.tile_size*2)):
                                    if not tilemap.solid_check((self.pos[0]+ (-8 if self.flip else 8+self.size[0]),self.pos[1]+8+tilemap.tile_size*3)):
                                        if not tilemap.solid_check((self.pos[0]+ (-8 if self.flip else 8+self.size[0]),self.pos[1]+8+tilemap.tile_size*4)):
                                            if not tilemap.solid_check((self.pos[0]+ (-8 if self.flip else 8+self.size[0]),self.pos[1]+8+tilemap.tile_size*5)):
                                                self.flip = not self.flip 
                                            else: 
                                                movement = (movement[0] - 1.5 if self.flip else 1.5, movement[1])
                                        else: 
                                            movement = (movement[0] - 1.5 if self.flip else 1.5, movement[1])
                                    else: 
                                        movement = (movement[0] - 1.5 if self.flip else 1.5, movement[1])
                                else: 
                                    movement = (movement[0] - 1.5 if self.flip else 1.5, movement[1])
                            else: 
                                movement = (movement[0] - 1.5 if self.flip else 1.5, movement[1])
                            
                    self.walking = max(0, self.walking - 1)
                
                elif random.random() < 0.01:
                    #things to do when you aren't walking 
                    
                    self.walking = random.randint(30,120)

        #update health bar 
        self.health_bar.x = self.pos[0] + 5
        self.health_bar.y = self.pos[1] -5
        self.health_bar.cur_resource = self.hp

        

        super().update_pos(tilemap,movement=movement)
       
        


        if self.hp <= 0 :
            if self.collisions['down']:
                self.set_state('grounded_death')
            #maybe add airborne death animations later 
            if self.air_time > 4:
                if self.velocity[1] < 0:
                    self.set_state('grounded_death')
            
                elif self.velocity[1] >0:
                    self.set_state('grounded_death')
            
            if self.animation.done: 
                del self 
                return True 
        else: 
            if self.collisions['down']:
                self.air_time = 0
        
            if self.air_time > 4:
                
                if self.velocity[1] < 0:
                    self.set_state('jump_up')
            
                elif self.velocity[1] >0:
                    self.set_state('jump_down')
                
            elif movement[0] != 0:
                self.set_state('run')    
            else: 
                self.set_state('idle') 

       
            return False 
            
    
        
    def render(self,surf,offset):
        if self.first_hit:
            self.health_bar.render(surf,offset)
        if self.hit_mask:
            for offset_ in [(-1,0),(1,0),(0,-1),(0,1)]:
                surf.blit(self.hit_mask.to_surface(unsetcolor=(0,0,0,0),setcolor=(255,255,255,255)),(self.pos[0] - offset[0]+offset_[0],self.pos[1]-offset[1]+offset_[1]))
            self.hit_mask = None
        
        super().render(surf,offset=offset)
       
        
        #also render the hit mask 
        #pathfinding testing
        """
        test_surf = pygame.Surface((2,2))
        test_surf.fill((180,0,0,255))
        surf.blit(test_surf,(self.pos[0]+self.size[0] + (-8 if self.flip else 8) -offset[0], self.pos[1]- offset[1]))
        """
        # (self.pos[0]+self.size[0] + (-8 if self.flip else 8),self.pos[1]//16-tilemap.tile_size)
        
        """
        if self.path: 
            for key in self.path: 
                test_surf = pygame.Surface((1,1))
                test_surf.fill((180,0,0,255))
                node =self.path[key]
               
                surf.blit(test_surf,(node.pos[0]*16 -offset[0] + 8,node.pos[1]*16 - offset[1]+8))
        """
        
        if self.path: 
            for node in self.path: 
              
                test_surf = pygame.Surface((1,1))
                test_surf.fill((180,0,0,255))
                surf.blit(test_surf,(node.pos[0]*16 -offset[0] + 8,node.pos[1]*16 - offset[1]+8))
        

    def jump(self,power = 3):
        if self.state == 'jump_down' or self.state == 'jump_up':
            #don't do anything. 
            pass 
        else: 
            if self.jump_count==1:
                self.jump_count -= 1
                self.velocity[1] = -power

    
    def hit(self,hit_damage):
        self.hp -= hit_damage
        self.first_hit = True 
        self.hit_mask = pygame.mask.from_surface(self.animation.img() if not self.flip else pygame.transform.flip(self.animation.img(),True,False))
        
    
        
        
class PlayerEntity(PhysicsEntity):
    def __init__(self,game,pos,size):
        #attributes required to implement weapon 
        self.equipped = False 
        self.cur_weapon = None 
        self.cur_weapon_index = None

        self.weapon_inven_size = 5 # maximum size of carry 

        self.weapon_inven = DoublyLinkedList()
       
        

        self.change_weapon_inc = False
        self.changing_done = 0 
        self.change_scroll = 0

        self.hit_mask = None

        super().__init__(game,'player',pos,size)

        self.recov_rate = 0.6
        self.stamina = 100
        self.health = 200

        self.jump_count = 2
        self.wall_slide = False
        self.slide = False 
        self.on_wall = self.collisions['left'] or self.collisions['right']
        self.air_time = 0
      
        

        #attributes required to implement double tap 
      

        self.fatigued = False 
        self.running = False 


        self.y_inertia = 0
        self.hard_land_recovery_time = 0

        self.d_cursor_pos = [0,0]
        self.time = 0
        
        

        
        
       
    def set_state(self,action):
        if action != self.state: 
            self.state = action 
            self.animation = self.game.assets[self.type + '/' + ('holding_gun/' if self.equipped else '') + self.state].copy() 

    def update_pos(self, tile_map,cursor_pos,frame_count,movement=(0, 0)):
        #print(self.velocity[0])
        self.time = frame_count
        self.d_cursor_pos = cursor_pos
        new_movement = [movement[0],movement[1]]

        if self.fatigued: 
            self.recov_rate = 0.3
            new_movement[0] *= 0.7
            if self.stamina >= 80:
                self.fatigued = False 
        else: 
            self.recov_rate = 0.6
            if self.running: 
                if self.stamina >= 10:
                    #then you can run. 
                    if movement[0] != 0:
                        self.stamina -= 1.2
                        new_movement[0] *= 1.4
                else: 
                    new_movement[0] *= 0.7
                    self.fatigued = True 
            else: 
                if self.stamina < 10: 
                    new_movement[0] *= 0.7
                    self.fatigued = True 
        
        if self.hard_land_recovery_time > 0 :
            new_movement[0] *= (20 - self.hard_land_recovery_time)/20 
            new_movement[1] *= (20 - self.hard_land_recovery_time)/20 
            self.hard_land_recovery_time -= 1
            
        super().update_pos(tile_map, new_movement)

        

        #every frame, the stamina is increased by 0.7
       
        self.stamina = min(100, self.stamina + self.recov_rate)
        self.air_time +=1
        
        
        self.changing_done += self.change_weapon_inc
        if self.changing_done == 6:
            self.change_weapon(self.change_scroll)
        

        if self.velocity[1] >=2:
            self.y_inertia += 1 

       
        self.cut_movement_input = False 


        #add particle spew effect, similar to how you've done it for the bullets when it collides with tiles. 
        #the number of particles that are created should depend on the impact force, which can be a function of y_inertia you've 
        #defined already. 

        if self.collisions['down']:
            if self.y_inertia > 6:
                self.set_state('land')
            entry_pos = (self.rect().centerx,self.rect().bottom)
            for offset in (0,-tile_map.tile_size,tile_map.tile_size):
                if tile_map.solid_check((entry_pos[0]+offset,entry_pos[1])):
                    color = tile_map.return_color((entry_pos[0]+offset,entry_pos[1]),side ='top')
                    break



            offsets = [(-2,0),(-1,0), (0,0), (1,0),(2,0)]                
            for i in range(min(8,self.y_inertia//2)):
                offset = random.choice(offsets)
                self.game.non_animated_particles.append(bullet_collide_particle(random.choice([(1,1),(2,1),(1,2),(3,1),(1,3),(2,2)]), (entry_pos[0] - offset[0],entry_pos[1] ) ,-90 + random.randint(-88,88),2.4+random.random(),color,tile_map,gravity_factor= 1.4 * min(8,self.y_inertia//2)/5))
        


            if self.y_inertia > 12 and self.y_inertia <35:
                land_smoke = Particle(self.game,'land',(self.pos[0] +8,self.pos[1]+14),'player')
                self.game.particles.append(land_smoke)
                self.game.screen_shake = max(5,self.game.screen_shake)
                self.hard_land_recovery_time = 7
                #self.set_state('land')
                

                
                
                
            elif self.y_inertia >= 35:
                land_smoke = Particle(self.game,'big_land',(self.pos[0] +7,self.pos[1]+7),'player')
                self.game.particles.append(land_smoke)
                #self.set_state('land')
                self.game.screen_shake = max(16,self.game.screen_shake)
                self.animation.img_dur = 5
                self.hard_land_recovery_time = 20

            self.y_inertia = 0
            self.jump_count =2 
            self.air_time = 0
            
            
        self.wall_slide = False
        self.on_wall = self.collisions['left'] or self.collisions['right']


        if self.on_wall and self.air_time > 4:
            self.wall_slide = True 
            self.velocity[1] = min(self.velocity[1],0.5)
            if self.collisions['right']:
                self.flip = False
            else:
                self.flip = True 
            
            self.set_state('wall_slide')
            self.y_inertia = 0
       
        if not self.wall_slide: 
            if self.air_time > 4:
                self.boost_on_next_tap = False 
                if self.velocity[1] < 0:
                    self.y_inertia = 0
                    self.set_state('jump_up')
                elif self.velocity[1] >0 :
                    self.set_state('jump_down')
               
            elif movement[0] != 0:
                if self.state == 'land':
                    if self.animation.done == True: 
                        if self.fatigued: 
                            self.set_state('walk')
                        else: 
                            self.set_state('run')
                else: 
                   
                    if self.fatigued: 
                        self.set_state('walk')
                    else: 
                        self.set_state('run')
                    """
                    anim_frame = self.animation.frame / self.animation.img_dur
                    if anim_frame == 0 or anim_frame == 3:
                        self.game.player_sfx['run'][str(random.randint(0,7))].play()
                    """
                if self.slide:
                    self.cut_movement_input = True
                    self.set_state('slide')
                self.y_inertia = 0
                    
            else: 
                self.y_inertia = 0
                if self.state == 'land':
                    if self.animation.done == True: 
                        self.set_state('idle') 
                else: 
                    self.set_state('idle')
                
        
        

        if self.equipped:
            self.cur_weapon.update(self.d_cursor_pos)
        
        #update the health and stamina bars 
        
    def accel(self):
        #check the stamina and return the speed. 
        if self.fatigued: 
            if self.stamina <= 70:
                return 1
            else: 
                self.fatigued = False 
                self.stamina -= 1.3
                return 2.3
        else: 
            if self.stamina > 10:
                self.stamina -= 1.3
                return 2.3
            else: 
                self.fatigued = True 
                return 1
        
        
    
    def render(self,surf,offset):
        
        knockback = (0,0) if not self.equipped else (self.cur_weapon.knockback[0]/5,self.cur_weapon.knockback[1]/9)

        super().render(surf,(offset[0] - knockback[0],offset[1] - knockback[1]))


        if self.hit_mask:
            for offset_ in [(-1,0),(1,0),(0,-1),(0,1)]:
                surf.blit(self.hit_mask.to_surface(unsetcolor=(0,0,0,0),setcolor=(255,255,255,255)),(self.pos[0] - offset[0]+offset_[0] - knockback[0],self.pos[1]-offset[1]+offset_[1]- knockback[1]))
            self.hit_mask = None

        """
        #render the health bar and the stamina bar 
        #add scaling later so that the health and stamina bars can dynamically change. 
        surf.blit(self.health_UI,(self.health_bar.x-2,self.health_bar.y-2)) 
        self.health_bar.render(surf,(0,0))

        surf.blit(self.stamina_UI,(self.stamina_bar.x-2,self.stamina_bar.y-2)) 
        self.stamina_bar.render(surf,(0,0))


        #render the health bar indicator 
        health_ind = indicator(int(self.health_bar.cur_resource),int(self.health_bar.max_resource))
        health_ind.render(self.health_bar.x + 84,self.health_bar.y-1,surf)
        
        #render the stamina bar indicator 
        stamina_ind = indicator(int(self.stamina_bar.cur_resource),int(self.stamina_bar.max_resource))
        stamina_ind.render(self.stamina_bar.x+34,self.stamina_bar.y-1,surf)
        """

        if self.equipped: 
            
            if self.changing_done == 0:
                self.cur_weapon.render(surf,offset,set_angle = None)
            else: 
                if self.cur_weapon.flipped: 
                    angles = [angle for angle in range(0,-121,-20)]  
                    
                else: 
                    angles = [angle for angle in range(120,-1,-20)]                    
                arm_pos_angle = angles[self.changing_done]
                self.cur_weapon.render(surf,offset,set_angle = arm_pos_angle) 
            
    
    def dash(self):
        if not self.fatigued: 
            dust = None
            
            if self.state == 'jump_up' or self.state == 'jump_down':
                if self.flip: 
                    dust = Particle(self.game,'dash_air',(self.rect().center[0] + 10,self.rect().center[1]),'player',velocity=[1,0],frame=0)
                    self.velocity[0] = -5.0
                else: 
                    dust = Particle(self.game,'dash_air',(self.rect().center[0] - 10,self.rect().center[1]),'player',velocity=[-1,0],frame=0)
                    self.velocity[0] = 5.0     
                self.stamina -= 25      
            else:
                if self.state != 'wall_slide':
                    if not self.flip:
                        dust = Particle(self.game,'dash_right',(self.rect().topleft[0]-1.4,self.rect().topleft[1]+2),'player',velocity=[-1.0,0],frame=0)
                        self.velocity[0] = 5.0
                    else: 
                        #flip the dust particle effect
                        dust = Particle(self.game,'dash_left',(self.rect().topright[0]+1.4,self.rect().topright[1]+2),'player',velocity=[1.0,0],frame=0)
                        self.velocity[0] = -5.0
                    self.stamina -= 25

            self.game.particles.append(dust)
        
    def player_jump(self):
     
        if self.wall_slide: 
            self.jump_count = 1
            
            if self.collisions['left']:
                
                self.velocity[0] =  4.2
            if self.collisions['right']:
                
                self.velocity[0] = -4.2
            #self.accel_up() 
            
            self.velocity[1] =-4.2
            

            air = Particle(self.game,'jump',(self.rect().centerx,self.rect().bottom), 'player',velocity=[0,0.1],frame=0)
            self.game.particles.append(air)

        if self.jump_count == 2:
            if self.state == 'jump_down':
                self.jump_count -=2
                #self.accel_up() 

                self.velocity[1] = -4.2
                
                air = Particle(self.game,'jump',(self.rect().centerx,self.rect().bottom), 'player',velocity=[0,0.1],frame=0)
                self.game.particles.append(air)
            else: 
                self.jump_count -=1
                #self.accel_up() 

                self.velocity[1] = -4.2    
            
        elif self.jump_count ==1: 
            self.jump_count -=1
            #self.accel_up() 
            self.velocity[1] = -4.2  
            air = Particle(self.game,'jump',(self.rect().centerx,self.rect().bottom), 'player',velocity=[0,0.1],frame=0)
            self.game.particles.append(air)
            
    

    def jump_cut(self):
        #called when the player releases the jump key before maximum height. 

        if self.velocity[1] < 0: 
            if self.velocity[1] > -4.2:
                if self.air_time >0 and self.air_time <= 8:
                    self.velocity[1] = -1.5
                if self.air_time >8 and self.air_time <=11 :
                    self.velocity[1] = -2.2

    
    def change_weapon(self,scroll):
        if self.weapon_inven.head and ((self.weapon_inven.head.next and scroll ==1) or (self.weapon_inven.head.prev and scroll == -1)): 
            self.change_scroll =scroll
            self.change_weapon_inc= True 
            if self.changing_done == 6:
                if self.change_scroll == 1:
                    self.weapon_inven.head = self.weapon_inven.head.next
                else:
                    self.weapon_inven.head = self.weapon_inven.head.prev 
                self.equip()
                self.changing_done = 0
                self.change_scroll = 0 
                self.change_weapon_inc = False
            
            
        """
        if self.cur_weapon:
            #first check if scrolling in that direction is valid. 
            if 0 <= self.cur_weapon_index + scroll <= len(self.weapon_inven) -1 :
                self.change_scroll = scroll
                self.change_weapon_inc = True 
                if self.changing_done == 6:
                    self.cur_weapon_index = self.weapon_inven.index(self.cur_weapon)
                    self.cur_weapon_index = max(0,self.cur_weapon_index - 1) if scroll == -1 else min(len(self.weapon_inven)-1,self.cur_weapon_index+1)
                    self.cur_weapon = self.weapon_inven[self.cur_weapon_index]
                    self.weapon_inven[self.cur_weapon_index].equip(self) 
                    self.changing_done = 0 
                    self.change_scroll = 0
                    self.change_weapon_inc = False 
        """

    def equip(self):
        if self.weapon_inven.head:
            self.cur_weapon = self.weapon_inven.head.weapon
            self.equipped = True 
            self.cur_weapon.equip(self)
        else: 
            self.cur_weapon = None
            self.equipped = False
        """
        if len(self.weapon_inven) < self.weapon_inven_size:
            
            self.weapon_inven.insert(0 if self.cur_weapon == None else self.weapon_inven.index(self.cur_weapon),weapon)
            

            self.cur_weapon = self.weapon_inven[0 if self.cur_weapon == None else self.weapon_inven.index(self.cur_weapon)-1]
            self.cur_weapon_index = self.weapon_inven.index(self.cur_weapon) 
            self.equipped = True 
            self.weapon_inven[self.cur_weapon_index].equip(self)
        """
        

    def shoot_weapon(self,frame):
        #testing bullet firing
        if self.equipped: 
            if self.cur_weapon.rapid_firing:
                if frame % self.cur_weapon.fire_rate == 0:
                    """
                    test_shell_image = self.game.bullets['rifle_small'].copy()
                    test_shell = Bullet(self.game,self.cur_weapon.opening_pos,test_shell_image.get_size(),test_shell_image,'rifle_small').copy()
                    self.cur_weapon.load(test_shell)
                    """
                    self.cur_weapon.shoot(self.time,self.d_cursor_pos) 
                   
                    #self.game.Tilemap.bullets.append(shot_bullet)
                    #self.game.bullets_on_screen.append(shot_bullet)
                    #rotate the images in the animation 
                    

            else: 
                """
                test_shell_image = self.game.bullets['rifle_small'].copy()
                test_shell = Bullet(self.game,self.cur_weapon.opening_pos,test_shell_image.get_size(),test_shell_image,'rifle_small').copy()
                self.cur_weapon.load(test_shell)
                """
          
                self.cur_weapon.shoot(self.time,self.d_cursor_pos) 
               
                #self.game.Tilemap.bullets.append(shot_bullet)
                #self.game.bullets_on_screen.append(shot_bullet)

            #add bullet drop particles and smoke particles 
                
           
            
                    
                    
    def toggle_rapid_fire(self):
        if self.equipped:
            self.cur_weapon.toggle_rapid_fire()


    def weapon_toggle_state(self):
        if self.equipped:
            return self.cur_weapon.rapid_firing 
    
    def hit(self,hit_damage):
        self.health -= hit_damage
        self.hit_mask = pygame.mask.from_surface(self.animation.img() if not self.flip else pygame.transform.flip(self.animation.img(),True,False))
        

class Item(PhysicsEntity):
    def __init__(self, game,size,sprite):
        super().__init__(game, 'item', [0,0], size)
        self.sprite = sprite 

    """ what would you need for an item class to have? """


    def copy(self):
        return Item(self.game,self.size,self.sprite)


class Grenade(Item):
    def __init__(self, game, size, sprite):
        super().__init__(game, size, sprite)


    def update(self):
        pass


    def render(self,surf,offset = [0,0]):
        pass 




class Bullet(PhysicsEntity): 
    def __init__(self,game,pos,size,sprite,type):
        super().__init__(game,'bullet',pos,size)
        self.damage = 1
        self.angle = 0
        self.sprite = sprite
        self.bullet_type = type
        self.center = [self.sprite.get_width()/2,self.sprite.get_height()/2]
        self.set_state('in_place')
        self.frames_flown = 0
        self.test_tile = None
        self.light = LIGHT(20,pixel_shader(20,(255,255,255),1,False))
        
        
  
    def set_state(self, action):
        self.state = action

    def rect(self):
        
        return pygame.Rect(self.pos[0],self.pos[1],self.sprite.get_width(),self.sprite.get_height())

    def collision_handler(self,tilemap,rect_tile,ent_rect,dir,axis):
        if isinstance(rect_tile,pygame.Rect):
            rect_tile = rect_tile
        else: 
            rect_tile = rect_tile[0]

        

        og_end_point_vec = pygame.math.Vector2((6,0))
        og_end_point_vec.rotate(self.angle)

        
        
        end_point = [self.center[0]+og_end_point_vec[0] - (self.sprite.get_width()/2 if self.velocity[0] >=0 else 0),self.center[1] + og_end_point_vec[1]] 
        
        entry_pos = ( rect_tile.left if dir else rect_tile.right ,end_point[1]) if axis else (end_point[0],rect_tile.top if dir else rect_tile.bottom )

        sample_side = {(True,True) : 'left',(False,True) : 'right',(True,False) : 'top',(False,False) : 'bottom'}


        color = tilemap.return_color(rect_tile,sample_side[(dir,axis)])
        
        #you need to tweak the particle spawning positions depending on the side where the bullet has hit, and make the spawning position more 
        #precise. 


        offsets = [(-1,0), (0,0), (1,0)]
        for i in range(random.randint(6,11)):
            offset = random.choice(offsets)
            self.game.non_animated_particles.append(bullet_collide_particle(random.choice([(1,1),(2,1),(1,2),(3,1),(1,3),(2,2)]), entry_pos,(180-self.angle) + random.randint(-88,88),3+random.random(),color,tilemap))
        
        bullet_mask = pygame.mask.from_surface(self.sprite)
        tile_mask = pygame.mask.Mask((rect_tile.width,rect_tile.height))
        #bullet_mask.fill()
        tile_mask.fill()
        offset = (ent_rect[0] - rect_tile[0],ent_rect[1] - rect_tile[1])
        
        #I guess create the decal object here, when the mask collision is done. 

        if tile_mask.overlap_area(bullet_mask,offset)>2:
            collided_tile = tilemap.return_tile(rect_tile)
            
            collide_particle = Particle(self.game,'bullet_collide/rifle',end_point,'player')
            rotated_collide_particle_images = [pygame.transform.rotate(image,180+self.angle) for image in collide_particle.animation.copy().images]
            collide_particle.animation.images = rotated_collide_particle_images

            self.game.particles.append(collide_particle)

            if collided_tile.type != 'box':
                pass
                """
                decal_mask  = tile_mask.overlap_mask(bullet_mask,offset)
                decal_surf = decal_mask.to_surface(unsetcolor=(135,135,135,0))
                decal_surf.set_colorkey((0,0,0))
                
                collided_tile.decals.append([decal_surf,0])
                """
                
            else:
                del tilemap.tilemap[str(collided_tile.pos[0]) + ';' + str(collided_tile.pos[1])]
                destroy_box_smoke = Particle(self.game,'box_smoke',(rect_tile.centerx,rect_tile.centery),'tile',velocity=[0,0],frame = 10)  
                self.game.particles.append(destroy_box_smoke)
                collided_tile.drop_item()
                
            
            return True
        

    def update_pos(self, tile_map,offset = (0,0)):
        
        kill= False

        self.collisions = {'up' :False,'down' : False, 'left': False, 'right': False }
        self.frames_flown +=1 
        
        if self.frames_flown >= 50:
            del self 
            return True
        
        #make collision detection more precise. 
        
        self.pos[0] += self.velocity[0] 
        self.center = [self.pos[0]+self.sprite.get_width()/3, self.pos[1] + self.sprite.get_height()/2]
        entity_rect = self.rect()

        #when a bullet collides with a physics block, it leaves decals - based on their masks overlapping with the tiles. 
        #add a black smudge effect to the tiles.

        for rect_tile in tile_map.physics_rects_around(self.pos,self.size):
            if entity_rect.colliderect(rect_tile[0]):
                if rect_tile[1].type == 'stairs' and  rect_tile[1].variant.split(';')[0] in ['0','1']:
                    #you check for separate collisions 
                    #make separate rects for ramps 
                    if rect_tile[1].variant.split(';')[0] == '0':
                        #left stairs
                        #this part where check rects are created is not dynamic, so if tilesize changes this part needs to be changed manually. maybe figure out a mathematical 
                        #way to create rects. 
                        check_rects = [pygame.Rect(rect_tile[0].left,rect_tile[0].bottom + 4,rect_tile[0].width,4),
                                       pygame.Rect(rect_tile[0].left + 12,rect_tile[0].top,4,12),
                                       pygame.Rect(rect_tile[0].left + 6,rect_tile[0].top + 6,6,6)
                                       ]
                        for check_rect in check_rects:
                            if entity_rect.colliderect(check_rect):
                                kill = self.collision_handler(tile_map,check_rect,entity_rect,self.velocity[0] > 0, True)
                    else: 
                        check_rects = [pygame.Rect(rect_tile[0].left,rect_tile[0].bottom + 4,rect_tile[0].width,4),
                                       pygame.Rect(rect_tile[0].left,rect_tile[0].top,4,12),
                                       pygame.Rect(rect_tile[0].left + 4,rect_tile[0].top + 6,6,6)
                                       ]
                        for check_rect in check_rects:
                            if entity_rect.colliderect(check_rect):
                                kill = self.collision_handler(tile_map,check_rect,entity_rect,self.velocity[0] > 0, True)
                else: 
                    kill = self.collision_handler(tile_map,rect_tile,entity_rect,self.velocity[0] > 0, True)

                    """
                    color = tile_map.return_color(rect_tile[0])

                    og_end_point_vec = pygame.math.Vector2((6,0))
                    og_end_point_vec.rotate(self.angle)

                    
                    
                    end_point = [self.center[0]+og_end_point_vec[0] - (self.sprite.get_width()/2 if self.velocity[0] >=0 else 0),self.center[1] + og_end_point_vec[1]] 

                    collide_particle = Particle(self.game,'bullet_collide/rifle',end_point,'player')
                    rotated_collide_particle_images = [pygame.transform.rotate(image,180+self.angle) for image in collide_particle.animation.copy().images]
                    collide_particle.animation.images = rotated_collide_particle_images

                    self.game.particles.append(collide_particle)
                    
                    offsets = [(-1,0), (0,0), (1,0)]
                    for i in range(random.randint(6,11)):
                        offset = random.choice(offsets)
                        self.game.non_animated_particles.append(bullet_collide_particle(random.choice([(1,1),(2,1),(1,2)]),end_point,(180-self.angle) + random.randint(-88,88),3+random.random(),color,tile_map))
                    
                    bullet_mask = pygame.mask.from_surface(self.sprite)
                    tile_mask = pygame.mask.Mask((rect_tile[0].width,rect_tile[0].height))
                    bullet_mask.fill()
                    tile_mask.fill()
                    offset = (entity_rect[0] - rect_tile[0][0],entity_rect[1] - rect_tile[0][1])
                    

                    if tile_mask.overlap_area(bullet_mask,offset)>13:
                        #add sparks particle when a bullet hits an enemy 
                    

                        collided_tile = tile_map.return_tile(rect_tile[0])
                        if collided_tile.type == 'box':
                
                            del tile_map.tilemap[str(collided_tile.pos[0]) + ';' + str(collided_tile.pos[1])]
                            destroy_box_smoke = Particle(self.game,'box_smoke',(rect_tile[0].centerx,rect_tile[0].centery),'tile',velocity=[0,0],frame = 10)  
                            self.game.particles.append(destroy_box_smoke)
                            collided_tile.drop_item()
                            

                        del self 
                        return True
                    """
        if kill:
            
            del self 
            return True 
        
        self.pos[1] += self.velocity[1] 


        self.center = [self.pos[0]+self.sprite.get_width()/3, self.pos[1] + self.sprite.get_height()/2]
        
        entity_rect = self.rect()

        #when a bullet collides with a physics block, it leaves decals - based on their masks overlapping with the tiles. 
        #add a black smudge effect to the tiles.

        for rect_tile in tile_map.physics_rects_around(self.pos,self.size):
            if entity_rect.colliderect(rect_tile[0]):
                if rect_tile[1].type == 'stairs' and  rect_tile[1].variant.split(';')[0] in ['0','1']:
                    #you check for separate collisions 
                    #make separate rects for ramps 
                    if rect_tile[1].variant.split(';')[0] == '0':
                        #left stairs
                        #this part where check rects are created is not dynamic, so if tilesize changes this part needs to be changed manually. maybe figure out a mathematical 
                        #way to create rects. 
                        check_rects = [pygame.Rect(rect_tile[0].left,rect_tile[0].bottom + 4,rect_tile[0].width,4),
                                       pygame.Rect(rect_tile[0].left + 12,rect_tile[0].top,4,12),
                                       pygame.Rect(rect_tile[0].left + 6,rect_tile[0].top + 6,6,6)
                                       ]
                        for check_rect in check_rects:
                            if entity_rect.colliderect(check_rect):
                                kill = self.collision_handler(tile_map,check_rect,entity_rect,self.velocity[1] > 0 ,False)
                    else: 
                        check_rects = [pygame.Rect(rect_tile[0].left,rect_tile[0].bottom + 4,rect_tile[0].width,4),
                                       pygame.Rect(rect_tile[0].left,rect_tile[0].top,4,12),
                                       pygame.Rect(rect_tile[0].left + 4,rect_tile[0].top + 6,6,6)
                                       ]
                        for check_rect in check_rects:
                            if entity_rect.colliderect(check_rect):
                                kill = self.collision_handler(tile_map,check_rect,entity_rect,self.velocity[1] > 0 ,False)
                else: 
                    kill = self.collision_handler(tile_map,rect_tile,entity_rect,self.velocity[1] > 0 ,False)


        if kill:
            
            del self 
            return True 
       
      
        #collision with entities crude method....
        
        """
        entity_rect = self.rect() 
        for enemy in self.game.existing_enemies:
            if entity_rect.colliderect(enemy.rect()):
                enemy.hit(self.damage)
                og_end_point_vec = pygame.math.Vector2((6,0))
                og_end_point_vec.rotate(self.angle)

                center_pos = [self.pos[0]+self.sprite.get_width()/2, self.pos[1] + self.sprite.get_height()/2]
                end_point = [center_pos[0]+og_end_point_vec[0]- (self.sprite.get_width()/2 if self.velocity[0] >=0 else 0),center_pos[1] + og_end_point_vec[1]] 
                collide_particle = Particle(self.game,'bullet_collide/rifle',end_point,'player')
                rotated_collide_particle_images = [pygame.transform.rotate(image,180+self.angle) for image in collide_particle.animation.copy().images]
                collide_particle.animation.images = rotated_collide_particle_images

                self.game.particles.append(collide_particle)

                del self 
                return True 
        """

            
        
             
    
    
    def render(self,surf,offset = (0,0)):
        #test_surface = pygame.Surface((self.sprite.get_width(),self.sprite.get_height()))
        #surf.blit(test_surface,(self.pos[0]-offset[0],self.pos[1]-offset[1]))
        bullet_glow_mask = pygame.mask.from_surface(self.sprite)
        #surf.blit(bullet_glow_mask.to_surface(unsetcolor=(0,0,0,0),setcolor=(255,255,255,255)),(self.pos[0] - offset[0],self.pos[1]-offset[1]))
        surf.blit(self.sprite, (self.pos[0]-offset[0],self.pos[1]-offset[1]),special_flags = pygame.BLEND_RGB_ADD)

    def copy(self):
        return Bullet(self.game,self.pos,self.size,self.sprite,self.bullet_type)

class tile_ign_Bullet(Bullet):

    def __init__(self,game,pos,size,sprite,type):
        super().__init__(game,pos,size,sprite,type)


    def update_pos(self, tile_map, offset=(0, 0)):
        self.collisions = {'up' :False,'down' : False, 'left': False, 'right': False }
        self.frames_flown +=1 

        if self.frames_flown >= 50:
            del self 
            return True
        
        self.pos[0] += self.velocity[0] 
        self.pos[1] += self.velocity[1] 

        #you only check for collisions between it and the player. and maybe other entities. 
        
        entity_rect = self.rect()
        if entity_rect.colliderect(self.game.player.rect()):
            self.game.player.hit(self.damage)
            del self 
            return True 
       
        
class Dropped_item(PhysicsEntity):
    def __init__(self, game, e_type, pos, size):
        super().__init__(game, e_type, pos, size)        
       
class Wheelbot_bullet(tile_ign_Bullet):
    def __init__(self,game,animation,pos,size,type):
        self.game = game
        self.animation = animation
        self.pos = pos
        self.size = size
        self.type = type
        self.frames_flown = 0
        self.trailing_particles = []
        self.flip = False 

        self.light = LIGHT(40,pixel_shader(40,(137,31,227),1,False))
        self.center = [self.pos[0]+self.animation.img().get_width()/2, self.pos[1] + self.animation.img().get_height()/2]

    def rect(self):
        return pygame.Rect(self.pos[0]+1,self.pos[1]+2,self.animation.img().get_width()-2,self.animation.img().get_height()-4)
    
    def update_pos(self, tile_map, offset=(0, 0)):
        self.animation.update()
        self.collisions = {'up' :False,'down' : False, 'left': False, 'right': False }
        self.frames_flown +=1 
      

        if self.frames_flown >= 300:
            del self 
            return True
        
        

        self.pos[0] += self.velocity[0] 
        self.pos[1] += self.velocity[1] 

        #you only check for collisions between it and the player. and maybe other entities. 
        trail_color = [(48,3,217),(122,9,250)]
        pos = self.pos.copy()
        

        #trail particles 
        pos[0] += self.animation.img().get_width()/2
        pos[1] += self.animation.img().get_height()/2
        for i in range(random.randint(3,6)):
            factor = random.random()
            offset = random.choice([(-1,0),(0,0),(1,0),(0,1),(0,-1),(-1,-1),(1,-1),(-1,1),(1,1)])
            up_down = random.choice([-1,1])
            self.game.non_animated_particles.append(bullet_trail_particle_wheelbot(3,0.8,[pos[0] + offset[0]+ (-self.velocity[1] * factor*up_down)/4 ,pos[1] + offset[1]+(self.velocity[0] * factor*up_down)/4],random.choice(trail_color)))
            


        self.center =  [self.pos[0]+self.animation.img().get_width()/2, self.pos[1] + self.animation.img().get_height()/2]


        entity_rect = self.rect()
        if entity_rect.colliderect(self.game.player.rect()):
            self.game.player.hit(self.damage)
            og_end_point_vec = pygame.math.Vector2((6,0))
            og_end_point_vec.rotate(self.angle)

            self.center  = [self.pos[0]+self.animation.img().get_width()/2, self.pos[1] + self.animation.img().get_height()/2]
            end_point = [self.center [0]+og_end_point_vec[0],self.center[1] + og_end_point_vec[1]] 

            
      
            

            collide_particle = Particle(self.game,'bullet_collide/laser_weapon',end_point,'Wheel_bot')
            

            self.game.particles.append(collide_particle)
            self.game.temp_lights.append([LIGHT(40,pixel_shader(40,(137,31,227),1,False)),4,end_point])
            del self 
            return True 
            
        
    
    def render(self,surf,offset = (0,0)):
        #test_surf = pygame.Surface(self.animation.img().get_size())
        #surf.blit(test_surf,(self.pos[0]-offset[0],self.pos[1]-offset[1]))
        surf.blit(self.animation.img(),(self.pos[0]-offset[0],self.pos[1]-offset[1]),special_flags = pygame.BLEND_RGB_ADD)
        
       
            
        #here you are going to use the render function from the physics entity class. 



