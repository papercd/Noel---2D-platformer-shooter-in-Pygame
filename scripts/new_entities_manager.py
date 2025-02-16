from scripts.new_tilemap import Tilemap
from pygame.rect import Rect
from pygame.math import Vector2 as vec2
from scripts.components import * 
import esper

from numpy import uint32,uint16

from scripts.new_resource_manager import ResourceManager

class EntitiesManager:
    _instance = None
    max_entities =  uint32(1000)

    @staticmethod
    def get_instance()->"EntitiesManager":
        if EntitiesManager._instance is None: 
            EntitiesManager._instance = EntitiesManager()
        return EntitiesManager._instance

    def __init__(self)->None:
        self._ref_rm =  ResourceManager.get_instance()
        self._create_player_entity()

    def _create_player_entity(self)->None: 
        self._player_state = StateInfoComponent(type='player',max_jump_count=uint16(1000))
        self._player_physics = PhysicsComponent(size=(uint32(16),uint32(16)),collision_rect= Rect(0,0,12,16))
        self._player_render = RenderComponent(self._ref_rm.animation_data_collections['player'],self._ref_rm.entity_local_vertices_bytes['player'])
        self._player_input = InputComponent()
        self._player = esper.create_entity(self._player_state,self._player_physics,self._player_render,self._player_input)



    """
    ,position= vec2(386,0),collision_rect=Rect(380,0,12,16),displacement_buffer=vec2(0,0)
    """

    def set_initial_player_position(self,pos:tuple[int32,int32])->None: 
        self._player_physics.position[0] = pos[0]
        self._player_physics.position[1] = pos[1]

        self._player_physics.collision_rect.top = int(pos[1])
        self._player_physics.collision_rect.left = int(pos[0])

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
    



