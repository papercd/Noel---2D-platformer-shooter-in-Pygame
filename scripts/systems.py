import esper
from scripts.game_state import GameState
from scripts.game_state import GameState
from scripts.data import TERMINAL_VELOCITY,GRAVITY
from scripts.new_resource_manager import ResourceManager
from scripts.new_entities_manager import EntitiesManager 
from scripts.components import PhysicsComponent,RenderComponent, StateInfoComponent,InputComponent
from my_pygame_light2d.double_buffer import DoubleBuffer
from my_pygame_light2d.color import normalize_color_arguments
import pygame
from moderngl import NEAREST,LINEAR,BLEND
from math import sqrt,ceil
import numpy as np

from typing import TYPE_CHECKING 

if TYPE_CHECKING: 
    from my_pygame_light2d.light import PointLight
    from my_pygame_light2d.hull import Hull
    from scripts.background import Background
    from pygame.rect import Rect
    from scripts.data import TileInfo, TileInfoDataClass
    from moderngl import Context
    from scripts.new_tilemap import Tilemap

class PhysicsSystem(esper.Processor):
    def __init__(self)->None: 
        self._ref_tilemap:"Tilemap" = None

    def _handle_collision(self,physics_comp:PhysicsComponent,rect_tile: tuple["Rect","TileInfoDataClass"],
                          tile_size:int, dt:float,axis_bit:bool)->None: 

        if axis_bit == True: # x_axis
            pass 
        else: 
            if rect_tile[1].info.type.endswith('stairs'):
                pass 
            else: 
                if rect_tile[1].info.type.endswith('door'):
                    pass

                if physics_comp.velocity[1] >0 :
                    physics_comp.position[1] = rect_tile[0].top - physics_comp.size[1] // 2
                    physics_comp.collision_rect.bottom = rect_tile[0].top 
                    physics_comp.velocity[1] = GRAVITY * dt
                elif physics_comp.velocity[1] < 0:
                    physics_comp.position[1] = rect_tile[0].bottom + physics_comp.size[1] // 2
                    physics_comp.collision_rect.top = rect_tile[0].bottom 
                    physics_comp.velocity[1] = 0



    def attatch_tilemap(self,tilemap:"Tilemap")->None: 
        self._ref_tilemap =tilemap

    def process(self,dt:float)->None: 
        for entity, physics_comp in esper.get_component(PhysicsComponent):
            #print(physics_comp.velocity[1])
            physics_comp.flip = physics_comp.velocity[0] < 0
            
            physics_comp.velocity[0] = physics_comp.velocity[0] + physics_comp.acceleration[0] * dt
            physics_comp.velocity[1] = min(TERMINAL_VELOCITY,physics_comp.velocity[1] + physics_comp.acceleration[1] * dt)
            
            
            physics_comp.position[0] += physics_comp.velocity[0] * dt
            physics_comp.collision_rect.x += physics_comp.velocity[0] * dt

            for rect_tile in self._ref_tilemap.query_rect_tile_pair_around_ent(physics_comp.collision_rect.topleft,
                                                                               physics_comp.collision_rect.size):
                if physics_comp.collision_rect.colliderect(rect_tile[0]):
                    self._handle_collision(physics_comp,rect_tile,self._ref_tilemap.regular_tile_size,dt,axis_bit = False)
            


            physics_comp.position[1] += physics_comp.velocity[1] * dt 
            physics_comp.collision_rect.y += physics_comp.velocity[1] * dt

            for rect_tile in self._ref_tilemap.query_rect_tile_pair_around_ent(physics_comp.collision_rect.topleft,
                                                                               physics_comp.collision_rect.size):
                if physics_comp.collision_rect.colliderect(rect_tile[0]):
                    self._handle_collision(physics_comp,rect_tile,self._ref_tilemap.regular_tile_size,dt,axis_bit = True)
 






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

        self.shadow_blur_radious = 5

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


    def _create_programs(self)->None: 
        vertex_src,fragment_src = self._load_shader_srcs('my_pygame_light2d/vertex.glsl',
                                                         'my_pygame_light2d/fragment_draw.glsl')

        tile_draw_vert_src,tile_draw_frag_src = self._load_shader_srcs('my_pygame_light2d/tile_vert.glsl',
                                                                       'my_pygame_light2d/tile_frag.glsl')


        entities_draw_vert_src,entities_draw_frag_src = self._load_shader_srcs('my_pygame_light2d/entity_draw_vert.glsl',
                                                                                 'my_pygame_light2d/entity_draw_frag.glsl')
        

        self._entity_draw_prog = self._ctx.program(vertex_shader = entities_draw_vert_src,
                                                    fragment_shader = entities_draw_frag_src)


        self._to_screen_draw_prog = self._ctx.program(vertex_shader =vertex_src,
                                                                 fragment_shader= fragment_src)
        self._tile_draw_prog = self._ctx.program(vertex_shader=tile_draw_vert_src,
                                                         fragment_shader= tile_draw_frag_src)
        

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

        """
        if non_physical_tiles_render_bit:
            buffer_data = np.array(non_physical_tiles_texcoords_array).astype(np.float32)
            self._ref_tilemap.write_to_non_physical_tiles_texcoords_vbo(buffer_data)

            positions_buffer_data = np.array(non_physical_tiles_positions_array).astype(np.float32)
            self._ref_tilemap.write_to_non_physical_tiles_positions_vbo(positions_buffer_data)

            self._fbo_bg.use()
            self._ref_tilemap.ref_texture_atlas.use()

            self._vao_non_physical_tiles_draw.render(vertices = 6, instances= non_physical_tile_instances)
        """
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



    def process(self,camera_offset:tuple[int,int],interpolation_delta:float)->None: 
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
                animation_data_collection = render_comp.animation_data_collection
                animation = animation_data_collection.get_animation(state_info_comp.curr_state)

                texcoords = self._ref_rm.entity_texcoords[(state_info_comp.type,state_info_comp.has_weapon,state_info_comp.curr_state,animation.curr_frame())]
                entity_local_vertices = render_comp.vertices    

                clip_transform = self._projection_transform @ self._view_transform @ physics_comp.transform 

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

        self._ctx.screen.use()
        self._tex_bg.use()
        self._vao_to_screen_draw.render()



class InputHandler(esper.Processor):

    def __init__(self,game_context,scroll:list[int,int])->None: 
        self._ref_game_conetxt = game_context

        # temporary scroll reference 
        self._scroll = scroll


    def _handle_common_events(self,event:pygame.Event)->None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                quit()
            if event.key == pygame.K_F12:
                pygame.display.toggle_fullscreen()


    def process(self)->None: 
        player, (player_input_comp,player_physics_comp,player_state_comp) = esper.get_components(InputComponent,PhysicsComponent,StateInfoComponent)[0]

        if self._ref_game_conetxt['gamestate'] == GameState.GameLoop: 
            for event in pygame.event.get():
                self._handle_common_events(event)

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_w:
                        player_input_comp.up = True
                        # move player up by 1 pixel to avoid collision with the ground
                        
                        player_physics_comp.position[1] -= 1
                        player_physics_comp.collision_rect.y -= 1

                        player_physics_comp.velocity[1] = -400


                    """
                    if event.key == pygame.K_w: 
                        self._scroll[1] -= 100
                    if event.key == pygame.K_s: 
                        self._scroll[1] += 100
                    if event.key == pygame.K_a: 
                        self._scroll[0] -= 100
                    if event.key == pygame.K_d: 
                        self._scroll[0] += 100
                    """
 
        




