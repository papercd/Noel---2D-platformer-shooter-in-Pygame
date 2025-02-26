import esper
from scripts.mandelae_hud import HUD
from scripts.game_state import GameState
from scripts.game_state import GameState
from scripts.data import TERMINAL_VELOCITY,GRAVITY,ENTITIES_ACCELERATION,ENTITIES_JUMP_SPEED,ENTITIES_MAX_HORIZONTAL_SPEED,HORIZONTAL_DECELERATION,WALL_SLIDE_CAP_VELOCITY,SPRINT_FACTOR,ITEM_SIZES,\
                        PLAYER_LEFT_AND_RIGHT_ANCHOR_OFFSETS,BULLET_MAX_STEP
from pygame.rect import Rect
from pygame.mouse import get_pos
from scripts.new_resource_manager import ResourceManager
from scripts.new_entities_manager import EntitiesManager 
from scripts.components import PhysicsComponent,AnimatedRenderComponent, StateInfoComponent,InputComponent,WeaponHolderComponent,BulletPhysicsComponent,StaticRenderComponent
from my_pygame_light2d.double_buffer import DoubleBuffer
from my_pygame_light2d.color import normalize_color_arguments
from scripts.layer import Layer_
from scripts.item import Item,AK47,FlameThrower
from scripts.lists import interpolatedLightNode
import pygame
from moderngl import NEAREST,LINEAR,BLEND,Texture,Framebuffer
from OpenGL.GL import glUniformBlockBinding,glGetUniformBlockIndex,glViewport
from math import sqrt,dist,degrees,pi
from random import choice

import numpy as np

from numpy import float32,uint16,uint32,int32,uint8,array, cos,sin

from typing import TYPE_CHECKING 


if TYPE_CHECKING: 
    from my_pygame_light2d.light import DynamicPointLight,PointLight
    from my_pygame_light2d.hull import Hull
    from scripts.background import Background
    from scripts.data import TileInfo, TileInfoDataClass
    from moderngl import Context
    from scripts.new_tilemap import Tilemap
    from scripts.mandelae_hud import HUD 

