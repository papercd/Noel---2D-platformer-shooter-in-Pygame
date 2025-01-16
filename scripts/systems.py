import esper

from scripts.game_state import GameState
from scripts.game_state import GameState
from scripts.data import TERMINAL_VELOCITY,GRAVITY,ENTITIES_ACCELERATION,ENTITIES_JUMP_SPEED,ENTITIES_MAX_HORIZONTAL_SPEED,HORIZONTAL_DECELERATION
from pygame.rect import Rect
from scripts.new_resource_manager import ResourceManager
from scripts.new_entities_manager import EntitiesManager 
from scripts.components import PhysicsComponent,RenderComponent, StateInfoComponent,InputComponent
from my_pygame_light2d.double_buffer import DoubleBuffer
from my_pygame_light2d.color import normalize_color_arguments
from scripts.layer import Layer_

from scripts.lists import interpolatedLightNode
import pygame
from moderngl import NEAREST,LINEAR,BLEND,Texture,Framebuffer
from OpenGL.GL import glUniformBlockBinding,glGetUniformBlockIndex
from math import sqrt,ceil,floor,dist
import numpy as np

from typing import TYPE_CHECKING 


if TYPE_CHECKING: 
    from my_pygame_light2d.light import PointLight
    from my_pygame_light2d.hull import Hull
    from scripts.background import Background
    from scripts.data import TileInfo, TileInfoDataClass
    from moderngl import Context
    from scripts.new_tilemap import Tilemap

