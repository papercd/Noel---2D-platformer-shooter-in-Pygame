from scripts.data import TRUE_RES_TO_HEALTH_BAR_WIDTH_RATIO,TRUE_RES_TO_STAMINA_BAR_WIDTH_RATIO,TRUE_RES_TO_HEALTH_STAMINA_BAR_HEIGHT_RATIO,SPACE_BETWEEN_INVENTORY_ELEMENTS
from scripts.new_cursor import Cursor

class HUD: 
    def __init__(self,true_res:tuple[int,int])->None: 
        
        self.cursor = Cursor()

        self._true_res = true_res
        self._inven_open_state = False

        self._create_diplay_elements()
        

    def _create_diplay_elements(self)->None:
        self._health_bar_topleft = (0,0)
        self._health_bar_dimensions = (int(TRUE_RES_TO_HEALTH_BAR_WIDTH_RATIO * self._true_res[0]),
                                       int(TRUE_RES_TO_HEALTH_STAMINA_BAR_HEIGHT_RATIO * self._true_res[1]))

        self._stamina_bar_topelft = (0,0)
        self._stamina_bar_dimensions = (int(TRUE_RES_TO_STAMINA_BAR_WIDTH_RATIO * self._true_res[0]),
                                       int(TRUE_RES_TO_HEALTH_STAMINA_BAR_HEIGHT_RATIO * self._true_res[1])) 


        self._weapon_inventory_rows_cols = (1,4)
        self._weapon_inventory_topleft = (0,0)
        self._weapon_inventory_cell_dim = (0,0)

        self._open_item_inventory_rows_cols = (1,5)
        self._open_item_inventory_topleft = (0,0)
        self._open_item_inventory_cell_dim = (0,0)

        self._hidden_item_inventory_rows_cols = (3,5)
        self._hidden_item_inventory_topleft = (0,0)
        self._hidden_item_inventory_cell_dim = (0,0)
        self._hidden_item_inventory_max_rows = 0




