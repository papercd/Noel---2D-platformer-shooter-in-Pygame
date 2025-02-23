from scripts.new_tilemap import Tilemap
from scripts.data import ITEM_SIZES,ITEM_TYPES,ITEM_PROBABILITIES
from pygame.rect import Rect
from pygame.math import Vector2 as vec2
from scripts.components import * 
import esper

from random import choice
from numpy import uint32,uint16,float64
from numpy.random import choice as npchoice

from scripts.new_resource_manager import ResourceManager

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scripts.spatial_grid import ItemSpatialGrid

class EntitiesManager:
    _instance = None
    max_dynamic_entities =  uint32(1000)
    max_item_entities = uint32(300)

    @staticmethod
    def get_instance()->"EntitiesManager":
        if EntitiesManager._instance is None: 
            EntitiesManager._instance = EntitiesManager()
        return EntitiesManager._instance

    def __init__(self)->None:
        self._ref_rm =  ResourceManager.get_instance()
        self._ref_isp : "ItemSpatialGrid" = None

        self._last_item_drop_time = array([0],dtype = float64)
        self._last_enemey_spawn_time = array([0],dtype = float64)

        self._item_drop_cooldown = array([10],dtype = float64)
        self._enemey_spawn_cooldown = array([10],dtype = float64)

        self._create_player_entity()
        self._create_item_entity_pools()

    def _create_player_entity(self)->None: 
        self._player_state = StateInfoComponent(type='player',max_jump_count=uint16(1000))
        self._player_physics = PhysicsComponent(size=(uint32(16),uint32(16)),collision_rect= Rect(0,0,12,16))
        self._player_render = AnimatedRenderComponent(self._ref_rm.animation_data_collections['player'],self._ref_rm.entity_local_vertices_bytes['player'])
        self._player_input = InputComponent()
        self._player = esper.create_entity(self._player_state,self._player_physics,self._player_render,self._player_input)


    def _create_item_entity_pools(self)->None: 
        self.item_entities_index_start = uint32(2)
        self.item_entities_index_end = uint32(302)

        self.active_items = array([0],dtype = uint32)
        self.active_item_entities = []
        self.current_item_pool_index= array([2],dtype = uint32)

        for i in range(self.max_item_entities):
            esper.create_entity(ItemInfoComponent(),PhysicsComponent(size = (uint32(16),uint32(16)), collision_rect= Rect(0,0,16,16)), StaticRenderComponent())


    def set_initial_player_position(self,pos:tuple[int32,int32])->None: 
        self._player_physics.position[0] = pos[0]
        self._player_physics.position[1] = pos[1]

        self._player_physics.collision_rect.top = int(pos[1] - self._player_physics.size[1] // 2 )
        self._player_physics.collision_rect.left = int(pos[0] ) -  6


    def set_item_spawning_positions(self,item_spawning_positions:"ItemSpatialGrid")->None:
        self._ref_isp = item_spawning_positions

    def process(self,current_game_time:float64)->None: 
        #print(self._player_physics.position)

        if current_game_time - self._last_item_drop_time[0] > self._item_drop_cooldown[0]:
            self._last_item_drop_time[0] = current_game_time
            # drop item logic 
            
            # query a spawn position for the item 
            nearby_item_spawn_positions = self._ref_isp.query(self._player_physics.position[0] - 200,self._player_physics.position[1] - 200,self._player_physics.position[0] + 200,self._player_physics.position[1] + 200)

            spawn_position = choice(nearby_item_spawn_positions)

            # activate an item entity from the pool with the fields of the chosen item data 
            item_entity = self.current_item_pool_index[0]
            item_info_comp,item_phy_comp,item_render_comp= esper.components_for_entity(item_entity)

            item_type = npchoice(ITEM_TYPES,p=ITEM_PROBABILITIES) 
            item_info_comp.type = item_type

            item_phy_comp.position[0] = spawn_position[0] * self._ref_isp.cell_size
            item_phy_comp.position[1] = spawn_position[1] * self._ref_isp.cell_size

            item_phy_comp.collision_rect.top = int(item_phy_comp.position[1] + int32(item_phy_comp.size[1]) // -2)
            item_phy_comp.collision_rect.left = int(item_phy_comp.position[0] + int32(item_phy_comp.size[0]) // -2) 

            item_render_comp.vertices_bytes = self._ref_rm.item_local_vertices_bytes[item_type]

            # add the item entity to the active item entities set
            self.active_item_entities.append(item_entity)

            self.current_item_pool_index[0] = max(2, (self.current_item_pool_index[0] + uint32(1) ) % self.item_entities_index_end )
            self.active_items[0] += uint32(1)


        if current_game_time - self._last_enemey_spawn_time[0] > self._enemey_spawn_cooldown[0]:
            self._last_enemey_spawn_time[0] = current_game_time
            # spawn enemy logic
            #print("enemy spawned")



    @property 
    def player_physics_comp(self)->PhysicsComponent:
        return self._player_physics
    
    @property
    def player_state_info_comp(self)->StateInfoComponent:
        return self._player_state
    
    @property 
    def player_render_comp(self)->AnimatedRenderComponent: 
        return self._player_render
    
    @property 
    def player_input_comp(self)->InputComponent:
        return self._player_input
    



