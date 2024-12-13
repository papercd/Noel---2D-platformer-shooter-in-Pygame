
class EntitiesManager:
    _instance = None

    @staticmethod
    def get_instance():
        if EntitiesManager._instance is None: 
            EntitiesManager._instance = EntitiesManager()
        return EntitiesManager._instance

    def __init__(self) -> None:
        self._bullets = []


    def update(self):
        pass

    
    def add_bullet(self,bullet) -> None: 
        self._bullets.append(bullet)


