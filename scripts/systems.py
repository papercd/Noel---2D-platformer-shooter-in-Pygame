import esper
from scripts.data import TERMINAL_VELOCITY,GRAVITY
from scripts.components import PhysicsComponent,RenderComponent
from my_pygame_light2d.double_buffer import DoubleBuffer
from my_pygame_light2d.color import normalize_color_arguments
from moderngl import NEAREST,LINEAR,BLEND
from math import sqrt
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
                    physics_comp.velocity[1] = GRAVITY * dt
                    physics_comp.collision_rect.bottom = rect_tile[0].top 
                elif physics_comp.velocity[1] < 0 :
                    physics_comp.velocity[1] = 0
                    physics_comp.collision_rect.top = rect_tile[0].bottom
                
                physics_comp.position[1] = physics_comp.collision_rect.y


    def attatch_tilemap(self,tilemap:"Tilemap")->None: 
        self._ref_tilemap =tilemap

    def process(self,dt:float)->None: 
        for entity, physics_comp in esper.get_component(PhysicsComponent):
            physics_comp.flip = physics_comp.velocity[0] < 0
            
            physics_comp.velocity[0] = physics_comp.velocity[0] + physics_comp.acceleration[0] * dt
            physics_comp.velocity[1] = min(TERMINAL_VELOCITY,physics_comp.velocity[1] + physics_comp.acceleration[1] * dt)
            
            physics_comp.position[0] += physics_comp.velocity[0] * dt
            physics_comp.collision_rect.move(physics_comp.velocity[0] * dt,0)

            for rect_tile in self._ref_tilemap.query_rect_tile_pair_around_ent(physics_comp.collision_rect.topleft,
                                                                               physics_comp.collision_rect.size):
                if physics_comp.collision_rect.colliderect(rect_tile[0]):
                    self._handle_collision(physics_comp,rect_tile,self._ref_tilemap.regular_tile_size,dt,axis_bit = False)
            

            physics_comp.position[1] += physics_comp.velocity[1] * dt 
            physics_comp.collision_rect.move(0,physics_comp.velocity[1] * dt)

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

        self._create_programs()
        self._create_frame_buffers()
        self._create_screen_vertex_buffers()

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


    def _render_tilemap_to_bg_fbo(self,camera_offset:tuple[int,int])->None: 
        physical_tiles_vertices_array = []
        physical_tiles_texcoords_array = []

        non_physical_tiles_vertices_array = []
        non_physical_tiles_texcoords_array = []

        tile_size = self._ref_tilemap.regular_tile_size

        physical_tiles_render_bit = False 
        non_physical_tiles_render_bit = False

        physical_tiles_buffer_data_size = 0
        non_physical_tiles_buffer_data_size = 0

        for x in range(camera_offset[0] // tile_size- 1, (camera_offset[0] + self._true_res[0]) // tile_size+ 1):
            for y in range(camera_offset[1] // tile_size- 1, (camera_offset[1] + self._true_res[1]) // tile_size+1):
                coor = (x,y) 
                for i,dict in enumerate(self._ref_tilemap.non_physical_tiles):
                    if coor in dict:
                        non_physical_tiles_render_bit = True
                        tile_info = self._ref_tilemap.non_physical_tiles[i][coor]
                        
                        vertices = self._create_tile_vertices(tile_info,camera_offset)
                        texcoords = self._ref_tilemap.tile_texcoords[(tile_info.type,tile_info.relative_pos_ind,tile_info.variant)]

                        non_physical_tiles_vertices_array.append(vertices)
                        non_physical_tiles_texcoords_array.append(texcoords)

                        non_physical_tiles_buffer_data_size += 96 

                if coor in self._ref_tilemap.physical_tiles:
                    physical_tiles_render_bit = True
                    tile_data = self._ref_tilemap.physical_tiles[coor]
                    tile_general_info =tile_data.info
                    relative_position_index,variant = tile_general_info.relative_pos_ind,tile_general_info.variant
                    
                    vertices = self._create_tile_vertices(tile_general_info,camera_offset)
                    texcoords= self._ref_tilemap.tile_texcoords[(tile_general_info.type,relative_position_index,variant)]

                    physical_tiles_vertices_array.append(vertices)
                    physical_tiles_texcoords_array.append(texcoords)

                    physical_tiles_buffer_data_size += 96 
        
        if non_physical_tiles_render_bit:
            
            vertices_array = np.concatenate(non_physical_tiles_vertices_array,axis = 0)
            texcoords_array = np.concatenate(non_physical_tiles_texcoords_array,axis = 0)

            buffer_data = np.column_stack((vertices_array,texcoords_array)).astype(np.float32)
            self._ref_tilemap.write_to_non_physical_tiles_vbo(buffer_data,non_physical_tiles_buffer_data_size)

            self._fbo_bg.use()
            self._ref_tilemap.ref_texture_atlas.use()
            self._vao_non_physical_tiles_draw.render(first = self._ref_tilemap.non_physical_tiles_vbo_vertices - non_physical_tiles_buffer_data_size // 16)

        if physical_tiles_render_bit:
            vertices_array = np.concatenate(physical_tiles_vertices_array,axis= 0)
            texcoords_array = np.concatenate(physical_tiles_texcoords_array,axis=0)

            buffer_data = np.column_stack((vertices_array,texcoords_array)).astype(np.float32)

            self._ref_tilemap.write_to_physical_tiles_vbo(buffer_data,physical_tiles_buffer_data_size)

            self._fbo_bg.use()
            self._ref_tilemap.ref_texture_atlas.use()
            self._vao_physical_tiles_draw.render(first = self._ref_tilemap.physical_tiles_vbo_vertices - physical_tiles_buffer_data_size // 16)


    def _create_tile_vertices(self,tile_info:"TileInfo",camera_scroll:tuple[int,int])->np.array: 
        tile_pos = tile_info.tile_pos 
        fbo_w,fbo_h = self._fbo_bg.size

        x = 2. * (tile_pos[0] * self._ref_tilemap._regular_tile_size-camera_scroll[0] )/ fbo_w- 1.
        y = 1. - 2. * (tile_pos[1] * self._ref_tilemap._regular_tile_size- camera_scroll[1])/ fbo_h
        w = 2. * 16 / fbo_w
        h = 2. * 16 /fbo_h 
        
        # vertices = np.array([(x, y), (x + w, y), (x, y - h),
        #                    (x, y - h), (x + w, y), (x + w, y - h)], dtype=np.float32)
        
        vertices = [(x, y), (x + w, y), (x, y - h),
                            (x, y - h), (x + w, y), (x + w, y - h)]

        return vertices




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
        self._vao_physical_tiles_draw = self._ctx.vertex_array(
            self._tile_draw_prog,
            [
                (self._ref_tilemap.physical_tiles_vbo, '2f 2f', 'in_position', 'in_texcoord'),
            ]
        )
        self._vao_non_physical_tiles_draw = self._ctx.vertex_array(
            self._tile_draw_prog,
            [
                (self._ref_tilemap.non_physical_tiles_vbo,'2f 2f','in_position','in_texcoord'),
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

        self._ctx.screen.use()
        self._tex_bg.use()
        self._vao_to_screen_draw.render()

        for entity, (physics_comp,render_comp) in esper.get_components(PhysicsComponent,RenderComponent):
            pass