class PhysicsSystem(esper.Processor):
    def __init__(self)->None: 
        self._ref_tilemap:"Tilemap" = None
        self._collision_rect_buffer = Rect(0,0,1,1)


    def _process_regular_tile_y_collision(self,physics_comp:PhysicsComponent,state_info_comp:StateInfoComponent,
                                          rect_tile:tuple["Rect","TileInfoDataClass"],dt:float)->None: 
        if physics_comp.velocity[1] > 0:
            state_info_comp.collide_bottom = True
            physics_comp.position[1] = rect_tile[0].top - physics_comp.size[1] // 2
            physics_comp.collision_rect.bottom = rect_tile[0].top 
            physics_comp.velocity[1] =GRAVITY * dt 
            state_info_comp.jump_count = 0

        elif physics_comp.velocity[1] < 0:
            state_info_comp.collide_top = True
            physics_comp.position[1] = rect_tile[0].bottom + physics_comp.size[1] // 2
            physics_comp.collision_rect.top = rect_tile[0].bottom
            physics_comp.velocity[1] = 0
        physics_comp.displacement_buffer[1] = 0


    def _process_regular_tile_x_collision(self,state_info_comp:StateInfoComponent,physics_comp:PhysicsComponent,
                                          rect_tile:tuple["Rect","TileInfoDataClass"])->None: 
        if physics_comp.velocity[0] > 0:
            state_info_comp.collide_right = True
            physics_comp.collision_rect.right = rect_tile[0].left 
            physics_comp.position[0]  = physics_comp.collision_rect.centerx 
        elif physics_comp.velocity[0] < 0 :
            state_info_comp.collide_left = True 
            physics_comp.collision_rect.left = rect_tile[0].right 
            physics_comp.position[0] = physics_comp.collision_rect.centerx 
        else: 
            if physics_comp.position[0] > rect_tile[0].centerx:
                state_info_comp.collide_left = True
                physics_comp.collision_rect.left = rect_tile[0].right
                physics_comp.position[0] = physics_comp.collision_rect.centerx
            else: 
                state_info_comp.collide_right = True
                physics_comp.collision_rect.right = rect_tile[0].left
                physics_comp.position[0] = physics_comp.collision_rect.centerx
        physics_comp.displacement_buffer[0] = 0



    def _handle_tile_collision(self,physics_comp:PhysicsComponent,state_info_comp:StateInfoComponent,rect_tile:tuple["Rect","TileInfoDataClass"],
                          tile_size:int,dt:float,axis_bit:bool)->None: 

    
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
                        physics_comp.position[1] = physics_comp.collision_rect.bottom - physics_comp.size[1] // 2 
                        physics_comp.velocity[1] = GRAVITY * dt
                        state_info_comp.jump_count = 0
                        state_info_comp.collide_bottom = True
                        physics_comp.displacement_buffer[1] = 0

                else: 
                    if rect_tile[1].info.type.endswith('door'):
                        pass
                    
                    self._process_regular_tile_y_collision(physics_comp,state_info_comp,rect_tile,dt)


    def _process_physics_updates(self,physics_comp:PhysicsComponent,state_info_comp:StateInfoComponent,dt:float,input_comp: InputComponent =None)->None:


        if input_comp is not None:  # for entities the physics updates of which are dependent on input.
            direction_bit = input_comp.right - input_comp.left
            if direction_bit != 0:
                physics_comp.flip = direction_bit == -1
            physics_comp.acceleration[0] = ENTITIES_ACCELERATION[state_info_comp.type] * direction_bit
            if input_comp.up and state_info_comp.jump_count < state_info_comp.max_jump_count:
                physics_comp.velocity[1] = -ENTITIES_JUMP_SPEED[state_info_comp.type]
            
                # to stop the player from jumping infinitely
                input_comp.up = False
                state_info_comp.jump_count += 1

    
        physics_comp.prev_transform = physics_comp.transform

        # apply deceleration to horizontal velocity
        if physics_comp.velocity[0] > 0:
            physics_comp.velocity[0] = max(0,physics_comp.velocity[0] - HORIZONTAL_DECELERATION * dt)
        elif physics_comp.velocity[0] < 0:
            physics_comp.velocity[0] = min(0,physics_comp.velocity[0] + HORIZONTAL_DECELERATION * dt)

        # clamp velocity to maximums
        physics_comp.velocity[0] = max(-ENTITIES_MAX_HORIZONTAL_SPEED[state_info_comp.type], min(ENTITIES_MAX_HORIZONTAL_SPEED[state_info_comp.type],physics_comp.velocity[0] + physics_comp.acceleration[0] * dt))
        physics_comp.velocity[1] = min(TERMINAL_VELOCITY,physics_comp.velocity[1] + physics_comp.acceleration[1] * dt) 

        physics_comp.displacement_buffer[0] += physics_comp.velocity[0] * dt
        physics_comp.displacement_buffer[1] += physics_comp.velocity[1] * dt

        displacement = 0
        collided = False 

        if physics_comp.displacement_buffer[0] >= 1.0 or physics_comp.displacement_buffer[0] <= -1.0:
            displacement = int(physics_comp.displacement_buffer[0]) 

            physics_comp.collision_rect.x += displacement
            physics_comp.position[0] += displacement 

            physics_comp.displacement_buffer[0] -= displacement

        for rect_tile in self._ref_tilemap.query_rect_tile_pair_around_ent((physics_comp.position[0]- physics_comp.size[0] //2 ,physics_comp.position[1] - physics_comp.size[1] //2),\
                                                                           physics_comp.size):
            if physics_comp.collision_rect.colliderect(rect_tile[0]):
                collided = True 
                self._handle_tile_collision(physics_comp,state_info_comp,rect_tile,self._ref_tilemap.regular_tile_size,dt,False)
        
        if not collided and (displacement >= 1.0 or displacement <= -1.0):
            state_info_comp.collide_left = False
            state_info_comp.collide_right = False 

        if physics_comp.displacement_buffer[1] >= 1.0 or physics_comp.displacement_buffer[1] <= -1.0:
            displacement = int(physics_comp.displacement_buffer[1]) 
            physics_comp.collision_rect.y += displacement
            physics_comp.position[1] += displacement 

            physics_comp.displacement_buffer[1] -= displacement

        collided = False

        for rect_tile in self._ref_tilemap.query_rect_tile_pair_around_ent((physics_comp.position[0]- physics_comp.size[0] //2 ,physics_comp.position[1] - physics_comp.size[1] //2),\
                                                                           physics_comp.size):
            if physics_comp.collision_rect.colliderect(rect_tile[0]):
                collided = True
                self._handle_tile_collision(physics_comp,state_info_comp,rect_tile,self._ref_tilemap.regular_tile_size,dt,True)
        if not collided and (displacement >= 1.0 or displacement <= -1.0):
            state_info_comp.collide_bottom = False 
            state_info_comp.collide_top = False

        #print(state_info_comp.collide_left,state_info_comp.collide_right,state_info_comp.collide_top,state_info_comp.collide_bottom)

        
    def attatch_tilemap(self,tilemap:"Tilemap")->None: 
        self._ref_tilemap =tilemap

    def process(self,dt:float)->None: 
        # process physics for player entity, which has an input component while the rest of the entities don't.
        player,(player_input_comp,state_info_comp,player_physics_comp) = esper.get_components(InputComponent,StateInfoComponent,PhysicsComponent)[0]

        self._process_physics_updates(player_physics_comp,state_info_comp,dt,player_input_comp)


        for entity, (state_info_comp,physics_comp) in esper.get_components(StateInfoComponent,PhysicsComponent):
            if state_info_comp.type != "player":
                self._process_physics_updates(physics_comp,state_info_comp,dt)



# I guess refactor the engine code to become a Render System?
class RenderSystem(esper.Processor):


    def __init__(self,ctx:"Context",true_to_screen_res_ratio:int=1,screen_res:tuple[int,int] = (500,500),\
                 true_res :tuple[int,int] = (500,500))->None: 
        self._ctx = ctx

        # references 
        self._ref_rm = ResourceManager.get_instance()

        self._ref_tilemap: "Tilemap" = None
        self._ref_background: "Background" = None
        self._ref_background_vertices_buffer : "Context.buffer" = None 
        
        # Initialize members 
        self._background_panels:int = 3

        self._true_to_native_ratio = true_to_screen_res_ratio 
        self._screen_res = screen_res
        self._true_res = true_res 

        self._diagonal = sqrt(self._true_res[0] ** 2 + self._true_res[1] ** 2)
        self._lightmap_res = true_res 
        self._ambient_light_RGBA = (.25, .25, .25, .25)


        self.lights:list["PointLight"] = []
        self.hulls:list["Hull"] = []

        self._prev_query_camera_scroll= (0,0)
        self._camera_displacement_buffer = [0,0]
        self._shadow_blur_radius = 5
        self._max_hull_count = 512

        self._projection_transform = np.array( 
            [
            [2. / self._true_res[0] , 0 , -1.],
            [0, -2. / self._true_res[1]  ,  1.],
            [0,0,1.]
        ],dtype=np.float32)

        self._view_transform = np.array([
            [1,0,0],
            [0,1,0],
            [0,0,1]
        ],dtype=np.float32)


        self._create_programs()
        self._create_ssbos()
        self._create_frame_buffers()
        self._create_screen_vertex_buffers()
        self._create_entity_vertex_buffers()

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
        
        light_frag_src = self._load_shader_src('my_pygame_light2d/fragment_light.glsl')

        blur_frag_src = self._load_shader_src('my_pygame_light2d/fragment_blur.glsl')

        mask_frag_src =  self._load_shader_src('my_pygame_light2d/fragment_mask.glsl')

        self._entity_draw_prog = self._ctx.program(vertex_shader = entities_draw_vert_src,
                                                    fragment_shader = entities_draw_frag_src)

        self._to_screen_draw_prog = self._ctx.program(vertex_shader =vertex_src,
                                                                 fragment_shader= fragment_src)
        self._tile_draw_prog = self._ctx.program(vertex_shader=tile_draw_vert_src,
                                                         fragment_shader= tile_draw_frag_src)
        
        self._prog_mask = self._ctx.program(vertex_shader= vertex_src,
                                            fragment_shader=mask_frag_src)


        self._prog_light = self._ctx.program(vertex_shader= vertex_src,
                                             fragment_shader= light_frag_src )
        
        self._prog_blur = self._ctx.program(vertex_shader= vertex_src,
                                            fragment_shader= blur_frag_src)
        
    
    def _create_ssbos(self)->None: 
        prog_glo = self._prog_light.glo

        blockIndex = glGetUniformBlockIndex(prog_glo, 'hullVSSBO')
        glUniformBlockBinding(prog_glo, blockIndex, 1)

        blockIndex = glGetUniformBlockIndex(prog_glo, 'hullIndSSBO')
        glUniformBlockBinding(prog_glo, blockIndex, 2)


        # Create SSBOs
        self._ssbo_v = self._ctx.buffer(reserve=4*8*self._max_hull_count)
        self._ssbo_v.bind_to_uniform_block(1)
        self._ssbo_ind = self._ctx.buffer(reserve=4*self._max_hull_count)
        self._ssbo_ind.bind_to_uniform_block(2)


        

    def _create_frame_buffers(self)->None: 
        # Frame buffers
        self._tex_bg = self._ctx.texture(self._true_res, components=4)
        self._tex_bg.filter = (NEAREST, NEAREST)
        self._fbo_bg = self._ctx.framebuffer([self._tex_bg])

        self._tex_fg = self._ctx.texture(self._true_res, components=4)
        self._tex_fg.filter = (NEAREST, NEAREST)
        self._fbo_fg = self._ctx.framebuffer([self._tex_fg])

        # Double buffer for lights
        self._buf_lt = DoubleBuffer(self._ctx, self._lightmap_res)

        # Ambient occlussion map
        self._tex_ao = self._ctx.texture(
            self._lightmap_res, components=4, dtype='f2')
        self._tex_ao.filter = (LINEAR, LINEAR)
        self._fbo_ao = self._ctx.framebuffer([self._tex_ao])


        # wrapping settings 
        self._buf_lt._tex1.repeat_x = False
        self._buf_lt._tex1.repeat_y = False
        self._buf_lt._tex2.repeat_x = False
        self._buf_lt._tex2.repeat_y = False

        self._tex_ao.repeat_x = False
        self._tex_ao.repeat_y = False
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

        screen_vbo = self._ctx.buffer(screen_vertex_data) 

        self._vao_light = self._ctx.vertex_array(
            self._prog_light,
            [
                (screen_vbo, '2f 2f', 'vertexPos', 'vertexTexCoord')
            ]
        )

        self._vao_blur = self._ctx.vertex_array(
            self._prog_blur,
            [
                (screen_vbo, '2f 2f' , 'vertexPos' , 'vertexTexCoord')
            ]
        )

        self._vao_mask = self._ctx.vertex_array(
            self._prog_mask,
            [
                (screen_vbo, '2f 2f' ,'vertexPos','vertexTexCoord')
            ]
        )

        self._vao_to_screen_draw = self._ctx.vertex_array(
            self._to_screen_draw_prog,
            [
                (screen_vbo, '2f 2f', 'vertexPos', 'vertexTexCoord'),
            ]
        )


    def _create_entity_vertex_buffers(self)->None:
        local_space_vertex_size = 2 * 4
        local_space_vertices_buffer_size = local_space_vertex_size * 6 * EntitiesManager.max_entities

        texcoords_vertex_size = 2 * 4
        texcoords_buffer_size = texcoords_vertex_size * 6 * EntitiesManager.max_entities

        transform_matrix_col_size  = 3 * 4 
        transform_column_buffer_size = transform_matrix_col_size *  3  * EntitiesManager.max_entities 

        self._entity_local_vertices_vbo= self._ctx.buffer(reserve=local_space_vertices_buffer_size, dynamic=True)
        self._entity_texcoords_vbo = self._ctx.buffer(reserve = texcoords_buffer_size, dynamic=True)
        
        
        self._entity_transform_matrices_vbo = self._ctx.buffer(reserve = transform_column_buffer_size, dynamic=True)


        self._vao_entity_draw = self._ctx.vertex_array(
            self._entity_draw_prog,
            [
                (self._entity_local_vertices_vbo, '12f/i', 'in_position'),
                (self._entity_texcoords_vbo, '12f/i', 'texcoord'),
                (self._entity_transform_matrices_vbo, '3f 3f 3f/i', 'col1', 'col2' ,'col3')
            ]
        )

    def _render_tilemap_to_bg_fbo(self,camera_offset:tuple[int,int])->None: 
        

        physical_tiles_render_bit = False
        non_physical_tiles_render_bit = False

        physical_tiles_texcoords_array = []
        physical_tiles_positions_array = []

        non_physical_tiles_texcoords_array = []
        non_physical_tiles_positions_array = []

        tile_size = self._ref_tilemap.regular_tile_size
        physical_tile_instances = 0
        non_physical_tile_instances= 0
        

        for x in range(camera_offset[0] // tile_size- 1, (camera_offset[0] + self._true_res[0]) // tile_size+ 1):
            for y in range(camera_offset[1] // tile_size- 1, (camera_offset[1] + self._true_res[1]) // tile_size+1):
                coor = (x,y) 

                for i, dict in enumerate(self._ref_tilemap.non_physical_tiles):
                    if coor in dict:
                        non_physical_tile_instances += 1
                        non_physical_tiles_render_bit = True
                        tile_info = self._ref_tilemap.non_physical_tiles[i][coor]

                        non_physical_tiles_texcoords_array.append(self._ref_tilemap.tile_texcoords[(tile_info.type,tile_info.relative_pos_ind,tile_info.variant)])
                        non_physical_tiles_positions_array.append(self._tile_position_to_ndc(coor,camera_offset))

                if coor in self._ref_tilemap.physical_tiles:
                    physical_tile_instances +=1
                    physical_tiles_render_bit = True
                    tile_data = self._ref_tilemap.physical_tiles[coor]
                    tile_general_info = tile_data.info 
                    relative_position_index, variant = tile_general_info.relative_pos_ind, tile_general_info.variant 

                    physical_tiles_texcoords_array.append(self._ref_tilemap.tile_texcoords[(tile_general_info.type,relative_position_index,variant)])
                    physical_tiles_positions_array.append(self._tile_position_to_ndc(coor,camera_offset))

        if non_physical_tiles_render_bit:
            buffer_data = np.array(non_physical_tiles_texcoords_array).astype(np.float32)
            self._ref_tilemap.write_to_non_physical_tiles_texcoords_vbo(buffer_data)

            positions_buffer_data = np.array(non_physical_tiles_positions_array).astype(np.float32)
            self._ref_tilemap.write_to_non_physical_tiles_positions_vbo(positions_buffer_data)

            self._fbo_bg.use()
            self._ref_tilemap.ref_texture_atlas.use()

            self._vao_non_physical_tiles_draw.render(vertices = 6, instances= non_physical_tile_instances)

        if physical_tiles_render_bit:
            buffer_data = np.array(physical_tiles_texcoords_array).astype(np.float32)
            self._ref_tilemap.write_to_physical_tiles_texcoords_vbo(buffer_data)

            positions_buffer_data = np.array(physical_tiles_positions_array).astype(np.float32)
            self._ref_tilemap.write_to_physical_tiles_positions_vbo(positions_buffer_data)

            self._fbo_bg.use()
            self._ref_tilemap.ref_texture_atlas.use()

            self._vao_physical_tiles_draw.render(vertices=6,instances= physical_tile_instances)



    def _tile_position_to_ndc(self,position:tuple[int,int],camera_offset:tuple[int,int])->tuple[float,float]:
        fbo_w,fbo_h = self._fbo_bg.size

        return (2. * (position[0] *self._ref_tilemap.regular_tile_size -camera_offset[0]) / fbo_w -1.
                , 1. - 2. * (position[1] * self._ref_tilemap.regular_tile_size - camera_offset[1]) / fbo_h)



    def _render_background_to_bg_fbo(self,camera_offset:tuple[int,int],infinite:bool = False)->None: 
        speed = 1
        
        for tex in self._ref_background.textures:
            if infinite: 
                num_tiles = (self._true_res[0]//tex.width) + 2

                for panel in range(-1,num_tiles):
                    x_pos = panel*tex.width - (camera_offset[0] * 0.05 *speed) % tex.width
                    vertex_data = self._create_infinite_background_texture_vertex_data(camera_offset,x_pos)
                    self._ref_background_vertices_buffer.write(vertex_data)

                    self._fbo_bg.use()
                    tex.use()

                    self._vao_background_draw.render()
            else: 
                for panel in range(-self._background_panels//2 , self._background_panels//2 +1):
                    vertex_data = self._create_background_texture_vertex_data(camera_offset,panel,speed)
                    self._ref_background_vertices_buffer.write(vertex_data)

                    self._fbo_bg.use()
                    tex.use()

                    self._vao_background_draw.render()
            speed += 1


    def _create_infinite_background_texture_vertex_data(self,camera_scroll:tuple[int,int],x_pos:int)->np.array:
        width,height = self._fbo_bg.size 
        x = 2. * (x_pos) / width - 1.
        y = 1. -2 * (-min(0,camera_scroll[1]) * 0.05) / height
        w = 2.
        h = 2.

        return np.array([(x,y),(x+w,y),(x,y-h),
                         (x,y-h),(x+w,y),(x+w,y-h)],dtype= np.float32)



    def _create_background_texture_vertex_data(self,camera_scroll:tuple[int,int],panel_num,speed:int)->np.array:
        width,height = self._fbo_bg.size 
        x = 2. * (panel_num*self._true_res[0]-camera_scroll[0] *0.05 * speed) / width - 1.
        y = 1. -2. * (-min(0,camera_scroll[1]) * 0.05) / height
        w = 2.
        h = 2. 

        return np.array([(x,y),(x+w,y),(x,y-h),
                         (x,y-h),(x+w,y),(x+w,y-h)],dtype= np.float32)


    def _point_to_uv(self, p: tuple[float, float]):
        return [p[0]/self._true_res[0], 1 - (p[1]/self._true_res[1])]

    
    def _send_hull_data_to_lighting_program(self,render_offset:tuple[int,int] = (0,0))->None: 
        vertices = []
        indices = []

        for hull in self.hulls:
            if not hull.enabled:
                continue
            vertices_buffer = [ ]

            #the vertices of the hulls are adjusted by the offset, then added to the list. 

            for vertice in hull.vertices:
                vertices_buffer.append((vertice[0]- render_offset[0], vertice[1]-render_offset[1]))
            vertices += vertices_buffer
            indices.append(len(vertices))

        # Store hull vertex data in SSBO
        vertices = [self._point_to_uv(v) for v in vertices]
        data_v = np.array(vertices, dtype=np.float32).flatten().tobytes()
        self._ssbo_v.write(data_v)

        # Store hull vertex indices in SSBO
        data_ind = np.array(indices, dtype=np.int32).flatten().tobytes()
        self._ssbo_ind.write(data_ind)


    def _render_to_light_buffer(self,interpolation_delta: float, dt, render_offset :tuple[int,int] = (0,0))->None:
        # Disable alpha blending to render lights
        ambient_lighting_range = self._ref_tilemap._ambient_node_ptr.range

        self._ctx.disable(BLEND)

        for i in range(len(self._ref_tilemap.lights) -1, -1,-1):
            light = self._ref_tilemap.lights[i]
            if light.popped:
                del self._ref_tilemap.lights[i]
                continue 
            if light.illuminator and light.illuminator.dead:
                del self._ref_tilemap.lights[i]
                continue 

            if not light.illuminator and (light.position[0] < ambient_lighting_range[0] or light.position[0] > ambient_lighting_range[1]):
                light.cur_power = max(0.0,light.cur_power - 8*dt*light.power)
            else: 
                light.cur_power = min(light.power,light.cur_power + 8*dt*light.power)

            if light.life == 0: 
                del self._ref_tilemap.lights[i]
                continue 
            elif light.life > 0: 
                light.life -= dt
            
            if not light.enabled:
                continue 

            self._buf_lt.tex.use()
            self._buf_lt.fbo.use()
            if light.radius_decay: 
                light.radius = max(1,light.radius * (light.life/light.maxlife))

            if light.illuminator: 
                
                #light.cur_power = max(0,light.power * (light.life/light.maxlife))
                light.position = (int(light.illuminator.center[0]+light.illuminator.velocity[0]*interpolation_delta) ,\
                                   int(light.illuminator.center[1]+light.illuminator.velocity[1]*interpolation_delta))    
                
            elif light.life > 0: 
                if light.maxlife-1 == light.life: 
                    light.position = (int(light.position[0]) , int(light.position[1]))
                
             
            # Send light uniforms
            self._prog_light['lightPos'] = self._point_to_uv((light.position[0]-render_offset[0] ,light.position[1]-render_offset[1]))
            self._prog_light['lightCol'] = light._color
            self._prog_light['lightPower'] = light.cur_power
            self._prog_light['radius'] = light.radius
            self._prog_light['castShadows'] = light.cast_shadows
            self._prog_light['native_width'] = self._true_res[0]
            self._prog_light['native_height'] = self._true_res[1]

            # Send number of hulls
            self._prog_light['numHulls'] = len(self.hulls)

            # Render onto lightmap
            self._vao_light.render()

            # Flip double buffer
            self._buf_lt.flip()

        self._ctx.enable(BLEND)


    def _render_aomap(self)->None:
        self._fbo_ao.use()
        self._buf_lt.tex.use()

        self._prog_blur['blurRadius'] = self._shadow_blur_radius
        self._vao_blur.render()


    def _render_background_layer(self)->None: 
        self._ctx.screen.use()
        self._tex_bg.use()
        self._tex_ao.use(1)

        self._prog_mask['lightmap'].value = 1
        self._prog_mask['ambient'].value = self._ambient_light_RGBA

        self._vao_mask.render()


    def _set_ambient(self, R: (int | tuple[int]) = 0, G: int = 0, B: int = 0, A: int = 255) -> None:
        self._ambient_light_RGBA = normalize_color_arguments(R, G, B, A)


    def _update_hulls(self,camera_scroll:tuple[int,int] = (0,0))->None: 
        if dist(self._prev_query_camera_scroll,camera_scroll) >= 16: 
            self.hulls = self._ref_tilemap.hull_grid.query(camera_scroll[0]-self._ref_tilemap.regular_tile_size * 10, camera_scroll[1] - self._ref_tilemap.regular_tile_size * 10,\
                                                           camera_scroll[0] + self._true_res[0] + self._ref_tilemap.regular_tile_size * 10, camera_scroll[1] + self._true_res[1] + self._ref_tilemap.regular_tile_size * 10)
            
            self._prev_query_camera_scroll = camera_scroll
    



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

        tex = self._ctx.texture(sfc.get_size(), components=4, data=img_data)
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

        vbo = self._ctx.buffer(buffer_data)
        vao = self._ctx.vertex_array(self._to_screen_draw_prog, [
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
        buffer_surf = pygame.Surface(self._true_res).convert_alpha()
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
            if 0 <= screen_x < self._true_res[0] and 0 <= screen_y < self._true_res[1]:
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



    def _render_fbos_to_screen_with_lighting(self,camera_scroll:tuple[int,int],interpolation_delta:float,dt:float,screen_shake:tuple[int,int] = (0,0))->None: 
        
        self._fbo_ao.clear(0,0,0,0)
        self._buf_lt.clear(0,0,0,0)

        render_offset = (camera_scroll[0] - screen_shake[0],camera_scroll[1] - screen_shake[1])

        self._update_hulls(camera_scroll)

        self._render_rectangles(camera_scroll)

        self._send_hull_data_to_lighting_program(render_offset)
 
        self._render_to_light_buffer(interpolation_delta,dt,render_offset)

        self._render_aomap()

        self._render_background_layer()
        



    def attatch_tilemap(self,tilemap:"Tilemap")->None:
        self._ref_tilemap = tilemap

        self._tile_draw_prog['NDCVertices'] = self._ref_tilemap.NDC_tile_vertices

        self._vao_physical_tiles_draw = self._ctx.vertex_array(
            self._tile_draw_prog,
            [
                (self._ref_tilemap.physical_tiles_position_vbo,'2f/i','in_position'),
                (self._ref_tilemap.physical_tiles_texcoords_vbo,'12f/i','in_texcoord'),
            ]
        )

        self._vao_non_physical_tiles_draw = self._ctx.vertex_array(
            self._tile_draw_prog,
            [
                (self._ref_tilemap.non_physical_tiles_position_vbo, '2f/i' , 'in_position'),
                (self._ref_tilemap.non_physical_tiles_texcoords_vbo, '12f/i' ,'in_texcoord')
            ]
        )


    def attatch_background(self,background:"Background")->None: 
        self._ref_background = background 
        background_vertices = np.zeros(shape=(12,),dtype=np.float32)

        self._ref_background_vertices_buffer = self._ctx.buffer(background_vertices,dynamic=True)
        texcoords_buffer = self._ctx.buffer(self._ref_background.identity_texcoords)

        self._vao_background_draw = self._ctx.vertex_array(
            self._to_screen_draw_prog,
            [
                (self._ref_background_vertices_buffer, '2f' , 'vertexPos'),
                (texcoords_buffer, '2f' , 'vertexTexCoord'),
            ]
        )


    def clear(self,R:int = 0, G:int = 0, B:int = 0,A:int =255)->None: 
        R,G,B,A =   normalize_color_arguments(R,G,B,A,)
        self._ctx.screen.clear(0,0,0,255)
        self._fbo_bg.clear(R,G,B,A)



    def process(self,camera_offset:tuple[int,int],interpolation_delta:float,dt:float)->None: 
        self._ctx.enable(BLEND)
        self._render_background_to_bg_fbo(camera_offset)
        self._render_tilemap_to_bg_fbo(camera_offset)

        entity_vertices = []
        entity_texcoords = []
        entity_matrices = []

        self._view_transform[0][2] = -camera_offset[0]
        self._view_transform[1][2] = -camera_offset[1]

        instance = 0 

        for entity, (state_info_comp,physics_comp,render_comp) in esper.get_components(StateInfoComponent,PhysicsComponent,RenderComponent):
            if state_info_comp.type == 'player':

                self._ref_tilemap.update_ambient_node_ptr(physics_comp.position[0])

                if isinstance(self._ref_tilemap._ambient_node_ptr,interpolatedLightNode):
                    self._set_ambient(self._ref_tilemap._ambient_node_ptr.get_interpolated_RGBA(physics_comp.position[0]))
                else: 
                    self._set_ambient(*self._ref_tilemap._ambient_node_ptr.colorValue)

                animation_data_collection = render_comp.animation_data_collection
                animation = animation_data_collection.get_animation(state_info_comp.curr_state)

                texcoords = self._ref_rm.entity_texcoords[(state_info_comp.type,state_info_comp.has_weapon,state_info_comp.curr_state,animation.curr_frame())]
                entity_local_vertices = render_comp.vertices    
                
                interpolated_model_transform = physics_comp.prev_transform * (1.0 - interpolation_delta) + physics_comp.transform * interpolation_delta

                clip_transform = self._projection_transform @ self._view_transform @ interpolated_model_transform 

                entity_vertices.extend(entity_local_vertices)
                entity_texcoords.extend(texcoords)

                column_major_clip_transform = clip_transform.T.flatten()
                entity_matrices.extend(column_major_clip_transform)

            else: 
                pass
            instance += 1

        self._entity_local_vertices_vbo.write(np.array(entity_vertices,dtype=np.float32).tobytes())
        self._entity_texcoords_vbo.write(np.array(entity_texcoords,dtype=np.float32).tobytes())
        self._entity_transform_matrices_vbo.write(np.array(entity_matrices,dtype=np.float32).tobytes())

        self._fbo_bg.use()
        self._ref_rm.texture_atlasses['entities'].use()
        self._vao_entity_draw.render(vertices= 6, instances= instance)

        self._render_fbos_to_screen_with_lighting(camera_offset,interpolation_delta,dt)

        # final render to the screen from the bg fbo 
        """
        self._ctx.screen.use()
        self._tex_bg.use()
        self._vao_to_screen_draw.render()
        """

class StateSystem(esper.Processor):


    def __init__(self)->None: 
        self._player_state_machine = PlayerStateMachine()
        self._enemy_state_machine = EnemyStateMachine()

    def process(self,dt:float)->None: 
        
        player, (input_comp,state_info_comp,physics_comp,render_comp) = esper.get_components(InputComponent,StateInfoComponent,PhysicsComponent,RenderComponent)[0]

        new_state = self._player_state_machine.change_state(input_comp,state_info_comp,physics_comp,render_comp,dt)
                

        for entity, (state_info_comp,physics_comp,render_comp) in esper.get_components(StateInfoComponent,PhysicsComponent,RenderComponent):
            if state_info_comp.type == 'player':
                continue

class InputHandler(esper.Processor):

    def __init__(self,game_context)->None: 
        self._ref_game_conetxt = game_context



    def _handle_common_events(self,event:pygame.Event)->None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                quit()
            if event.key == pygame.K_F12:
                pygame.display.toggle_fullscreen()

        if event.type == pygame.QUIT:
            pygame.quit()
            quit()


    def process(self,dt:float)->None: 
        player, (player_input_comp,player_physics_comp,player_state_comp) = esper.get_components(InputComponent,PhysicsComponent,StateInfoComponent)[0]

        hot_reload = False

        if self._ref_game_conetxt['gamestate'] == GameState.GameLoop: 
            for event in pygame.event.get():
                self._handle_common_events(event)

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F5: 
                        hot_reload = True 
                    if event.key == pygame.K_LSHIFT:
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
                        player_input_comp.open_inventory = not player_input_comp.open_inventory
                        # toggle inventory

                if event.type == pygame.KEYUP:
                    
                    if event.key == pygame.K_LSHIFT:
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


        return hot_reload


class StateMachine:

    def __init__(self)->None: 
        pass

    def change_state(self,physics_comp:PhysicsComponent)->str: 
        pass


class PlayerStateMachine(StateMachine):
    def change_state(self,input_comp:InputComponent,state_info_comp:StateInfoComponent,physics_comp:PhysicsComponent,render_comp:RenderComponent,dt:float):
        if state_info_comp.curr_state == 'land':
            pass
        else:
            if state_info_comp.collide_bottom:
                if physics_comp.velocity[0] == 0:
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
                    if physics_comp.velocity[1] > 0:
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