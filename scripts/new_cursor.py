from pygame import Rect
from pygame.mouse import get_pos
from scripts.data import TIME_FOR_ONE_LOGICAL_STEP
import numpy as np
class Cursor: 
    def __init__(self,in_editor :bool = False)-> None:

        self.in_editor = in_editor 
        self.topleft = [0,0]  
        self.text = None 
        self.size = (9,10)
        self.interacting = False 
        self.item = None
        self.state = "default"
        self.prev_state = "default"
        self.box = Rect(*self.topleft,1,1)
        self.cooldown = 10 * TIME_FOR_ONE_LOGICAL_STEP
        self.pressed=  0 
        self.magnet = False 
        self.move = False 
        self.text = None 
        self.special_actions = False 
        self.pressed = [0,0]

    def set_cooldown(self) -> None:
        self.cooldown = 10 * TIME_FOR_ONE_LOGICAL_STEP

    def update(self,display_scale_ratio:int,dt:float,cursor_state_change_callback)-> None:
 
        new_topleft = get_pos()
        self.topleft[0] = new_topleft[0] // display_scale_ratio
        self.topleft[1] = new_topleft[1] // display_scale_ratio


        if not self.in_editor:
            if self.cooldown >0 :
                self.cooldown -= dt
            
            self.magnet = self.special_actions and self.item is not None 
            self.move = self.special_actions and not self.magnet 


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

        if self.prev_state != self.state: 
            cursor_state_change_callback(self.state)
            self.prev_state = self.state
