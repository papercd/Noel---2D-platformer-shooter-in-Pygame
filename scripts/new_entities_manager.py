from scripts.new_tilemap import Tilemap
from pygame.rect import Rect
from pygame.math import Vector2 as vec2
from scripts.components import * 
import esper

from scripts.new_resource_manager import ResourceManager

class EntitiesManager:
    _instance = None
    max_entities = 1000

    @staticmethod
    def get_instance()->"EntitiesManager":
        if EntitiesManager._instance is None: 
            EntitiesManager._instance = EntitiesManager()
        return EntitiesManager._instance

    def __init__(self)->None:
        self._ref_rm =  ResourceManager.get_instance()
        self._create_player_entity()
        #self.physics_system = PhysicsSystem()


    def _create_player_entity(self)->None: 
        self._player = esper.create_entity(StateInfoComponent(type='player'),PhysicsComponent(size=(16,16),position= vec2(1186,0),collision_rect=Rect(1180,0,12,16),floating_point_rect_position_buffer=vec2(0,0)),
                                           RenderComponent(self._ref_rm.animation_data_collections['player'],self._ref_rm.entity_local_vertices['player']),InputComponent())
                                           

    def attatch_tilemap_to_physics_system(self,tilemap:Tilemap)->None: 
        self.physics_system.attatch_tilemap(tilemap)

