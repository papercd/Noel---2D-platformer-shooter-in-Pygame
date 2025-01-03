from scripts.second_entities import Player
from scripts.new_tilemap import Tilemap
class EntitiesManager:
    _instance = None

    @staticmethod
    def get_instance()->"EntitiesManager":
        if EntitiesManager._instance is None: 
            EntitiesManager._instance = EntitiesManager()
        return EntitiesManager._instance

    def __init__(self)->None:
        self.player = Player()
        self.player._pos.x = 1184
        self.player._pos.y = 150


    def update(self,tilemap:Tilemap,dt:float)->None: 
        self.player.update(tilemap,dt)
        print(self.player._pos)
        #print(self.player._collisions['down'])