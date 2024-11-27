from scripts.new_entities import Player
from scripts.new_inventory import Inventory_Engine
from scripts.atlass_positions import UI_ATLAS_POSITIONS_AND_SIZES
from scripts.new_ui import HealthBar,StaminaBar
import numpy as np


class HUD: 
    def __init__(self,ui_atlas,player:Player,true_res:tuple[int,int]):
        self._player = player
        self._true_res = true_res
        self._ui_atlas = ui_atlas

        self._create_display_elements()
        self._precompute_texture_coords_and_vertices()


    def _precompute_texture_coords_and_vertices(self):
        self._tex_dict = {}
        for key in self._elements: 
            pos,size = UI_ATLAS_POSITIONS_AND_SIZES[key]
            self._tex_dict[key] = self._get_texture_coords_for_ui(pos,size)


    def _get_texture_coords_for_ui(self,bottomleft:tuple[int,int],size:tuple[int,int]) ->np.array:
        x = (bottomleft[0] ) / self._ui_atlas.width
        y = (bottomleft[1] ) / self._ui_atlas.height

        w = size[0] / self._ui_atlas.width
        h = size[1] / self._ui_atlas.height

        p1 = (x,y+h) 
        p2 = (x+w,y+h)
        p3 = (x,y) 
        p4 = (x+w,y)

        return np.array([p1,p2,p3,
                         p3,p2,p4],dtype = np.float32 )


    def _create_display_elements(self):
        self._health_bar_topleft = (self._true_res[0]//12,self._true_res[1] * 26 // 30)
        self._stamina_bar_topleft = (self._true_res[0]//12,self._true_res[1] * 27//30 + 1)

        self._health_bar_width = self._true_res[0]*4//10
        self._stamina_bar_width = self._true_res[0]*3//10

        self._bar_height = self._true_res[1] // 30 

        self._health_bar = HealthBar(*self._health_bar_topleft,self._health_bar_width,self._bar_height,self._player.health)
        self._stamina_bar = StaminaBar(*self._stamina_bar_topleft,self._stamina_bar_width,self._bar_height,self._player.stamina)
        self._inven_list = [

        ]
        self._items_engine = Inventory_Engine(self._inven_list,self._player)
        
        
        self._elements = {
            'health_bar' : self._health_bar,
            'stamina_bar' : self._stamina_bar,
        }


    def update(self):
        self._health_bar.update(self._player.health)
        self._stamina_bar.update(self._player.stamina)
