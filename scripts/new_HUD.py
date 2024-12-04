from scripts.new_cursor import Cursor 
from scripts.new_entities import Player
from scripts.new_inventory import Inventory_Engine,Inventory,WeaponInventory    
from scripts.atlass_positions import UI_ATLAS_POSITIONS_AND_SIZES,ITEM_ATLAS_POSITIONS
from scripts.new_ui import HealthBar,StaminaBar
from scripts.item import Item
import numpy as np


class HUD: 
    def __init__(self,ui_items_atlas,player:Player,true_res:tuple[int,int]):
        self._player = player
        self._true_res = true_res
        self._ui_items_atlas = ui_items_atlas
        self._inven_open_state = False
      
        self._create_display_elements()
        self._precompute_texture_coords()
        self._precompute_vertices()

    

    @property
    def inven_open_state(self):
        return self._inven_open_state
    
    def set_inven_open_state(self,state:bool):
        self._inven_open_state = state

    def _precompute_texture_coords(self):
        
        self._tex_dict = {}
        self._item_tex_dict = {}

        for key in UI_ATLAS_POSITIONS_AND_SIZES: 
            if key.endswith("slot"):   
                self._tex_dict[key] = {}
                for state in UI_ATLAS_POSITIONS_AND_SIZES[key]:
                    pos,size = UI_ATLAS_POSITIONS_AND_SIZES[key][state]
                    self._tex_dict[key][state] = self._get_texture_coords_for_ui(pos,size)
            elif key == "cursor":
                self._tex_dict[key] = {}
                for state in UI_ATLAS_POSITIONS_AND_SIZES[key]:
                    pos,size = UI_ATLAS_POSITIONS_AND_SIZES[key][state]
                    self._tex_dict[key][state] = self._get_texture_coords_for_ui(pos,size)
            else:
                pos,size = UI_ATLAS_POSITIONS_AND_SIZES[key]
                self._tex_dict[key] = self._get_texture_coords_for_ui(pos,size)

        for key in ITEM_ATLAS_POSITIONS:
            pos= ITEM_ATLAS_POSITIONS[key]
            self._item_tex_dict[key] = self._get_texture_coords_for_item(pos)

    
    def _precompute_vertices(self):
        self._vertices_dict = {}
        self._item_vertices_dict = {} 
        for inventory in self._inven_list:
            if inventory.expandable:
                self._vertices_dict[f"{inventory.name}_{inventory.ind}_background"] = {}
                for i in range(6):
                    self._vertices_dict[f"{inventory.name}_{inventory.ind}_background"][i] = self._create_vertices_for_background(i,inventory)
            self._vertices_dict[f"{inventory._name}_{inventory._ind}"] = []
            self._item_vertices_dict[f"{inventory._name}_{inventory._ind}"] = []
            for i in range(inventory._rows):
                for j in range(inventory._columns):
                    self._vertices_dict[f"{inventory._name}_{inventory._ind}"].append(self._create_vertices_for_cell(i,j,inventory))
                    self._item_vertices_dict[f"{inventory._name}_{inventory._ind}"].append(self._create_vertices_for_item(i,j,inventory))



    def _create_vertices_for_background(self,step:int, inventory: Inventory) -> np.array:
        topleft = inventory.topleft
        background_dim = inventory.size

        x = 2. * (topleft[0]-5) / self._true_res[0] -1.
        y = 1. - 2. * (topleft[1] -5- (5-step) * inventory._cell_dim[1]//4 ) / self._true_res[1] 
        w = 2. *(background_dim[0]+10)/ self._true_res[0]
        h = 2. * (background_dim[1]+10) / self._true_res[1]

        return  np.array([(x,y),(x+w,y),(x,y-h),
                         (x,y-h), (x+w,y),(x+w,y-h)],dtype=np.float32)


    def _create_vertices_for_item(self,i:int,j:int,inventory:Inventory)->np.array:
        topleft = inventory._topleft
        cell_dim = inventory._cell_dim
        space_between_cells = inventory._space_between_cells

        x = 2. * (topleft[0]+ cell_dim[0]//4 + j * cell_dim[0] + ((space_between_cells * (j)) if j >0 else 0)) / self._true_res[0] -1.
        y = 1. - 2. * (topleft[1] + cell_dim[1]//4 + i * cell_dim[1] + ((space_between_cells * (i)) if i >0 else 0)) / self._true_res[1]
        w = 2. * (cell_dim[0]//2)/ self._true_res[0]
        h = 2. * (cell_dim[1]//2) / self._true_res[1]

        return np.array([(x,y),(x+w,y),(x,y-h),
                         (x,y-h), (x+w,y),(x+w,y-h)],dtype=np.float32)

    def _create_vertices_for_cell(self,i:int,j:int,inventory:Inventory)->np.array:
        topleft = inventory._topleft
        non_expanded_cell_dim = inventory._cell_dim
        space_between_cells = inventory._space_between_cells

        x = 2. * (topleft[0] + j * non_expanded_cell_dim[0] + ((space_between_cells * (j)) if j >0 else 0)) / self._true_res[0] -1.
        y = 1. - 2. * (topleft[1] + i * non_expanded_cell_dim[1] + ((space_between_cells * (i)) if i >0 else 0)) / self._true_res[1] 
        w = 2. * non_expanded_cell_dim[0] / self._true_res[0]
        h = 2. * non_expanded_cell_dim[1] / self._true_res[1]

        non_expanded_vertices =  np.array([(x,y),(x+w,y),(x,y-h),
                         (x,y-h), (x+w,y),(x+w,y-h)],dtype=np.float32)

        offset = (-2,-2)

        x = 2. * (topleft[0] + j * non_expanded_cell_dim[0] + ((space_between_cells * (j)) if j >0 else 0) + offset[0]) / self._true_res[0] -1.
        y = 1. - 2. * (topleft[1] + i * non_expanded_cell_dim[1] + ((space_between_cells * (i)) if i >0 else 0) + offset[0]) / self._true_res[1] 
        w = 2. * (non_expanded_cell_dim[0] + 4)/ self._true_res[0]
        h = 2. * (non_expanded_cell_dim[1] + 4)/ self._true_res[1]

        expanded_vertices = np.array([(x,y),(x+w,y),(x,y-h),
                         (x,y-h), (x+w,y),(x+w,y-h)],dtype=np.float32)

        return (non_expanded_vertices,expanded_vertices)

    def _get_texture_coords_for_ui(self,bottomleft:tuple[int,int],size:tuple[int,int]) ->np.array:

            x = (bottomleft[0] ) / self._ui_items_atlas.width
            y = (bottomleft[1] ) / self._ui_items_atlas.height

            w = size[0] / self._ui_items_atlas.width
            h = size[1] / self._ui_items_atlas.height

            p1 = (x,y+h) 
            p2 = (x+w,y+h)
            p3 = (x,y) 
            p4 = (x+w,y)

            return np.array([p1,p2,p3,
                            p3,p2,p4],dtype = np.float32 )

    def _get_texture_coords_for_item(self,bottomleft:tuple[int,int]) ->np.array:
        # 16 is a magic number that is the size of the items in the atlas. 
        x = (bottomleft[0] ) / self._ui_items_atlas.width
        y = (bottomleft[1] ) / self._ui_items_atlas.height

        w = 16 / self._ui_items_atlas.width
        h = 16 / self._ui_items_atlas.height

        p1 = (x,y+h) 
        p2 = (x+w,y+h)
        p3 = (x,y) 
        p4 = (x+w,y)

        return np.array([p1,p2,p3,
                        p3,p2,p4],dtype = np.float32 )

        
    def _create_display_elements(self):


        self._health_bar_width = self._true_res[0]*8//24
        self._stamina_bar_width = self._true_res[0]*3//12

        self._closed_items_rows_cols = (2,5)
        self._showing_items_rows_cols = (1,5)
        self._weapon_rows_cols = (1,4)

        self._item_inventory_cell_side = (self._true_res[0]*5//12) // self._closed_items_rows_cols[1]
        self._weapon_inventory_cell_length = (self._true_res[0]*5//12) // self._weapon_rows_cols[1]

        if self._item_inventory_cell_side < 20:
            self._item_inventory_cell_side = 20
        elif self._item_inventory_cell_side < 45: 
            self._item_inventory_cell_side = 23
        else: 
            self._item_inventory_cell_side = 28

        if self._weapon_inventory_cell_length < 40 : 
            self._weapon_inventory_cell_length = 24 
            self._weapon_inventory_cell_height = 14
            self._space_between_weapon_inventory_cells = 5
        else: 
            self._weapon_inventory_cell_length = 44 
            self._weapon_inventory_cell_height = 23  
            self._space_between_weapon_inventory_cells = 5  


        self._space_between_item_inventory_cells = ((self._true_res[0] *5//12 - self._item_inventory_cell_side * self._closed_items_rows_cols[1]) // self._closed_items_rows_cols[1]) // 1.5

        self._item_inventory_cell_dim = (self._item_inventory_cell_side,self._item_inventory_cell_side )
        self._weapon_inven_cell_dim = (self._weapon_inventory_cell_length, self._weapon_inventory_cell_height)
        
        self._closed_items_topleft = (self._true_res[0]//12 + self._health_bar_width + self._true_res[0]//7,self._true_res[1] * 36//40 - 2 - self._item_inventory_cell_dim[1] * self._closed_items_rows_cols[0]\
                                      -self._space_between_item_inventory_cells * (self._closed_items_rows_cols[0])) 
        self._showing_items_topleft = (self._true_res[0]//12 + self._health_bar_width + self._true_res[0]//7,self._true_res[1] * 36//40 - 2) 
        self._weapons_topleft = (self._true_res[0]//12  , self._true_res[1] * 36//40 - self._weapon_inven_cell_dim[1] * 1.5)

        self._bar_height = self._true_res[1] // 40 

        # clamp the dimensions of the display elements to be 
        # a multiple of a certain predefined value. 

        if self._bar_height < 8: 
            self._bar_height = 8
        else: 
            self._bar_height = 9



        self._health_bar_topleft = (self._true_res[0]//12,self._true_res[1] * 36 // 40)
        self._stamina_bar_topleft = (self._true_res[0]//12,self._true_res[1] * 36//40 + self._bar_height + 1)

        self._health_bar = HealthBar(self._health_bar_topleft,(self._health_bar_width,self._bar_height),self._player.health)
        self._stamina_bar = StaminaBar(self._stamina_bar_topleft,(self._stamina_bar_width,self._bar_height),self._player.stamina)
        self._inven_list = [
            Inventory("item", 1, 5, self._showing_items_topleft,self._item_inventory_cell_dim,self._space_between_item_inventory_cells,16, expandable= False), 
           Inventory("item", 2,5,self._closed_items_topleft, self._item_inventory_cell_dim,self._space_between_item_inventory_cells,16,expandable = True),
           WeaponInventory(1,4, self._weapons_topleft,self._weapon_inven_cell_dim,self._space_between_weapon_inventory_cells,1, expandable = True)

        ]
        self._items_engine = Inventory_Engine(self._inven_list,self._player)
        
        
        self._bars = {
            'health_bar' : self._health_bar,
            'stamina_bar' : self._stamina_bar,
        }

        self.cursor = Cursor(in_editor= False)

    
    # temporary method to test items 
    def add_item(self, item: Item):
        if item.type == 'weapon' :
            pass 
        else:
            self._inven_list[0].add_item(item) 
            pass 


    def update(self):
        self._health_bar.update(self._player.health)
        self._stamina_bar.update(self._player.stamina)
        self._items_engine.update(self.cursor,self._inven_open_state)
        self.cursor.update()