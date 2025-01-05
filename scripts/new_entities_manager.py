from scripts.new_tilemap import Tilemap
from pygame import FRect
from pygame.math import Vector2 as vec2
from scripts.components import * 
import esper

from scripts.resourceManager import ResourceManager

class EntitiesManager:
    _instance = None

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
        self._player = esper.create_entity(PhysicsComponent(size=(16,16),position= vec2(1186,150),collision_rect=FRect(1188,152,12,14)))
                                           


    def attatch_tilemap_to_physics_system(self,tilemap:Tilemap)->None: 
        self.physics_system.attatch_tilemap(tilemap)

