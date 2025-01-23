from scripts.new_cursor import Cursor 
from scripts.new_entities import Player,CollectableItem
from scripts.new_inventory import Inventory_Engine,Inventory,WeaponInventory    
from scripts.data import UI_ATLAS_POSITIONS_AND_SIZES,ITEM_ATLAS_POSITIONS_AND_SIZES,TEXT_ATLAS_POSITIONS_AND_SPACE_AND_SIZES,UI_WEAPON_ATLAS_POSITIONS_AND_SIZES
from scripts.new_ui import HealthBar,StaminaBar
from scripts.item import Item,Weapon
import numpy as np

class HUD: 
    def __init__(self,player:Player,true_res:tuple[int,int]):
        self._player = player
        self._true_res = true_res

        self._inven_open_state = False
      
        self._create_display_elements()
        self._precompute_vertices()

    

    @property
    def inven_open_state(self):
        return self._inven_open_state
    
    def set_inven_open_state(self,state:bool):
        self._inven_open_state = state
    
    def _precompute_vertices(self):
        self._vertices_dict = {}
        self._item_vertices_dict = {} 
        for bar_name in self._bars: 
            topleft = self._bars[bar_name].topleft
            size = self._bars[bar_name].size
            vertices = self._create_vertices(topleft,size)
            self._vertices_dict[bar_name] = vertices


        for inventory in self._inven_list:
            if inventory.expandable:
                self._vertices_dict[f"{inventory.name}_{inventory.ind}_background"] = {}
                for i in range(6):
                    topleft = (inventory.topleft[0]-self._inventory_background_padding,\
                               inventory.topleft[1]- self._inventory_background_padding - (self._inventory_background_padding - i )*inventory._cell_dim[1]//4)
                    size = (inventory.size[0] + self._inventory_background_padding*2,inventory.size[1] + self._inventory_background_padding*2)
                    
                    self._vertices_dict[f"{inventory.name}_{inventory.ind}_background"][i] = self._create_vertices(topleft,size)
            self._vertices_dict[f"{inventory._name}_{inventory._ind}"] = []
            self._item_vertices_dict[f"{inventory._name}_{inventory._ind}"] = []
            for i in range(inventory._rows):
                for j in range(inventory._columns):
                    size = inventory._cell_dim
                    space_between_cells = inventory._space_between_cells
                    topleft = (inventory._topleft[0] + j * size[0] + ((space_between_cells*(j)) if j>0 else 0),\
                               inventory._topleft[1] + i * size[1] + ((space_between_cells*(i)) if i>0 else 0))   
                    non_expanded_vertices = self._create_vertices(topleft,size)
                    
                    topleft = (topleft[0] -2,topleft[1] -2)
                    size = (size[0] +4,size[1]+4)

                    expanded_vertices = self._create_vertices(topleft,size)

                    self._vertices_dict[f"{inventory._name}_{inventory._ind}"].append((non_expanded_vertices,expanded_vertices))
                    size = inventory._cell_dim
                    if inventory.name == 'weapon':
                        offset = (size[0] - self._display_weapon_dim[0],size[1]-self._display_weapon_dim[1])
                        topleft = (inventory._topleft[0] + offset[0] /2 + j * size[0]  +((space_between_cells *(j)) if j> 0 else 0),\
                                   inventory._topleft[1] + offset[1] /2 + i * size[1]  +((space_between_cells *(i)) if i> 0 else 0))
                        size = self._display_weapon_dim

                        non_expanded_vertices = self._create_vertices(topleft,size)

                    else: 
                        topleft = (inventory._topleft[0] + (size[0] - self._item_dim[0])/2 + j * size[0] + ((space_between_cells * (j)) if j >0 else 0),\
                                   inventory._topleft[1] + (size[1] - self._item_dim[1])/2 + i * size[1] + ((space_between_cells * (i)) if i>0 else 0))
                        size = self._item_dim

                        non_expanded_vertices = self._create_vertices(topleft,size)

                    topleft = (topleft[0],topleft[1]-2)
                    expanded_vertices = self._create_vertices(topleft,size)

                    self._item_vertices_dict[f"{inventory._name}_{inventory._ind}"].append((non_expanded_vertices,expanded_vertices))

        # precompute vertices for current weapon display 

        topleft = self._current_weapon_display_topleft
        size =self._weapon_inven_cell_dim 
        
        non_expanded_vertices = self._create_vertices(topleft,size)

        topleft=  (topleft[0]-2,topleft[1]-2)
        size = (size[0] +4 ,size[1] +4)

        expanded_vertices = self._create_vertices(topleft,size)

        self._vertices_dict["current_weapon"] = ((non_expanded_vertices,expanded_vertices))

        offset = (self._weapon_inven_cell_dim[0]/2 - self._display_weapon_dim[0]/2,self._weapon_inven_cell_dim[1]/2 -self._display_weapon_dim[1]/2)
        topleft = (self._current_weapon_display_topleft[0] + offset[0], self._current_weapon_display_topleft[1] + offset[1])
        size = self._display_weapon_dim

        self._item_vertices_dict["current_weapon"] = self._create_vertices(topleft,size)


    def _create_vertices(self,topleft,size)->np.array: 
        x = 2. * (topleft[0]) / self._true_res[0] -1.
        y = 1. - 2. * (topleft[1]) / self._true_res[1] 
        w = 2. * size[0] / self._true_res[0]
        h = 2. * size[1] / self._true_res[1]

        vertices =  np.array([(x,y),(x+w,y),(x,y-h),
                        (x,y-h), (x+w,y),(x+w,y-h)],dtype=np.float32)
        

        return vertices



    def _create_display_elements(self):

        self._text_dim = (16,16)
        self._item_dim = (16,16)
        self._cursor_text_box_max_width = 200

        self._health_bar_width = self._true_res[0]*8//24
        self._stamina_bar_width = self._true_res[0]*3//12

        self._closed_items_rows_cols = (2,5)
        self._showing_items_rows_cols = (1,5)
        self._weapon_rows_cols = (1,4)

        self._item_inventory_cell_side = (self._true_res[0]*5//12) // self._closed_items_rows_cols[1]

        self._weapon_inventory_cell_length = (self._true_res[0]*5//12) // self._weapon_rows_cols[1]

        self._inventory_background_padding =5

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


        self._space_between_item_inventory_cells = ((self._true_res[0] *5//12 - self._item_inventory_cell_side * self._closed_items_rows_cols[1]) // self._closed_items_rows_cols[1]) // 2 

        self._item_inventory_cell_dim = (self._item_inventory_cell_side,self._item_inventory_cell_side )
        self._weapon_inven_cell_dim = (self._weapon_inventory_cell_length, self._weapon_inventory_cell_height)
        
        self._closed_items_topleft = (self._true_res[0]//12 + self._health_bar_width + self._true_res[0]//7,self._true_res[1] * 36//40 - 2 - self._item_inventory_cell_dim[1] * self._closed_items_rows_cols[0]\
                                      -self._space_between_item_inventory_cells * (self._closed_items_rows_cols[0])) 
        self._showing_items_topleft = (self._true_res[0]//12 + self._health_bar_width + self._true_res[0]//7,self._true_res[1] * 36//40 - 2) 
        self._weapons_topleft = (self._true_res[0]//12  , self._true_res[1] * 36//40 - self._weapon_inven_cell_dim[1] * 1.5)

        self._current_weapon_display_topleft = (self._true_res[0]//12 + self._health_bar_width + self._true_res[0]//14 -self._weapon_inven_cell_dim[0]//2, self._true_res[1] * 36/40 -2)

        self._bar_height = self._true_res[1] // 40 

        # clamp the dimensions of the display elements to be 
        # a multiple of a certain predefined value. 

        if self._bar_height < 8: 
            self._bar_height = 8
        else: 
            self._bar_height = 9



        self._health_bar_topleft = (self._true_res[0]//12,self._true_res[1] * 36 // 40)
        self._stamina_bar_topleft = (self._true_res[0]//12,self._true_res[1] * 36//40 + self._bar_height + 1)

        self._weapon_display_topleft = (self._true_res[0] // 12 + self._health_bar_width, self._true_res[1] * 36//40 -2 ) 
        self._display_weapon_dim = (31,12)

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
        if isinstance(item,Weapon):
            self._inven_list[2].add_weapon(item)
        else:
            self._inven_list[0].add_item(item) 


    def remove_current_weapon(self,em)->None: 
        item = self._inven_list[2].remove_current_weapon(em)
        # em.add_collectable_item()


    def change_weapon(self,scroll):
        self._inven_list[2].change_weapon(scroll)

    def update(self,dt):
        self._health_bar.update(self._player.health)
        self._stamina_bar.update(self._player.stamina)
        self._items_engine.update(self.cursor,self._inven_open_state)
        self.cursor.update(dt)