class PhysicsSystem(esper.Processor):
    def __init__(self,game_ctx)->None: 
        
        self._ref_hud: "HUD" = None
        self._ref_game_ctx = game_ctx
        self._ref_tilemap:"Tilemap" = None
        self._ref_em : EntitiesManager = EntitiesManager.get_instance()
        self._collision_rect_buffer = Rect(0,0,1,1)


    def _process_regular_tile_y_collision(self,physics_comp:PhysicsComponent,state_info_comp:StateInfoComponent,
                                          rect_tile:tuple["Rect","TileInfoDataClass"],dt:float32)->None: 
        if physics_comp.velocity[1] > float32(0):
            state_info_comp.collide_bottom = True
            physics_comp.position[1] = rect_tile[0].top + int32(physics_comp.size[1]) // -2
            physics_comp.collision_rect.bottom = rect_tile[0].top 
            physics_comp.velocity[1] =GRAVITY * dt 

            if state_info_comp.dynamic : state_info_comp.jump_count[0] = uint16(0)

        elif physics_comp.velocity[1] < float32(0):
            state_info_comp.collide_top = True
            physics_comp.position[1] = rect_tile[0].bottom + int32(physics_comp.size[1]) // 2
            physics_comp.collision_rect.top = rect_tile[0].bottom
            physics_comp.velocity[1] = float32(0)
        physics_comp.displacement_buffer[1] = float32(0)


    def _process_regular_tile_x_collision(self,state_info_comp:StateInfoComponent,physics_comp:PhysicsComponent,
                                          rect_tile:tuple["Rect","TileInfoDataClass"])->None: 
        if physics_comp.velocity[0] > float32(0):
            state_info_comp.collide_right = True
            physics_comp.collision_rect.right = rect_tile[0].left 
            physics_comp.position[0]  = int32(physics_comp.collision_rect.centerx) 
            
        elif physics_comp.velocity[0] < float32(0) :
            state_info_comp.collide_left = True 
            physics_comp.collision_rect.left = rect_tile[0].right 
            physics_comp.position[0] = int32(physics_comp.collision_rect.centerx) 
        else: 
            if physics_comp.position[0] > int32(rect_tile[0].centerx):
                state_info_comp.collide_left = True
                physics_comp.collision_rect.left = rect_tile[0].right
                physics_comp.position[0] = int32(physics_comp.collision_rect.centerx)
            else: 
                state_info_comp.collide_right = True
                physics_comp.collision_rect.right = rect_tile[0].left
                physics_comp.position[0] = int32(physics_comp.collision_rect.centerx)
        physics_comp.displacement_buffer[0] = float32(0)



    def _handle_tile_collision(self,physics_comp:PhysicsComponent,state_info_comp:StateInfoComponent,rect_tile:tuple["Rect","TileInfoDataClass"],
                          tile_size:int32,dt:float32,axis_bit:bool)->None: 

    
        rel_pos_ind= rect_tile[1].info.relative_pos_ind 

        if axis_bit == False: # x_axis
                state_info_comp.collide_left = False
                state_info_comp.collide_right = False
            
                if rect_tile[1].info.type.endswith('stairs'): 
                    if rel_pos_ind in (2,3):
                        self._process_regular_tile_x_collision(state_info_comp,physics_comp,rect_tile)
                else: 
                    if rect_tile[1].info.type.endswith('door'):
                        pass
                    else: 
                        self._process_regular_tile_x_collision(state_info_comp,physics_comp,rect_tile)

        else:  # y_axis: 
                state_info_comp.collide_bottom = False 
                state_info_comp.collide_top = False

                if rect_tile[1].info.type.endswith('stairs') and rel_pos_ind in (0,1):
                    relative_height_from_stair_base = 0
                    if rel_pos_ind == 0 :
                        relative_x_from_stair_left = physics_comp.collision_rect.right - rect_tile[0].left 
                        if 0 <= relative_x_from_stair_left <= tile_size:
                            relative_height_from_stair_base =relative_x_from_stair_left 
                    else:
                        relative_x_from_stair_right =rect_tile[0].right - physics_comp.collision_rect.left 
                        if 0 <= relative_x_from_stair_right <= tile_size:
                            relative_height_from_stair_base = relative_x_from_stair_right
                    
                    new_collision_rect_bottom = rect_tile[0].bottom - relative_height_from_stair_base

                    if physics_comp.collision_rect.bottom > new_collision_rect_bottom:
                        physics_comp.collision_rect.bottom = new_collision_rect_bottom
                        physics_comp.position[1] = physics_comp.collision_rect.bottom + int32(physics_comp.size[1]) // -2 
                        physics_comp.velocity[1] = GRAVITY * dt
                        if state_info_comp.dynamic: state_info_comp.jump_count[0] = uint16(0) 
                        state_info_comp.collide_bottom = True
                        physics_comp.displacement_buffer[1] = float32(0)

                else: 
                    if rect_tile[1].info.type.endswith('door'):
                        pass
                    
                    self._process_regular_tile_y_collision(physics_comp,state_info_comp,rect_tile,dt)


    def _process_common_physics_updates(self,physics_comp: PhysicsComponent,state_info_comp:StateInfoComponent,dt:float32,sprinting:bool = False)->None: 

        physics_comp.prev_transform = physics_comp.transform

        # apply deceleration to horizontal velocity
        if physics_comp.velocity[0] > float32(0):
            physics_comp.velocity[0] = max(float32(0),physics_comp.velocity[0] - HORIZONTAL_DECELERATION * dt)
        elif physics_comp.velocity[0] < float32(0):
            physics_comp.velocity[0] = min(float32(0),physics_comp.velocity[0] + HORIZONTAL_DECELERATION * dt)

        sprint_factor = SPRINT_FACTOR if sprinting else float32(1)

        # clamp velocity to maximums
        physics_comp.velocity[0] = max(-ENTITIES_MAX_HORIZONTAL_SPEED[state_info_comp.type]*sprint_factor, min(ENTITIES_MAX_HORIZONTAL_SPEED[state_info_comp.type]*sprint_factor,physics_comp.velocity[0] + physics_comp.acceleration[0] * dt * sprint_factor))
        physics_comp.velocity[1] = min(TERMINAL_VELOCITY,physics_comp.velocity[1] + physics_comp.acceleration[1]   * dt ) if not state_info_comp.mouse_hold else GRAVITY * dt

        physics_comp.displacement_buffer[0] += physics_comp.velocity[0] * dt
        physics_comp.displacement_buffer[1] += physics_comp.velocity[1] * dt if not state_info_comp.mouse_hold else float32(0)

        displacement = 0
        collided = False 

        if physics_comp.displacement_buffer[0] >= float32(1.0) or physics_comp.displacement_buffer[0] <= float32(-1.0):
            displacement = int32(physics_comp.displacement_buffer[0]) 

            physics_comp.collision_rect.x += displacement
            physics_comp.position[0] += displacement 

            physics_comp.displacement_buffer[0] -= displacement

        for rect_tile in self._ref_tilemap.query_rect_tile_pair_around_ent((physics_comp.position[0]+ int32(physics_comp.size[0]) // -2 ,physics_comp.position[1] + int32(physics_comp.size[1]) //-2),\
                                                                           physics_comp.size,dir = physics_comp.flip):
            if physics_comp.collision_rect.colliderect(rect_tile[0]):
                collided = True 
                self._handle_tile_collision(physics_comp,state_info_comp,rect_tile,self._ref_tilemap.tile_size,dt,False)
        
        if not collided :
            state_info_comp.collide_left = False
            state_info_comp.collide_right = False 

        if physics_comp.displacement_buffer[1] >= 1.0 or physics_comp.displacement_buffer[1] <= -1.0:
            displacement = int32(physics_comp.displacement_buffer[1]) 
            physics_comp.collision_rect.y += displacement
            physics_comp.position[1] += displacement 

            physics_comp.displacement_buffer[1] -= displacement

        collided = False

        for rect_tile in self._ref_tilemap.query_rect_tile_pair_around_ent((physics_comp.position[0]- physics_comp.size[0] //2 ,physics_comp.position[1] - physics_comp.size[1] //2),\
                                                                           physics_comp.size,dir = physics_comp.flip):
            if physics_comp.collision_rect.colliderect(rect_tile[0]):
                collided = True
                self._handle_tile_collision(physics_comp,state_info_comp,rect_tile,self._ref_tilemap.tile_size,dt,True)

        if not collided :
            state_info_comp.collide_bottom = False 
            state_info_comp.collide_top = False



    def _process_physics_updates_for_player(self,input_comp:InputComponent,weapon_holder_comp:WeaponHolderComponent,physics_comp:PhysicsComponent
                                            ,state_info_comp:StateInfoComponent,dt:float32)->None:
        
        
        direction = int32(input_comp.right - input_comp.left)
        if direction != int32(0):
            physics_comp.flip = direction == int32(-1)
        
        physics_comp.acceleration[0] = float32(ENTITIES_ACCELERATION[state_info_comp.type] * direction)
        if input_comp.up and state_info_comp.jump_count[0] < state_info_comp.max_jump_count:
            physics_comp.velocity[1] = float32(-ENTITIES_JUMP_SPEED[state_info_comp.type])
        
            # to stop the player from jumping infinitely
            input_comp.up = False
            state_info_comp.jump_count[0] += uint16(1)

        self._process_common_physics_updates(physics_comp, state_info_comp,dt,sprinting = input_comp.shift)

        if (state_info_comp.collide_left or state_info_comp.collide_right) and not state_info_comp.collide_bottom:
            physics_comp.velocity[1] = min(physics_comp.velocity[1] , WALL_SLIDE_CAP_VELOCITY)

        camera_offset = self._ref_game_ctx['camera_offset']

        # update weapon holder component 
        weapon_holder_comp.weapon_flip = physics_comp.position[0] - camera_offset[0] > self._ref_hud.cursor.topleft[0]
        weapon_holder_comp.weapon_anchor_pos_offset_from_center = PLAYER_LEFT_AND_RIGHT_ANCHOR_OFFSETS[physics_comp.flip][state_info_comp.curr_state][weapon_holder_comp.weapon_flip]
        weapon_holder_comp.anchor_to_cursor_angle = self._ref_hud.cursor.get_angle_from_point((physics_comp.position[0] - camera_offset[0] + weapon_holder_comp.weapon_anchor_pos_offset_from_center[0],
                                                                                               physics_comp.position[1] - camera_offset[1] + weapon_holder_comp.weapon_anchor_pos_offset_from_center[1]))
        weapon_holder_comp.opening_pos[0] = physics_comp.position[0] + weapon_holder_comp.weapon_anchor_pos_offset_from_center[0] + cos(weapon_holder_comp.anchor_to_cursor_angle) * self._ref_em.player_main_weapon.size[0] 
        weapon_holder_comp.opening_pos[1] = physics_comp.position[1] + weapon_holder_comp.weapon_anchor_pos_offset_from_center[1] - sin(weapon_holder_comp.anchor_to_cursor_angle) * self._ref_em.player_main_weapon.size[0] 

        if weapon_holder_comp.knockback[0] < float32(0):
            weapon_holder_comp.knockback[0] = min(weapon_holder_comp.knockback[0] + float32(100) * dt, float32(0))
        elif weapon_holder_comp.knockback[0] > float32(0): 
            weapon_holder_comp.knockback[0] = max(weapon_holder_comp.knockback[0] - float32(100) * dt, float32(0))

        if weapon_holder_comp.knockback[1] < float32(0):
            weapon_holder_comp.knockback[1] = min(weapon_holder_comp.knockback[1] + float32(100) * dt, float32(0))
        elif weapon_holder_comp.knockback[1] > float32(0): 
            weapon_holder_comp.knockback[1] = max(weapon_holder_comp.knockback[1] - float32(100) * dt, float32(0))

        #print(weapon_holder_comp.opening_pos, physics_comp.position)

        

    def _process_non_player_physics_updates(self,physics_comp:PhysicsComponent,state_info_comp:StateInfoComponent,dt:float)->None:
        physics_comp.flip = physics_comp.velocity[0] < 0
        self._process_common_physics_updates(physics_comp,state_info_comp,dt)

 
    def _process_physics_for_bullet(self,bullet_phy_comp:BulletPhysicsComponent,dt:float32)->None: 


        if bullet_phy_comp.active_time[0] >0:

                bullet_phy_comp.prev_translate_transform = bullet_phy_comp.translate_transform

                bullet_phy_comp.displacement_buffer[0] += bullet_phy_comp.velocity[0] * dt 
              
                accum_step = 0

                while abs(bullet_phy_comp.displacement_buffer[0]) >= BULLET_MAX_STEP:
                    step = int32(BULLET_MAX_STEP if bullet_phy_comp.displacement_buffer[0] > 0 else -BULLET_MAX_STEP)
                    bullet_phy_comp.position[0] += step 
                    bullet_phy_comp.displacement_buffer[0] -= step 
                    accum_step += step    
                    for rect_tile in self._ref_tilemap.query_rect_tile_pair_around_ent((bullet_phy_comp.position[0],bullet_phy_comp.position[1]),(bullet_phy_comp.size[0],bullet_phy_comp.size[1]),dir = bullet_phy_comp.flip):
                        if rect_tile[0].collidepoint(bullet_phy_comp.position):
                            return True
                bullet_phy_comp.displacement_buffer[1] += bullet_phy_comp.velocity[1] * dt 

                accum_step = 0

                while abs(bullet_phy_comp.displacement_buffer[1]) >= BULLET_MAX_STEP: 
                    step = int32(BULLET_MAX_STEP if bullet_phy_comp.displacement_buffer[1] > 0 else -BULLET_MAX_STEP)
                    bullet_phy_comp.position[1] += step 
                    bullet_phy_comp.displacement_buffer[1] -= step 
                    accum_step += step
                    for rect_tile in self._ref_tilemap.query_rect_tile_pair_around_ent((bullet_phy_comp.position[0],bullet_phy_comp.position[1]),(bullet_phy_comp.size[0],bullet_phy_comp.size[1]),dir = bullet_phy_comp.flip) :
                        if rect_tile[0].collidepoint(bullet_phy_comp.position):
                            return True
        return False


    def attatch_tilemap(self,tilemap:"Tilemap")->None: 
        self._ref_tilemap =tilemap
    
    def attatch_hud(self,hud:"HUD")->None: 
        self._ref_hud = hud
    
    def process(self,dt:float32)->None: 
        # process physics for player entity, which has an input component while the rest of the entities don't.
        #player,(player_input_comp,player_state_info_comp,player_physics_comp) = esper.get_components(InputComponent,StateInfoComponent,PhysicsComponent)[0]

        for entity, (state_info_comp,physics_comp) in esper.get_components(StateInfoComponent,PhysicsComponent):
            if state_info_comp.type == "player":
                self._process_physics_updates_for_player(self._ref_em.player_input_comp,self._ref_em._player_weapon_holder,physics_comp,state_info_comp,dt)
            else: 
                self._process_non_player_physics_updates(physics_comp,state_info_comp,dt)

        # update items 

        for i in range(self._ref_em.active_items[0] -1,-1,-1):
            entity = self._ref_em.active_item_entities[i]
            item_info_comp,item_phy_comp,static_render_comp = esper.components_for_entity(entity)

            if item_info_comp.active_time[0] < float32(9):
                self._process_non_player_physics_updates(item_phy_comp,item_info_comp,dt)
                item_info_comp.active_time[0] += dt
            else: 
                item_info_comp.active_time[0] = float32(0)
                self._ref_em.active_items[0] -= uint32(1)
                self._ref_em.active_item_entities.pop(i)

        # update bullets 
        
        for i in range(self._ref_em.active_bullets[0] -1 ,-1,-1):
            bullet_entity = self._ref_em.active_bullet_entities[i]
            
            bullet_phy_comp = esper.component_for_entity(bullet_entity,BulletPhysicsComponent)
            
            collided = False

            if bullet_phy_comp.active_time[0] < float32(1.6):
                collided = self._process_physics_for_bullet(bullet_phy_comp,dt)
                bullet_phy_comp.active_time[0] += dt 
            else: 
                bullet_phy_comp.active_time[0] = float32(0)
                self._ref_em.active_bullets[0] -=uint32(1) 
                self._ref_em.active_bullet_entities.pop(i)

            if collided:
                bullet_phy_comp.active_time[0] = float32(0)
                self._ref_em.active_bullets[0] -=uint32(1) 
                self._ref_em.active_bullet_entities.pop(i)


            



class ParticleSystem(esper.Processor):
    pass


class RenderSystem(esper.Processor):


    def __init__(self,gl_ctx:"Context",game_context)->None: 
        self._gl_ctx = gl_ctx

        # references 
        self._ref_em = EntitiesManager.get_instance()
        self._ref_rm = ResourceManager.get_instance()
        self._ref_tilemap: "Tilemap" = None
        self._ref_background: "Background" = None
        self._ref_background_vertices_buffer : "Context.buffer" = None 
        self._ref_hud : "HUD" =None
        
        # Initialize members 
        self._background_panels:int32= int32(3)

        self._game_ctx = game_context
        
        self._ambient_light_RGBA = array([.25,.25,.25,.25],dtype= float32)

        self._active_static_lights : list["PointLight"] = []
        self.dynamic_lights:list["DynamicPointLight"] = []
        self.hulls:list["Hull"] = []

        self._prev_hull_query_player_pos = array([0,0],dtype = int32) 

        self._prev_hull_query_camera_scroll = array([0,0],dtype = int32)

        self._prev_lights_query_camera_scroll = array([0,0],dtype = int32)

        self._shadow_blur_radius = uint8(5)
        self._max_hull_count = uint16(512) 

        self._projection_matrix = np.array([
            [2. / self._game_ctx['true_res'][0] , 0 , -1.],
            [0, -2. / self._game_ctx['true_res'][1]  ,  1.],
            [0,0,1.]
        ],dtype=np.float32)

        self._view_matrix = np.array([
            [1,0,0],
            [0,1,0],
            [0,0,1]
        ],dtype=np.float32)


        self._create_programs()
        self._create_ssbos()
        self._create_frame_buffers()
        self._create_screen_vertex_buffers()
        self._create_entity_vertex_buffers()
        self._create_weapon_vertex_buffers()
        self._create_bullet_vertex_buffers()
        self._create_item_vertex_buffers()

    def _load_shader_srcs(self,vertex_src_path:str,fragment_src_path:str)->tuple[str,str]:
        try:
            with open(vertex_src_path,encoding= 'utf-8') as file: 
                vertex_src = file.read()
        except:
           print("vertex shader source file could not be opened.")
        try:
            with open(fragment_src_path,encoding= 'utf-8') as file: 
                fragment_src = file.read()
        except:
            print("vertex shader source file could not be opened.")

        return (vertex_src,fragment_src)
    

    def _load_shader_src(self,shader_src_path:str)->str: 
        try: 
            with open(shader_src_path,encoding='utf-8') as file: 
                src = file.read()
        except:
            print("shader source file could not be opened.")

        return src

    def _create_programs(self)->None: 
        vertex_src,fragment_src = self._load_shader_srcs('my_pygame_light2d/vertex.glsl',
                                                         'my_pygame_light2d/fragment_draw.glsl')
    
        tile_draw_vert_src,tile_draw_frag_src = self._load_shader_srcs('my_pygame_light2d/tile_vert.glsl',
                                                                       'my_pygame_light2d/tile_frag.glsl')

        entities_draw_vert_src,entities_draw_frag_src = self._load_shader_srcs('my_pygame_light2d/entity_draw_vert.glsl',
                                                                                 'my_pygame_light2d/entity_draw_frag.glsl')
        
        cursor_draw_vert_src,cursor_draw_frag_src = self._load_shader_srcs('my_pygame_light2d/cursor_draw_vert.glsl',
                                                                           'my_pygame_light2d/cursor_draw_frag.glsl')
        
        bar_draw_vert_src,bar_draw_frag_src = self._load_shader_srcs('my_pygame_light2d/vertex_bar.glsl',
                                                                     'my_pygame_light2d/fragment_bar.glsl')

        light_frag_src = self._load_shader_src('my_pygame_light2d/fragment_light.glsl')

        blur_frag_src = self._load_shader_src('my_pygame_light2d/fragment_blur.glsl')

        mask_frag_src =  self._load_shader_src('my_pygame_light2d/fragment_mask.glsl')

        hidden_draw_frag_src = self._load_shader_src('my_pygame_light2d/fragment_hidden_ui_draw.glsl')

        self._entity_draw_prog = self._gl_ctx.program(vertex_shader = entities_draw_vert_src,
                                                    fragment_shader = entities_draw_frag_src)
        
        self._to_screen_draw_prog = self._gl_ctx.program(vertex_shader =vertex_src,
                                                                 fragment_shader= fragment_src)
        self._tile_draw_prog = self._gl_ctx.program(vertex_shader=tile_draw_vert_src,
                                                         fragment_shader= tile_draw_frag_src)
        
        self._opaque_ui_draw_prog = self._gl_ctx.program(vertex_shader=vertex_src,
                                                      fragment_shader= fragment_src)
        
        self._hidden_ui_draw_prog = self._gl_ctx.program(vertex_shader= vertex_src,
                                                      fragment_shader=hidden_draw_frag_src)

        self._prog_bar_draw = self._gl_ctx.program(vertex_shader= bar_draw_vert_src,   
                                                fragment_shader= bar_draw_frag_src)
        
        self._prog_mask = self._gl_ctx.program(vertex_shader= vertex_src,
                                            fragment_shader=mask_frag_src)
        
        self._prog_cursor_draw = self._gl_ctx.program(vertex_shader =cursor_draw_vert_src,
                                                   fragment_shader= cursor_draw_frag_src )

        self._prog_light = self._gl_ctx.program(vertex_shader= vertex_src,
                                             fragment_shader= light_frag_src )
        
        self._prog_blur = self._gl_ctx.program(vertex_shader= vertex_src,
                                            fragment_shader= blur_frag_src)
        
    
    def _create_ssbos(self)->None: 
        prog_glo = self._prog_light.glo

        blockIndex = glGetUniformBlockIndex(prog_glo, 'hullVSSBO')
        glUniformBlockBinding(prog_glo, blockIndex, 1)

        blockIndex = glGetUniformBlockIndex(prog_glo, 'hullIndSSBO')
        glUniformBlockBinding(prog_glo, blockIndex, 2)


        # Create SSBOs``
        self._ssbo_v = self._gl_ctx.buffer(reserve=4*8*self._max_hull_count)
        self._ssbo_v.bind_to_uniform_block(1)
        self._ssbo_ind = self._gl_ctx.buffer(reserve=4*self._max_hull_count)
        self._ssbo_ind.bind_to_uniform_block(2)


    
    def _create_frame_buffers(self)->None: 
        # background framebufffer
        self._tex_bg = self._gl_ctx.texture(self._game_ctx['true_res'], components=4)
        self._tex_bg.filter = (NEAREST, NEAREST)
        self._fbo_bg = self._gl_ctx.framebuffer([self._tex_bg])

        # foreground framebuffer
        self._tex_fg = self._gl_ctx.texture(self._game_ctx['true_res'], components=4)
        self._tex_fg.filter = (NEAREST, NEAREST)
        self._fbo_fg = self._gl_ctx.framebuffer([self._tex_fg])

        # set wrapping settings for buffers 
        self._tex_bg.repeat_x = False
        self._tex_bg.repeat_y = False 
        self._tex_fg.repeat_x = False
        self._tex_fg.repeat_y = False 


    def _create_screen_vertex_buffers(self)->None: 
        screen_vertices = np.array([(-1.0, 1.0), (1.0, 1.0), (-1.0, -1.0),
                                    (-1.0, -1.0), (1.0, 1.0), (1.0, -1.0)], dtype=np.float32)
        screen_tex_coords = np.array([(0.0, 1.0), (1.0, 1.0), (0.0, 0.0),
                                      (0.0, 0.0), (1.0, 1.0), (1.0, 0.0)], dtype=np.float32)

        screen_vertex_data = np.hstack([screen_vertices, screen_tex_coords])
        screen_vbo = self._gl_ctx.buffer(screen_vertex_data) 
  

        self._vao_light = self._gl_ctx.vertex_array(
            self._prog_light,
            [
                (screen_vbo, '2f 2f', 'vertexPos', 'vertexTexCoord')
            ]
        )

        self._vao_blur = self._gl_ctx.vertex_array(
            self._prog_blur,
            [
                (screen_vbo, '2f 2f' , 'vertexPos' , 'vertexTexCoord')
            ]
        )

        self._vao_mask = self._gl_ctx.vertex_array(
            self._prog_mask,
            [
                (screen_vbo, '2f 2f' ,'vertexPos','vertexTexCoord')
            ]
        )

        self._vao_to_screen_draw = self._gl_ctx.vertex_array(
            self._to_screen_draw_prog,
            [
                (screen_vbo, '2f 2f', 'vertexPos', 'vertexTexCoord'),
            ]
        )


    def _create_entity_vertex_buffers(self)->None:
        local_space_vertex_size = 2 * 4
        local_space_vertices_buffer_size = local_space_vertex_size * 6 * EntitiesManager.max_dynamic_entities

        texcoords_vertex_size = 2 * 4
        texcoords_buffer_size = texcoords_vertex_size * 6 * EntitiesManager.max_dynamic_entities

        transform_matrix_col_size  = 3 * 4 
        transform_column_buffer_size = transform_matrix_col_size *  3  * EntitiesManager.max_dynamic_entities

        self._entity_local_vertices_vbo= self._gl_ctx.buffer(reserve=local_space_vertices_buffer_size, dynamic=True)
        self._entity_texcoords_vbo = self._gl_ctx.buffer(reserve = texcoords_buffer_size, dynamic=True)
        
        self._entity_transform_matrices_vbo = self._gl_ctx.buffer(reserve = transform_column_buffer_size, dynamic=True)
       
        self._vao_entity_draw = self._gl_ctx.vertex_array(
            self._entity_draw_prog,
            [
                (self._entity_local_vertices_vbo, '2f', 'in_position'),
                (self._entity_texcoords_vbo, '2f', 'texcoord'),
                (self._entity_transform_matrices_vbo, '3f 3f 3f/i', 'col1', 'col2' ,'col3')
            ]
        )
        


    def _create_weapon_vertex_buffers(self)->None:
        local_space_vertex_size = 2* 4 
        local_space_vertices_buffer_size = local_space_vertex_size * 6 * EntitiesManager.max_dynamic_entities

        texcoords_vertex_size = 2 * 4 
        texcoords_buffer_size = texcoords_vertex_size * 6 * EntitiesManager.max_dynamic_entities

        transform_matrix_col_size = 3 * 4 
        transform_column_buffer_size = transform_matrix_col_size * 3 * EntitiesManager.max_dynamic_entities

        self._entity_weapons_local_vertices_vbo = self._gl_ctx.buffer(reserve=local_space_vertices_buffer_size,dynamic=True)
        self._entity_weapons_texcoords_vbo = self._gl_ctx.buffer(reserve=texcoords_buffer_size , dynamic= True)

        self._entity_weapons_transform_matrices_vbo = self._gl_ctx.buffer(reserve= transform_column_buffer_size , dynamic= True)
        
        self._vao_entity_weapons_draw = self._gl_ctx.vertex_array(
            self._entity_draw_prog,
            [
                (self._entity_weapons_local_vertices_vbo, '2f', 'in_position'),
                (self._entity_weapons_texcoords_vbo, '2f', 'texcoord'),
                (self._entity_weapons_transform_matrices_vbo, '3f 3f 3f/i', 'col1', 'col2', 'col3')
            ]
        )


    def _create_bullet_vertex_buffers(self)->None: 
        local_space_vertex_size = 2* 4 
        local_space_vertices_buffer_size = local_space_vertex_size * 6 * EntitiesManager.max_bullet_entities

        texcoords_vertex_size = 2 * 4 
        texcoords_buffer_size = texcoords_vertex_size * 6 * EntitiesManager.max_bullet_entities

        transform_matrix_col_size = 3 * 4 
        transform_column_buffer_size = transform_matrix_col_size * 3 * EntitiesManager.max_bullet_entities

        self._bullets_local_vertices_buffer = self._gl_ctx.buffer(reserve=local_space_vertices_buffer_size,dynamic=True)
        self._bullets_texcoords_vbo = self._gl_ctx.buffer(reserve=texcoords_buffer_size , dynamic= True)

        self._bullets_transform_matrices_vbo = self._gl_ctx.buffer(reserve= transform_column_buffer_size , dynamic= True)
        
        self._vao_bullets_draw = self._gl_ctx.vertex_array(
            self._entity_draw_prog,
            [
                (self._bullets_local_vertices_buffer, '2f', 'in_position'),
                (self._bullets_texcoords_vbo, '2f', 'texcoord'),
                (self._bullets_transform_matrices_vbo, '3f 3f 3f/i', 'col1', 'col2', 'col3')
            ]
        )
       

    def _create_item_vertex_buffers(self)->None: 
        local_space_vertex_size = 2 * 4 
        local_space_vertices_buffer_size = local_space_vertex_size * 6 * EntitiesManager.max_item_entities 

        texcoords_vertex_size = 2 * 4
        texcoords_buffer_size = texcoords_vertex_size * 6 * EntitiesManager.max_item_entities

        transform_matrix_col_size = 3 * 4 
        transform_column_buffer_size = transform_matrix_col_size * 3 * EntitiesManager.max_item_entities 

        self._items_local_vertices_vbo = self._gl_ctx.buffer(reserve= local_space_vertices_buffer_size,dynamic= True)
        self._item_texcoords_vbo = self._gl_ctx.buffer(reserve=texcoords_buffer_size,dynamic=True)

        self._items_transform_matrices_vbo = self._gl_ctx.buffer(reserve=transform_column_buffer_size, dynamic= True)

        self._vao_items_draw = self._gl_ctx.vertex_array(
            self._entity_draw_prog,
            [
                (self._items_local_vertices_vbo, '2f' , 'in_position'),
                (self._item_texcoords_vbo, '2f' , 'texcoord'),
                (self._items_transform_matrices_vbo, '3f 3f 3f/i' , 'col1', 'col2', 'col3')
            ]
        )


    def _opt_render_tilemap_to_bg_fbo(self,camera_offset:tuple[int32,int32])->None: 
        self._tile_draw_prog['cameraOffset'] = self._camera_offset_to_ndc_component(camera_offset) 

        self._fbo_bg.use()
        self._ref_rm.texture_atlasses['tiles'].use()

        self._vao_non_physical_tiles_draw.render(vertices= 6, instances = self._ref_tilemap.tiles_in_buffer * self._ref_tilemap._non_physical_tile_layers) 
        self._vao_physical_tiles_draw.render(vertices= 6 , instances = self._ref_tilemap.tiles_in_buffer)


    
    def _camera_offset_to_ndc_component(self,camera_offset:tuple[int32,int32])->np.ndarray: 
        return np.array([ 2. * camera_offset[0] / self._game_ctx['true_res'][0],
                         -2. * camera_offset[1] / self._game_ctx['true_res'][1]],dtype=np.float32)

    def _render_HUD_to_fg_fbo(self,dt:float32)->None: 

        self._ref_rm.texture_atlasses['ui'].use()   
        self._fbo_fg.use()

        self._vao_hud_draw.render()

        # draw the actual health and stamina bars here 

        self._vao_bars_draw.render()


        self._write_cursor_position_to_buffer()

        self._vao_cursor_draw.render()
        #self._ref_rm.texture_atlasses['ui'].use()
        #self._fbo_fg.use()
        """
        if self._ref_hud.inven_open_time > 0:
            self._hidden_ui_draw_prog['alpha'] = self._ref_hud.inven_open_time/self._ref_hud.max_inven_open_time
            self._vao_hidden_ui_draw.render()
            self._vao_hidden_items_draw.render()

        self._vao_opaque_ui_draw.render()  

        if self._ref_hud.cursor.item:
            self._ref_hud.opaque_items_vertices_buffer.write(self._create_cursor_item_vertices(),
                                                             offset = self._ref_hud.opaque_items_vertices_buffer.size - BYTES_PER_TEXTURE_QUAD)
        
        self._vao_opaque_items_draw.render()   

        self._write_cursor_position_to_buffer()
        self._ref_rm.texture_atlasses['ui'].use()
        self._vao_cursor_draw.render()
        """


    def _create_cursor_item_vertices(self)->bytes: 
        if self._ref_hud.cursor.item.type == 'item':
            item_dim = (self._ref_hud.open_item_inventory_cell_length//2,
                        self._ref_hud.open_item_inventory_cell_length//2)
        else: 
            item_dim = (self._ref_hud.weapon_inventory_cell_dim[0] * 4 // 6,
                        self._ref_hud.weapon_inventory_cell_dim[1] * 4 // 6)

        x = 2. * (self._ref_hud.cursor.topleft[0]-item_dim[0] //2)/ self._game_ctx['true_res'][0]- 1.
        y = 1. - 2. * (self._ref_hud.cursor.topleft[1]- item_dim[1]//2)/ self._game_ctx['true_res'][1]
        w = 2. * item_dim[0] / self._game_ctx['true_res'][0]
        h = 2. * item_dim[1] /self._game_ctx['true_res'][1]

        return np.array([(x, y - h),(x + w, y - h),(x,y),
                         (x,y),(x + w, y - h),(x+w,y)],dtype= np.float32).tobytes()


    def _write_cursor_position_to_buffer(self)->None: 
        x = 2. * (self._ref_hud.cursor.topleft[0] )/ self._game_ctx['true_res'][0]- 1.
        y = 1. - 2. * (self._ref_hud.cursor.topleft[1] )/ self._game_ctx['true_res'][1]
        w = 2. * self._ref_hud.cursor.size[0] / self._game_ctx['true_res'][0]
        h = 2. * self._ref_hud.cursor.size[1] / self._game_ctx['true_res'][1]

        self._ref_hud.cursor.ndc_vertices[0] = (x,y-h)
        self._ref_hud.cursor.ndc_vertices[1] = (x+w,y-h)
        self._ref_hud.cursor.ndc_vertices[2] = (x,y)
        self._ref_hud.cursor.ndc_vertices[3]  = (x,y)
        self._ref_hud.cursor.ndc_vertices[4] = (x+w,y-h)
        self._ref_hud.cursor.ndc_vertices[5] = (x+w,y)

        self._ref_hud.cursor.ndc_vertices_buffer.write(self._ref_hud.cursor.ndc_vertices.tobytes())


    def cursor_state_change_callback(self,new_cursor_state:str)->None: 
        # change the texcoords uniform in the cursor draw program according to the new cursor state 
        self._prog_cursor_draw['texCoords'] = self._ref_rm.ui_element_texcoords_array['cursor'][new_cursor_state]


    def _tile_position_to_ndc(self,position:tuple[int,int],camera_offset:tuple[int,int])->bytes:
        fbo_w,fbo_h = self._fbo_bg.size
        return np.array([2. * (position[0] *self._ref_tilemap.tile_size -camera_offset[0]) / fbo_w -1.
                , 1. - 2. * (position[1] * self._ref_tilemap.tile_size - camera_offset[1]) / fbo_h],dtype=np.float32).tobytes()


    def _render_background_to_bg_fbo(self,camera_offset:tuple[int32,int32],infinite:bool = False)->None: 
        speed = array([0],dtype= int32)
        for tex in self._ref_background.textures:
            if infinite: 
                tex_width_int32 = int32(tex.width)
                num_tiles = (int32(self._game_ctx['true_res'][0])//tex_width_int32) + int32(2)

                for panel in range(-1,num_tiles):
                    x_pos = panel*tex_width_int32- (camera_offset[0] * 0.05 *speed[0]) % tex_width_int32 
                    vertex_data = self._create_infinite_background_texture_vertex_data(camera_offset,x_pos)
                    self._ref_background_vertices_buffer.write(vertex_data)

                    self._fbo_bg.use()
                    tex.use()

                    self._vao_background_draw.render()
            else: 
                for panel in range(self._background_panels//-2 , self._background_panels//2 +int32(1)):
                    vertex_data = self._create_background_texture_vertex_data(camera_offset,panel,speed[0])
                    self._ref_background_vertices_buffer.write(vertex_data)

                    self._fbo_bg.use()
                    tex.use()

                    self._vao_background_draw.render()
            speed[0] += int32(1)


    def _create_infinite_background_texture_vertex_data(self,camera_scroll:tuple[int,int],x_pos:int)->bytes:
        width,height = self._fbo_bg.size 
        x = 2. * (x_pos) / width - 1.
        y = 1. -2 * (-min(0,camera_scroll[1]) * 0.05) / height
        w = 2.
        h = 2.

        return np.array([(x,y),(x+w,y),(x,y-h),
                         (x,y-h),(x+w,y),(x+w,y-h)],dtype= np.float32).tobytes()



    def _create_background_texture_vertex_data(self,camera_scroll:tuple[int,int],panel_num:int,speed:int32)->np.array:
        width,height = self._fbo_bg.size 
        x = 2. * (panel_num*self._game_ctx['true_res'][0]-camera_scroll[0] *0.05 * speed) / width - 1.
        y = 1. -2. * (-min(0,camera_scroll[1]) * 0.05) / height
        w = 2.
        h = 2. 

        return np.array([(x,y),(x+w,y),(x,y-h),
                         (x,y-h),(x+w,y),(x+w,y-h)],dtype= np.float32)

    
    def _send_hull_data_to_lighting_program(self,render_offset:tuple[int,int] = (0,0))->None: 
        vertices = []
        indices = []

        for hull in self.hulls:
            if not hull.enabled:
                continue
            vertices_buffer = [ ]

            # the vertices of the hulls are adjusted by the offset, then added to the list. 
            # the vertices are then converted to uv coords (lightmap)

            for vertice in hull.vertices:
                vertices_buffer.append((vertice[0]+self._lightmap_buffer_slack - render_offset[0], 
                                        vertice[1]+self._lightmap_buffer_slack - render_offset[1]))
            vertices += vertices_buffer
            indices.append(len(vertices))

        # Store hull vertex data in SSBO
        vertices = [self._pos_to_lightmap_uv(v) for v in vertices]
        data_v = np.array(vertices, dtype=np.float32).flatten().tobytes()
        self._ssbo_v.write(data_v)

        # Store hull vertex indices in SSBO
        data_ind = np.array(indices, dtype=np.int32).flatten().tobytes()
        self._ssbo_ind.write(data_ind)

    def _render_dynamic_lights_to_light_buffer(self,render_offset:tuple[int,int])->None: 
        # render static lightmap buffer onto dynamic light buffer
        
        # render dynamic lights onto dynamic light buffer 

        self._gl_ctx.disable(BLEND)

        for i in range(len(self.dynamic_lights)-1,-1,-1):
            dynamic_light = self.dynamic_lights[i]
            self._buf_dyn_lt.tex.use()
            self._buf_dyn_lt.fbo.use()
            
            #self._prog_light['lightPos'] = self._pos_to_lightmap_uv((dynamic_light.position[0]+self._lightmap_buffer_slack- render_offset[0],
            #                                                  dynamic_light.position[1]+self._lightmap_buffer_slack-render_offset[1]))
            self._prog_light['lightPos'] = self._dynamic_light_pos_to_lightmap_uv((dynamic_light.position[0] + self._lightmap_buffer_slack - self._prev_hull_query_camera_scroll[0] ,
                                                                                   dynamic_light.position[1]  + self._lightmap_buffer_slack - self._prev_hull_query_camera_scroll[1] ))


            self._prog_light['lightCol'] = dynamic_light._color
            self._prog_light['lightPower'] = dynamic_light.cur_power
            self._prog_light['radius'] = dynamic_light.radius
            self._prog_light['castShadows'] = dynamic_light.cast_shadows
            self._prog_light['lightmapWidth'] = self._lightmap_res[0]
            self._prog_light['lightmapHeight'] = self._lightmap_res[1]

            # Send number of hulls
            self._prog_light['numHulls'] = len(self.hulls)

            # Render onto lightmap
            self._vao_light.render()

            # Flip double buffer
            self._buf_dyn_lt.flip()

        self._gl_ctx.enable(BLEND)

            # send dynamic lights uniform 


    def _render_static_lights_to_light_buffer(self,render_offset:tuple[int,int])->None:

        self._gl_ctx.disable(BLEND)

        for i in range(len(self._active_static_lights)-1,-1,-1):
            light = self._active_static_lights[i]
            self._buf_lt.tex.use()
            self._buf_lt.fbo.use()
            # Send light uniforms
            self._prog_light['lightPos'] = self._pos_to_lightmap_uv((light.position[0]+self._lightmap_buffer_slack-render_offset[0],
                                                              light.position[1]+self._lightmap_buffer_slack-render_offset[1]))
            self._prog_light['lightCol'] = light._color
            self._prog_light['lightPower'] = light.cur_power
            self._prog_light['radius'] = light.radius
            self._prog_light['castShadows'] = light.cast_shadows
            self._prog_light['lightmapWidth'] = self._lightmap_res[0]
            self._prog_light['lightmapHeight'] = self._lightmap_res[1]

            # Send number of hulls
            self._prog_light['numHulls'] = len(self.hulls)

            # Render onto lightmap
            self._vao_light.render()

            # Flip double buffer
            self._buf_lt.flip()

        self._gl_ctx.enable(BLEND)

    def _dynamic_light_pos_to_lightmap_uv(self,pos): 
        return (pos[0] / self._lightmap_res[0], 1 - (pos[1] / self._lightmap_res[1]))

    def _pos_to_lightmap_uv(self,world_coords)->tuple[int,int]:
        return (world_coords[0] / self._lightmap_res[0], 1 - (world_coords[1] / self._lightmap_res[1]))
        

    def _render_aomap(self,camera_scroll:tuple[int,int])->None:
        self._buf_dyn_lt.tex.use()
        self._fbo_ao.use()

        # render offset of the lastly rendered lightmap to the current camera position 
        self._prog_blur['renderOffset'] = (self._prev_hull_query_camera_scroll[0] - camera_scroll[0],
                                           -self._prev_hull_query_camera_scroll[1] + camera_scroll[1])
                                           

        self._prog_blur['blurRadius'] = self._shadow_blur_radius
        self._vao_blur.render()


    def _render_background_layer(self)->None: 
        self._gl_ctx.screen.use()
        self._tex_bg.use()
        self._tex_ao.use(1)

        self._prog_mask['lightmap'].value = 1
        self._prog_mask['ambient'].value = self._ambient_light_RGBA

        self._vao_mask.render()


    def _render_foreground_layer(self)->None:
        self._gl_ctx.screen.use()
        self._tex_fg.use()
        self._vao_to_screen_draw.render()


    def _set_ambient(self, R: (int | tuple[int]) = 0, G: int = 0, B: int = 0, A: int = 255) -> None:
        self._ambient_light_RGBA = normalize_color_arguments(R, G, B, A)


    def _update_hulls(self,player_position:tuple[int,int],camera_scroll:tuple[int,int])->bool: 
        tile_size = self._ref_tilemap.tile_size
  
        if dist(self._prev_hull_query_player_pos,player_position) >= tile_size * 7: 
            self.hulls = self._ref_tilemap.hull_grid.query(camera_scroll[0] - 10 * tile_size, camera_scroll[1] - 10 * tile_size,\
                                                           camera_scroll[0] + self._game_ctx['true_res'][0] +  10 * tile_size, camera_scroll[1] + self._game_ctx['true_res'][1] + 10 * tile_size)
            
            self._prev_hull_query_player_pos = tuple(player_position)
            self._prev_hull_query_camera_scroll = camera_scroll
            return True

        return False



    def surface_to_texture(self, sfc: pygame.Surface) -> Texture:
        """
        Convert a pygame.Surface to a moderngl.Texture.

        Args:
            sfc (pygame.Surface): Surface to convert.

        Returns:
            moderngl.Texture: Converted texture.
        """

        img_flip = pygame.transform.flip(sfc, False, True)
        img_data = pygame.image.tostring(img_flip, "RGBA")

        tex = self._gl_ctx.texture(sfc.get_size(), components=4, data=img_data)
        tex.filter = (NEAREST, NEAREST)
        return tex


    # temporary helper debugging method 

    def render_texture(self, tex: Texture, layer: Layer_, dest: pygame.Rect, source: pygame.Rect,angle:float=0.0,flip : tuple[bool,bool]= (False,False)):
        """
        Render a texture onto a specified Layer_'s framebuffer using the draw shader.

        Args:
            tex (moderngl.Texture): Texture to render.
            Layer_ (Layer_): Layer_ to render the texture onto.
            dest (pygame.Rect): Destination rectangle.
            source (pygame.Rect): Source rectangle from the texture.
            angle (float) : angle to rotate around center in radians 
            flip (tuple[bool,bool]) : values to indicate flip vertically and horizontally 
        """

        # Render texture onto Layer_ with the draw shader
        fbo = self._get_fbo(layer)
        self._render_tex_to_fbo(tex, fbo, dest, source )



    def _get_fbo(self, Layer_: Layer_):
        if Layer_ == Layer_.BACKGROUND:
            return self._fbo_bg
        elif Layer_ == Layer_.FOREGROUND:
            return self._fbo_fg
        return None

    def _render_tex_to_fbo(self, tex: Texture, fbo: Framebuffer, dest: pygame.Rect, source: pygame.Rect,flip:bool = False):
        # Mesh for destination rect on screen
        width, height = fbo.size
        x = 2. * dest.x / width - 1.
        y = 1. - 2. * dest.y / height
        w = 2. * dest.w / width
        h = 2. * dest.h / height
        vertices = np.array([(x, y), (x + w, y), (x, y - h),
                            (x, y - h), (x + w, y), (x + w, y - h)], dtype=np.float32)

        # Mesh for source within the texture
        x = source.x / tex.width
        y = source.y / tex.height
        w = source.w / tex.width
        h = source.h / tex.height

        if flip: 
            p1 = (x + w, y + h)  # Top-right becomes top-left
            p2 = (x, y + h)      # Top-left becomes top-right
            p3 = (x + w, y)      # Bottom-right becomes bottom-left
            p4 = (x, y)          # Bottom-left becomes bottom-right
        else: 
                
            p1 = (x, y + h) 
            p2 = (x + w, y + h) 
            p3 = (x, y) 
            p4 = (x + w, y) 
        tex_coords = np.array([p1, p2, p3,
                               p3, p2, p4], dtype=np.float32)

        # Create VBO and VAO
        buffer_data = np.hstack([vertices, tex_coords])

        vbo = self._gl_ctx.buffer(buffer_data)
        vao = self._gl_ctx.vertex_array(self._to_screen_draw_prog, [
            (vbo, '2f 2f', 'vertexPos', 'vertexTexCoord'),
        ])

        # Use buffers and render
        tex.use()
        fbo.use()
        vao.render()

        # Free vertex data
        vbo.release()
        vao.release()



    def _render_rectangles(self,camera_scroll:tuple[int,int])->None: 
        buffer_surf = pygame.Surface(self._game_ctx['true_res']).convert_alpha()
        buffer_surf.fill((0, 0, 0, 0))

        # Iterate over rectangles
        for rectangle in self._ref_tilemap._rectangles:
            # Rectangle properties
            rect_x, rect_y, rect_x2, rect_y2 = rectangle
            rect_w = rect_x2 - rect_x
            rect_h = rect_y2 - rect_y


            # Calculate screen position relative to the offset
            screen_x = rect_x - camera_scroll[0]
            screen_y = rect_y - camera_scroll[1]

            # Check if the rectangle is within the visible screen
            if 0 <= screen_x < self._game_ctx['true_res'][0] and 0 <= screen_y < self._game_ctx['true_res'][1]:
                # Draw the rectangle directly onto the buffer surface
                pygame.draw.rect(
                    buffer_surf,
                    (244, 244, 244, 244),  # Color with alpha
                    pygame.Rect(screen_x, screen_y, rect_w, rect_h),  # Position and size
                    width=1,  # Line width
                )

        # Convert the buffer surface to a texture
        tex = self.surface_to_texture(buffer_surf)

        # Render the texture
        self.render_texture(
            tex,
            Layer_.BACKGROUND,
            dest=pygame.Rect(0, 0, tex.width, tex.height),
            source=pygame.Rect(0, 0, tex.width, tex.height),
        )

        # Release the texture
        tex.release()


    def _render_fbos_to_screen_with_lighting(self,player_position:tuple[int,int],camera_scroll:tuple[int,int],\
                                             screen_shake:tuple[int,int],interpolation_delta:float)->None: 
        """
        self._tex_bg.use()
        self._gl_ctx.screen.use()
        self._vao_to_screen_draw.render()
        """
        
        render_offset = (camera_scroll[0] - screen_shake[0],camera_scroll[1] - screen_shake[1])

        hulls_updated = self._update_hulls(player_position,camera_scroll)
        
        self._fbo_ao.clear(0,0,0,0)
    
        if hulls_updated:
            self._buf_lt.clear(0,0,0,0)
            self._send_hull_data_to_lighting_program(render_offset)
            self._render_static_lights_to_light_buffer(render_offset)

        self._buf_dyn_lt.fbo.use()
        self._gl_ctx.clear(0.,0.,0.,1.0)

        self._buf_lt.tex.use(0)

        self._vao_to_screen_draw.render()
        
        self._buf_dyn_lt.flip()

        if self.dynamic_lights: 
            self._render_dynamic_lights_to_light_buffer(render_offset)
        
        self._render_aomap(camera_scroll)

        self._render_background_layer()

        self._render_foreground_layer()


    def _on_ambient_node_change_callback(self,camera_offset:tuple[int,int],screen_shake:tuple[int,int],
                                         player_position:tuple[int,int])->None:
        
        self._update_active_static_lights(camera_offset)

        render_offset = (camera_offset[0]- screen_shake[0],camera_offset[1] -screen_shake[1])

        tile_size = self._ref_tilemap.tile_size

        self.hulls = self._ref_tilemap.hull_grid.query(camera_offset[0] - 10 * tile_size, camera_offset[1] - 10 * tile_size,\
                                                           camera_offset[0] + self._game_ctx['true_res'][0] +  10 * tile_size, camera_offset[1] + self._game_ctx['true_res'][1] + 10 * tile_size)
        
        self._prev_hull_query_player_pos = tuple(player_position)
        self._prev_hull_query_camera_scroll = camera_offset


        self._fbo_ao.clear(0,0,0,0)
        self._buf_lt.clear(0,0,0,0)
        self._send_hull_data_to_lighting_program(render_offset)
        self._render_static_lights_to_light_buffer(render_offset)

        self._render_aomap(camera_offset)



    def _update_active_static_lights(self,camera_offset:tuple[int,int])->None: 
     

        ambient_lighting_range = self._ref_tilemap._ref_ambient_node.range

        if dist(self._prev_lights_query_camera_scroll,camera_offset) >= 16:
            # query the lights 
            self._active_static_lights = self._ref_tilemap.lights_grid.query(camera_offset[0]- 2 * self._lightmap_buffer_slack,
                                                                            camera_offset[1]- 2 * self._lightmap_buffer_slack,
                                                                             camera_offset[0] + self._game_ctx['true_res'][0] + 2 * self._lightmap_buffer_slack,
                                                                            camera_offset[1] +self._game_ctx['true_res'][1] + 2 * self._lightmap_buffer_slack )
            
            self._prev_lights_query_camera_scroll = camera_offset

        for i in range(len(self._active_static_lights)-1,-1,-1):
            light = self._active_static_lights[i] 
            if light.popped or not light.enabled: 
                continue
            if light.position[0] < ambient_lighting_range[0] or light.position[0] > ambient_lighting_range[1]:
                light.cur_power = 0
                continue 
            else: 
                light.cur_power = light.power


    def _update_dynamic_lights(self,dt:float32)->None:
        for i in range(len(self.dynamic_lights)-1,-1,-1):
            dynamic_light = self.dynamic_lights[i]
            
            if dynamic_light.life > 0 : 
                if dynamic_light.radius_decay:
                    dynamic_light.radius = dynamic_light.radius * dynamic_light.life / dynamic_light.maxlife
                
                
                #dynamic_light.position[0] += dynamic_light.velocity[0] * dt 
                #dynamic_light.position[1] += dynamic_light.velocity[1] * dt

                dynamic_light.life -= dt
            else: 
                self.dynamic_lights.pop(i)
     

    def attatch_hud(self,hud:"HUD")->None:
        self._ref_hud = hud

        self._prog_cursor_draw['texCoords'] = self._ref_rm.ui_element_texcoords_array['cursor']['default']

        # TODO: OPTIMIZE cursor draw program to use a uniform to position cursor 
        self._vao_cursor_draw = self._gl_ctx.vertex_array(
            self._prog_cursor_draw,
            [
                (self._ref_hud.cursor.ndc_vertices_buffer, '2f' , 'in_position')
            ]
        )  
    
        self._vao_hud_draw = self._gl_ctx.vertex_array(
            self._opaque_ui_draw_prog,
            [
                (self._ref_hud.vertices_buffer , '2f' , 'vertexPos'),
                (self._ref_hud.texcoords_buffer, '2f' , 'vertexTexCoord')
            ]
        )

        self._vao_bars_draw = self._gl_ctx.vertex_array(
            self._prog_bar_draw,
            [
                (self._ref_hud.bars_vertices_and_color_buffer, '2f 4f' , 'in_vert', 'in_color')       
            ]
        )


        """
        self._vao_opaque_ui_draw = self._gl_ctx.vertex_array(
            self._opaque_ui_draw_prog,
            [
                (self._ref_hud.opaque_vertices_buffer, '2f' ,'vertexPos'),
                (self._ref_hud.opaque_texcoords_buffer, '2f', 'vertexTexCoord')
            ]
        )

        self._vao_hidden_ui_draw = self._gl_ctx.vertex_array(
            self._hidden_ui_draw_prog,
            [
                (self._ref_hud.hidden_vertices_buffer, '2f', 'vertexPos'),
                (self._ref_hud.hidden_texcoords_buffer, '2f' ,'vertexTexCoord')
            ]
        )

        self._vao_opaque_items_draw = self._gl_ctx.vertex_array(
            self._opaque_ui_draw_prog,
            [
                (self._ref_hud.opaque_items_vertices_buffer, '2f', 'vertexPos'),
                (self._ref_hud.opaque_items_texcoords_buffer, '2f', 'vertexTexCoord')
            ]
        )
        
        self._vao_hidden_items_draw = self._gl_ctx.vertex_array(
            self._hidden_ui_draw_prog,
            [
                (self._ref_hud.hidden_items_vertices_buffer, '2f' , 'vertexPos'),
                (self._ref_hud.hidden_items_texcoords_buffer, '2f' , 'vertexTexCoord')
            ]
        )
        """

    def attatch_tilemap(self,tilemap:"Tilemap")->None:
        self._ref_tilemap = tilemap

        self._lightmap_buffer_slack = 10 * self._ref_tilemap.tile_size

        # lightmap res according to tilemap tilesize 
        self._lightmap_res = (self._game_ctx['true_res'][0]+ 2 * self._lightmap_buffer_slack,
                              self._game_ctx['true_res'][1]+ 2 * self._lightmap_buffer_slack)
        
        # Double buffer for lights
        self._buf_lt = DoubleBuffer(self._gl_ctx, self._lightmap_res)

        # Final double buffer to add dynamic lights ontop of static lights 
        self._buf_dyn_lt = DoubleBuffer(self._gl_ctx,self._lightmap_res)

        self._prog_blur['iResolution'] = self._lightmap_res
        self._prog_mask['nativeRes'] = self._game_ctx['true_res']
        self._prog_mask['lightmapRes'] = self._lightmap_res

        # Ambient occlussion map
        self._tex_ao = self._gl_ctx.texture(
            self._lightmap_res, components=4, dtype='f2')
        self._tex_ao.filter = (LINEAR, LINEAR)
        self._fbo_ao = self._gl_ctx.framebuffer([self._tex_ao])

        # wrapping settings 
        self._buf_lt._tex1.repeat_x = False
        self._buf_lt._tex1.repeat_y = False
        self._buf_lt._tex2.repeat_x = False
        self._buf_lt._tex2.repeat_y = False

        self._buf_dyn_lt._tex1.repeat_x = False
        self._buf_dyn_lt._tex1.repeat_y = False
        self._buf_dyn_lt._tex2.repeat_x = False
        self._buf_dyn_lt._tex2.repeat_y = False

        self._tex_ao.repeat_x = False
        self._tex_ao.repeat_y = False
 

        self._tile_draw_prog['NDCVertices'] = self._ref_tilemap.NDC_tile_vertices_array

        self._vao_physical_tiles_draw = self._gl_ctx.vertex_array(
            self._tile_draw_prog,
            [
                (self._ref_tilemap.physical_tiles_position_vbo,'2f/i','in_position'),
                (self._ref_tilemap.physical_tiles_texcoords_vbo,'12f/i','in_texcoord'),
            ]
        )

        self._vao_non_physical_tiles_draw = self._gl_ctx.vertex_array(
            self._tile_draw_prog,
            [
                (self._ref_tilemap.non_physical_tiles_position_vbo, '2f/i' , 'in_position'),
                (self._ref_tilemap.non_physical_tiles_texcoords_vbo, '12f/i' ,'in_texcoord')
            ]
        )


    def attatch_background(self,background:"Background")->None: 
        self._ref_background = background 
        background_vertices = np.zeros(shape=(12,),dtype=np.float32)

        self._ref_background_vertices_buffer = self._gl_ctx.buffer(background_vertices,dynamic=True)
        texcoords_buffer = self._gl_ctx.buffer(self._ref_background.identity_texcoords)

        self._vao_background_draw = self._gl_ctx.vertex_array(
            self._to_screen_draw_prog,
            [
                (self._ref_background_vertices_buffer, '2f' , 'vertexPos'),
                (texcoords_buffer, '2f' , 'vertexTexCoord'),
            ]
        )

    def clear(self,R:int = 0, G:int = 0, B:int = 0,A:int =255)->None: 
        R,G,B,A =   normalize_color_arguments(R,G,B,A)
        self._gl_ctx.screen.clear(0,0,0,255)
        self._fbo_bg.clear(R,G,B,A)
        self._fbo_fg.clear(R,G,B,A)
        
    def process(self,game_context,interpolation_delta:float32,dt:float32)->None: 

        camera_offset = tuple(game_context['camera_offset'])
        screen_shake  = tuple(game_context['screen_shake'])

        self._gl_ctx.enable(BLEND)
        self._render_background_to_bg_fbo(camera_offset)
        self._opt_render_tilemap_to_bg_fbo(camera_offset)
        self._ref_hud.update(dt,interpolation_delta,camera_offset,self.cursor_state_change_callback)

        entity_vertices_byte_array = bytearray()
        entity_texcoords_byte_array = bytearray()
        entity_matrices_byte_array = bytearray()

        weapon_vertices_byte_array = bytearray()
        weapon_texcoords_byte_array = bytearray() 
        weapon_matrices_byte_array  = bytearray()

        item_vertices_byte_array = bytearray()
        item_texcoords_byte_array = bytearray()
        item_matrices_byte_array = bytearray()

        bullet_vertices_byte_array = bytearray()
        bullet_texcoords_byte_array = bytearray()
        bullet_matrices_byte_array = bytearray()

        self._view_matrix[0][2] = -camera_offset[0]
        self._view_matrix[1][2] = -camera_offset[1]

        entity_instances = 0
        weapon_instances = 0 


        # render the player and moving entities 

        for entity, (state_info_comp,physics_comp,render_comp) in esper.get_components(StateInfoComponent,PhysicsComponent,AnimatedRenderComponent):
            if state_info_comp.type == 'player':

                wpn_holder_comp = self._ref_em.weapon_holder_comp

                self._ref_tilemap.update_tilemap_vbos(physics_comp.position)
                self._ref_tilemap.update_ambient_node_ref(physics_comp.position,self._on_ambient_node_change_callback,camera_offset,screen_shake)

                if isinstance(self._ref_tilemap._ref_ambient_node,interpolatedLightNode):
                    self._set_ambient(self._ref_tilemap._ref_ambient_node.get_interpolated_RGBA(physics_comp.position[0]))
                else: 
                    self._set_ambient(*self._ref_tilemap._ref_ambient_node.colorValue)

                self._set_ambient(99,88,88,255)

                animation_data_collection = render_comp.animation_data_collection
                animation = animation_data_collection.get_animation(state_info_comp.curr_state)

                texcoords_bytes = self._ref_rm.entity_texcoords_bytes[(state_info_comp.type,True,state_info_comp.curr_state,animation.curr_frame())]
                entity_local_vertices_bytes = render_comp.vertices_bytes
          
                interpolated_model_transform = physics_comp.prev_transform * (1.0 - interpolation_delta) + physics_comp.transform * interpolation_delta
                interpolated_model_transform[0][2] += wpn_holder_comp.knockback[0] / 4
                interpolated_model_transform[1][2] += wpn_holder_comp.knockback[1] / 4 

                player_model_interpolated_translation = (interpolated_model_transform[0][2], interpolated_model_transform[1][2]) 

                clip_transform = self._projection_matrix @ self._view_matrix @ interpolated_model_transform 

                entity_vertices_byte_array.extend(entity_local_vertices_bytes)
                entity_texcoords_byte_array.extend(texcoords_bytes)

                column_major_clip_transform_bytes = clip_transform.T.flatten().tobytes()
                entity_matrices_byte_array.extend(column_major_clip_transform_bytes)

                # write to weapon vertex buffer (ak47) 

                weapon_instances += 1

                sin_a = np.sin(pi - wpn_holder_comp.anchor_to_cursor_angle if wpn_holder_comp.weapon_flip else - wpn_holder_comp.anchor_to_cursor_angle) 
                cos_a = np.cos(pi - wpn_holder_comp.anchor_to_cursor_angle if wpn_holder_comp.weapon_flip else - wpn_holder_comp.anchor_to_cursor_angle)
                
                self._ref_em.player_weapon_render_comp.weapon_model_to_pivot_transform[0][2] = -self._ref_em.player_main_weapon.origin_offset_from_center[0]
                self._ref_em.player_weapon_render_comp.weapon_model_to_pivot_transform[1][2] = -self._ref_em.player_main_weapon.origin_offset_from_center[1]
 
                self._ref_em.player_weapon_render_comp.weapon_model_rotate_transform[0][0] = cos_a
                self._ref_em.player_weapon_render_comp.weapon_model_rotate_transform[0][1] = -sin_a

                self._ref_em.player_weapon_render_comp.weapon_model_rotate_transform[1][0] = sin_a 
                self._ref_em.player_weapon_render_comp.weapon_model_rotate_transform[1][1] = cos_a 

                self._ref_em.player_weapon_render_comp.weapon_model_flip_transform[0][0] = -2 * wpn_holder_comp.weapon_flip +1


                self._ref_em.player_weapon_render_comp.weapon_model_translate_transform[0][2] = player_model_interpolated_translation[0] + wpn_holder_comp.weapon_anchor_pos_offset_from_center[0] + wpn_holder_comp.knockback[0]
                self._ref_em.player_weapon_render_comp.weapon_model_translate_transform[1][2] = player_model_interpolated_translation[1] + wpn_holder_comp.weapon_anchor_pos_offset_from_center[1] + wpn_holder_comp.knockback[1]

                weapon_clip_transform = self._projection_matrix @ self._view_matrix @ self._ref_em.player_weapon_render_comp.weapon_model_translate_transform @ self._ref_em.player_weapon_render_comp.weapon_model_rotate_transform @ \
                    self._ref_em.player_weapon_render_comp.weapon_model_flip_transform @ self._ref_em.player_weapon_render_comp.weapon_model_to_pivot_transform
                
                weapon_vertices_byte_array.extend(self._ref_em.player_weapon_render_comp.vertices_bytes)
                weapon_texcoords_byte_array.extend(self._ref_em.player_weapon_render_comp.texcoords_bytes)

                column_major_clip_transform_bytes = weapon_clip_transform.T.flatten().tobytes()

                weapon_matrices_byte_array.extend(column_major_clip_transform_bytes)

                """
                if player_weapon_equipped:
                    weapon_instances += 1  
                    weapon = self._ref_hud.curr_weapon
                    
                    weapon_texcoords_bytes = self._ref_rm.holding_weapon_texcoords_bytes[weapon.name] 
                    weapon_local_vertices_bytes = self._ref_rm.holding_weapon_vertices_bytes[weapon.name] 

                    weapon_flip = physics_comp.position[0] - camera_offset[0] > self._ref_hud.cursor.topleft[0]


                    anchor_position_offset_from_center = PLAYER_LEFT_AND_RIGHT_ANCHOR_OFFSETS[physics_comp.flip][state_info_comp.curr_state][weapon_flip]

                    anchor_to_cursor_angle = self._ref_hud.cursor.get_angle_from_point((physics_comp.position[0]-camera_offset[0] + anchor_position_offset_from_center[0],
                                                                                        physics_comp.position[1]-camera_offset[1] + anchor_position_offset_from_center[1]))

                    sin_a = np.sin(pi - anchor_to_cursor_angle if weapon_flip else - anchor_to_cursor_angle) 
                    cos_a = np.cos(pi - anchor_to_cursor_angle if weapon_flip else  - anchor_to_cursor_angle)

                    weapon_model_to_pivot_transform = np.array([
                        [1,0,-weapon.origin_offset_from_center[0]],
                        [0,1,-weapon.origin_offset_from_center[1]],
                        [0,0,1]
                    ],dtype = np.float32)

                    weapon_model_rotate_transform = np.array([
                        [cos_a,-sin_a,0],
                        [sin_a,cos_a,0],
                        [0,0,1]
                    ],dtype = np.float32)

                    weapon_model_flip_transform = np.array([
                        [(-2*weapon_flip +1),0,0],
                        [0,1,0],
                        [0,0,1]
                    ],dtype = np.float32)


                    weapon_model_translate_transform = np.array([
                        [1,0,player_model_interpolated_translation[0]+anchor_position_offset_from_center[0]],
                        [0,1,player_model_interpolated_translation[1]+anchor_position_offset_from_center[1]],
                        [0,0,1]
                    ],dtype= np.float32)
                    

                    weapon_model_translate_transform = np.array([
                        [1,0,physics_comp.position[0]],
                        [0,1,physics_comp.position[1]],
                        [0,0,1]
                    ],dtype= np.float32)

                    weapon_clip_transform = self._projection_matrix @ self._view_matrix @ weapon_model_translate_transform @ weapon_model_rotate_transform @ weapon_model_flip_transform  @ weapon_model_to_pivot_transform

                    weapon_vertices_byte_array.extend(weapon_local_vertices_bytes)
                    weapon_texcoords_byte_array.extend(weapon_texcoords_bytes)

                    column_major_clip_transform_bytes = weapon_clip_transform.T.flatten().tobytes()
                    weapon_matrices_byte_array.extend(column_major_clip_transform_bytes) 
                """

            else: 
                pass

            entity_instances += 1
        
        # render the item entities 

        item_instances = 0

        for item_entity in self._ref_em.active_item_entities:
            item_info_comp,item_phy_comp,static_render_comp = esper.components_for_entity(item_entity)

            if item_info_comp.active_time[0] > float32(0.05):
                item_instances += 1
                texcoords_bytes = self._ref_rm.item_texcoords_bytes[item_info_comp.type] 
                item_local_vertices_bytes = static_render_comp.vertices_bytes

                interpolated_model_transform = item_phy_comp.prev_transform * (1.0 - interpolation_delta) + item_phy_comp.transform * interpolation_delta

                clip_transform = self._projection_matrix @ self._view_matrix @ interpolated_model_transform

                item_vertices_byte_array.extend(item_local_vertices_bytes)
                item_texcoords_byte_array.extend(texcoords_bytes)

                column_major_clip_transform_bytes = clip_transform.T.flatten().tobytes()
                item_matrices_byte_array.extend(column_major_clip_transform_bytes)

        # render the bullets 

        bullet_instances = 0

        for bullet_entity in self._ref_em.active_bullet_entities:
            bullet_phys_comp, bullet_render_comp = esper.components_for_entity(bullet_entity)
            
            if bullet_phys_comp.active_time[0] > float32(0.05):
                bullet_instances += 1 

                texcoords_bytes = self._ref_rm.bullet_texcoords_bytes
                bullet_local_vertices_bytes = self._ref_rm.bullet_local_vertices_bytes

                interpolated_model_translate_transform = bullet_phys_comp.prev_translate_transform * (1.0 - interpolation_delta) + bullet_phys_comp.translate_transform * interpolation_delta

                bullet_clip_transform = self._projection_matrix @ self._view_matrix @ interpolated_model_translate_transform @ bullet_render_comp.bullet_model_rotate_transform @ \
                                        bullet_render_comp.bullet_model_flip_transform 
                
                bullet_vertices_byte_array.extend(bullet_local_vertices_bytes)
                bullet_texcoords_byte_array.extend(texcoords_bytes)

                column_major_clip_transform_bytes = bullet_clip_transform.T.flatten().tobytes()

                bullet_matrices_byte_array.extend(column_major_clip_transform_bytes)


        self._entity_weapons_local_vertices_vbo.write(weapon_vertices_byte_array)
        self._entity_weapons_texcoords_vbo.write(weapon_texcoords_byte_array)
        self._entity_weapons_transform_matrices_vbo.write(weapon_matrices_byte_array)

        self._entity_local_vertices_vbo.write(entity_vertices_byte_array)
        self._entity_texcoords_vbo.write(entity_texcoords_byte_array)
        self._entity_transform_matrices_vbo.write(entity_matrices_byte_array)

        self._items_local_vertices_vbo.write(item_vertices_byte_array)
        self._item_texcoords_vbo.write(item_texcoords_byte_array)
        self._items_transform_matrices_vbo.write(item_matrices_byte_array)


        self._bullets_local_vertices_buffer.write(bullet_vertices_byte_array)
        self._bullets_texcoords_vbo.write(bullet_texcoords_byte_array)
        self._bullets_transform_matrices_vbo.write(bullet_matrices_byte_array)

        self._fbo_bg.use()

        self._ref_rm.texture_atlasses['entities'].use()
        self._vao_entity_draw.render(instances= entity_instances)

        self._ref_rm.texture_atlasses['holding_weapons'].use()
        self._vao_entity_weapons_draw.render(instances= weapon_instances)

        self._fbo_fg.use()

        self._ref_rm.texture_atlasses['items'].use()
        self._vao_items_draw.render(instances=item_instances)
         
        self._ref_rm.texture_atlasses['bullet'].use()
        self._vao_bullets_draw.render(instances= bullet_instances)

        self._render_HUD_to_fg_fbo(dt)

        self._update_active_static_lights(camera_offset)
        self._update_dynamic_lights(dt)
        self._render_fbos_to_screen_with_lighting(self._ref_em.player_physics_comp.position,camera_offset,screen_shake,interpolation_delta)


class StateSystem(esper.Processor):

    def __init__(self)->None: 
        self._ref_em :EntitiesManager = EntitiesManager.get_instance()
        self._player_state_machine = PlayerStateMachine()
        self._enemy_state_machine = EnemyStateMachine()

    def process(self,dt:float32)->None: 
        
        for entity, (state_info_comp,physics_comp,render_comp) in esper.get_components(StateInfoComponent,PhysicsComponent,AnimatedRenderComponent):
            if state_info_comp.type == 'player':
                self._player_state_machine.change_state(self._ref_em.player_input_comp,state_info_comp,physics_comp,render_comp,dt)
            else: 
                pass

class InputHandler(esper.Processor):

    def __init__(self,game_context,render_system)->None: 
        
        self._ref_em : EntitiesManager = EntitiesManager.get_instance()
        self._ref_game_context = game_context
        self._ref_hud: "HUD" = None
        self._ref_rs :RenderSystem = render_system
        self._mouse_left_held :bool = False
        


    def _handle_common_events(self,event:pygame.event)->None:
        
        new_topleft = get_pos()

        self._ref_hud.cursor.topleft = (int32(new_topleft[0]) // int32(self._ref_game_context['display_scale_ratio']), 
                                        int32(new_topleft[1]) // int32(self._ref_game_context['display_scale_ratio']))
        
        self._ref_hud.cursor.box.x  = self._ref_hud.cursor.topleft[0]
        self._ref_hud.cursor.box.x = self._ref_hud.cursor.topleft[1]

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                quit()
            if event.key == pygame.K_F12:
                pygame.display.toggle_fullscreen()
        elif event.type == pygame.QUIT:
            pygame.quit()
            quit()


        """

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self._ref_em.shoot_bullet(self._ref_rs.dynamic_lights)
                pass
                self._ref_hud.cursor.pressed[0] = True 
            elif event.button==3:
                self._ref_hud.cursor.pressed[1] = True 
                pass

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self._ref_hud.cursor.pressed[0] = False 
                pass
            elif event.button==3:
                self._ref_hud.cursor.pressed[1] = False 
                pass
        """

    def attatch_hud(self,hud:"HUD")->None:
        self._ref_hud = hud


    def process(self,on_hot_reload_callback:"function")->None: 
        player_input_comp = self._ref_em.player_input_comp

        if self._ref_game_context['gamestate'] == GameState.GameLoop: 
            self._ref_hud.cursor.pressed[0] = pygame.mouse.get_pressed()[0]
            if self._ref_hud.cursor.pressed[0] and self._ref_hud.cursor.state != 'grab':
                self._ref_em.shoot_bullet(self._ref_rs.dynamic_lights)
            for event in pygame.event.get():
                self._handle_common_events(event)

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F5: 
                        on_hot_reload_callback()
                    if event.key == pygame.K_LSHIFT:
                        self._ref_hud.cursor.special_actions = True
                        player_input_comp.shift = True 
                    if event.key == pygame.K_w:
                        player_input_comp.up = True
                        #player_physics_comp.velocity[1] = -PLAYER_JUMP_SPEED
                    if event.key == pygame.K_a:
                        player_input_comp.left = True
                        #player_physics_comp.acceleration[0] = -PLAYER_ACCELERATION
                        
                    if event.key == pygame.K_d:
                        player_input_comp.right = True 
                        #player_physics_comp.acceleration[0] = PLAYER_ACCELERATION

                    if event.key == pygame.K_s:
                        player_input_comp.down = True
                        # crouch maybe?
                    if event.key == pygame.K_SPACE:
                        player_input_comp.interact = True
                        # interact with interactable objects
                    if event.key == pygame.K_e:
                        pass
                        # toggle inventory
                        #self._ref_hud.inven_open_state = not self._ref_hud.inven_open_state

                    if event.key == pygame.K_i:
                        # temporary keybinding to add items to inventory 
                        #self._ref_hud.add_item(Item(choice(list(ITEM_ATLAS_POSITIONS_AND_SIZES.keys()))),0)
                        pass
                    if event.key == pygame.K_f: 
                        pass
                        #self._ref_hud.add_item(AK47(),2)
                    if event.key == pygame.K_g: 
                        pass
                        #self._ref_hud.add_item(FlameThrower(),2)
                
                elif event.type == pygame.MOUSEWHEEL:
                    #self._ref_hud.change_weapon(event.y)
                    pass

                elif event.type == pygame.KEYUP:
                    
                    if event.key == pygame.K_LSHIFT:
                        self._ref_hud.cursor.special_actions = False
                        player_input_comp.shift = False

                    if event.key == pygame.K_w:
                        player_input_comp.up = False
                    if event.key == pygame.K_a:
                        player_input_comp.left = False
                        #player_physics_comp.acceleration[0] = 0

                    if event.key == pygame.K_d:
                        player_input_comp.right = False
                        #player_physics_comp.acceleration[0] = 0

                    if event.key == pygame.K_s:
                        player_input_comp.down = False
                    if event.key == pygame.K_SPACE:
                        player_input_comp.interact = False




class StateMachine:

    def __init__(self)->None: 
        pass

    def change_state(self,physics_comp:PhysicsComponent)->str: 
        pass


class PlayerStateMachine(StateMachine):
    def change_state(self,input_comp:InputComponent,state_info_comp:StateInfoComponent,physics_comp:PhysicsComponent,render_comp:AnimatedRenderComponent,dt:float32):
        if state_info_comp.curr_state == 'land':
            pass
        else:
            if state_info_comp.collide_bottom:
                if physics_comp.velocity[0] == float32(0):
                    if state_info_comp.collide_bottom:
                        if input_comp.down: 
                            new_state = 'slide'
                        else: 
                            new_state = 'idle'
                else: 
                    if not (state_info_comp.collide_left or state_info_comp.collide_right):
                        if input_comp.shift:
                            new_state = 'sprint'
                        else:
                            new_state = 'run' 
                    else: 
                        new_state = 'idle'
            else: 
                if state_info_comp.collide_left or state_info_comp.collide_right:
                    new_state = 'wall_slide'
                else: 
                    if physics_comp.velocity[1] > float32(0):
                        new_state = 'jump_down'
                    else: 
                        new_state = 'jump_up'

    
        if new_state != state_info_comp.curr_state:
            render_comp.animation_data_collection.get_animation(state_info_comp.curr_state).reset()
            state_info_comp.curr_state = new_state
        else: 
            render_comp.animation_data_collection.get_animation(state_info_comp.curr_state).update(dt)

        """
        animation_data_collection = render_comp.animation_data_collection
        immediate_animation = animation_data_collection.get_animation(curr_state)

        immediate_animation.reset()
        """

class EnemyStateMachine(StateMachine):
    def change_state(self, physics_comp):
        return super().change_state(physics_comp)