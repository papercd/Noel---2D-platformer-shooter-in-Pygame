import pygame 
from my_pygame_light2d.engine import RenderEngine
from moderngl import Texture
class Background:
    "A class for managing Background scene with parallax"

    def __init__(self,textures:list[Texture],infinite :bool = False):
        """
        Initialize the Background object.
        
        Args:
            textures (list[moderngl.Texture]) : the list of textures that are to be rendered in the way they are ordered. 
            infinite (bool = False) : a boolean to indicate whether the background should wrap around the screen 
        """
        self.bg_textures =textures 
        self.infinite = infinite
    

    def render(self,render_engine_ref:RenderEngine,layer,offset= (0,0)): 
        scroll = offset[0]
        native_res = render_engine_ref.get_native_res() 
        speed = 1
        for tex in self.bg_textures:
            for panels in range(-1,2):
                render_engine_ref.render_texture(
                    tex,layer,
                    dest= pygame.Rect(panels*native_res[0]-scroll * 0.05 * speed,-min(0,offset[1]) * 0.05,native_res[0],native_res[1]),
                    source= pygame.Rect(0,0,tex.width,tex.height)   
                )
            speed += 1 