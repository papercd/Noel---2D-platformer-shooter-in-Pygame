
from math import sqrt
import numpy as np 
from moderngl import Context

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
        
