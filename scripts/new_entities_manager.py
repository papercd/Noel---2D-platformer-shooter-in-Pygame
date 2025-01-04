from scripts.second_entities import Player
from scripts.new_tilemap import Tilemap
from scripts.components import * 
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


    def _create_player_entity(self)->None: 
        self._player = esper.create_entity(PhysicsComponent(),RenderComponent())

class PhysicsSystem(esper.Processor):
    def process(self)->None: 
        pass


# I guess refactor the engine code to become a Render System?
class RenderSystem(esper.Processor):
    
    def process(self)->None: 
        pass