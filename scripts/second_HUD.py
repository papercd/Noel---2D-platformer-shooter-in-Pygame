from scripts.data import BYTES_PER_TEXTURE_QUAD,TRUE_RES_TO_HEALTH_BAR_WIDTH_RATIO,TRUE_RES_TO_STAMINA_BAR_WIDTH_RATIO,TRUE_RES_TO_HEALTH_STAMINA_BAR_HEIGHT_RATIO,SPACE_BETWEEN_INVENTORY_ELEMENTS,\
                        TRUE_RES_TO_HEALTH_BAR_TOPLEFT_RATIO,TRUE_RES_TO_WEAPON_INVEN_DIM_RATIO,TRUE_RES_TO_OPAQUE_ITEM_INVEN_DIM_RATIO,TRUE_RES_TO_HIDDEN_ITEM_INVEN_DIM_RATIO,\
                        TRUE_RES_TO_CURRENT_WEAPON_DISPLAY_DIM_RATIO, SPACE_BETWEEN_INVENTORY_CELLS,INVENTORY_CELL_EXPANSION_RATIO,PHYSICS_TIMESTEP
from scripts.new_cursor import Cursor
from scripts.new_resource_manager import ResourceManager
from scripts.new_inventory import Inventory,InventoryEngine,WeaponInventory,Cell
from scripts.lists import WeaponNode
import numpy as np 

from typing import TYPE_CHECKING

