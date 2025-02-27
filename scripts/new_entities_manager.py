from scripts.new_tilemap import Tilemap
from my_pygame_light2d.light import DynamicPointLight 
from scripts.item import AK47
from scripts.data import ITEM_SIZES,ITEM_TYPES,ITEM_PROBABILITIES,MUZZLE_PARTICLE_COLORS
from pygame.rect import Rect
from pygame.math import Vector2 as vec2
from scripts.components import * 
import esper

from random import choice,randint
from numpy import uint32,uint16,float64,pi
from numpy.random import choice as npchoice,uniform
from scripts.new_resource_manager import ResourceManager

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scripts.spatial_grid import ItemSpatialGrid

class EntitiesManager:

    _instance = None
    _game_ctx = None
    max_dynamic_entities =  uint32(1000)
    max_item_entities = uint32(300)
    max_bullet_entities = uint32(200)
    max_basic_particles = uint32(300)

    @staticmethod
    def get_instance(game_ctx=None)->"EntitiesManager":
        if EntitiesManager._instance is None: 
            EntitiesManager._game_ctx = game_ctx
            EntitiesManager._instance = EntitiesManager()
        return EntitiesManager._instance

    def __init__(self)->None:
        self._ref_rm =  ResourceManager.get_instance()

        # TODO: create the particle system. 

        self._ref_ps = None
        self._ref_isp : "ItemSpatialGrid" = None

    
        self._last_bullet_shot_time = array([0],dtype= float64)
        self._last_item_drop_time = array([0],dtype = float64)
        self._last_enemey_spawn_time = array([0],dtype = float64)

        self._item_drop_cooldown = array([10],dtype = float64)
        self._enemey_spawn_cooldown = array([10],dtype = float64)

        self._create_player_entity()
        self._create_weapon_entity()
        self._create_item_entity_pool()
        self._create_bullet_entity_pool()
        self._create_basic_particle_pool()

    def _create_player_entity(self)->None: 
        self._player_state = StateInfoComponent(type='player',max_jump_count=uint16(1000))
        self._player_physics = PhysicsComponent(size=(uint32(16),uint32(16)),collision_rect= Rect(0,0,12,16))
        self._player_render = AnimatedRenderComponent(self._ref_rm.animation_data_collections['player'],self._ref_rm.entity_local_vertices_bytes['player'])
        self._player_input = InputComponent()
        self._player_weapon_holder = WeaponHolderComponent()
        self._player = esper.create_entity(self._player_physics,self._player_state,self._player_render,self._player_input,self._player_weapon_holder)

    def _create_weapon_entity(self)->None: 
        self.player_main_weapon= AK47() 
        self.player_weapon_render_comp = WeaponRenderComponent(texcoords_bytes= self._ref_rm.holding_weapon_texcoords_bytes['ak47'],vertices_bytes= self._ref_rm.holding_weapon_vertices_bytes['ak47'])
        

        

    def _create_item_entity_pool(self)->None: 
        self.item_entities_index_start = uint32(2)
        self.item_entities_index_end = uint32(301)

        self.active_items = array([0],dtype = uint32)
        self.active_item_entities = []
        self.current_item_pool_index= array([2],dtype = uint32)

        for i in range(self.max_item_entities):
            esper.create_entity(PhysicsComponent(size = (uint32(16),uint32(16)), collision_rect= Rect(0,0,16,16)),ItemInfoComponent(),StaticRenderComponent(),BasicParticleEmiiterComponent())

    def _create_bullet_entity_pool(self)->None: 
        self.bullet_entities_index_start =uint32(302)
        self.bullet_entities_index_end = uint32(501)

        self.active_bullets = array([0],dtype = uint32)
        self.active_bullet_entities = []
        self.current_bullet_pool_index = array([302],dtype =uint32)

        for i in range(self.max_bullet_entities):
            esper.create_entity(BulletPhysicsComponent(size=(uint32(16),uint32(5))),BulletRenderComponent())

    def _create_basic_particle_pool(self)->None: 
        self.basic_particle_entities_index_start = uint32(502)
        self.basic_particle_entities_index_end = uint32(801)

        self.active_basic_particles = array([0],dtype = uint32)
        self.active_basic_particle_entities = []
        self.current_basic_particle_pool_index = array([502],dtype= uint32)

        for i in range(self.max_basic_particles):
            esper.create_entity(BasicParticlePhysicsComponent())


    def set_initial_player_position(self,pos:tuple[int32,int32])->None: 
        self._player_physics.position[0] = pos[0]
        self._player_physics.position[1] = pos[1]

        self._player_physics.collision_rect.top = int(pos[1] - self._player_physics.size[1] // 2 )
        self._player_physics.collision_rect.left = int(pos[0] ) -  6


    def set_item_spawning_positions(self,item_spawning_positions:"ItemSpatialGrid")->None:
        self._ref_isp = item_spawning_positions

    
    def shoot_bullet(self,dynamic_lights_list:list[DynamicPointLight])->None: 
        if self._game_ctx['game_timer'][0]- self._last_bullet_shot_time[0] >= self.player_main_weapon.fire_rate and self.player_main_weapon.magazine[0] > uint32(0):
            # fire the weapon

            # activate a bullet entity from the pool with the fields of the rotation and velocity and direction
            bullet_entity = self.current_bullet_pool_index[0]
            bullet_phy_comp ,bullet_render_comp= esper.components_for_entity(bullet_entity)

            # center the bullet to the opening position of the weapon, set the velocity and damage and angle. 
            bullet_phy_comp.active_time[0] = float32(0)
            bullet_phy_comp.dead = False

            bullet_phy_comp.damage = self.player_main_weapon.power
            bullet_phy_comp.flip = self.weapon_holder_comp.weapon_flip 
            
            bullet_phy_comp.rotation = pi - self._player_weapon_holder.anchor_to_cursor_angle if bullet_phy_comp.flip else - self._player_weapon_holder.anchor_to_cursor_angle 

            bullet_phy_comp.position[0] = self._player_weapon_holder.opening_pos[0] - cos(self._player_weapon_holder.anchor_to_cursor_angle) * self.player_main_weapon.size[0] * 1 // 2
            bullet_phy_comp.position[1] = self._player_weapon_holder.opening_pos[1] + sin(self._player_weapon_holder.anchor_to_cursor_angle) * self.player_main_weapon.size[0] * 1 // 2

            sin_a = sin(bullet_phy_comp.rotation)
            cos_a = cos(bullet_phy_comp.rotation)

            bullet_phy_comp.velocity[0] = cos(self._player_weapon_holder.anchor_to_cursor_angle) * self.player_main_weapon.bullet_speed
            bullet_phy_comp.velocity[1] = -sin(self._player_weapon_holder.anchor_to_cursor_angle) * self.player_main_weapon.bullet_speed

            self._player_weapon_holder.knockback = - bullet_phy_comp.velocity / 170

            bullet_render_comp.bullet_model_rotate_transform[0][0] = cos_a 
            bullet_render_comp.bullet_model_rotate_transform[0][1] = -sin_a

            bullet_render_comp.bullet_model_rotate_transform[1][0] = sin_a
            bullet_render_comp.bullet_model_rotate_transform[1][1] = cos_a

            bullet_render_comp.bullet_model_flip_transform[0][0] = -2 * bullet_phy_comp.flip + 1

            self.active_bullet_entities.append(bullet_entity)

            muzzle_flash_light1 = DynamicPointLight(self._player_weapon_holder.opening_pos.copy(),power=1.0,radius=8,life = 0.05)
            muzzle_flash_light1.set_color(253,108,50)
            muzzle_flash_light1.cast_shadows = True 
            dynamic_lights_list.append(muzzle_flash_light1)

            muzzle_flash_light2 = DynamicPointLight(self._player_weapon_holder.opening_pos.copy(),power=0.8,radius=24,life = 0.05)
            muzzle_flash_light2.set_color(248,129,153)
            muzzle_flash_light2.cast_shadows = True 
            dynamic_lights_list.append(muzzle_flash_light2)

            muzzle_flash_light3 = DynamicPointLight(self._player_weapon_holder.opening_pos.copy(),power=0.7,radius=50,life = 0.05)
            muzzle_flash_light3.set_color(248,129,153)
            muzzle_flash_light3.cast_shadows = True 
            dynamic_lights_list.append(muzzle_flash_light3)

            bullet_light = DynamicPointLight(bullet_phy_comp.position,power= 1, radius = 23,illuminator = bullet_entity)
            bullet_light.set_color(245,110,150)
            dynamic_lights_list.append(bullet_light)

            # create muzzle flash particles 
            particle_count = randint(11,14)
            for _ in range(particle_count):
                basic_particle_entity = self.current_basic_particle_pool_index[0]
                particle_phy_comp = esper.component_for_entity(basic_particle_entity,BasicParticlePhysicsComponent)

                particle_phy_comp.position[0] = self._player_weapon_holder.opening_pos[0]
                particle_phy_comp.position[1] = self._player_weapon_holder.opening_pos[1]

                particle_phy_comp.speed = randint(100,340)
                particle_phy_comp.active_time[0] = float32(0)

                particle_phy_comp.color = choice(MUZZLE_PARTICLE_COLORS['ak47'])
                
                particle_phy_comp.rotation = uniform(bullet_phy_comp.rotation- pi /6 + (pi if bullet_phy_comp.flip else 0), bullet_phy_comp.rotation + pi/6 + (pi if bullet_phy_comp.flip else 0 ))
                
                particle_phy_comp.dead = False

                self.current_basic_particle_pool_index[0] = max(self.basic_particle_entities_index_start,(self.current_basic_particle_pool_index[0] + uint32(1)) % (self.basic_particle_entities_index_end + uint32(1)))

                self.active_basic_particles[0] += uint32(1)

                self.active_basic_particle_entities.append(basic_particle_entity)

            self.current_bullet_pool_index[0] = max(self.bullet_entities_index_start,(self.current_bullet_pool_index[0] + uint32(1)) % (self.bullet_entities_index_end+uint32(1))) 

            self.active_bullets[0] += uint32(1)

            self.player_main_weapon.magazine[0] -= uint32(1)
            self._last_bullet_shot_time[0] = self._game_ctx['game_timer'][0] 

    def process(self,dynamic_lights_list:list[DynamicPointLight])->None: 
        #print(self._player_physics.position)

        if self._game_ctx['game_timer'][0]- self._last_item_drop_time[0] > self._item_drop_cooldown[0]:

            self._last_item_drop_time[0] = self._game_ctx['game_timer'][0]
            # drop item logic 
            
            # query a spawn position for the item 
            nearby_item_spawn_positions = self._ref_isp.query(self._player_physics.position[0] - 200,self._player_physics.position[1] - 200,self._player_physics.position[0] + 200,self._player_physics.position[1] + 200)

            spawn_position = choice(nearby_item_spawn_positions)

            # activate an item entity from the pool with the fields of the chosen item data 
            item_entity = self.current_item_pool_index[0]
            item_phy_comp,item_info_comp,item_render_comp,basic_particle_emission_comp = esper.components_for_entity(item_entity)

            item_type = npchoice(ITEM_TYPES,p=ITEM_PROBABILITIES) 
            item_info_comp.type = item_type

            item_phy_comp.dead = False

            item_phy_comp.position[0] = spawn_position[0] * self._ref_isp.cell_size
            item_phy_comp.position[1] = spawn_position[1] * self._ref_isp.cell_size

            item_phy_comp.collision_rect.top = int(item_phy_comp.position[1] + int32(item_phy_comp.size[1]) // -2)
            item_phy_comp.collision_rect.left = int(item_phy_comp.position[0] + int32(item_phy_comp.size[0]) // -2) 

            item_render_comp.vertices_bytes = self._ref_rm.item_local_vertices_bytes[item_type]

            # add the item entity to the active item entities set
            self.active_item_entities.append(item_entity)

            item_shine_light = DynamicPointLight(item_phy_comp.position,power= 1 ,radius_decay= True,radius = 32, illuminator= item_entity)
            item_shine_light.set_color(255,255,255)
            dynamic_lights_list.append(item_shine_light)

            self.current_item_pool_index[0] = max(self.item_entities_index_start, (self.current_item_pool_index[0] + uint32(1) ) % (self.item_entities_index_end+uint32(1)) )
            self.active_items[0] += uint32(1)


        if self._game_ctx['game_timer'][0]- self._last_enemey_spawn_time[0] > self._enemey_spawn_cooldown[0]:
            self._last_enemey_spawn_time[0] = self._game_ctx['game_timer'][0]
            # spawn enemy logic
            #print("enemy spawned")


    @property 
    def weapon_holder_comp(self)->WeaponHolderComponent:
        return self._player_weapon_holder

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
    



