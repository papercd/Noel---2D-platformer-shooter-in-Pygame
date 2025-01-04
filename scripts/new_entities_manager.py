from scripts.second_entities import Player
from scripts.new_tilemap import Tilemap
from pygame import FRect
from pygame.rect import Rect
from pygame.math import Vector2 as vec2
from scripts.components import * 
from scripts.data import TERMINAL_VELOCITY,TileInfoDataClass
import esper

class EntitiesManager:
    _instance = None

    @staticmethod
    def get_instance()->"EntitiesManager":
        if EntitiesManager._instance is None: 
            EntitiesManager._instance = EntitiesManager()
        return EntitiesManager._instance

    def __init__(self)->None:
        self._create_player_entity()
        self.physics_system = PhysicsSystem()


    def _create_player_entity(self)->None: 
        self._player = esper.create_entity(MovementComponent(size=(16,16),position= vec2(1186,150),collision_rect=FRect(1188,152,12,14)))


    def attatch_tilemap_to_physics_system(self,tilemap:Tilemap)->None: 
        self.physics_system.attatch_tilemap(tilemap)

class PhysicsSystem(esper.Processor):
    def __init__(self)->None: 
        self._ref_tilemap:Tilemap = None

    def _handle_collision(self,movement_comp:MovementComponent,rect_tile: tuple[Rect,TileInfoDataClass],tile_size:int, dt:float,axis_bit:bool)->None: 
        if axis_bit == True: # x_axis
            pass 
        else: 
            if rect_tile[1].info.type.endswith('stairs'):
                pass 
            else: 
                if rect_tile[1].info.type.endswith('door'):
                    pass

                if movement_comp.velocity[1] >0 :
                    movement_comp.velocity[1] = GRAVITY * dt
                    movement_comp.collision_rect.bottom = rect_tile[0].top 
                elif movement_comp.velocity[1] < 0 :
                    movement_comp.velocity[1] = 0
                    movement_comp.collision_rect.top = rect_tile[0].bottom
                
                movement_comp.position[1] = movement_comp.collision_rect.y


    def attatch_tilemap(self,tilemap:Tilemap)->None: 
        self._ref_tilemap =tilemap

    def process(self,dt:float)->None: 
        for entity, physics_comp in esper.get_component(MovementComponent):
            physics_comp.flip = physics_comp.velocity[0] < 0
            
            physics_comp.velocity[0] = physics_comp.velocity[0] + physics_comp.acceleration[0] * dt
            physics_comp.velocity[1] = min(TERMINAL_VELOCITY,physics_comp.velocity[1] + physics_comp.acceleration[1] * dt)
            
            physics_comp.position[0] += physics_comp.velocity[0] * dt
            physics_comp.collision_rect.x += physics_comp.velocity[0] * dt

            for rect_tile in self._ref_tilemap.query_rect_tile_pair_around_ent(physics_comp.collision_rect.topleft,
                                                                               physics_comp.collision_rect.size):
                if physics_comp.collision_rect.colliderect(rect_tile[0]):
                    self._handle_collision(physics_comp,rect_tile,self._ref_tilemap.regular_tile_size,dt,axis_bit = False)
            

            physics_comp.position[1] += physics_comp.velocity[1] * dt 
            physics_comp.collision_rect.y += physics_comp.velocity[1] * dt

            for rect_tile in self._ref_tilemap.query_rect_tile_pair_around_ent(physics_comp.collision_rect.topleft,
                                                                               physics_comp.collision_rect.size):
                if physics_comp.collision_rect.colliderect(rect_tile[0]):
                    self._handle_collision(physics_comp,rect_tile,self._ref_tilemap.regular_tile_size,dt,axis_bit = True)
 






# I guess refactor the engine code to become a Render System?
class RenderSystem(esper.Processor):
    def process(self)->None: 
        pass