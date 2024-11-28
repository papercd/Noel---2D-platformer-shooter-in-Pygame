from pygame import Rect,mouse
from moderngl import Texture

class Cursor: 
    def __init__(self,texture_atl: Texture,in_editor :bool = False):
        self._tex_atl = texture_atl

        self.in_editor = in_editor 
        self.pos = [0,0] 

        self.text = None 

        self.interacting = False 
        self.item = None
        self.state = "default"
        self.box = Rect(*self.pos,1,1)
        self.cooldown = 0
        self.pressed=  0 
        self.magnet = False 
        self.move = False 
        self.text = None 
        self.special_actions = False 
        self.pressed = [0,0]

    @property   
    def texture_atlas(self) -> Texture: 
        return self._tex_atl

    def set_cooldown(self) -> None:
        self.cooldown = 10

    def update(self):
        if not self.in_editor:
            if self.cooldown >0 :
                self.cooldown -=1 
            
            self.magnet = self.special_actions and self.item is not None 
            self.move = self.special_actions and not self.magnet 

            if self.text is not None:
                #TODO : add this part later. 
                self.text = None 

            if self.interacting: 
                if self.magnet : self.state = 'magnet'
                elif self.move: self.state = 'move'
                elif self.item is not None: self.state = 'grab'
                else: self.state = "default"
            else: 
                #TODO: add the crosshair here later. 

                self.state = "default"
        else: 
            if self.interacting: 
                if self.item : self.state = "grab"
                else: self.state = 'default'
            pass 