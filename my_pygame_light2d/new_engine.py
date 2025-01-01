
from math import sqrt
import numpy as np 
from moderngl import Context,NEAREST,LINEAR
from my_pygame_light2d.double_buff import DoubleBuffer

from typing import TYPE_CHECKING

if TYPE_CHECKING: 
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

        self._create_screen_vertex_buffers()

        self._create_frame_buffers()




    
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
        
        self._no_transform_draw_prog = RenderEngine._ctx.program(vertex_shader =vertex_src,
                                                                 fragment_shader= fragment_src)
        

    def _create_screen_vertex_buffers(self)->None: 
        screen_vertices = np.array([(-1.0, 1.0), (1.0, 1.0), (-1.0, -1.0),
                                    (-1.0, -1.0), (1.0, 1.0), (1.0, -1.0)], dtype=np.float32)
        screen_tex_coords = np.array([(0.0, 1.0), (1.0, 1.0), (0.0, 0.0),
                                      (0.0, 0.0), (1.0, 1.0), (1.0, 0.0)], dtype=np.float32)
        screen_vertex_data = np.hstack([screen_vertices, screen_tex_coords])

        screen_vbo = RenderEngine._ctx.buffer(screen_vertex_data) 
        self._vao_no_transform_draw = RenderEngine._ctx.vertex_array(
            self._no_transform_draw_prog,
            [
                (screen_vbo, '2f 2f', 'vertexPos', 'vertexTexCoord'),
            ]
        )
