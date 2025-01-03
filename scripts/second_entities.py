from pygame.math import Vector2 as vec2
from pygame.rect import Rect
from scripts.new_tilemap import Tilemap
from scripts.data import GRAVITY,TERMINAL_VELOCITY,TileInfoDataClass
class PhysicsEntity: 
    def __init__(self,name:str,collision_rect:Rect,size_in_pixels:tuple[int,int])->None: 
        self._size_in_pixels = size_in_pixels 
        self._collision_rect = collision_rect
        self._name = name 

        self._on_ramp = 0 
        self._state = 'idle'
        self._flip = False

        self._collisions = {'up':False,'down':False,'left':False,'right':False}

        self._pos = vec2(0,0)
        self._velocity = vec2(0,0)
        self._acceleration = vec2(0,GRAVITY)



    def _handle_collision(self,rect_tile:tuple[Rect,TileInfoDataClass],tile_size:int, dt:float, axis_bit: bool)->None: 
        if axis_bit == True: # x axis
            if rect_tile[1].info.type.endswith('stairs'):
                return 
            if rect_tile[1].info.type.endswith('door'):
                # TODO add collision for doors once you have them 

                pass
            else: 
                if self._velocity[0] > 0:
                    self._collisions['right'] = True
                    self._collision_rect.right = rect_tile[0].left
                
                elif self._velocity[0] < 0 :
                    self._collisions['left'] = True
                    self._collision_rect.left = rect_tile[0].right
                else: 
                    if self._collision_rect.centerx - rect_tile[0].centerx <0:
                        self._collisions['right'] = True 
                        self._collision_rect.right = rect_tile[0].left
                    else: 
                        self._collisions['left']
                        self._collision_rect.left = rect_tile[0].right
                    self._velocity[0] = 0
                    self.pos[0] = self._collision_rect.x 
        else: 
            if rect_tile[1].info.type.endswith('stairs'):
                tile_relative_pos_ind = rect_tile[1].info.relative_pos_ind
                stair_push_up_offset = 0
                x_offset_from_stair_tile_edge = rect_tile[0].x - self._collision_rect.right if tile_relative_pos_ind in (0,2) \
                                                else rect_tile[0].right - self._collision_rect.left
                
                if tile_relative_pos_ind == 0 :
                    if -tile_size <= x_offset_from_stair_tile_edge < 0 :
                        stair_push_up_offset = max(0, -x_offset_from_stair_tile_edge - self._size_in_pixels[0] // 4)
                elif tile_relative_pos_ind == 2:
                    if x_offset_from_stair_tile_edge < 0:
                        stair_push_up_offset = min(tile_size, -x_offset_from_stair_tile_edge + (tile_size - self._size_in_pixels[0] //4))
                elif tile_relative_pos_ind == 1:
                    if x_offset_from_stair_tile_edge > 0:
                        stair_push_up_offset = max(0, x_offset_from_stair_tile_edge -self._size_in_pixels[0] //4)
                elif tile_relative_pos_ind == 3:
                    if 0< x_offset_from_stair_tile_edge <= tile_size: 
                        stair_push_up_offset = min(tile_size, x_offset_from_stair_tile_edge +(tile_size - self._size_in_pixels[0]//4))
                
                y_coord_in_world_space = rect_tile[0].y + tile_size - stair_push_up_offset

                if self._collision_rect.bottom > y_coord_in_world_space:
                    self._on_ramp = 1 if tile_relative_pos_ind == 0 else -1 
                    self._collision_rect.bottom = y_coord_in_world_space
                    self._pos[1] = self._collision_rect.y
                    self._collisions['down'] = True
                    self._velocity[1] = 0
            else: 
                if rect_tile[1].info.type.endswith('door'):
                    # TODO: handle collisions with doors once you have them 
                    pass 

                if self._velocity[1] > 0 :
                    self._collisions['down'] = True 
                    self._velocity[1] = GRAVITY * dt
                    self._on_ramp = 0 
                    self._collision_rect.bottom = rect_tile[0].top
                elif self._velocity[1] < 0:
                    self._collisions['up'] = True 
                    self._velocity[1] = 0 
                    self._collision_rect.top = rect_tile[0].bottom
                self.pos[1] = self._collision_rect.y 
                     






    def set_state(self,state:str)->None: 
        if state != self._state:
            self._state = state 
        

    def update(self,tilemap:"Tilemap",dt:float)->None: 
        
        self._flip = self._velocity[0] < 0

        self._velocity[0] = self._velocity[0] + self._acceleration[0] * dt 
        self._velocity[1] = min(TERMINAL_VELOCITY,self._velocity[1] + self._acceleration[1] *dt) 

        self._pos[0] += self._velocity[0] * dt
        self._collision_rect.x += self._velocity[0] * dt

        for rect_tile in tilemap.query_rect_tile_pair_around_ent(self._collision_rect.topleft,self._collision_rect.size):
            if self._collision_rect.colliderect(rect_tile[0]):
                self._handle_collision(rect_tile,tilemap.regular_tile_size,dt,axis_bit = False)

        self._pos[1] += self._velocity[1] * dt 
        self._collision_rect.y += self._velocity[1] * dt 
         

        for rect_tile in tilemap.query_rect_tile_pair_around_ent(self._collision_rect.topleft,self._collision_rect.size):
            if self._collision_rect.colliderect(rect_tile[0]):
                self._handle_collision(rect_tile,tilemap.regular_tile_size,dt,axis_bit= True)



class Player(PhysicsEntity):
    def __init__(self)-> None:
        super().__init__('player',Rect(2,2,12,14), (16,16))