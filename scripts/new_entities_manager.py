from scripts.second_entities import Player

class EntitiesManager:
    _instance = None

    @staticmethod
    def get_instance()->"EntitiesManager":
        if EntitiesManager._instance is None: 
            EntitiesManager._instance = EntitiesManager()
        return EntitiesManager._instance

    def __init__(self)->None:
        self.player = Player()