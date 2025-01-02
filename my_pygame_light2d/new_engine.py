
from math import sqrt
import numpy as np 
from moderngl import Context,NEAREST,LINEAR
from my_pygame_light2d.color import normalize_color_arguments
from my_pygame_light2d.double_buff import DoubleBuffer
from typing import TYPE_CHECKING

if TYPE_CHECKING: 
    from scripts.data import TileInfo 
    from scripts.new_tilemap import Tilemap 
    from my_pygame_light2d.light import PointLight
    from my_pygame_light2d.hull import Hull


class RenderEngine:
    _instance = None 
    _ctx :"Context" = None 

    @staticmethod 
    def get_instance(ctx:"Context"= None,true_to_screen_res_ratio:int =1,screen_res:tuple[int,int] = (500,500),\
                     true_res:tuple[int,int] = (500,500))->"RenderEngine":
        if RenderEngine._instance is not None: 
            return RenderEngine._instance
        else: 
            assert isinstance(ctx,Context)
            RenderEngine._ctx = ctx
            RenderEngine._instance = RenderEngine(true_to_screen_res_ratio,screen_res,true_res)

        return RenderEngine._instance

    def __init__(self,true_to_screen_res_ratio:int, screen_res:tuple[int,int],true_res :tuple[int,int])->None:


        # Initialize  members
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





    
    def _create_frame_buffers(self)->None: 
        # Frame buffers
        self._tex_bg = RenderEngine._ctx.texture(self._true_res, components=4)
        self._tex_bg.filter = (NEAREST, NEAREST)
        self._fbo_bg = RenderEngine._ctx.framebuffer([self._tex_bg])

        self._tex_fg = RenderEngine._ctx.texture(self._true_res, components=4)
        self._tex_fg.filter = (NEAREST, NEAREST)
        self._fbo_fg = RenderEngine._ctx.framebuffer([self._tex_fg])

        # Double buffer for lights
        self._buf_lt = DoubleBuffer(RenderEngine._ctx, self._lightmap_res)

        # Ambient occlussion map
        self._tex_ao = RenderEngine._ctx.texture(
            self._lightmap_res, components=4, dtype='f2')
        self._tex_ao.filter = (LINEAR, LINEAR)
        self._fbo_ao = RenderEngine._ctx.framebuffer([self._tex_ao])


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
        
        
        self._to_screen_draw_prog = RenderEngine._ctx.program(vertex_shader =vertex_src,
                                                                 fragment_shader= fragment_src)
        self._tile_draw_prog = RenderEngine._ctx.program(vertex_shader=tile_draw_vert_src,
                                                         fragment_shader= tile_draw_frag_src)

    def _create_screen_vertex_buffers(self)->None: 
        screen_vertices = np.array([(-1.0, 1.0), (1.0, 1.0), (-1.0, -1.0),
                                    (-1.0, -1.0), (1.0, 1.0), (1.0, -1.0)], dtype=np.float32)
        screen_tex_coords = np.array([(0.0, 1.0), (1.0, 1.0), (0.0, 0.0),
                                      (0.0, 0.0), (1.0, 1.0), (1.0, 0.0)], dtype=np.float32)
        screen_vertex_data = np.hstack([screen_vertices, screen_tex_coords])

        screen_vbo = RenderEngine._ctx.buffer(screen_vertex_data) 

        self._vao_to_screen_draw = RenderEngine._ctx.vertex_array(
            self._to_screen_draw_prog,
            [
                (screen_vbo, '2f 2f', 'vertexPos', 'vertexTexCoord'),
            ]
        )


    def _render_tilemap(self,camera_scroll:tuple[int,int])->None: 
        vertices_array = []
        texcoords_array = []

        tile_size = self._ref_tilemap.regular_tile_size

        has_something_to_render = False
        tile_data_count =  0

        for x in range(camera_scroll[0] // tile_size- 3, (camera_scroll[0] + self._true_res[0]) // tile_size+ 3):
            for y in range(camera_scroll[1] // tile_size- 3, (camera_scroll[1] + self._true_res[1]) // tile_size+3):
                coor = (x,y) 
                if coor in self._ref_tilemap.physical_tiles:
                    tile_data_count +=1
                    has_something_to_render = True
                    tile_data = self._ref_tilemap.physical_tiles[coor]
                    tile_general_info =tile_data.info
                    relative_position_index,variant = tile_general_info.relative_pos_ind,tile_general_info.variant
                    
                    position = self._create_tile_vertices(tile_general_info,camera_scroll)
                    texcoords= self._ref_tilemap.tile_texcoords[(tile_general_info.type,relative_position_index,variant)]

                    vertices_array.append(position)
                    texcoords_array.append(texcoords)

        if has_something_to_render:
            vertices_array = np.concatenate(vertices_array,axis= 0)
            texcoords_array = np.concatenate(texcoords_array,axis=0)

            buffer_data = np.column_stack((vertices_array,texcoords_array)).astype(np.float32)
            self._ref_tilemap.write_to_physical_tiles(buffer_data)

            self._fbo_bg.use()
            self._ref_tilemap.ref_texture_atlas.use()
            self._vao_physical_tiles_draw.render(vertices=12 * tile_data_count)

    def _create_tile_vertices(self,tile_info:"TileInfo",camera_scroll:tuple[int,int])->np.array: 
        tile_pos = tile_info.tile_pos 
        fbo_w,fbo_h = self._fbo_bg.size

        x = 2. * (tile_pos[0] * self._ref_tilemap._regular_tile_size-camera_scroll[0] )/ fbo_w- 1.
        y = 1. - 2. * (tile_pos[1] * self._ref_tilemap._regular_tile_size- camera_scroll[1])/ fbo_h
        w = 2. * 16 / fbo_w
        h = 2. * 16 /fbo_h 
        vertices = np.array([(x, y), (x + w, y), (x, y - h),
                            (x, y - h), (x + w, y), (x + w, y - h)], dtype=np.float32)
        
        return vertices


    def bind_tilemap(self,tilemap:"Tilemap")->None: 
        self._ref_tilemap = tilemap 
        self._vao_physical_tiles_draw = RenderEngine._ctx.vertex_array(
            self._tile_draw_prog,
            [
                (self._ref_tilemap.physical_tiles_vbo, '2f 2f', 'in_position', 'in_texcoord'),
            ]
        )



    def render_to_background_fbo(self,camera_scroll:tuple[int,int])->None: 
        self._render_tilemap(camera_scroll)



    def clear(self,R = 0,G= 0 ,B= 0 ,A = 255)->None:
        R,G,B,A = normalize_color_arguments(R,G,B,A) 
        self._ctx.screen.clear(0,0,0,255)
        self._fbo_bg.clear(R,G,B,A) 


    def render_fbos_to_screen_with_lighting(self)->None: 
        # TESTING, doesn't have lighting yet. 


        RenderEngine._ctx.screen.use()
        self._tex_bg.use()
        self._vao_to_screen_draw.render()


    