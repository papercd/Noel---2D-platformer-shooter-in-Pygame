
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
        self._player_physics = PhysicsComponent(size=(16,16),position= vec2(700,0),collision_rect=Rect(700,0,12,16),displacement_buffer=vec2(0,0))
        self._player_render = RenderComponent(self._ref_rm.animation_data_collections['player'],self._ref_rm.entity_local_vertices_bytes['player'])
        self._player_input = InputComponent()
        self._player = esper.create_entity(self._player_state,self._player_physics,self._player_render,self._player_input)

    @property 
    def player_physics_comp(self)->PhysicsComponent:
        return self._player_physics
    
    @property
    def player_state_info_comp(self)->StateInfoComponent:
        return self._player_state
    
    @property 
    def player_render_comp(self)->RenderComponent: 
        return self._player_render
    
    @property 
    def player_input_comp(self)->InputComponent:
        return self._player_input
    