if TYPE_CHECKING: 
    from scripts.item import Weapon




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
        self.weapon_inventory_cells = self.weapon_inventory_rows_cols[0] * self.weapon_inventory_rows_cols[1]
        self.weapon_inventory_cell_dim = (int(self._true_res[0] * TRUE_RES_TO_WEAPON_INVEN_DIM_RATIO[0]) // self.weapon_inventory_rows_cols[1],
                                           int(self._true_res[1] * TRUE_RES_TO_WEAPON_INVEN_DIM_RATIO[1]) // self.weapon_inventory_rows_cols[0])

        self.open_item_inventory_rows_cols = (1,5)
        self.open_item_inventory_cells = self.open_item_inventory_rows_cols[0] * self.open_item_inventory_rows_cols[1]
        self.open_item_inventory_cell_length =int(self._true_res[0] * TRUE_RES_TO_OPAQUE_ITEM_INVEN_DIM_RATIO[0]) // self.open_item_inventory_rows_cols[1]  

        self.hidden_item_inventory_rows_cols = [2,5]
        self.hidden_item_inventory_cells = self.hidden_item_inventory_rows_cols[0] * self.open_item_inventory_rows_cols[1]
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
            self._ref_rm.create_hud_inven_vbos(3 + self.open_item_inventory_cells,self.hidden_item_inventory_cells + self.weapon_inventory_cells + 1)

        self.opaque_items_vertices_buffer, self.opaque_items_texcoords_buffer,self.hidden_items_vertices_buffer,self.hidden_items_texcoords_buffer =\
        self._ref_rm.create_hud_item_vbos(self.open_item_inventory_cells + 1,self.hidden_item_inventory_cells + self.weapon_inventory_cells)

        self._write_initial_state_to_buffers()

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
        self.null_vertices_bytes = np.zeros((6,2),dtype = np.float32).tobytes()
        self.null_texcoords_bytes = np.zeros((6,2),dtype= np.float32).tobytes()

        # health bar 
        self.health_bar_vertices_bytes = self._create_ui_element_vertices(self.health_bar_topleft,self.health_bar_dimensions) 

        # stamina bar 
        self.stamina_bar_vertices_bytes = self._create_ui_element_vertices(self.stamina_bar_topelft,self.stamina_bar_dimensions) 
        
        # open item inventory
        self.open_item_inven_vertices_bytes = {}
        self.open_item_inven_vertices_bytes[False] = {}
        self.open_item_inven_vertices_bytes[True] = {}

        self.open_item_vertices_bytes = {}
        self.open_item_vertices_bytes[False] = {}
        self.open_item_vertices_bytes[True] = {}

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

                self.open_item_vertices_bytes[False][(row,col)] = self._create_ui_element_vertices((item_idle_x,item_idle_y),(self.open_item_inventory_cell_length // 2 , self.open_item_inventory_cell_length // 2))
                self.open_item_vertices_bytes[True][(row,col)] = self._create_ui_element_vertices((item_hovered_x,item_hovered_y),(hovered_length// 2 , hovered_length // 2))

                self.open_item_inven_vertices_bytes[False][(row,col)] = self._create_ui_element_vertices((idle_x,idle_y),(self.open_item_inventory_cell_length,self.open_item_inventory_cell_length))
                self.open_item_inven_vertices_bytes[True][(row,col)] = self._create_ui_element_vertices((hovered_x,hovered_y),(hovered_length,hovered_length))

        # hidden item inventory 
        self.hidden_item_inven_vertices_bytes = {}
        self.hidden_item_inven_vertices_bytes[False] = {}
        self.hidden_item_inven_vertices_bytes[True] = {}

        self.hidden_item_vertices_bytes = {}
        self.hidden_item_vertices_bytes[False] = {}
        self.hidden_item_vertices_bytes[True] = {}

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

                self.hidden_item_vertices_bytes[False][(row,col)] = self._create_ui_element_vertices((item_idle_x,item_idle_y),(self.hidden_item_inventory_cell_length // 2 , self.hidden_item_inventory_cell_length // 2))
                self.hidden_item_vertices_bytes[True][(row,col)] = self._create_ui_element_vertices((item_hovered_x,item_hovered_y),(hovered_length// 2 , hovered_length // 2))

                self.hidden_item_inven_vertices_bytes[False][(row,col)] = self._create_ui_element_vertices((idle_x,idle_y),(self.hidden_item_inventory_cell_length,self.hidden_item_inventory_cell_length))
                self.hidden_item_inven_vertices_bytes[True][(row,col)] = self._create_ui_element_vertices((hovered_x,hovered_y),(hovered_length,hovered_length))


        # hidden item inventory background 
     
        self.hidden_item_inven_background_vertices_bytes = self._create_ui_element_vertices(self.hidden_item_inven_background_topleft,self.hidden_item_inven_background_dim)


        # weapon inventory (hidden)
        self.weapon_inven_vertices_bytes = {}
        self.weapon_inven_vertices_bytes[False] = {}
        self.weapon_inven_vertices_bytes[True] = {}

        self.weapon_vertices_bytes = {}
        self.weapon_vertices_bytes[False] = {}
        self.weapon_vertices_bytes[True] = {}

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
                
                weapon_idle_x = idle_x + self.weapon_inventory_cell_dim[0] // 7
                weapon_idle_y = idle_y + self.weapon_inventory_cell_dim[1] // 6

                weapon_hovered_x = weapon_idle_x 
                weapon_hovered_y = weapon_idle_y -1

                self.weapon_vertices_bytes[False][(row,col)] = self._create_ui_element_vertices((weapon_idle_x,weapon_idle_y),(self.weapon_inventory_cell_dim[0] * 5// 7,
                                                                                                                         self.weapon_inventory_cell_dim[1] * 4 //6))
                self.weapon_vertices_bytes[True][(row,col)] = self._create_ui_element_vertices((weapon_hovered_x,weapon_hovered_y),(self.weapon_inventory_cell_dim[0]* 5 //7 , 
                                                                                                                              self.weapon_inventory_cell_dim[1] * 4 //6))
            
                self.weapon_inven_vertices_bytes[False][(row,col)] = self._create_ui_element_vertices((idle_x,idle_y),self.weapon_inventory_cell_dim)
                self.weapon_inven_vertices_bytes[True][(row,col)] = self._create_ui_element_vertices((hovered_x,hovered_y),hovered_dim)


    def _create_ui_element_vertices(self,topleft:tuple[int,int],size:tuple[int,int])-> bytes:

        x = 2. * (topleft[0])/ self._true_res[0]- 1.
        y = 1. - 2. * (topleft[1])/ self._true_res[1]
        w = 2. * size[0] / self._true_res[0]
        h = 2. * size[1] /self._true_res[1]

        #return np.array([(x, y), (x + w, y), (x, y - h),
        #                    (x, y - h), (x + w, y), (x + w, y - h)], dtype=np.float32)
        
        return np.array([(x, y - h),(x + w, y - h),(x,y),
                         (x,y),(x + w, y - h),(x+w,y)],dtype= np.float32).tobytes()

    def _write_initial_state_to_buffers(self)->None: 
      
        opaque_element_to_buffer_write_offset = 0

        # health bar 
        self.opaque_vertices_buffer.write(self.health_bar_vertices_bytes)
        self.opaque_texcoords_buffer.write(self._ref_rm.ui_element_texcoords_bytes['health_bar'])

        opaque_element_to_buffer_write_offset += BYTES_PER_TEXTURE_QUAD

        # stamina bar 
        self.opaque_vertices_buffer.write(self.stamina_bar_vertices_bytes,offset = opaque_element_to_buffer_write_offset)
        self.opaque_texcoords_buffer.write(self._ref_rm.ui_element_texcoords_bytes['health_bar'],offset = opaque_element_to_buffer_write_offset)
        
        opaque_element_to_buffer_write_offset += BYTES_PER_TEXTURE_QUAD

        # open item inventory cells 
        for row in range(self.open_item_inventory_rows_cols[0]):
            for col in range(self.open_item_inventory_rows_cols[1]):
                self.opaque_vertices_buffer.write(self.open_item_inven_vertices_bytes[False][(row,col)],offset = opaque_element_to_buffer_write_offset)
                self.opaque_texcoords_buffer.write(self._ref_rm.ui_element_texcoords_bytes['item_slot'][False],offset = opaque_element_to_buffer_write_offset)

                opaque_element_to_buffer_write_offset += BYTES_PER_TEXTURE_QUAD

        # current weapon display 

        hidden_element_to_buffer_write_offset = 0

        # hidden item inventory background 
        self.hidden_vertices_buffer.write(self.hidden_item_inven_background_vertices_bytes,offset = hidden_element_to_buffer_write_offset)
        self.hidden_texcoords_buffer.write(self._ref_rm.ui_element_texcoords_bytes['background'],offset = hidden_element_to_buffer_write_offset)

        hidden_element_to_buffer_write_offset += BYTES_PER_TEXTURE_QUAD

        # hidden item inventory 
        for row in range(self.hidden_item_inventory_rows_cols[0]):
            for col in range(self.hidden_item_inventory_rows_cols[1]):
                self.hidden_vertices_buffer.write(self.hidden_item_inven_vertices_bytes[False][(row,col)],offset = hidden_element_to_buffer_write_offset)
                self.hidden_texcoords_buffer.write(self._ref_rm.ui_element_texcoords_bytes['item_slot'][False],offset = hidden_element_to_buffer_write_offset)

                hidden_element_to_buffer_write_offset += BYTES_PER_TEXTURE_QUAD

        # weapons inventory (hidden)
        for row in range(self.weapon_inventory_rows_cols[0]):
            for col in range(self.weapon_inventory_rows_cols[1]):
                self.hidden_vertices_buffer.write(self.weapon_inven_vertices_bytes[False][(row,col)],offset = hidden_element_to_buffer_write_offset)
                self.hidden_texcoords_buffer.write(self._ref_rm.ui_element_texcoords_bytes['weapon_slot'][False],offset = hidden_element_to_buffer_write_offset)

                hidden_element_to_buffer_write_offset += BYTES_PER_TEXTURE_QUAD

    def _get_inventory_id(self,inven_cell : Cell | WeaponNode)->int:
        if isinstance(inven_cell,WeaponNode):
            inventory_id = inven_cell.list.inventory_id
        else: 
            inventory_id = inven_cell.inventory_id

        return inventory_id
        

    def _on_current_weapon_change_callback(self,prev_current_node:WeaponNode,new_current_node:WeaponNode)->None: 

        weapon_inventory = self._inven_list[2]

        if prev_current_node:
            row = prev_current_node.ind // weapon_inventory.columns 
            col = prev_current_node.ind - row * weapon_inventory.columns 

            write_to_buffer_offset = (prev_current_node.ind + self.hidden_item_inventory_cells + 1) * BYTES_PER_TEXTURE_QUAD

            self.hidden_vertices_buffer.write(self.weapon_inven_vertices_bytes[False][(row,col)],offset = write_to_buffer_offset)
            self.hidden_texcoords_buffer.write(self._ref_rm.ui_element_texcoords_bytes['weapon_slot'][False],offset = write_to_buffer_offset)


        if new_current_node:
            row = new_current_node.ind // weapon_inventory.columns 
            col = new_current_node.ind - row * weapon_inventory.columns 

            write_to_buffer_offset = (new_current_node.ind + self.hidden_item_inventory_cells + 1) * BYTES_PER_TEXTURE_QUAD

            self.hidden_vertices_buffer.write(self.weapon_inven_vertices_bytes[True][(row,col)],offset = write_to_buffer_offset)
            self.hidden_texcoords_buffer.write(self._ref_rm.ui_element_texcoords_bytes['weapon_slot'][True],offset = write_to_buffer_offset)


    def _on_cursor_item_change_callback(self)->None: 

        if self.cursor.item: 
            self.opaque_items_texcoords_buffer.write(self._ref_rm.item_texcoords_bytes[self.cursor.item.name],offset = self.opaque_items_texcoords_buffer.size - BYTES_PER_TEXTURE_QUAD)    
        else: 
            self.opaque_items_texcoords_buffer.write(self.null_texcoords_bytes,offset = self.opaque_items_texcoords_buffer.size - BYTES_PER_TEXTURE_QUAD)
        

    def _on_inven_item_change_callback(self,inven_cell:Cell|WeaponNode)->None: 
        
        inventory_id = self._get_inventory_id(inven_cell)
        inventory = self._inven_list[inventory_id] 

        row = inven_cell.ind // inventory.columns
        col = inven_cell.ind - row * inventory.columns
    

        if inventory_id == 0: 
            # open item inventory : write to the open item vertices and texcoords buffer 
            # acquire the offset of the buffer position from the cell index. 
            write_to_buffer_offset = (inven_cell.ind * BYTES_PER_TEXTURE_QUAD)

            if inven_cell.item: 
                self.opaque_items_vertices_buffer.write(self.open_item_vertices_bytes[False][(row,col)],offset = write_to_buffer_offset)
                self.opaque_items_texcoords_buffer.write(self._ref_rm.item_texcoords_bytes[inven_cell.item.name],offset = write_to_buffer_offset)
            else:
                self.opaque_items_vertices_buffer.write(self.null_vertices_bytes,offset = write_to_buffer_offset)
                self.opaque_items_texcoords_buffer.write(self.null_texcoords_bytes,offset = write_to_buffer_offset)
                

        elif inventory_id == 1:
            # hidden item inventory
            write_to_buffer_offset = (inven_cell.ind * BYTES_PER_TEXTURE_QUAD)
            if inven_cell.item: 
                self.hidden_items_vertices_buffer.write(self.hidden_item_vertices_bytes[False][(row,col)],offset = write_to_buffer_offset)
                self.hidden_items_texcoords_buffer.write(self._ref_rm.item_texcoords_bytes[inven_cell.item.name],offset = write_to_buffer_offset)
            else: 
                self.hidden_items_vertices_buffer.write(self.null_vertices_bytes,offset = write_to_buffer_offset)
                self.hidden_items_texcoords_buffer.write(self.null_texcoords_bytes,offset = write_to_buffer_offset)

        else:
            # weapon inventory 

            write_to_buffer_offset = (self.hidden_item_inventory_cells +inven_cell.ind) * BYTES_PER_TEXTURE_QUAD
            if inven_cell.weapon: 
                self.hidden_items_vertices_buffer.write(self.weapon_vertices_bytes[False][(row,col)],offset = write_to_buffer_offset) 
                self.hidden_items_texcoords_buffer.write(self._ref_rm.item_texcoords_bytes[inven_cell.weapon.name],offset = write_to_buffer_offset) 
            else: 
                self.hidden_items_vertices_buffer.write(self.null_vertices_bytes,offset = write_to_buffer_offset)
                self.hidden_items_texcoords_buffer.write(self.null_texcoords_bytes,offset = write_to_buffer_offset)

    


    def cursor_cell_hover_state_change_callback(self)->None: 
        # when the cursor hover state changes, you need to overwrite the corresponding cell's vertex data 
        # in the buffers

        if self.cursor.ref_prev_hovered_cell:
            # write non-hover cell to buffer 
            inventory_id = self._get_inventory_id(self.cursor.ref_prev_hovered_cell)
            inventory = self._inven_list[inventory_id]
            row = self.cursor.ref_prev_hovered_cell.ind // inventory.columns
            col = self.cursor.ref_prev_hovered_cell.ind - row * inventory.columns

            if inventory_id == 0:
                inventory_id = self.cursor.ref_prev_hovered_cell.inventory_id
                inventory = self._inven_list[inventory_id] 
                
                buffer_offset = (self.cursor.ref_prev_hovered_cell.ind + 2) * BYTES_PER_TEXTURE_QUAD
                self.opaque_vertices_buffer.write(self.open_item_inven_vertices_bytes[False][(row,col)],offset = buffer_offset)
                self.opaque_texcoords_buffer.write(self._ref_rm.ui_element_texcoords_bytes['item_slot'][False],offset = buffer_offset)

                self.opaque_items_vertices_buffer.write(self.open_item_vertices_bytes[False][(row,col)],offset = self.cursor.ref_prev_hovered_cell.ind * BYTES_PER_TEXTURE_QUAD)

            elif inventory_id == 1:

                buffer_offset = (self.cursor.ref_prev_hovered_cell.ind+1) * BYTES_PER_TEXTURE_QUAD
                self.hidden_vertices_buffer.write(self.hidden_item_inven_vertices_bytes[False][(row,col)],offset = buffer_offset)
                self.hidden_texcoords_buffer.write(self._ref_rm.ui_element_texcoords_bytes['item_slot'][False],offset = buffer_offset)

                self.hidden_items_vertices_buffer.write(self.hidden_item_vertices_bytes[False][(row,col)],offset = self.cursor.ref_prev_hovered_cell.ind * BYTES_PER_TEXTURE_QUAD)
            else: 
                if not (inventory.weapons_list.curr_node and inventory.weapons_list.curr_node.ind == self.cursor.ref_prev_hovered_cell.ind):
                    buffer_offset = (self.hidden_item_inventory_rows_cols[0]*self.hidden_item_inventory_rows_cols[1]+self.cursor.ref_prev_hovered_cell.ind+1) * BYTES_PER_TEXTURE_QUAD
                    self.hidden_vertices_buffer.write(self.weapon_inven_vertices_bytes[False][(row,col)],offset = buffer_offset)
                    self.hidden_texcoords_buffer.write(self._ref_rm.ui_element_texcoords_bytes['weapon_slot'][False],offset = buffer_offset)

                    self.hidden_items_vertices_buffer.write(self.weapon_vertices_bytes[False][(row,col)],offset = (self.hidden_item_inventory_rows_cols[0] * 
                                                                                                                     self.hidden_item_inventory_rows_cols[1]+self.cursor.ref_prev_hovered_cell.ind) * BYTES_PER_TEXTURE_QUAD)

        if self.cursor.ref_hovered_cell: 
            inventory_id = self._get_inventory_id(self.cursor.ref_hovered_cell)
            inventory = self._inven_list[inventory_id]
            row = self.cursor.ref_hovered_cell.ind // inventory.columns
            col = self.cursor.ref_hovered_cell.ind - row * inventory.columns

            if inventory_id == 0:

                buffer_offset = (self.cursor.ref_hovered_cell.ind + 2) * 6 * 4 * 2
                self.opaque_vertices_buffer.write(self.open_item_inven_vertices_bytes[True][(row,col)],offset = buffer_offset)
                self.opaque_texcoords_buffer.write(self._ref_rm.ui_element_texcoords_bytes['item_slot'][True],offset = buffer_offset)

                self.opaque_items_vertices_buffer.write(self.open_item_vertices_bytes[True][(row,col)],offset = self.cursor.ref_hovered_cell.ind * BYTES_PER_TEXTURE_QUAD)
            elif inventory_id == 1:

                buffer_offset = (self.cursor.ref_hovered_cell.ind+1) * BYTES_PER_TEXTURE_QUAD
                self.hidden_vertices_buffer.write(self.hidden_item_inven_vertices_bytes[True][(row,col)],offset = buffer_offset)
                self.hidden_texcoords_buffer.write(self._ref_rm.ui_element_texcoords_bytes['item_slot'][True],offset = buffer_offset)

                self.hidden_items_vertices_buffer.write(self.hidden_item_vertices_bytes[True][(row,col)],offset = self.cursor.ref_hovered_cell.ind * BYTES_PER_TEXTURE_QUAD)
            else: 

                if not (inventory.weapons_list.curr_node and inventory.weapons_list.curr_node.ind == self.cursor.ref_hovered_cell.ind):
                
                    buffer_offset = (self.hidden_item_inventory_rows_cols[0] * self.hidden_item_inventory_rows_cols[1] + self.cursor.ref_hovered_cell.ind+1) * BYTES_PER_TEXTURE_QUAD
                    self.hidden_vertices_buffer.write(self.weapon_inven_vertices_bytes[True][(row,col)],offset=buffer_offset)
                    self.hidden_texcoords_buffer.write(self._ref_rm.ui_element_texcoords_bytes['weapon_slot'][True],offset = buffer_offset)

                    self.hidden_items_vertices_buffer.write(self.weapon_vertices_bytes[True][(row,col)],offset = (self.hidden_item_inventory_rows_cols[0] * 
                                                                                                                        self.hidden_item_inventory_rows_cols[1]+self.cursor.ref_hovered_cell.ind) * BYTES_PER_TEXTURE_QUAD)


    
    # temporary helper function to add item to open item inventory
    def add_item(self,item,inven_ind:int)->None: 
        if inven_ind == 2 :
            self._inven_list[2].add_weapon(item,self._on_inven_item_change_callback,self._on_current_weapon_change_callback)
        else: 
            self._inven_list[inven_ind].add_item(item,self._on_inven_item_change_callback)
    
    
    def change_weapon(self,direction:int)->None: 
        self._inven_list[2].change_weapon(direction,self._on_current_weapon_change_callback)



    def update(self,dt:float,cursor_state_change_callback:"function",cursor_cell_hover_callback:"function")->None:
        # inventory open time update 
        self.inven_open_time = max(0,min(self.max_inven_open_time,self.inven_open_time + (2*self.inven_open_state - 1) * 4 * dt))

        # cursor update 
        self.cursor.update(self._true_to_native_ratio,dt,cursor_state_change_callback)

        # TODO: stamina, health bar updates

        # inventory updates 
        self._items_engine.update(self.cursor,cursor_cell_hover_callback,self._on_inven_item_change_callback,self._on_current_weapon_change_callback,
                                  self._on_cursor_item_change_callback,self.inven_open_time == self.max_inven_open_time)

        
    @property 
    def weapon_equipped(self)->bool: 
        return self._inven_list[2].weapons_list.curr_node != None  
    
    @property 
    def curr_weapon(self)->"Weapon":
        return self._inven_list[2].weapons_list.curr_node.weapon