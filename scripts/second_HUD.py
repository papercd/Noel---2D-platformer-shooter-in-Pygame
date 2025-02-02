from scripts.data import TRUE_RES_TO_HEALTH_BAR_WIDTH_RATIO,TRUE_RES_TO_STAMINA_BAR_WIDTH_RATIO,TRUE_RES_TO_HEALTH_STAMINA_BAR_HEIGHT_RATIO,SPACE_BETWEEN_INVENTORY_ELEMENTS,\
                        TRUE_RES_TO_HEALTH_BAR_TOPLEFT_RATIO,TRUE_RES_TO_WEAPON_INVEN_DIM_RATIO,TRUE_RES_TO_OPAQUE_ITEM_INVEN_DIM_RATIO,TRUE_RES_TO_HIDDEN_ITEM_INVEN_DIM_RATIO,\
                        TRUE_RES_TO_CURRENT_WEAPON_DISPLAY_DIM_RATIO, SPACE_BETWEEN_INVENTORY_CELLS,INVENTORY_CELL_EXPANSION_RATIO,PHYSICS_TIMESTEP
from scripts.new_cursor import Cursor
from scripts.new_resource_manager import ResourceManager
from scripts.new_inventory import Inventory,InventoryEngine,WeaponInventory
from scripts.lists import WeaponNode
import numpy as np 

from typing import TYPE_CHECKING



