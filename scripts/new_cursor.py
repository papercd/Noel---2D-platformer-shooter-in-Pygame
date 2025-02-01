from pygame import Rect
from pygame.mouse import get_pos
from scripts.data import PHYSICS_TIMESTEP
from scripts.new_resource_manager import ResourceManager
import numpy as np
class Cursor: 
    def __init__(self,in_editor :bool = False)-> None:

        self._ref_rm = ResourceManager.get_instance()

        self.ndc_vertices,self.ndc_vertices_buffer = self._ref_rm.get_cursor_ndc_vertices_and_buffer()
        
        self.ref_prev_hovered_cell = None
        self.ref_hovered_cell = None

        self.in_editor = in_editor 
        self.topleft = [0,0]  
        self.text = None 
        self.size = (9,10)
        self.interacting = False 
        self.item = None
        self.state = "default"
        self.prev_state = "default"
        self.box = Rect(0,0,1,1)
        self.cooldown = 10 * PHYSICS_TIMESTEP
        self.pressed=  0 
        self.magnet = False 
        self.move = False 
        self.text = None 
        self.special_actions = False 
        self.pressed = [0,0]

    def set_cooldown(self) -> None:
        self.cooldown = 10 * PHYSICS_TIMESTEP

    def update(self,display_scale_ratio:int,dt:float,cursor_state_change_callback:"function")-> None:

        new_topleft = get_pos()
        self.topleft[0] = new_topleft[0] // display_scale_ratio
        self.topleft[1] = new_topleft[1] // display_scale_ratio

        self.box.x = self.topleft[0]
        self.box.y = self.topleft[1]

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
