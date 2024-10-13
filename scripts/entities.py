#alright, so this is where I am going to implement physics for the objects 
#of my game. 
import random
import pygame 
import math

from pygame.math import Vector2
from scripts.spark import Spark
from scripts.los import line_of_sight
from scripts.particles import Particle,non_animated_particle,bullet_collide_particle,bullet_trail_particle_wheelbot
from scripts.health import HealthBar,StaminaBar
from scripts.indicator import indicator 
from scripts.tilemap import Node,Tile
from scripts.fire import Flame_particle
from scripts.spark import Spark 
from scripts.Pygame_Lights import LIGHT,pixel_shader,global_light
from scripts.weapon_list import DoublyLinkedList
from scripts.range import Rectangle
from my_pygame_light2d.light import PointLight


INTERACTABLES = {'building_door','trap_door'}


#a body class to implement a more accurate body with better physics that require rotation, 
#utilizing the pymunk module. 

class Accurate_Rect_Body():
    def __init__(self) -> None:
        pass

    def update(self):
        pass 

    def render(self,surf,offset= [0,0]):
        pass 

class interactable:
    # a class that defines interactable objects, like doors, which physics don't apply constantly, but 
    # should still be recognized as a tile.
    pass 





class PhysicsEntity:
    def __init__(self, game, e_type, pos, size):
        self.game = game
        self.type = e_type
        self.pos = list(pos)
        self.collisions = {'up': False, 'down': False, 'left': False, 'right': False}
        self.size = size
        self.velocity = [0, 0]
        self.state = ''
        self.anim_offset = (0, 0)
        self.flip = False
        self.set_state('idle')
        self.cut_movement_input = False
        self.on_ramp = 0

    def set_state(self, action):
        if action != self.state:
            self.state = action
            self.animation = self.game.general_sprites[self.type + '/' + self.state].copy()

    def collide(self, other):
        return self.collision_rect().colliderect(other.collision_rect())

    def collision_rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])

    def rect(self):
        
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])

    def update_pos(self, tile_map, movement=(0, 0),anim_offset = (0,0)):
        if movement[0] > 0:
            self.flip = False
        if movement[0] < 0 :
            self.flip = True 

        self.animation.update()
        self.collisions = {'up': False, 'down': False, 'left': False, 'right': False}
        self.velocity[1] = min(5, self.velocity[1] + 0.26)

        if self.velocity[0] < 0:
            self.velocity[0] = min(self.velocity[0] + 0.21, 0)
        elif self.velocity[0] > 0:
            self.velocity[0] = max(self.velocity[0] - 0.21, 0)

        frame_movement = (movement[0] + self.velocity[0], movement[1] + self.velocity[1]) if not self.cut_movement_input else self.velocity

        interactables = []

        self.pos[0] += frame_movement[0]
        entity_rect = self.rect()
        for rect_tile in tile_map.physics_rects_around((self.pos[0] +anim_offset[0] ,self.pos[1] +anim_offset[1] ), self.size):
            
            tile_type = rect_tile[1].type
            
            if tile_type in INTERACTABLES:
                interactables.append(rect_tile) 
            

            if entity_rect.colliderect(rect_tile[0]) and tile_type.split('_')[1] != 'stairs':
                if tile_type.split('_')[1] == 'door':
                    if  rect_tile[1].open:
                        continue
                    else:

                        # if you close the door on youself (trap door and vertical door)
                        if rect_tile[1].trap: 
                            continue 
                        else: 
                            if frame_movement[0] > 0 :
                                self.collisions['right'] = True
                                
                                entity_rect.right = rect_tile[0].left
                            elif frame_movement[0] < 0:
                                self.collisions['left'] = True
                                
                                entity_rect.left = rect_tile[0].right
                            else: 
                                if entity_rect.centerx -rect_tile[0].centerx <0:
                                    self.collisions['right'] = True
                                    entity_rect.right = rect_tile[0].left
                                    
                                else:
                                    self.collisions['left'] = True 
                                    entity_rect.left = rect_tile[0].right 
                                
                            self.pos[0] = entity_rect.x - anim_offset[0]
                            
                else:
                    if frame_movement[0] > 0:
                        self.collisions['right'] = True
                        
                        entity_rect.right = rect_tile[0].left
                    elif frame_movement[0] < 0:
                        self.collisions['left'] = True
                        
                        entity_rect.left = rect_tile[0].right
                    else: 
                        if entity_rect.centerx -rect_tile[0].centerx <0:
                            self.collisions['right'] = True
                            entity_rect.right = rect_tile[0].left
                            
                        else:
                            self.collisions['left'] = True 
                            entity_rect.left = rect_tile[0].right 
                        



                    self.pos[0] = entity_rect.x - anim_offset[0]

        self.pos[1] += frame_movement[1]
        entity_rect = self.rect()
        for rect_tile in tile_map.physics_rects_around((self.pos[0] +anim_offset[0] ,self.pos[1] +anim_offset[1]), self.size):
            tile_type = rect_tile[1].type
            if entity_rect.colliderect(rect_tile[0]):
                if tile_type.split('_')[1] != 'stairs':
                    if tile_type.split('_')[1] == 'door' and  rect_tile[1].open:
                        continue 
                    

                    if frame_movement[1] > 0:
                        self.collisions['down'] = True
                        self.on_ramp = 0
                        entity_rect.bottom = rect_tile[0].top
                    elif frame_movement[1] < 0:
                        self.collisions['up'] = True
                        entity_rect.top = rect_tile[0].bottom
                    self.velocity[1] = 0
                    self.pos[1] = entity_rect.y - anim_offset[1]
                else:
                    variant = rect_tile[1].variant.split(';')[0]
                    pos_height = 0
                    rel_x = rect_tile[0].x - entity_rect.right if variant in ('0', '2') else rect_tile[0].right - entity_rect.left

                    if variant == '0':
                        if -16 <= rel_x < 0:
                            pos_height = max(0, -rel_x - self.size[0] // 4)
                    elif variant == '2':
                        if rel_x < 0:
                            pos_height = min(tile_map.tile_size, -rel_x + (tile_map.tile_size - self.size[0] // 4))
                    elif variant == '1':
                        if rel_x > 0:
                            pos_height = max(0, rel_x - self.size[0] // 4)
                    elif variant == '3':
                        if 0 < rel_x <= tile_map.tile_size:
                            pos_height = min(tile_map.tile_size, rel_x + (tile_map.tile_size - self.size[0] // 4))

                    target_y = rect_tile[0].y + tile_map.tile_size - pos_height
                    if entity_rect.bottom > target_y:
                        self.on_ramp = 1 if variant == '0' else -1
                        entity_rect.bottom = target_y
                        self.pos[1] = entity_rect.y -anim_offset[1]
                        self.collisions['down'] = True
        
        return interactables

    def render(self, surf, offset):
        surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False),
                  (int(self.pos[0] - offset[0] + self.anim_offset[0]), int(self.pos[1] - offset[1] + self.anim_offset[1])))


"""
when you drop an item into the environment, you would need to know 
the following things: 

1. the position (it is going to be udpated, physics is applied to it)
2. the image of the weapon 
3. the 'life' of the item, as if enough time has passed the item is going to be deleted. 

when you drop an item, I guess you would have to create an item object inerited from the physics entity class  
with much simpler properties 

"""

class CollectableItem:
    def __init__(self,game,pos,item):
        self.game = game 
        self.Item = item
        self.pos = pos
        self.e_type = 'item'
        self.state = 'inanimate'
        self.image = item.image.copy()
        self.size = [self.image.get_width()//2, self.image.get_height()//2]

        self.life = 100000
        self.velocity = [0,0]


    def rect(self):
        return pygame.Rect(self.pos[0] + self.size[0]/2 ,  self.pos[1] + self.size[1] / 2 , self.size[0] , self.size[1]) 

    def update_pos(self,tile_map):
        self.life -=1
        self.velocity[1] = min(3, self.velocity[1] +0.11)

        if self.velocity[0] < 0:
            self.velocity[0] = min(self.velocity[0] + 0.21, 0)
        elif self.velocity[0] > 0:
            self.velocity[0] = max(self.velocity[0] - 0.21, 0)

        self.pos[0] += self.velocity[0]
        entity_rect  = self.rect()
        

        for rect_tile in tile_map.physics_rects_around((self.pos[0] + self.size[0] /2 ,  self.pos[1] + self.size[1] / 2), self.size):
            
            tile_type = rect_tile[1].type
        

            if entity_rect.colliderect(rect_tile[0]) and tile_type.split('_')[1] != 'stairs':
                if tile_type.split('_')[1] == 'door':
                    if  rect_tile[1].open:
                        continue
                    else:
                        # if you close the door on youself (trap door and vertical door)
                        if rect_tile[1].trap: 
                            continue 
                        else: 
                            if self.velocity[0] > 0 :
                            
                                entity_rect.right = rect_tile[0].left
                            elif self.velocity[0] < 0:
                                
                                entity_rect.left = rect_tile[0].right
                            else: 
                                if entity_rect.centerx - rect_tile[0].centerx <0:
                                    
                                    entity_rect.right = rect_tile[0].left
                                    
                                else:
                                     
                                    entity_rect.left = rect_tile[0].right 
                                
                            self.pos[0] = entity_rect.x - self.size[0] /2
                            
                else:
                    if self.velocity[0] > 0:
                    
                        entity_rect.right = rect_tile[0].left
                    elif self.velocity[0] < 0:
                        
                        entity_rect.left = rect_tile[0].right
                    else: 
                        if entity_rect.centerx -rect_tile[0].centerx <0:
                        
                            entity_rect.right = rect_tile[0].left
                            
                        else:
                 
                            entity_rect.left = rect_tile[0].right 

                    self.pos[0] = entity_rect.x - self.size[0]/2

        
        self.pos[1] += self.velocity[1]
        entity_rect = self.rect()


        for rect_tile in tile_map.physics_rects_around((self.pos[0] + self.size[0] / 2 ,  self.pos[1] + self.size[1] / 2), self.size):
            tile_type = rect_tile[1].type
            if entity_rect.colliderect(rect_tile[0]):
                if tile_type.split('_')[1] != 'stairs':
                    if tile_type.split('_')[1] == 'door' and  rect_tile[1].open:
                        continue 

                    if self.velocity[1] > 0:
                        self.on_ramp = 0
                        entity_rect.bottom = rect_tile[0].top
                    elif self.velocity[1] < 0:
                
                        entity_rect.top = rect_tile[0].bottom
                    self.velocity[1] = 0
                    self.pos[1] = entity_rect.y - self.size[1]/2
                else:
                    variant = rect_tile[1].variant.split(';')[0]
                    pos_height = 0
                    rel_x = rect_tile[0].x - entity_rect.right if variant in ('0', '2') else rect_tile[0].right - entity_rect.left

                    if variant == '0':
                        if -16 <= rel_x < 0:
                            pos_height = max(0, -rel_x - (self.size[0]/2) // 4)
                    elif variant == '2':
                        if rel_x < 0:
                            pos_height = min(tile_map.tile_size, -rel_x + (tile_map.tile_size - (self.size[0]/2) // 4))
                    elif variant == '1':
                        if rel_x > 0:
                            pos_height = max(0, rel_x - (self.size[0]/2) // 4)
                    elif variant == '3':
                        if 0 < rel_x <= tile_map.tile_size:
                            pos_height = min(tile_map.tile_size, rel_x + (tile_map.tile_size - (self.size[0]/2) // 4))

                    target_y = rect_tile[0].y + tile_map.tile_size - pos_height
                    if entity_rect.bottom > target_y:
                        self.on_ramp = 1 if variant == '0' else -1
                        entity_rect.bottom = target_y
                        self.pos[1] = entity_rect.y - self.size[1]/2

    



    def render(self,surf,offset = (0,0)):
        if self.life < 60:
            self.image.set_alpha(255 * (self.life/60))
        surf.blit(self.image, (self.pos[0] - offset[0], self.pos[1] - offset[1]))
         


    

class Enemy(PhysicsEntity):
    def __init__(self, game, pos, size, variant, hp):
        super().__init__(game, variant, pos, size)
        self.e_type = "enemy"
        self.walking = 0
        self.air_time = 0
        self.aggro = False
        self.aggro_timer = 0
        self.hit_mask = None
        self.first_hit = False
        self.alerted = False
        self.hp = hp

    def set_state(self, action):
        if action != self.state:
            self.state = action
            self.animation = self.game.enemies[self.type + '/' + self.state].copy()

    def render(self, surf, offset=(0, 0), shake=0):
        x_min = offset[0] - self.size[0]
        x_max = offset[0] + surf.get_width() + self.size[0]
        y_min = offset[1] - self.size[1]
        y_max = offset[1] + surf.get_height() + self.size[1]

        if x_min < self.pos[0] < x_max and y_min < self.pos[1] < y_max:

            #---------- outlining 
            current_image = self.animation.img()
            if self.flip:
                current_image = pygame.transform.flip(current_image, True, False)
            self.outline = pygame.mask.from_surface(current_image)

            for offset_ in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                outline_surface = self.outline.to_surface(unsetcolor=(255, 255, 255, 0), setcolor=(0, 0, 0, 255))
                surf.blit(outline_surface, (int(self.pos[0] - offset[0] + offset_[0]), int(self.pos[1] - offset[1] + offset_[1])))
            #-----------
            super().render(surf, offset=offset)

            if self.hit_mask:
                hit_surface = self.hit_mask.to_surface(unsetcolor=(0, 0, 0, 0), setcolor=(255, 255, 255, 255))
                for offset_ in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    surf.blit(hit_surface, (int(self.pos[0] - offset[0] + offset_[0]), int(self.pos[1] - offset[1] + offset_[1])))
                self.hit_mask = None


    def _handle_movment(self,tilemap,movement,check_offset):
        flip_offset = -check_offset if self.flip else check_offset + self.size[0]
        solid_check_1 = tilemap.solid_check((self.pos[0] + flip_offset, self.pos[1] + 8))
        solid_check_2 = tilemap.solid_check((self.pos[0] + flip_offset, self.pos[1] + 8 - tilemap.tile_size))
        
        if solid_check_1:
            if solid_check_2:
                if tilemap.solid_check((self.pos[0] + flip_offset, self.pos[1] + 8 - 2 * tilemap.tile_size)):
                    self.flip = not self.flip
                else:
                    self.velocity[1] = -5
            else:
                tile = tilemap.return_tile(None, (self.pos[0] + flip_offset, self.pos[1] + 8))
                if tile is None or tile.type == 'stairs':
                    movement = (movement[0] + (-1.5 if self.flip else 1.5), movement[1])
                else:
                    self.velocity[1] = -3.3
        else:
            if solid_check_2:
                if not tilemap.solid_check((self.pos[0] + flip_offset, self.pos[1] + 8 - 2 * tilemap.tile_size)):
                    self.velocity[1] = -5
                else:
                    self.flip = not self.flip
            else:
                movement = self._handle_fall(tilemap, movement, flip_offset)

        return movement
        

    
    def _handle_fall(self,tilemap,movement,flip_offset):
        for i in range(1, 6):
            if tilemap.solid_check((self.pos[0] + flip_offset, self.pos[1] + 8 + i * tilemap.tile_size)):
                movement = (movement[0] + (-1.5 if self.flip else 1.5), movement[1])
                break
        else:
            self.flip = not self.flip
        return movement

    def _update_health_bar(self,offset = (0,0)):
        self.health_bar.x = self.pos[0] + offset[0]
        self.health_bar.y = self.pos[1] + offset[1]
        self.health_bar.update(self.hp)


    def _handle_death(self):
        self.set_state('death')
        if self.animation.done:
            del self
            return True
    

    def _handle_aggro_state(self, distance, tilemap,movement, player_pos,):
        if distance < 12 * tilemap.tile_size or self.first_hit:
            self.aggro = True
        if self.hurt:
            self._handle_hurt_state(player_pos)
        else:
            self._handle_combat_state(movement, player_pos,tilemap) 

    
    def _handle_hurt_state(self, player_pos):
        pass 


    def _handle_combat_state(self, movement, player_pos):
        pass 


    def _handle_attack_state(self, player_pos):
        pass 

    def hit(self,hit_damage):
        pass 
    



    def hit(self, hit_damage):
        if self.hp > 0:
            self.hp -= hit_damage
            self.first_hit = True
            self.hurt = True
            current_image = self.animation.img()
            if self.flip:
                current_image = pygame.transform.flip(current_image, True, False)
            self.hit_mask = pygame.mask.from_surface(current_image)


"""
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
        
"""



class Wheel_bot(Enemy):
    def __init__(self, game, pos, size):
        super().__init__(game, pos, size, 'Wheel_bot', 200)
        self.weapon = self.game.weapons['laser_weapon'].copy()
        self.weapon.equip(self)
        self.wake = False
        self.charge_time = 0
        self.shooting = False
        self.hurt = False
        self.hit_mask = None
        self.health_bar = HealthBar(self.pos[0] + 3, self.pos[1] - 5, 16, 2, self.hp, True)

    def collision_rect(self):
        return pygame.Rect(self.pos[0] + 3, self.pos[1] + 1, 14, 20)

    def update(self, tilemap, player_pos, dt, movement=(0, 0)):   
        if math.dist(self.pos, player_pos) > 15 * tilemap.tile_size:
           
            self.aggro_timer = self.aggro = self.charge_time = 0
            self.first_hit = self.shooting = False

        if self.hp > 0 and self.wake:
            if self.walking:
                if self.aggro:
                    self.aggro_timer += self.aggro
                else:
                    movement = self._handle_movement(tilemap, movement)
                    self.walking = max(0, self.walking - 1)
            elif random.random() < 0.01:
                self.walking = random.randint(30, 120)
        else:
            pass

        self._update_health_bar()
        super().update_pos(tilemap, movement=movement)
        kill= False
        if self.hp <= 0:
            kill = self._handle_death()
        else:
            self._handle_awake_state(tilemap, movement,player_pos)
        if kill: return True 

    def _handle_movement(self, tilemap, movement):
        flip_offset = -8 if self.flip else 8 + self.size[0]
        solid_check_1 = tilemap.solid_check((self.pos[0] + flip_offset, self.pos[1] + 8))
        solid_check_2 = tilemap.solid_check((self.pos[0] + flip_offset, self.pos[1] + 8 - tilemap.tile_size))
        if self.aggro: 
            # follow the player:
            pass 
        else:
            if solid_check_1:
                if solid_check_2:
                    if tilemap.solid_check((self.pos[0] + flip_offset, self.pos[1] + 8 - 2 * tilemap.tile_size)):
                        self.flip = not self.flip
                    else:
                        self.velocity[1] = -5
                else:
                    tile = tilemap.return_tile(None, (self.pos[0] + flip_offset, self.pos[1] + 8))
                    if tile is None or tile.type == 'stairs':
                        movement = (movement[0] + (-1.5 if self.flip else 1.5), movement[1])
                    else:
                        self.velocity[1] = -3.3
            else:
                if solid_check_2:
                    if not tilemap.solid_check((self.pos[0] + flip_offset, self.pos[1] + 8 - 2 * tilemap.tile_size)):
                        self.velocity[1] = -5
                    else:
                        self.flip = not self.flip
                else:
                    movement = self._handle_fall(tilemap, movement, flip_offset)

            return movement



    def _handle_fall(self, tilemap, movement, flip_offset):
        for i in range(1, 6):
            if tilemap.solid_check((self.pos[0] + flip_offset, self.pos[1] + 8 + i * tilemap.tile_size)):
                movement = (movement[0] + (-1.5 if self.flip else 1.5), movement[1])
                break
        else:
            self.flip = not self.flip
        return movement

    def _update_health_bar(self):
        self.health_bar.x = self.pos[0] + 1
        self.health_bar.y = self.pos[1] - 6
        self.health_bar.update(self.hp)

    def _handle_death(self):
        self.set_state('death')
        if self.animation.done:
            del self
            return True

    def _handle_awake_state(self, tilemap,movement, player_pos):
        distance = math.dist(self.pos, player_pos)
        if not self.wake:
            if distance < 4 * tilemap.tile_size or self.first_hit:
                self.set_state('wake')
                if self.animation.done:
                    self.wake = True
            else:
                self.set_state('dormant')
        else:
            self._handle_aggro_state(distance, tilemap, movement, player_pos)

    def _handle_aggro_state(self, distance, tilemap,movement, player_pos):
        
            if (distance < 12 * tilemap.tile_size or self.first_hit):
                if line_of_sight(player_pos,self.pos,tilemap.tilemap,16):
                    self.aggro = True
                else: 
                    self.aggro  = False 
            if self.hurt:
                self._handle_hurt_state(player_pos)
            else:
                self._handle_combat_state(movement, player_pos,tilemap)

    def _handle_hurt_state(self, player_pos):
        self.shooting = False
        self.charge_time += 0.1
        self.set_state('hit')
        self.weapon.update(player_pos)
        if self.animation.done:
            self.hurt = False
            self.alerted = True

    def _handle_combat_state(self, movement, player_pos,tilemap):
        if not self.aggro:
            self.charge_time = 0
            if self.collisions['down']:
                self.air_time = 0
            if movement[0] != 0:
                self.set_state('move')
            else:
                self.set_state('idle')
        else:
            self._handle_attack_state(player_pos,tilemap)

    def _handle_attack_state(self, player_pos,tilemap):
        self.flip = player_pos[0] < self.pos[0]
        if not self.alerted:
            self.set_state('alert')
            if self.animation.done:
                self.charge_time = 0
                self.alerted = True
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
                self._handle_shooting()

    def _handle_shooting(self):
        self.set_state('shoot')
        if self.animation.frame / self.animation.img_dur == 0:
            self.weapon.load(Wheelbot_bullet(self.game, self.game.bullets['laser_weapon'].copy(), [0, 0], self.game.bullets['laser_weapon'].images[0].get_size(), 'laser_weapon'))
            self.weapon.shoot()
        if self.animation.done:
            self.shooting = False

    def hit(self, hit_damage):
        if self.hp > 0:
            self.hp -= hit_damage
            self.first_hit = True
            self.hurt = True
            self.hit_mask = pygame.mask.from_surface(self.animation.img() if not self.flip else pygame.transform.flip(self.animation.img(), True, False))

    def render(self, surf, offset):
        if self.alerted:
            self.health_bar.render(surf, offset)

        super().render(surf, (offset[0] - self.weapon.knockback[0] / 4, offset[1] - self.weapon.knockback[1] / 4))

        if self.state in {'new_charge', 'shoot', 'hit'}:
            self.weapon.render(surf, offset)


class Tormentor(Enemy):
    def __init__(self, game, pos, size, variant, hp):
        super().__init__(game, pos, size, 'tormentor', 500)



class Shotgunner(Enemy):
    def __init__(self, game, pos, size):
        super().__init__(game, pos, size, 'shotgunner', 300)




class Ball_slinger(Enemy):
    def __init__(self, game, pos, size):
        super().__init__(game, pos, size,'ball_slinger', 300)
        self.charge_time = 0
        self.hurt = False 
        self.hit_mask = None 
        self.health_bar = HealthBar(self.pos[0] + 6, self.pos[1] - 5, 16, 2, self.hp, True)
        self.attacking = False 
    
    def rect(self):
        
        return pygame.Rect(self.pos[0] +9,self.pos[1]+8,13,19)

    def collision_rect(self):
        return pygame.Rect(self.pos[0] -3,self.pos[1]+8,13,19) 

    

    def update(self,tilemap,player_pos,dt,movement = (0,0)):
   
        
        if self.hp > 0:
            if self.walking: 
                if self.aggro: 
                    self.aggro_timer += self.aggro 
                    #movement = self._handle_movement(tilemap,movement)
                else:
                    self.walking = max(0,self.walking-1)
                movement = self._handle_movement(tilemap,movement)
            elif random.random() < 0.01:
                self.walking = random.randint(30,120)
        else: 
            pass 
        
        self._update_health_bar()
        super().update_pos(tilemap,movement=movement,anim_offset= (9,8))

        kill = False 
        if self.hp <= 0 :
            kill = self._handle_death()
        else:
            pass
            self._handle_states(tilemap, movement,player_pos)
        if kill: return True 
        
    def _update_health_bar(self, offset=(0, 0)):
        self.health_bar.x = self.pos[0] +6
        self.health_bar.y = self.pos[1] - 6
        self.health_bar.update(self.hp)
    
    def _handle_states(self,tilemap,movement,player_pos):
        if math.dist(self.pos, player_pos) > 15 * tilemap.tile_size:
            # the wandering state 
            self.attacking = False 
            self.aggro = False
            
            if self.collisions['down']:
                self.air_time = 0
            if movement[0] != 0:
                self.set_state('move')
            else:
                self.set_state('idle') 
        elif math.dist(self.pos, player_pos) < 3 * tilemap.tile_size or self.attacking:
            # the attacking state 
            
            self.flip = player_pos[0] < self.pos[0]
            self.aggro = True
            self.attacking = True

            if self.charge_time == 0:
                self.set_state('transition')
                if self.animation.done: 
                    self.charge_time +=1
            elif self.charge_time ==1:
                self.set_state('charge')
                if self.animation.done: 
                    self.charge_time +=1
            else: 
                
                self.set_state('attack')
                
                if (self.animation.frame/self.animation.img_dur) == 0.0 or (self.animation.frame/self.animation.img_dur) == 4.0:
                    if (self.animation.frame/self.animation.img_dur) == 0.0:     
                        attack_particle = Particle(self.game,'ball_slinger_attack' + ('' if not self.flip else '_flipped'),(self.pos[0] + (-3 if self.flip else 40),self.pos[1]+18),'ball_slinger') 
                        self.game.particles.append(attack_particle)

                    light = PointLight((self.pos[0] + (-23 if self.flip else 60),self.pos[1]+22),power = 0.82,radius = 52,life = 3)
                    light.set_color(255,35,19)
                    light.cast_shadows = False
                    self.game.lights_engine.lights.append(light)
                    
                if self.animation.done:
                    self.attacking = False
                    self.charge_time = 0  
        else: 

            # maybe add the a star algorithm here. Maybe. 
            self.flip = player_pos[0] < self.pos[0]
            # the following state
            self.charge_time = 0
            
            self.attacking = False 
            self.aggro = True 
            self.walking = 120
            self.set_state('move')
             
        
    
    def _handle_movement(self,tilemap,movement):
        flip_offset = -8 if self.flip else 8 + self.size[0]
        solid_check_1 = tilemap.solid_check((self.pos[0] + flip_offset, self.pos[1] + 8))
        solid_check_2 = tilemap.solid_check((self.pos[0] + flip_offset, self.pos[1] + 8 - tilemap.tile_size))
        
        if self.aggro == True:
            if self.attacking: 
                
                movement = (0,0)
            else: 
                
                movement = (movement[0] + (-2.5 if self.flip else 2.5), movement[1])  
            return movement
            
        else: 
            
            self.charge_time = 0
            if solid_check_1:
                if solid_check_2:
                    if tilemap.solid_check((self.pos[0] + flip_offset, self.pos[1] + 8 - 2 * tilemap.tile_size)):
                        self.flip = not self.flip
                    else:
                        self.velocity[1] = -5
                else:
                    tile = tilemap.return_tile(None, (self.pos[0] + flip_offset, self.pos[1] + 8))
                    if tile is None or tile.type == 'stairs':
                        movement = (movement[0] + (-2.5 if self.flip else 2.5), movement[1])
                    else:
                        self.velocity[1] = -3.3
            else:
                if solid_check_2:
                    if not tilemap.solid_check((self.pos[0] + flip_offset, self.pos[1] + 8 - 2 * tilemap.tile_size)):
                        self.velocity[1] = -5
                    else:
                        self.flip = not self.flip
                else:
                    movement = self._handle_fall(tilemap, movement, flip_offset)

            return movement
            
        
    def render(self,surf,offset):
        if self.aggro:
            self.health_bar.render(surf, offset)
        super().render(surf, (offset[0], offset[1]))

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
        
        test_surf = pygame.Surface((2,2))
        test_surf.fill((180,0,0,255))
        surf.blit(test_surf,(self.pos[0]+self.size[0] + (-8 if self.flip else 8) -offset[0], self.pos[1]- offset[1]))
        
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
        #self.equipped = False 
        self.e_type = 'player'
        self.cur_weapon_node = None 

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
        self.crouch = False 
        self.on_wall = self.collisions['left'] or self.collisions['right']
        self.air_time = 0
        self.on_ladder = False 
        

        #attributes required to implement double tap 
      

        self.fatigued = False 
        self.running = False 


        self.y_inertia = 0
        self.hard_land_recovery_time = 0

        self.d_cursor_pos = [0,0]
        self.time = 0
        
        self.interactables = None
        self.nearest_collectable_item = None
        

        
    def rect(self):
        return pygame.Rect(self.pos[0]+3,self.pos[1]+1,10,15)
       
    def set_state(self,action):
        if action != self.state: 
            self.state = action 
            self.animation = self.game.general_sprites[self.type + '/' + ('holding_gun/' if self.cur_weapon_node else '') + self.state]

    def change_gun_holding_state(self):
        self.animation = self.game.general_sprites[self.type + '/' + ('holding_gun/' if self.cur_weapon_node else '') + self.state ]


    def update_pos(self, tile_map,quadtree,cursor_pos,frame_count,movement=(0, 0)):
        
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
            
        self.interactables = super().update_pos(tile_map, new_movement,anim_offset= (3,1))
        r = max(self.size) * 2

        rangeRect = Rectangle(Vector2(self.pos[0] - self.size[0]//2 - r /2 ,self.pos[1]  - r /2 ), Vector2(r,r))

        self.nearest_collectable_item = quadtree.queryRange(rangeRect,"item")

        #every frame, the stamina is increased by 0.7
       
        self.stamina = min(100, self.stamina + self.recov_rate)
        self.air_time +=1
        
        
        self.changing_done = min(2,self.change_weapon_inc + self.changing_done)
        if self.changing_done == 2:
             
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
            for offset in range(-tile_map.tile_size, tile_map.tile_size, 4):
            #(0,-tile_map.tile_size,tile_map.tile_size):
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
                if self.crouch and (self.game.player_movement[0] or self.game.player_movement[1]) :
                    self.cut_movement_input = True
                    self.set_state('slide')
                self.y_inertia = 0
                    
            else: 
                self.y_inertia = 0
                if self.state == 'land':
                    if self.animation.done == True: 
                        self.set_state('idle') 
                else: 
                    if self.crouch: 
                        self.set_state('crouch')
                        pass 
                    else: 
                        self.set_state('idle')
                
        
        
        #print(self.changing_done)
        if self.cur_weapon_node:
            self.cur_weapon_node.weapon.update(self.d_cursor_pos)
        
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
        
        knockback = (0,0) if not self.cur_weapon_node else (self.cur_weapon_node.weapon.knockback[0]/5,self.cur_weapon_node.weapon.knockback[1]/9)

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
        #print(self.changing_done)
        if self.cur_weapon_node: 
            """
            if self.changing_done == 0:
                self.cur_weapon_node.weapon.render(surf,offset,set_angle = None)
            else: 
                if self.cur_weapon_node.weapon.flipped: 
                    angles = [angle for angle in range(0,-121,-40)]  
                    
                else: 
                    angles = [angle for angle in range(120,-1,-40)]      
                        
                arm_pos_angle = angles[self.changing_done]
            """
            self.cur_weapon_node.weapon.render(surf,offset) 
            
    
    def interact(self):
        # find the interactable that is closest to the player's center position. 
        if self.nearest_collectable_item and self.state =='crouch':
            
            #now make it so that you can pick the item up. 
            
            inven_is_full = self.game.HUD.Items_list[2][1].add_item(self.nearest_collectable_item[0].Item)
            if not inven_is_full: 
                self.nearest_collectable_item[0].life =0

            
            
        if self.interactables: 
            min_distance = float('inf')
            closest_interactable = None 
            player_rect = self.rect()
            for interactable in self.interactables:
                distance = math.sqrt((interactable[0].centerx-player_rect.centerx)**2 + (interactable[0].centery-player_rect.centery)**2)
                if distance < min_distance:
                    min_distance = distance
                    closest_interactable = interactable

            closest_interactable[1].interact(self)

    
    
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
        if self.on_ladder:
            pass 
        else: 
            if self.wall_slide: 
                self.jump_count = 1
                
                if self.collisions['left']:
                    
                    self.velocity[0] =  4.2
                if self.collisions['right']:
                    
                    self.velocity[0] = -4.2
                #self.accel_up() 
                
                self.velocity[1] =-4.4
                

                air = Particle(self.game,'jump',(self.rect().centerx,self.rect().bottom), 'player',velocity=[0,0.1],frame=0)
                self.game.particles.append(air)

            if self.jump_count == 2:
                if self.state == 'jump_down':
                    self.jump_count -=2
                    #self.accel_up() 

                    self.velocity[1] = -4.4
                    
                    air = Particle(self.game,'jump',(self.rect().centerx,self.rect().bottom), 'player',velocity=[0,0.1],frame=0)
                    self.game.particles.append(air)
                else: 
                    self.jump_count -=1
                    #self.accel_up() 

                    self.velocity[1] = -4.4    
                
            elif self.jump_count ==1: 
                self.jump_count -=1
                #self.accel_up() 
                self.velocity[1] = -4.4  
                air = Particle(self.game,'jump',(self.rect().centerx,self.rect().bottom), 'player',velocity=[0,0.1],frame=0)
                self.game.particles.append(air)
            
    

    def jump_cut(self):
        #called when the player releases the jump key before maximum height. 
        if not self.on_ladder: 
            if self.velocity[1] < 0: 
                if self.velocity[1] > -4.2:
                    if self.air_time >0 and self.air_time <= 8:
                        self.velocity[1] = -1.2
                    if self.air_time >8 and self.air_time <=11 :
                        self.velocity[1] = -2.2

    
    def change_weapon(self,scroll):
        if self.cur_weapon_node: 
            if (self.cur_weapon_node.next and scroll ==1) or (self.cur_weapon_node.prev and scroll ==-1):
                self.change_scroll = scroll
                self.change_weapon_inc = True 
                if self.changing_done == 2:
                    if scroll ==1:
                        self.cur_weapon_node = self.cur_weapon_node.next
                        self.weapon_inven.curr = self.cur_weapon_node 
                        self.cur_weapon_node.weapon.equip(self)
                    else: 
                        self.cur_weapon_node = self.cur_weapon_node.prev
                        self.weapon_inven.curr = self.cur_weapon_node
                        self.cur_weapon_node.weapon.equip(self)
                         
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
        
        
        
        if self.weapon_inven.curr:
            #self.equipped = True 
            self.animation = self.game.general_sprites[self.type + '/holding_gun/' + self.state]
            #self.cur_weapon_node = self.weapon_inven.head
            self.cur_weapon_node = self.weapon_inven.curr 
            self.cur_weapon_node.weapon.equip(self)
            
            
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
        if self.cur_weapon_node: 
            if self.cur_weapon_node.weapon.rapid_firing:
                if frame % self.cur_weapon_node.weapon.fire_rate == 0:
                    """
                    test_shell_image = self.game.bullets['rifle_small'].copy()
                    test_shell = Bullet(self.game,self.cur_weapon.opening_pos,test_shell_image.get_size(),test_shell_image,'rifle_small').copy()
                    self.cur_weapon.load(test_shell)
                    """
                    
                    self.cur_weapon_node.weapon.shoot(self.time,self.d_cursor_pos) 
                   
                    #self.game.Tilemap.bullets.append(shot_bullet)
                    #self.game.bullets_on_screen.append(shot_bullet)
                    #rotate the images in the animation 
                    

            else: 
                """
                test_shell_image = self.game.bullets['rifle_small'].copy()
                test_shell = Bullet(self.game,self.cur_weapon.opening_pos,test_shell_image.get_size(),test_shell_image,'rifle_small').copy()
                self.cur_weapon.load(test_shell)
                """
                
          
                self.cur_weapon_node.weapon.shoot(self.time,self.d_cursor_pos) 
               
                #self.game.Tilemap.bullets.append(shot_bullet)
                #self.game.bullets_on_screen.append(shot_bullet)

            #add bullet drop particles and smoke particles 
                
           
    def discard_current_weapon(self):
        #here you are going to throw away your current weapon. 
        discard_pos = self.pos.copy()
        discard_pos[0] += self.size[0] // 2
        discard_pos[0] -= self.cur_weapon_node.weapon.image.get_width() if self.flip else 0
        item = CollectableItem(self.game,discard_pos,self.cur_weapon_node.weapon)
        item.velocity = [-1.5,-1.5] if self.flip else [1.5,-1.5] 
        self.game.collectable_items.append(item)
        
                    
                    
    def toggle_rapid_fire(self):
        if self.cur_weapon_node:
            self.cur_weapon_node.weapon.toggle_rapid_fire()


    def return_weapon_toggle_state(self):
        if self.cur_weapon_node:
            return self.cur_weapon_node.weapon.rapid_firing 
    
    def hit(self,hit_damage):
        self.health -= hit_damage
        self.game.screen_shake = max(hit_damage/2.2,self.game.screen_shake)
        self.hit_mask = pygame.mask.from_surface(self.animation.img() if not self.flip else pygame.transform.flip(self.animation.img(),True,False))
        

class Item(PhysicsEntity):
    def __init__(self, game,size,sprite):
        super().__init__(game, 'item', [0,0], size)
        self.sprite = sprite 
        self.e_type = 'item'

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
    def __init__(self, game, pos, size, sprite, bullet_type):
        super().__init__(game, 'bullet', pos, size)
        self.e_type = "bullet"
        self.damage = 1
        self.angle = 0
        self.sprite = sprite
        self.bullet_type = bullet_type
        self.center = [sprite.get_width() / 2, sprite.get_height() / 2]
        self.set_state('in_place')
        self.life = 50
        self.frames_flown = 50
        self.test_tile = None
        self.dead = False
        self.light = LIGHT(20, pixel_shader(20, (255, 255, 255), 1, False))
        
        
        
    def set_state(self, action):
        self.state = action

    def copy(self):
        return Bullet(self.game, self.pos, self.size, self.sprite, self.bullet_type)
    

    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.sprite.get_width(), self.sprite.get_height())

    def collision_handler(self, tilemap, rect_tile, ent_rect, dir, axis):
        rect_tile = rect_tile if isinstance(rect_tile, pygame.Rect) else rect_tile[0]

        og_end_point_vec = pygame.math.Vector2(6, 0).rotate(self.angle)
        end_point = [self.center[0] + og_end_point_vec[0] - (self.sprite.get_width() / 2 if self.velocity[0] >= 0 else 0),
                     self.center[1] + og_end_point_vec[1]]
        entry_pos = (rect_tile.left if dir else rect_tile.right, end_point[1]) if axis else (end_point[0], rect_tile.top if dir else rect_tile.bottom)
        sample_side = {(True, True): 'left', (False, True): 'right', (True, False): 'top', (False, False): 'bottom'}
        color = tilemap.return_color(rect_tile, sample_side[(dir, axis)])

        offsets = [(-1, 0), (0, 0), (1, 0)]
        for _ in range(random.randint(6, 11)):
            offset = random.choice(offsets)
            self.game.non_animated_particles.append(bullet_collide_particle(random.choice([(1, 1), (2, 1), (1, 2), (3, 1), (1, 3), (2, 2)]),
                                                                             entry_pos, (180 - self.angle) + random.randint(-88, 88), 3 + random.random(), color, tilemap))

        bullet_mask = pygame.mask.from_surface(self.sprite)
        tile_mask = pygame.mask.Mask((rect_tile.width, rect_tile.height))
        tile_mask.fill()
        offset = (ent_rect[0] - rect_tile[0], ent_rect[1] - rect_tile[1])

        if tile_mask.overlap_area(bullet_mask, offset) > 2:
            collided_tile = tilemap.return_tile(rect_tile)
            collide_particle = Particle(self.game, 'bullet_collide/rifle', end_point, 'player')
            collide_particle.animation.images = [pygame.transform.rotate(img, 180 + self.angle) for img in collide_particle.animation.copy().images]
            self.game.particles.append(collide_particle)

            if collided_tile.type != 'box':
                pass
            else:
                tilemap.tilemap.pop(f'{collided_tile.pos[0]};{collided_tile.pos[1]}')
                destroy_box_smoke = Particle(self.game, 'box_smoke', rect_tile.center, 'tile', velocity=[0, 0], frame=10)
                self.game.particles.append(destroy_box_smoke)
                collided_tile.drop_item()
            return True
        return False

    def update_pos(self, tile_map, offset=(0, 0)):
        self.collisions = {'up': False, 'down': False, 'left': False, 'right': False}
        self.frames_flown -= 1
        
        if self.frames_flown == 0:
            self.dead = True 
            return True
        
        self.pos[0] += self.velocity[0]
        self.center = [self.pos[0] + self.sprite.get_width() / 3, self.pos[1] + self.sprite.get_height() / 2]
        entity_rect = self.rect()

        for rect_tile in tile_map.physics_rects_around(self.pos, self.size):
            if entity_rect.colliderect(rect_tile[0]):
                if rect_tile[1].type.split('_')[1] == 'stairs' and rect_tile[1].variant.split(';')[0] in ['0', '1']:
                    check_rects = [pygame.Rect(rect_tile[0].left, rect_tile[0].bottom + 4, rect_tile[0].width, 4),
                                   pygame.Rect(rect_tile[0].left + 12, rect_tile[0].top, 4, 12),
                                   pygame.Rect(rect_tile[0].left + 6, rect_tile[0].top + 6, 6, 6)] if rect_tile[1].variant.split(';')[0] == '0' else \
                                  [pygame.Rect(rect_tile[0].left, rect_tile[0].bottom + 4, rect_tile[0].width, 4),
                                   pygame.Rect(rect_tile[0].left, rect_tile[0].top, 4, 12),
                                   pygame.Rect(rect_tile[0].left + 4, rect_tile[0].top + 6, 6, 6)]
                    for check_rect in check_rects:
                        if entity_rect.colliderect(check_rect):
                            if self.collision_handler(tile_map, check_rect, entity_rect, self.velocity[0] > 0, True):

                                for i in range(6):
                                    self.game.sparks.append(Spark(self.center.copy(),math.radians(random.randint(0,360)),\
                                                                random.randint(1,3),(255,255,255),0.4))
                                self.dead = True 
                                return True
                else:
                    if self.collision_handler(tile_map, rect_tile, entity_rect, self.velocity[0] > 0, True):

                        for i in range(6):
                            self.game.sparks.append(Spark(self.center.copy(),math.radians(random.randint(0,360)),\
                                                        random.randint(1,3),(255,255,255),0.4))
                        self.dead = True 
                        return True

        self.pos[1] += self.velocity[1]
        self.center = [self.pos[0] + self.sprite.get_width() / 3, self.pos[1] + self.sprite.get_height() / 2]
        entity_rect = self.rect()

        for rect_tile in tile_map.physics_rects_around(self.pos, self.size):
            if entity_rect.colliderect(rect_tile[0]):
                if rect_tile[1].type.split('_')[1] == 'stairs' and rect_tile[1].variant.split(';')[0] in ['0', '1']:
                    check_rects = [pygame.Rect(rect_tile[0].left, rect_tile[0].bottom + 4, rect_tile[0].width, 4),
                                   pygame.Rect(rect_tile[0].left + 12, rect_tile[0].top, 4, 12),
                                   pygame.Rect(rect_tile[0].left + 6, rect_tile[0].top + 6, 6, 6)] if rect_tile[1].variant.split(';')[0] == '0' else \
                                  [pygame.Rect(rect_tile[0].left, rect_tile[0].bottom + 4, rect_tile[0].width, 4),
                                   pygame.Rect(rect_tile[0].left, rect_tile[0].top, 4, 12),
                                   pygame.Rect(rect_tile[0].left + 4, rect_tile[0].top + 6, 6, 6)]
                    for check_rect in check_rects:
                        if entity_rect.colliderect(check_rect):
                            if self.collision_handler(tile_map, check_rect, entity_rect, self.velocity[1] > 0, False):
                                for i in range(6):
                                    self.game.sparks.append(Spark(self.center.copy(),math.radians(random.randint(0,360)),\
                                                                random.randint(1,3),(255,255,255),0.4))
                                self.dead = True 
                                return True
                else:
                    if self.collision_handler(tile_map, rect_tile, entity_rect, self.velocity[1] > 0, False):
                        for i in range(6):
                            self.game.sparks.append(Spark(self.center.copy(),math.radians(random.randint(0,360)),\
                                                        random.randint(1,3),(255,255,255),0.4))
                        self.dead = True 
                        return True
        return False

    def render(self, surf, offset=(0, 0)):
        #bullet_glow_mask = pygame.mask.from_surface(self.sprite)
        surf.blit(self.sprite, (self.pos[0] - offset[0], self.pos[1] - offset[1]), special_flags=pygame.BLEND_RGB_ADD)


class RocketShell():
    def __init__(self,game,pos,size,sprite,bullet_type):
        self.game = game
        self.velocity = [0,0]
        self.pos = pos
        self.sprite = sprite
        self.angle = 0
        self.frames_flown = 100
        self.dead = False
        self.size = size
        self.damage = 20
        self.bullet_type = bullet_type 

        # flame particle parameters---------------------------------
        self.flame_size = 3
        self.flame_density = 1
        self.flame_rise = 1.6
        self.flame_spread = 1
        self.flame_wind = 0
        # --------------------------------

        self.flame_spawn_pos_offsets = [(-7,0),(-7,-1),(-7,-2),(-7,1),
                                         (-8,0),(-8,-1),(-9,0),(-9,-1)]

    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.sprite.get_width(), self.sprite.get_height())
        

    
    def collision_handler(self, tilemap, rect_tile, ent_rect, dir, axis):
        rect_tile = rect_tile if isinstance(rect_tile, pygame.Rect) else rect_tile[0]

        og_end_point_vec = pygame.math.Vector2(6, 0).rotate(self.angle)
        end_point = [self.center[0] + og_end_point_vec[0] - (self.sprite.get_width() / 2 if self.velocity[0] >= 0 else 0),
                     self.center[1] + og_end_point_vec[1]]
        entry_pos = (rect_tile.left if dir else rect_tile.right, end_point[1]) if axis else (end_point[0], rect_tile.top if dir else rect_tile.bottom)
        sample_side = {(True, True): 'left', (False, True): 'right', (True, False): 'top', (False, False): 'bottom'}
        color = tilemap.return_color(rect_tile, sample_side[(dir, axis)])

        offsets = [(-1, 0), (0, 0), (1, 0)]
        for _ in range(random.randint(6, 11)):
            offset = random.choice(offsets)
            self.game.non_animated_particles.append(bullet_collide_particle(random.choice([(1, 1), (2, 1), (1, 2), (3, 1), (1, 3), (2, 2)]),
                                                                             entry_pos, (180 - self.angle) + random.randint(-88, 88), 3 + random.random(), color, tilemap))

        bullet_mask = pygame.mask.from_surface(self.sprite)
        tile_mask = pygame.mask.Mask((rect_tile.width, rect_tile.height))
        tile_mask.fill()
        offset = (ent_rect[0] - rect_tile[0], ent_rect[1] - rect_tile[1])

        if tile_mask.overlap_area(bullet_mask, offset) > 2:
            collided_tile = tilemap.return_tile(rect_tile)
            collide_particle = Particle(self.game, 'bullet_collide/rifle', end_point, 'player')
            collide_particle.animation.images = [pygame.transform.rotate(img, 180 + self.angle) for img in collide_particle.animation.copy().images]
            self.game.particles.append(collide_particle)

            if collided_tile.type != 'box':
                pass
            else:
                tilemap.tilemap.pop(f'{collided_tile.pos[0]};{collided_tile.pos[1]}')
                destroy_box_smoke = Particle(self.game, 'box_smoke', rect_tile.center, 'tile', velocity=[0, 0], frame=10)
                self.game.particles.append(destroy_box_smoke)
                collided_tile.drop_item()
            return True
        return False
    


    #change the collision particle effects on the shells 

    def update_pos(self,tile_map):
        self.frames_flown -= 1
        if self.frames_flown%2 ==0 :
            #every three frames leave a smoke particle behind - like metal slug 
            #particle = Particle(self.game,'rocket_launcher_smoke',(self.pos[0] + self.size[0] //2 , self.pos[1]+ self.size[1]//2) , 'rocket_launcher')
            self.game.particles.append(Particle(self.game,'rocket_launcher_smoke',(self.pos[0] + self.size[0] //2 , self.pos[1]+ self.size[1]//2) , 'rocket_launcher') ) 
        if self.frames_flown == 0 :
             self.dead = True 
             return True 
        
        self.pos[0] += self.velocity[0]
        self.center = [self.pos[0] + self.sprite.get_width() / 3, self.pos[1] + self.sprite.get_height() / 2]
        entity_rect = self.rect()

        for rect_tile in tile_map.physics_rects_around(self.pos, self.size):
            if entity_rect.colliderect(rect_tile[0]):
                if rect_tile[1].type.split('_')[1] == 'stairs' and rect_tile[1].variant.split(';')[0] in ['0', '1']:
                    check_rects = [pygame.Rect(rect_tile[0].left, rect_tile[0].bottom + 4, rect_tile[0].width, 4),
                                   pygame.Rect(rect_tile[0].left + 12, rect_tile[0].top, 4, 12),
                                   pygame.Rect(rect_tile[0].left + 6, rect_tile[0].top + 6, 6, 6)] if rect_tile[1].variant.split(';')[0] == '0' else \
                                  [pygame.Rect(rect_tile[0].left, rect_tile[0].bottom + 4, rect_tile[0].width, 4),
                                   pygame.Rect(rect_tile[0].left, rect_tile[0].top, 4, 12),
                                   pygame.Rect(rect_tile[0].left + 4, rect_tile[0].top + 6, 6, 6)]
                    for check_rect in check_rects:
                        if entity_rect.colliderect(check_rect):
                            if self.collision_handler(tile_map, check_rect, entity_rect, self.velocity[0] > 0, True):
                                #collision sparks get appended here 
                                
                                for i in range(20):
                                    
                                    self.game.sparks.append(Spark(self.center.copy(),math.radians(random.randint(0,360)),\
                                                                random.randint(3,6),(255,255,255),1,3))
                                self.dead = True 
                                return True
                else:
                    if self.collision_handler(tile_map, rect_tile, entity_rect, self.velocity[0] > 0, True):
                        #collision sparks get appended here
                        
                        for i in range(20):
                            self.game.sparks.append(Spark(self.center.copy(),math.radians(random.randint(0,360)),\
                                                        random.randint(3,6),(255,255,255),1,3))
                        self.dead = True 
                        return True

        self.pos[1] += self.velocity[1]
        self.center = [self.pos[0] + self.sprite.get_width() / 3, self.pos[1] + self.sprite.get_height() / 2]
        entity_rect = self.rect()

        for rect_tile in tile_map.physics_rects_around(self.pos, self.size):
            if entity_rect.colliderect(rect_tile[0]):
                if rect_tile[1].type.split('_')[1] == 'stairs' and rect_tile[1].variant.split(';')[0] in ['0', '1']:
                    check_rects = [pygame.Rect(rect_tile[0].left, rect_tile[0].bottom + 4, rect_tile[0].width, 4),
                                   pygame.Rect(rect_tile[0].left + 12, rect_tile[0].top, 4, 12),
                                   pygame.Rect(rect_tile[0].left + 6, rect_tile[0].top + 6, 6, 6)] if rect_tile[1].variant.split(';')[0] == '0' else \
                                  [pygame.Rect(rect_tile[0].left, rect_tile[0].bottom + 4, rect_tile[0].width, 4),
                                   pygame.Rect(rect_tile[0].left, rect_tile[0].top, 4, 12),
                                   pygame.Rect(rect_tile[0].left + 4, rect_tile[0].top + 6, 6, 6)]
                    for check_rect in check_rects:
                        if entity_rect.colliderect(check_rect):
                            if self.collision_handler(tile_map, check_rect, entity_rect, self.velocity[1] > 0, False):
                                #collision sparks get appended here 
                                
                                for i in range(20):
                                    self.game.sparks.append(Spark(self.center.copy(),math.radians(random.randint(0,360)),\
                                                                random.randint(3,6),(255,255,255),1,3))
                                self.dead = True 
                                return True
                else:
                    if self.collision_handler(tile_map, rect_tile, entity_rect, self.velocity[1] > 0, False):
                        #collision sparks get appended here 
                        
                        for i in range(20):
                            self.game.sparks.append(Spark(self.center.copy(),math.radians(random.randint(0,360)),\
                                                        random.randint(3,6),(255,255,255),1,3))
                        self.dead = True 
                        return True
        return False

        
        #collision detection for rocket shells 

    def render(self,surf, offset = (0,0)):
        surf.blit(self.sprite, (self.pos[0] - offset[0], self.pos[1] - offset[1]), special_flags=pygame.BLEND_RGB_ADD) 


    

class shotgun_Bullet(Bullet):
    def __init__(self, game, pos, size, sprite, bullet_type):
        super().__init__(game, pos, size, sprite, bullet_type)
        self.frames_flown = 15


    def update_pos(self, tile_map, offset=(0, 0)):
        
        return super().update_pos(tile_map, offset)

    def render(self, surf, offset= (0,0)):
        self.sprite.set_alpha(int(0* (self.frames_flown/self.life)))
       
        surf.blit(self.sprite, (self.pos[0] - offset[0], self.pos[1] - offset[1]), special_flags=pygame.BLEND_RGB_ADD)

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
       
        

       
class Wheelbot_bullet(tile_ign_Bullet):
    def __init__(self,game,animation,pos,size,type):
        self.game = game
        self.animation = animation
        self.pos = pos
        self.size = size
        self.type = type
        self.frames_flown = 300
        self.trailing_particles = []
        self.flip = False 
        self.dead = False

        #self.light = LIGHT(40,pixel_shader(40,(137,31,227),1,False))
        self.center = [self.pos[0]+self.animation.img().get_width()/2, self.pos[1] + self.animation.img().get_height()/2]

    def rect(self):
        return pygame.Rect(self.pos[0]+1,self.pos[1]+2,self.animation.img().get_width()-2,self.animation.img().get_height()-4)
    
    def update_pos(self, tile_map, offset=(0, 0)):
        self.animation.update()
        self.collisions = {'up' :False,'down' : False, 'left': False, 'right': False }
        self.frames_flown -=1 
      

        if self.frames_flown == 300:
            self.dead = True
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
            self.dead = True
            self.game.player.hit(self.damage)
            og_end_point_vec = pygame.math.Vector2((6,0))
            og_end_point_vec.rotate(self.angle)

            self.center  = [self.pos[0]+self.animation.img().get_width()/2, self.pos[1] + self.animation.img().get_height()/2]
            end_point = [self.center [0]+og_end_point_vec[0],self.center[1] + og_end_point_vec[1]] 

            
      
            

            collide_particle = Particle(self.game,'bullet_collide/laser_weapon',end_point,'Wheel_bot')
            

            self.game.particles.append(collide_particle)
            #self.game.temp_lights.append([LIGHT(40,pixel_shader(40,(137,31,227),1,False)),4,end_point])
            del self 
            return True 
            
        
    
    def render(self,surf,offset = (0,0)):
        #test_surf = pygame.Surface(self.animation.img().get_size())
        #surf.blit(test_surf,(self.pos[0]-offset[0],self.pos[1]-offset[1]))
        surf.blit(self.animation.img(),(self.pos[0]-offset[0],self.pos[1]-offset[1]),special_flags = pygame.BLEND_RGB_ADD)
        
       
            
        #here you are going to use the render function from the physics entity class. 