class HUD:

    def __init__(self,true_res:tuple[int,int],true_to_native_ratio:int)->None: 
        self._ref_rm = ResourceManager.get_instance()
        self._true_res = true_res
        self._true_to_native_ratio = true_to_native_ratio

        self.inven_open_state = False
        self.inven_open_time = 0
        self.max_inven_open_time = 30 * PHYSICS_TIMESTEP
        self.cursor = Cursor()

        self._create_diplay_elements()
        

    def _create_diplay_elements(self)->None:
        self.health_bar_topleft = (int(self._true_res[0] * TRUE_RES_TO_HEALTH_BAR_TOPLEFT_RATIO[0]),
                                    int(self._true_res[1] * TRUE_RES_TO_HEALTH_BAR_TOPLEFT_RATIO[1]))
        self.health_bar_dimensions = (int(TRUE_RES_TO_HEALTH_BAR_WIDTH_RATIO * self._true_res[0]),
                                       int(TRUE_RES_TO_HEALTH_STAMINA_BAR_HEIGHT_RATIO * self._true_res[1]))

        self.stamina_bar_topelft = (self.health_bar_topleft[0],self.health_bar_topleft[1] + self.health_bar_dimensions[1] + 1)
        self.stamina_bar_dimensions = (int(TRUE_RES_TO_STAMINA_BAR_WIDTH_RATIO * self._true_res[0]),
                                       int(TRUE_RES_TO_HEALTH_STAMINA_BAR_HEIGHT_RATIO * self._true_res[1])) 

        self.weapon_inventory_rows_cols = (1,4)
        self.weapon_inventory_cell_dim = (int(self._true_res[0] * TRUE_RES_TO_WEAPON_INVEN_DIM_RATIO[0]) // self.weapon_inventory_rows_cols[1],
                                           int(self._true_res[1] * TRUE_RES_TO_WEAPON_INVEN_DIM_RATIO[1]) // self.weapon_inventory_rows_cols[0])

        self.open_item_inventory_rows_cols = (1,5)
        self.open_item_inventory_cell_length =int(self._true_res[0] * TRUE_RES_TO_OPAQUE_ITEM_INVEN_DIM_RATIO[0]) // self.open_item_inventory_rows_cols[1]  

        self.hidden_item_inventory_rows_cols = [2,5]
        self.hidden_item_inventory_cell_length = int(self._true_res[0] * TRUE_RES_TO_HIDDEN_ITEM_INVEN_DIM_RATIO[0]) // self.open_item_inventory_rows_cols[1] 

        self.current_weapon_display_cell_dim = (int(self._true_res[0] * TRUE_RES_TO_CURRENT_WEAPON_DISPLAY_DIM_RATIO[0]),
                                                 int(self._true_res[1] * TRUE_RES_TO_CURRENT_WEAPON_DISPLAY_DIM_RATIO[1]))
        

        # TODO: COMPUTE THIS: 
        self.hidden_item_inventory_max_rows = 0

        self._clamp_dimensions()

        self.weapon_inventory_topleft = (self.health_bar_topleft[0],
                                          self.health_bar_topleft[1] -self.weapon_inventory_rows_cols[0] * (self.weapon_inventory_cell_dim[1] + SPACE_BETWEEN_INVENTORY_CELLS)\
                                            +SPACE_BETWEEN_INVENTORY_CELLS -SPACE_BETWEEN_INVENTORY_ELEMENTS)

        self.current_weapon_display_topleft = (self.health_bar_topleft[0] + self.health_bar_dimensions[0]+SPACE_BETWEEN_INVENTORY_ELEMENTS,
                                                self.health_bar_topleft[1] -2)

        self.open_item_inventory_topleft = (self.health_bar_topleft[0]+self.health_bar_dimensions[0]+self.current_weapon_display_cell_dim[0]+SPACE_BETWEEN_INVENTORY_ELEMENTS,\
                                             self.health_bar_topleft[1] - int(0.5 * self.open_item_inventory_cell_length) + self.health_bar_dimensions[1])

        self.hidden_item_inventory_topleft = (self.open_item_inventory_topleft[0],self.open_item_inventory_topleft[1] -(self.hidden_item_inventory_rows_cols[0]) * (self.hidden_item_inventory_cell_length+SPACE_BETWEEN_INVENTORY_CELLS))

        self.hidden_item_inven_background_topleft = (self.hidden_item_inventory_topleft[0] - 2*self.hidden_item_inventory_cell_length * INVENTORY_CELL_EXPANSION_RATIO,\
                                                     self.hidden_item_inventory_topleft[1] - 2*self.hidden_item_inventory_cell_length * INVENTORY_CELL_EXPANSION_RATIO)
        self.hidden_item_inven_background_dim = (self.hidden_item_inventory_rows_cols[1] * (self.hidden_item_inventory_cell_length + SPACE_BETWEEN_INVENTORY_CELLS) -SPACE_BETWEEN_INVENTORY_CELLS + 4 *self.hidden_item_inventory_cell_length* INVENTORY_CELL_EXPANSION_RATIO ,\
                                                 self.hidden_item_inventory_rows_cols[0] * (self.hidden_item_inventory_cell_length + SPACE_BETWEEN_INVENTORY_CELLS) -SPACE_BETWEEN_INVENTORY_CELLS + 4 *self.hidden_item_inventory_cell_length * INVENTORY_CELL_EXPANSION_RATIO  )


        self._precompute_hud_display_elements_vertices()

        self.opaque_vertices_buffer,self.opaque_texcoords_buffer, self.hidden_vertices_buffer, self.hidden_texcoords_buffer = \
            self._ref_rm.create_hud_inven_vbos(3 + self.open_item_inventory_rows_cols[0] * self.open_item_inventory_rows_cols[1],
            self.hidden_item_inventory_rows_cols[0] * self.hidden_item_inventory_rows_cols[1]+ self.weapon_inventory_rows_cols[0] * self.weapon_inventory_rows_cols[1] + 1)

        self.opaque_items_vertices_buffer, self.opaque_items_texcoords_buffer,self.hidden_items_vertices_buffer,self.hidden_items_texcoords_buffer =\
        self._ref_rm.create_hud_item_vbos(self.open_item_inventory_rows_cols[0] * self.open_item_inventory_rows_cols[1],
                                          self.hidden_item_inventory_rows_cols[0] * self.hidden_item_inventory_rows_cols[1] +\
                                          self.weapon_inventory_rows_cols[0] * self.weapon_inventory_rows_cols[1])

        self._write_to_buffers()

        self._inven_list= [
            Inventory('item',*self.open_item_inventory_rows_cols,self.open_item_inventory_topleft,(self.open_item_inventory_cell_length,self.open_item_inventory_cell_length),SPACE_BETWEEN_INVENTORY_CELLS,
                      16,expandable = False),
            Inventory('item',*self.hidden_item_inventory_rows_cols,self.hidden_item_inventory_topleft,(self.hidden_item_inventory_cell_length,self.hidden_item_inventory_cell_length),SPACE_BETWEEN_INVENTORY_CELLS,
                      16, expandable= True),
            WeaponInventory(*self.weapon_inventory_rows_cols,self.weapon_inventory_topleft,self.weapon_inventory_cell_dim,SPACE_BETWEEN_INVENTORY_CELLS,
                            1,expandable= True)
        ]

        self._items_engine = InventoryEngine(self._inven_list)



    def _clamp_dimensions(self)->None: 
        # clamp the dimensions of the health and stamina bars 
        # clamp the height of the health and stamina bars to 9 maximum
        self.health_bar_dimensions  = (self.health_bar_dimensions[0],min(9,self.health_bar_dimensions[1])) 
        self.stamina_bar_dimensions = (self.stamina_bar_dimensions[0],min(9,self.stamina_bar_dimensions[1])) 

        self.open_item_inventory_cell_length= min(28,self.open_item_inventory_cell_length)
        self.hidden_item_inventory_cell_length = min(28,self.hidden_item_inventory_cell_length)

        #self.weapon_inventory_cell_dim = (min(self.weapon_inventory_cell_dim[0],44),max(23,min(28,self.weapon_inventory_cell_dim[1])))
        self.weapon_inventory_cell_dim = (42,20)
    
    def _precompute_hud_display_elements_vertices(self)->None:
        
        # empty vertices and texcoords 
        self.null_vertices = np.zeros((6,2),dtype = np.float32)
        self.null_texcoords = np.zeros((6,2),dtype= np.float32)

        # health bar 
        self.health_bar_vertices = self._create_ui_element_vertices(self.health_bar_topleft,self.health_bar_dimensions) 

        # stamina bar 
        self.stamina_bar_vertices = self._create_ui_element_vertices(self.stamina_bar_topelft,self.stamina_bar_dimensions) 
        
        # open item inventory
        self.open_item_inven_vertices = {}
        self.open_item_inven_vertices[False] = {}
        self.open_item_inven_vertices[True] = {}

        self.open_item_vertices = {}
        self.open_item_vertices[False] = {}
        self.open_item_vertices[True] = {}

        hovered_length = int(self.open_item_inventory_cell_length*(1+2*INVENTORY_CELL_EXPANSION_RATIO))

        for row in range(self.open_item_inventory_rows_cols[0]):
            for col in range(self.open_item_inventory_rows_cols[1]):
                idle_x = self.open_item_inventory_topleft[0] + col * (self.open_item_inventory_cell_length + SPACE_BETWEEN_INVENTORY_CELLS) 
                idle_y = self.open_item_inventory_topleft[1] + row * (self.open_item_inventory_cell_length + SPACE_BETWEEN_INVENTORY_CELLS)

                hovered_x = self.open_item_inventory_topleft[0] + col * (self.open_item_inventory_cell_length + SPACE_BETWEEN_INVENTORY_CELLS)\
                                -int(INVENTORY_CELL_EXPANSION_RATIO * self.open_item_inventory_cell_length)

                hovered_y = self.open_item_inventory_topleft[1]+ row * (self.open_item_inventory_cell_length + SPACE_BETWEEN_INVENTORY_CELLS)\
                                -int(INVENTORY_CELL_EXPANSION_RATIO * self.open_item_inventory_cell_length)
                
                item_idle_x = idle_x + self.open_item_inventory_cell_length // 4 
                item_idle_y =  idle_y + self.open_item_inventory_cell_length // 4 

                item_hovered_x =  hovered_x + hovered_length // 4
                item_hovered_y =  hovered_y + hovered_length // 4

                self.open_item_vertices[False][(row,col)] = self._create_ui_element_vertices((item_idle_x,item_idle_y),(self.open_item_inventory_cell_length // 2 , self.open_item_inventory_cell_length // 2))
                self.open_item_vertices[True][(row,col)] = self._create_ui_element_vertices((item_hovered_x,item_hovered_y),(hovered_length// 2 , hovered_length // 2))

                self.open_item_inven_vertices[False][(row,col)] = self._create_ui_element_vertices((idle_x,idle_y),(self.open_item_inventory_cell_length,self.open_item_inventory_cell_length))
                self.open_item_inven_vertices[True][(row,col)] = self._create_ui_element_vertices((hovered_x,hovered_y),(hovered_length,hovered_length))

        # hidden item inventory 
        self.hidden_item_inven_vertices = {}
        self.hidden_item_inven_vertices[False] = {}
        self.hidden_item_inven_vertices[True] = {}

        self.hidden_item_vertices = {}
        self.hidden_item_vertices[False] = {}
        self.hidden_item_vertices[True] = {}

        hovered_length = int(self.hidden_item_inventory_cell_length*(1+2*INVENTORY_CELL_EXPANSION_RATIO))

        for row in range(self.hidden_item_inventory_rows_cols[0]):
            for col in range(self.hidden_item_inventory_rows_cols[1]):
                idle_x = self.hidden_item_inventory_topleft[0] + col * (self.hidden_item_inventory_cell_length + SPACE_BETWEEN_INVENTORY_CELLS) 
                idle_y = self.hidden_item_inventory_topleft[1] + row * (self.hidden_item_inventory_cell_length + SPACE_BETWEEN_INVENTORY_CELLS)

                hovered_x = self.hidden_item_inventory_topleft[0] + col * (self.hidden_item_inventory_cell_length + SPACE_BETWEEN_INVENTORY_CELLS)\
                                -int(INVENTORY_CELL_EXPANSION_RATIO * self.hidden_item_inventory_cell_length)

                hovered_y = self.hidden_item_inventory_topleft[1]+ row * (self.hidden_item_inventory_cell_length + SPACE_BETWEEN_INVENTORY_CELLS)\
                                -int(INVENTORY_CELL_EXPANSION_RATIO * self.hidden_item_inventory_cell_length)

                item_idle_x = idle_x + self.hidden_item_inventory_cell_length // 4 
                item_idle_y =  idle_y + self.hidden_item_inventory_cell_length // 4 

                item_hovered_x =  hovered_x + hovered_length // 4
                item_hovered_y =  hovered_y + hovered_length // 4

                self.hidden_item_vertices[False][(row,col)] = self._create_ui_element_vertices((item_idle_x,item_idle_y),(self.hidden_item_inventory_cell_length // 2 , self.hidden_item_inventory_cell_length // 2))
                self.hidden_item_vertices[True][(row,col)] = self._create_ui_element_vertices((item_hovered_x,item_hovered_y),(hovered_length// 2 , hovered_length // 2))

                self.hidden_item_inven_vertices[False][(row,col)] = self._create_ui_element_vertices((idle_x,idle_y),(self.hidden_item_inventory_cell_length,self.hidden_item_inventory_cell_length))
                self.hidden_item_inven_vertices[True][(row,col)] = self._create_ui_element_vertices((hovered_x,hovered_y),(hovered_length,hovered_length))


        # hidden item inventory background 
     
        self.hidden_item_inven_background_vertices = self._create_ui_element_vertices(self.hidden_item_inven_background_topleft,self.hidden_item_inven_background_dim)


        # weapon inventory (hidden)
        self.weapon_inven_vertices = {}
        self.weapon_inven_vertices[False] = {}
        self.weapon_inven_vertices[True] = {}

        self.weapon_vertices = {}
        self.weapon_vertices[False] = {}
        self.weapon_vertices[True] = {}

        hovered_dim = (int(self.weapon_inventory_cell_dim[0]*(1+2*INVENTORY_CELL_EXPANSION_RATIO)),\
                            int(self.weapon_inventory_cell_dim[1]*(1+2*INVENTORY_CELL_EXPANSION_RATIO)))
        for row in range(self.weapon_inventory_rows_cols[0]):
            for col in range(self.weapon_inventory_rows_cols[1]):
                idle_x = self.weapon_inventory_topleft[0] + col * (self.weapon_inventory_cell_dim[0]+ SPACE_BETWEEN_INVENTORY_CELLS) 
                idle_y = self.weapon_inventory_topleft[1] + row * (self.weapon_inventory_cell_dim[1]+ SPACE_BETWEEN_INVENTORY_CELLS)

                hovered_x = self.weapon_inventory_topleft[0] + col * (self.weapon_inventory_cell_dim[0]+ SPACE_BETWEEN_INVENTORY_CELLS)\
                                -int(INVENTORY_CELL_EXPANSION_RATIO * self.weapon_inventory_cell_dim[0])

                hovered_y = self.weapon_inventory_topleft[1]+ row * (self.weapon_inventory_rows_cols[1]+ SPACE_BETWEEN_INVENTORY_CELLS)\
                                -int(INVENTORY_CELL_EXPANSION_RATIO * self.weapon_inventory_cell_dim[1])
                
                weapon_idle_x = idle_x + self.weapon_inventory_cell_dim[0] // 6
                weapon_idle_y = idle_y + self.weapon_inventory_cell_dim[1] // 6

                weapon_hovered_x = weapon_idle_x 
                weapon_hovered_y = weapon_idle_y -1

                self.weapon_vertices[False][(row,col)] = self._create_ui_element_vertices((weapon_idle_x,weapon_idle_y),(self.weapon_inventory_cell_dim[0] * 4// 6,
                                                                                                                         self.weapon_inventory_cell_dim[1] * 4 //6))
                self.weapon_vertices[True][(row,col)] = self._create_ui_element_vertices((weapon_hovered_x,weapon_hovered_y),(self.weapon_inventory_cell_dim[0]* 4 //6 , 
                                                                                                                              self.weapon_inventory_cell_dim[1] * 4 //6))
            
                self.weapon_inven_vertices[False][(row,col)] = self._create_ui_element_vertices((idle_x,idle_y),self.weapon_inventory_cell_dim)
                self.weapon_inven_vertices[True][(row,col)] = self._create_ui_element_vertices((hovered_x,hovered_y),hovered_dim)


    def _create_ui_element_vertices(self,topleft:tuple[int,int],size:tuple[int,int])->np.array:

        x = 2. * (topleft[0])/ self._true_res[0]- 1.
        y = 1. - 2. * (topleft[1])/ self._true_res[1]
        w = 2. * size[0] / self._true_res[0]
        h = 2. * size[1] /self._true_res[1]

        #return np.array([(x, y), (x + w, y), (x, y - h),
        #                    (x, y - h), (x + w, y), (x + w, y - h)], dtype=np.float32)
        
        return np.array([(x, y - h),(x + w, y - h),(x,y),
                         (x,y),(x + w, y - h),(x+w,y)],dtype= np.float32)

    def _write_to_buffers(self)->None: 
        bytes_per_cell = 48 

        opaque_vertices_write_offset = 0
        opaque_texcoords_write_offset= 0 

        # health bar 
        self.opaque_vertices_buffer.write(self.health_bar_vertices.tobytes())
        self.opaque_texcoords_buffer.write(self._ref_rm.ui_element_texcoords['health_bar'].tobytes())

        opaque_vertices_write_offset += bytes_per_cell 
        opaque_texcoords_write_offset +=bytes_per_cell 

        # stamina bar 
        self.opaque_vertices_buffer.write(self.stamina_bar_vertices.tobytes(),offset = opaque_vertices_write_offset)
        self.opaque_texcoords_buffer.write(self._ref_rm.ui_element_texcoords['health_bar'].tobytes(),offset = opaque_texcoords_write_offset)

        opaque_vertices_write_offset +=bytes_per_cell 
        opaque_texcoords_write_offset += bytes_per_cell

        # open item inventory cells 
        for row in range(self.open_item_inventory_rows_cols[0]):
            for col in range(self.open_item_inventory_rows_cols[1]):
                self.opaque_vertices_buffer.write(self.open_item_inven_vertices[False][(row,col)].tobytes(),offset = opaque_vertices_write_offset)
                self.opaque_texcoords_buffer.write(self._ref_rm.ui_element_texcoords['item_slot'][False].tobytes(),offset = opaque_texcoords_write_offset)

                opaque_vertices_write_offset +=bytes_per_cell 
                opaque_texcoords_write_offset +=bytes_per_cell 

        # current weapon display 


        hidden_vertices_write_offset = 0
        hidden_texcoords_write_offset = 0

        # hidden item inventory background 
        self.hidden_vertices_buffer.write(self.hidden_item_inven_background_vertices.tobytes(),offset =hidden_vertices_write_offset)
        self.hidden_texcoords_buffer.write(self._ref_rm.ui_element_texcoords['background'].tobytes(),offset =hidden_texcoords_write_offset)

        hidden_vertices_write_offset += bytes_per_cell
        hidden_texcoords_write_offset += bytes_per_cell

        # hidden item inventory 
        for row in range(self.hidden_item_inventory_rows_cols[0]):
            for col in range(self.hidden_item_inventory_rows_cols[1]):
                self.hidden_vertices_buffer.write(self.hidden_item_inven_vertices[False][(row,col)].tobytes(),offset = hidden_vertices_write_offset)
                self.hidden_texcoords_buffer.write(self._ref_rm.ui_element_texcoords['item_slot'][False].tobytes(),offset = hidden_texcoords_write_offset)

                hidden_vertices_write_offset +=bytes_per_cell 
                hidden_texcoords_write_offset +=bytes_per_cell 

        # weapons inventory (hidden)
        for row in range(self.weapon_inventory_rows_cols[0]):
            for col in range(self.weapon_inventory_rows_cols[1]):
                self.hidden_vertices_buffer.write(self.weapon_inven_vertices[False][(row,col)].tobytes(),offset = hidden_vertices_write_offset)
                self.hidden_texcoords_buffer.write(self._ref_rm.ui_element_texcoords['weapon_slot'][False].tobytes(),offset = hidden_texcoords_write_offset)

                hidden_vertices_write_offset += bytes_per_cell
                hidden_texcoords_write_offset +=  bytes_per_cell

        # the items for the inventories also need a preallocated buffer.             



    def _get_inventory_id(self,cell)->int:
        if isinstance(cell,WeaponNode):
            inventory_id = cell.list.inventory_id
        else: 
            inventory_id = cell.inventory_id

        return inventory_id
        
    def _on_cursor_item_change_callback(self)->None: 

        if self.cursor.item: 
            self.opaque_items_texcoords_buffer.write(self._ref_rm.item_texcoords[self.cursor.item.name].tobytes(),offset = self.opaque_items_texcoords_buffer.size - 48)    
        else: 
            self.opaque_items_texcoords_buffer.write(self.null_texcoords.tobytes(),offset = self.opaque_items_texcoords_buffer.size - 48)
        

    def _on_inven_item_change_callback(self,inven_cell)->None: 
        bytes_per_item = 48 
        
        inventory_id = self._get_inventory_id(inven_cell)
        inventory = self._inven_list[inventory_id] 

        row = inven_cell.ind // inventory.columns
        col = inven_cell.ind - row * inventory.columns
    

        if inventory_id == 0: 
            # open item inventory : write to the open item vertices and texcoords buffer 
            # acquire the offset of the buffer position from the cell index. 
            buffer_offset = (inven_cell.ind * bytes_per_item)
            if inven_cell.item: 
                self.opaque_items_vertices_buffer.write(self.open_item_vertices[False][(row,col)].tobytes(),offset = buffer_offset)
                self.opaque_items_texcoords_buffer.write(self._ref_rm.item_texcoords[inven_cell.item.name].tobytes(),offset = buffer_offset)
            else:
                self.opaque_items_vertices_buffer.write(self.null_vertices.tobytes(),offset = buffer_offset)
                self.opaque_items_texcoords_buffer.write(self.null_texcoords.tobytes(),offset = buffer_offset)
                

        elif inventory_id == 1:
            # hidden item inventory
            buffer_offset = (inven_cell.ind * bytes_per_item)
            if inven_cell.item: 
                self.hidden_items_vertices_buffer.write(self.hidden_item_vertices[False][(row,col)].tobytes(),offset = buffer_offset)
                self.hidden_items_texcoords_buffer.write(self._ref_rm.item_texcoords[inven_cell.item.name].tobytes(),offset = buffer_offset)
            else: 
                self.hidden_items_vertices_buffer.write(self.null_vertices.tobytes(),offset = buffer_offset)
                self.hidden_items_texcoords_buffer.write(self.null_texcoords.tobytes(),offset = buffer_offset)

        else:
            # weapon inventory 
            buffer_offset = (self.hidden_item_inventory_rows_cols[0] * self.hidden_item_inventory_rows_cols[1]+inven_cell.ind) * bytes_per_item
            if inven_cell.weapon: 
                self.hidden_items_vertices_buffer.write(self.weapon_vertices[False][(row,col)].tobytes(),offset = buffer_offset) 
                self.hidden_items_texcoords_buffer.write(self._ref_rm.item_texcoords[inven_cell.weapon.name].tobytes(),offset = buffer_offset) 
            else: 
                self.hidden_items_vertices_buffer.write(self.null_vertices.tobytes(),offset = buffer_offset)
                self.hidden_items_texcoords_buffer.write(self.null_texcoords.tobytes(),offset = buffer_offset)

    


    def cursor_cell_hover_state_change_callback(self)->None: 
        # when the cursor hover state changes, you need to overwrite the corresponding cell's vertex data 
        # in the buffers

        bytes_per_element = 48 

        if self.cursor.ref_prev_hovered_cell:
            # write non-hover cell to buffer 
            inventory_id = self._get_inventory_id(self.cursor.ref_prev_hovered_cell)
            inventory = self._inven_list[inventory_id]
            row = self.cursor.ref_prev_hovered_cell.ind // inventory.columns
            col = self.cursor.ref_prev_hovered_cell.ind - row * inventory.columns

            if inventory_id == 0:
                inventory_id = self.cursor.ref_prev_hovered_cell.inventory_id
                inventory = self._inven_list[inventory_id] 
                
                buffer_offset = (self.cursor.ref_prev_hovered_cell.ind + 2) * bytes_per_element
                self.opaque_vertices_buffer.write(self.open_item_inven_vertices[False][(row,col)].tobytes(),offset = buffer_offset)
                self.opaque_texcoords_buffer.write(self._ref_rm.ui_element_texcoords['item_slot'][False].tobytes(),offset = buffer_offset)

                self.opaque_items_vertices_buffer.write(self.open_item_vertices[False][(row,col)].tobytes(),offset = self.cursor.ref_prev_hovered_cell.ind * bytes_per_element)

            elif inventory_id == 1:

                buffer_offset = (self.cursor.ref_prev_hovered_cell.ind+1) * bytes_per_element
                self.hidden_vertices_buffer.write(self.hidden_item_inven_vertices[False][(row,col)].tobytes(),offset = buffer_offset)
                self.hidden_texcoords_buffer.write(self._ref_rm.ui_element_texcoords['item_slot'][False].tobytes(),offset = buffer_offset)

                self.hidden_items_vertices_buffer.write(self.hidden_item_vertices[False][(row,col)].tobytes(),offset = self.cursor.ref_prev_hovered_cell.ind * bytes_per_element)
            else: 

                buffer_offset = (self.hidden_item_inventory_rows_cols[0]*self.hidden_item_inventory_rows_cols[1]+self.cursor.ref_prev_hovered_cell.ind+1) * bytes_per_element
                self.hidden_vertices_buffer.write(self.weapon_inven_vertices[False][(row,col)].tobytes(),offset = buffer_offset)
                self.hidden_texcoords_buffer.write(self._ref_rm.ui_element_texcoords['weapon_slot'][False].tobytes(),offset = buffer_offset)

                self.hidden_items_vertices_buffer.write(self.weapon_vertices[False][(row,col)].tobytes(),offset = (self.hidden_item_inventory_rows_cols[0] * 
                                                                                                                     self.hidden_item_inventory_rows_cols[1]+self.cursor.ref_prev_hovered_cell.ind) * bytes_per_element)

            

        if self.cursor.ref_hovered_cell: 
            inventory_id = self._get_inventory_id(self.cursor.ref_hovered_cell)
            inventory = self._inven_list[inventory_id]
            row = self.cursor.ref_hovered_cell.ind // inventory.columns
            col = self.cursor.ref_hovered_cell.ind - row * inventory.columns

            if inventory_id == 0:

                buffer_offset = (self.cursor.ref_hovered_cell.ind + 2) * 6 * 4 * 2
                self.opaque_vertices_buffer.write(self.open_item_inven_vertices[True][(row,col)].tobytes(),offset = buffer_offset)
                self.opaque_texcoords_buffer.write(self._ref_rm.ui_element_texcoords['item_slot'][True].tobytes(),offset = buffer_offset)

                self.opaque_items_vertices_buffer.write(self.open_item_vertices[True][(row,col)].tobytes(),offset = self.cursor.ref_hovered_cell.ind * bytes_per_element)
            elif inventory_id == 1:

                buffer_offset = (self.cursor.ref_hovered_cell.ind+1) * bytes_per_element
                self.hidden_vertices_buffer.write(self.hidden_item_inven_vertices[True][(row,col)].tobytes(),offset = buffer_offset)
                self.hidden_texcoords_buffer.write(self._ref_rm.ui_element_texcoords['item_slot'][True].tobytes(),offset = buffer_offset)

                self.hidden_items_vertices_buffer.write(self.hidden_item_vertices[True][(row,col)].tobytes(),offset = self.cursor.ref_hovered_cell.ind * bytes_per_element)
            else: 

                buffer_offset = (self.hidden_item_inventory_rows_cols[0] * self.hidden_item_inventory_rows_cols[1] + self.cursor.ref_hovered_cell.ind+1) * bytes_per_element
                self.hidden_vertices_buffer.write(self.weapon_inven_vertices[True][(row,col)].tobytes(),offset=buffer_offset)
                self.hidden_texcoords_buffer.write(self._ref_rm.ui_element_texcoords['weapon_slot'][True].tobytes(),offset = buffer_offset)

                self.hidden_items_vertices_buffer.write(self.weapon_vertices[True][(row,col)].tobytes(),offset = (self.hidden_item_inventory_rows_cols[0] * 
                                                                                                                     self.hidden_item_inventory_rows_cols[1]+self.cursor.ref_hovered_cell.ind) * bytes_per_element)


    
    # temporary helper function to add item to open item inventory
    def add_item(self,item,inven_ind:int)->None: 
        if inven_ind == 2 :
            self._inven_list[2].add_weapon(item,self._on_inven_item_change_callback)
        else: 
            self._inven_list[inven_ind].add_item(item,self._on_inven_item_change_callback)
    
    

    def update(self,dt:float,cursor_state_change_callback:"function",cursor_cell_hover_callback:"function")->None:
        # inventory open time update 
        self.inven_open_time = max(0,min(self.max_inven_open_time,self.inven_open_time + (2*self.inven_open_state - 1) * 4 * dt))

        # cursor update 
        self.cursor.update(self._true_to_native_ratio,dt,cursor_state_change_callback)

        # TODO: stamina, health bar updates

        # inventory updates 
        self._items_engine.update(self.cursor,cursor_cell_hover_callback,self._on_inven_item_change_callback,
                                  self._on_cursor_item_change_callback,self.inven_open_time == self.max_inven_open_time)
