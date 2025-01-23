from scripts.data import TRUE_RES_TO_HEALTH_BAR_WIDTH_RATIO,TRUE_RES_TO_STAMINA_BAR_WIDTH_RATIO,TRUE_RES_TO_HEALTH_STAMINA_BAR_HEIGHT_RATIO,SPACE_BETWEEN_INVENTORY_ELEMENTS,\
                        TRUE_RES_TO_HEALTH_BAR_TOPLEFT_RATIO,TRUE_RES_TO_WEAPON_INVEN_DIM_RATIO,TRUE_RES_TO_OPAQUE_ITEM_INVEN_DIM_RATIO,TRUE_RES_TO_HIDDEN_ITEM_INVEN_DIM_RATIO,\
                        TRUE_RES_TO_CURRENT_WEAPON_DISPLAY_DIM_RATIO, SPACE_BETWEEN_INVENTORY_CELLS,INVENTORY_CELL_EXPANSION_RATIO
from scripts.new_cursor import Cursor
from scripts.new_resource_manager import ResourceManager
from scripts.new_inventory import Inventory,InventoryEngine,WeaponInventory
import numpy as np 
class HUD:

    def __init__(self,true_res:tuple[int,int])->None: 
        self._ref_rm = ResourceManager.get_instance()
        self._true_res = true_res
 
        self.inven_open_state = False
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

        self.hidden_item_inventory_rows_cols = [3,5]
        self.hidden_item_inventory_cell_length = int(self._true_res[0] * TRUE_RES_TO_HIDDEN_ITEM_INVEN_DIM_RATIO[0]) // self.open_item_inventory_rows_cols[1] 

        self.current_weapon_display_cell_dim = (int(self._true_res[0] * TRUE_RES_TO_CURRENT_WEAPON_DISPLAY_DIM_RATIO[0]),
                                                 int(self._true_res[1] * TRUE_RES_TO_CURRENT_WEAPON_DISPLAY_DIM_RATIO[1]))
        

        # TODO: COMPUTE THIS: 
        self.hidden_item_inventory_max_rows = 0

        self._clamp_dimensions()

        self.weapon_inventory_topleft = (self.health_bar_topleft[0],
                                          self.health_bar_topleft[1] -self.weapon_inventory_rows_cols[0] * (self.weapon_inventory_cell_dim[1] + 1))

        self.current_weapon_display_topleft = (self.health_bar_topleft[0] + self.health_bar_dimensions[0]+SPACE_BETWEEN_INVENTORY_ELEMENTS,
                                                self.health_bar_topleft[1] -2)

        self.open_item_inventory_topleft = (self.health_bar_topleft[0]+self.health_bar_dimensions[0]+self.current_weapon_display_cell_dim[0]+SPACE_BETWEEN_INVENTORY_ELEMENTS,\
                                             self.health_bar_topleft[1] - int(0.5 * self.open_item_inventory_cell_length) + self.health_bar_dimensions[1])

        self.hidden_item_inventory_topleft = (self.open_item_inventory_topleft[0],self.open_item_inventory_topleft[1] -self.hidden_item_inventory_rows_cols[0] * (self.hidden_item_inventory_cell_length + 1))

        self._precompute_hud_display_elements_vertices()

        self.opqaue_vertices_buffer,self.opaque_texcoords_buffer, self.hidden_vertices_buffer, self.hidden_texcoords_buffer = \
            self._ref_rm.create_hud_vbos(3 + self.open_item_inventory_rows_cols[0] * self.open_item_inventory_rows_cols[1],
            self.hidden_item_inventory_rows_cols[0] * self.hidden_item_inventory_rows_cols[1]+ self.weapon_inventory_rows_cols[0] * self.weapon_inventory_rows_cols[1])

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

    def _precompute_hud_display_elements_vertices(self)->None:
        # health bar 
        self.health_bar_vertices = self._create_ui_element_vertices(self.health_bar_topleft,self.health_bar_dimensions) 

        # stamina bar 
        self.stamina_bar_vertices = self._create_ui_element_vertices(self.stamina_bar_topelft,self.stamina_bar_dimensions) 
        
        # open item inventory
        self.open_item_inven_vertices = {}
        self.open_item_inven_vertices[False] = {}
        self.open_item_inven_vertices[True] = {}

        for row in range(self.open_item_inventory_rows_cols[0]):
            for col in range(self.open_item_inventory_rows_cols[1]):
                idle_x = self.open_item_inventory_topleft[0] + col * (self.open_item_inventory_cell_length + SPACE_BETWEEN_INVENTORY_CELLS) 
                idle_y = self.open_item_inventory_topleft[1] + row * (self.open_item_inventory_cell_length + SPACE_BETWEEN_INVENTORY_CELLS)

                hovered_x = self.open_item_inventory_topleft[0] + col * (self.open_item_inventory_cell_length + SPACE_BETWEEN_INVENTORY_CELLS)\
                                -int(INVENTORY_CELL_EXPANSION_RATIO * self.open_item_inventory_cell_length)

                hovered_y = self.open_item_inventory_topleft[1]+ row * (self.open_item_inventory_cell_length + SPACE_BETWEEN_INVENTORY_CELLS)\
                                -int(INVENTORY_CELL_EXPANSION_RATIO * self.open_item_inventory_cell_length)

                hovered_length = int(self.open_item_inventory_cell_length*(1+2*INVENTORY_CELL_EXPANSION_RATIO))

                self.open_item_inven_vertices[False][(row,col)] = self._create_ui_element_vertices((idle_x,idle_y),(self.open_item_inventory_cell_length,self.open_item_inventory_cell_length))
                self.open_item_inven_vertices[True][(row,col)] = self._create_ui_element_vertices((hovered_x,hovered_y),(hovered_length,hovered_length))

        # open inventory cells 


    def _create_ui_element_vertices(self,topleft:tuple[int,int],size:tuple[int,int])->np.array:

        x = 2. * (topleft[0])/ self._true_res[0]- 1.
        y = 1. - 2. * (topleft[1])/ self._true_res[1]
        w = 2. * size[0] / self._true_res[0]
        h = 2. * size[1] /self._true_res[1]

        return np.array([(x, y), (x + w, y), (x, y - h),
                            (x, y - h), (x + w, y), (x + w, y - h)], dtype=np.float32)
        

    def _write_to_buffers(self)->None: 
        opaque_vertices_write_offset = 0
        opaque_texcoords_write_offset= 0 

        # health bar 
        self.opqaue_vertices_buffer.write(self.health_bar_vertices.tobytes())
        self.opaque_texcoords_buffer.write(self._ref_rm.ui_element_texcoords['health_bar'].tobytes())

        opaque_vertices_write_offset += 6*4*2
        opaque_texcoords_write_offset += 6*4*2

        # stamina bar 
        self.opqaue_vertices_buffer.write(self.stamina_bar_vertices.tobytes(),offset = opaque_vertices_write_offset)
        self.opaque_texcoords_buffer.write(self._ref_rm.ui_element_texcoords['health_bar'].tobytes(),offset = opaque_texcoords_write_offset)

        opaque_vertices_write_offset += 6*4*2
        opaque_texcoords_write_offset += 6*4*2

        # open item inventory cells 
        for row in range(self.open_item_inventory_rows_cols[0]):
            for col in range(self.open_item_inventory_rows_cols[1]):
                self.opqaue_vertices_buffer.write(self.open_item_inven_vertices[False][(row,col)].tobytes(),offset = opaque_vertices_write_offset)
                self.opaque_texcoords_buffer.write(self._ref_rm.ui_element_texcoords['item_slot'][False].tobytes(),offset = opaque_texcoords_write_offset)

                opaque_vertices_write_offset += 6*4*2
                opaque_texcoords_write_offset += 6*4*2



    def update_inventories(self)->None:
        # TODO: stamina, health bar updates

        # inventory updates 
        self._items_engine.update(self.cursor,self.inven_open_state)

        pass