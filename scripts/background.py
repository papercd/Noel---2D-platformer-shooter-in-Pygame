import pygame 

class Background:
    def __init__(self,textures,infinite = True):
        self.bg_layers =textures 
        self.infinite = infinite

    def render(self,render_engine_ref,layer,offset= (0,0)): 
        scroll = offset[0]
        native_res = render_engine_ref.get_native_res() 
        speed = 1
        for tex in self.bg_layers:
            for panels in range(-1,2):
                render_engine_ref.render_texture(
                    tex,layer,
                    dest= pygame.Rect(panels*native_res[0]-scroll * 0.05 * speed,-min(0,offset[1]) * 0.05,native_res[0],native_res[1]),
                    source= pygame.Rect(0,0,tex.width,tex.height)   
                )
            speed += 1 