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

    def _create_player_entity(self)->None: 
        self._player_state = StateInfoComponent(type='player',max_jump_count=2)
        self._player_physics = PhysicsComponent(size=(16,16),position= vec2(386,0),collision_rect=Rect(380,0,12,16),displacement_buffer=vec2(0,0))
        self._player_render = RenderComponent(self._ref_rm.animation_data_collections['player'],self._ref_rm.entity_local_vertices['player'])
        self._player_input = InputComponent()
        self._player_weapon_holder = WeaponHolderComponent()

        self._player = esper.create_entity(self._player_state,self._player_physics,self._player_render,self._player_input,self._player_weapon_holder)

       

    @property
    def player_position(self)->vec2:
        return self._player_physics.position



