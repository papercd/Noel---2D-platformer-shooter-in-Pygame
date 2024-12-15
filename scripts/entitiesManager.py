from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from my_pygame_light2d.light import PointLight
    from scripts.new_tilemap import Tilemap
    from scripts.new_entities import Bullet
    from scripts.new_particles import ParticleSystem
class EntitiesManager:
    _instance = None

    @staticmethod
    def get_instance():
        if EntitiesManager._instance is None: 
            EntitiesManager._instance = EntitiesManager()
        return EntitiesManager._instance

    def __init__(self) -> None:
        self._bullet_count:int= 0
        self._bullets:list["Bullet"]= []


    def update(self,tilemap:"Tilemap",ps: "ParticleSystem",engine_lights:list["PointLight"]) ->None:
        count = self._bullet_count
        for i in range(count-1,-1,-1):
            bullet = self._bullets[i]
            kill = bullet.update(tilemap,ps,engine_lights)
            if kill: 
                self._bullet_count -=1
                del self._bullets[i]
                continue 
    
    def add_bullet(self,bullet:"Bullet") -> None: 
        self._bullet_count +=1 
        self._bullets.append(bullet)


