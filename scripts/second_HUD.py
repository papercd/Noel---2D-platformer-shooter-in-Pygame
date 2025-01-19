from scripts.data import TRUE_RES_TO_HEALTH_BAR_WIDTH_RATIO,TRUE_RES_TO_STAMINA_BAR_WIDTH_RATIO,TRUE_RES_TO_HEALTH_STAMINA_BAR_HEIGHT_RATIO,SPACE_BETWEEN_INVENTORY_ELEMENTS,\
                        TRUE_RES_TO_HEALTH_BAR_TOPLEFT_RATIO,TRUE_RES_TO_WEAPON_INVEN_DIM_RATIO,TRUE_RES_TO_OPAQUE_ITEM_INVEN_DIM_RATIO,TRUE_RES_TO_HIDDEN_ITEM_INVEN_DIM_RATIO,\
                        TRUE_RES_TO_CURRENT_WEAPON_DISPLAY_DIM_RATIO
from scripts.new_cursor import Cursor
from scripts.new_resource_manager import ResourceManager

class HUD: 
    def __init__(self,true_res:tuple[int,int])->None: 
        
        self._ref_rm = ResourceManager.get_instance()
        self.cursor = Cursor()
        self._true_res = true_res
        self._inven_open_state = False

        self._create_diplay_elements()
        

    def _create_diplay_elements(self)->None:
        self._health_bar_topleft = (int(self._true_res[0] * TRUE_RES_TO_HEALTH_BAR_TOPLEFT_RATIO[0]),
                                    int(self._true_res[1] * TRUE_RES_TO_HEALTH_BAR_TOPLEFT_RATIO[1]))
        self._health_bar_dimensions = (int(TRUE_RES_TO_HEALTH_BAR_WIDTH_RATIO * self._true_res[0]),
                                       int(TRUE_RES_TO_HEALTH_STAMINA_BAR_HEIGHT_RATIO * self._true_res[1]))

        self._stamina_bar_topelft = (self._health_bar_topleft[0],self._health_bar_topleft[1] + self._health_bar_dimensions[1] + 1)
        self._stamina_bar_dimensions = (int(TRUE_RES_TO_STAMINA_BAR_WIDTH_RATIO * self._true_res[0]),
                                       int(TRUE_RES_TO_HEALTH_STAMINA_BAR_HEIGHT_RATIO * self._true_res[1])) 

        self._weapon_inventory_rows_cols = (1,4)
        self._weapon_inventory_cell_dim = (int(self._true_res[0] * TRUE_RES_TO_WEAPON_INVEN_DIM_RATIO[0]) // self._weapon_inventory_rows_cols[1],
                                           int(self._true_res[1] * TRUE_RES_TO_WEAPON_INVEN_DIM_RATIO[1]) // self._weapon_inventory_rows_cols[0])

        self._open_item_inventory_rows_cols = (1,5)
        self._open_item_inventory_cell_dim = (int(self._true_res[0] * TRUE_RES_TO_OPAQUE_ITEM_INVEN_DIM_RATIO[0]) // self._open_item_inventory_rows_cols[1] ,
                                              int(self._true_res[1] * TRUE_RES_TO_OPAQUE_ITEM_INVEN_DIM_RATIO[1]) // self._open_item_inventory_rows_cols[0])

        self._hidden_item_inventory_rows_cols = [3,5]
        self._hidden_item_inventory_cell_dim = (int(self._true_res[0] * TRUE_RES_TO_HIDDEN_ITEM_INVEN_DIM_RATIO[0]) // self._open_item_inventory_rows_cols[1] ,
                                              int(self._true_res[1] * TRUE_RES_TO_HIDDEN_ITEM_INVEN_DIM_RATIO[1]) // self._open_item_inventory_rows_cols[0])

        self._current_weapon_display_cell_dim = (int(self._true_res[0] * TRUE_RES_TO_CURRENT_WEAPON_DISPLAY_DIM_RATIO[0]),
                                                 int(self._true_res[1] * TRUE_RES_TO_CURRENT_WEAPON_DISPLAY_DIM_RATIO[1]))
        

        # TO BE COMPUTED: 
        self._hidden_item_inventory_max_rows = 0

        self._clamp_inventory_cell_dims()

        self._weapon_inventory_topleft = (self._health_bar_topleft[0],
                                          self._health_bar_topleft[1] -self._weapon_inventory_rows_cols[0] * (self._weapon_inventory_cell_dim[1] + 1))

        self._current_weapon_display_topleft = (self._health_bar_topleft[0] + self._health_bar_dimensions[0]+SPACE_BETWEEN_INVENTORY_ELEMENTS,
                                                self._health_bar_topleft[1] -2)

        self._open_item_inventory_topleft = (self._health_bar_topleft[0]+self._health_bar_dimensions[0]+self._current_weapon_display_cell_dim[0]+SPACE_BETWEEN_INVENTORY_ELEMENTS,
                                             self._health_bar_topleft[1] - 1)

        self._hidden_item_inventory_topleft = (self._open_item_inventory_topleft[0],self._open_item_inventory_topleft[1] -self._hidden_item_inventory_rows_cols[0] * (self._hidden_item_inventory_cell_dim[1] + 1))

        self._ref_rm.precompute_hud_display_elements_vertices(self._health_bar_dimensions,self._stamina_bar_dimensions,
                                                              self._weapon_inventory_cell_dim,self._open_item_inventory_cell_dim,
                                                              self._hidden_item_inventory_cell_dim, self._current_weapon_display_cell_dim)


    def _clamp_inventory_cell_dims(self)->None: 
        pass


