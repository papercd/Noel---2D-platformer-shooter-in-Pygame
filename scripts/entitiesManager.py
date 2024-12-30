from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scripts.new_entities import CollectableItem
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

        self._collectable_items_count:int = 0
        self._collectable_items:list["CollectableItem"] = []



    def update(self,tilemap:"Tilemap",ps: "ParticleSystem",engine_lights:list["PointLight"],dt:float) ->None:
        count = self._bullet_count
        for i in range(count-1,-1,-1):
            bullet = self._bullets[i]
            kill = bullet.update(tilemap,ps,engine_lights,dt)
            if kill: 
                self._bullet_count -=1
                del self._bullets[i]
                continue 

        count = self._collectable_items_count
        for i in range(count-1, -1,-1):
            item = self._collectable_items[i]
            kill = item.update(tilemap,dt)
            if kill: 
                self._collectable_items_count -=1 
                del self._collectable_items[i] 
                continue 
    
    def add_bullet(self,bullet:"Bullet") -> None: 
        self._bullet_count +=1 
        self._bullets.append(bullet)


    def add_collectable_item(self,item:"CollectableItem") ->None: 
        self._collectable_items_count += 1 
        self._collectable_items.append(item)

