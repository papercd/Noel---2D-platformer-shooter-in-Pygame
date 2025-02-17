from pygame import Rect
from pygame.mouse import get_pos
from scripts.data import PHYSICS_TIMESTEP
from scripts.new_resource_manager import ResourceManager
from math import atan2

from numpy import uint8,uint16,float32,int32,array
class Cursor: 
    def __init__(self,in_editor :bool = False)-> None:

        self._ref_rm = ResourceManager.get_instance()

        self.ndc_vertices,self.ndc_vertices_buffer = self._ref_rm.get_cursor_ndc_vertices_and_buffer()
        
        self.ref_prev_hovered_cell = None
        self.ref_hovered_cell = None

        self.in_editor = in_editor 
        self.topleft = array([0,0],dtype = int32)
        self.text = None 
        self.size = (uint16(9),uint16(10))
        self.interacting = False 
        self.item = None
        self.state = "default"
        self.prev_state = "default"
        self.box = Rect(0,0,1,1)
        self.cooldown = array([10 * PHYSICS_TIMESTEP],dtype = float32)
        self.magnet = False 
        self.move = False 
        self.text = None 
        self.special_actions = False 
        self.pressed = [False,False]

    def set_cooldown(self) -> None:
        self.cooldown[0] = 10 * PHYSICS_TIMESTEP


    def get_angle_from_point(self,point)->float: 
        dx = self.topleft[0] - point[0]
        dy = self.topleft[1] - point[1]

        return atan2(-dy,dx)

        

    def update(self,display_scale_ratio:uint8,dt:float32,cursor_state_change_callback:"function")-> None:

        new_topleft = get_pos()

        self.topleft[0] = int32(new_topleft[0]) // int32(display_scale_ratio)
        self.topleft[1] = int32(new_topleft[1]) // int32(display_scale_ratio)

        self.box.x = self.topleft[0]
        self.box.y = self.topleft[1]

        if not self.in_editor:
            if self.cooldown[0] > float32(0) :
                self.cooldown[0] -= dt
            
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
