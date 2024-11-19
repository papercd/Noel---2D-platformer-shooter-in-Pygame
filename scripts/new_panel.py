from scripts.atlass_positions import TILE_ATLAS_POSITIONS
from scripts.lists import TileCategories,Category
from scripts.new_cursor import Cursor 

class TilePanel:
    """ A Class to manage tiles for tilemap creation """

    def __init__(self,true_res:tuple[int,int]):
        self._true_res = true_res   

        self._size = (self._true_res[0] * 3 // 8, self._true_res[1])
        self._category_panel_size = (self._true_res[0] *3// 8, self._true_res[1] //5)

        self._stick_grid = False 
        self._on_grid = False 
        self._randomize_autotile = False 
        self._create_selection_box = False 
        self._selection_box_del_option = 0
        self._mark_tiles_for_AT = False 
        

        self._categories = TileCategories((0,0),self._category_panel_size,TILE_ATLAS_POSITIONS.keys())
        self._indicator_labels = ('stick_grid','on_grid','randomize_autotile','create_selection_box','selection_box_del_option','mark_tiles_for_AT')
        self._tile_panel_scroll = 0
        self._categories_scroll = 0



    @property
    def category_panel_scroll(self):
        return self._categories_scroll

    @property 
    def current_category(self) -> Category:
        return self._categories.curr_node
    
    
    @property
    def categories(self) -> TileCategories:
        return self._categories


    def _mouse_within_bounds(self,cursor):
        if (0<= cursor.pos[0] <= self._size[0]):
            if   (0<=cursor.pos[1]<= self._category_panel_size[1]):
                return 1
            elif (self._category_panel_size[1] < cursor.pos[1] <= self._size[1] *3//5):
                return 2 
            else:     
                return 3 
        else: 
            return 0 
        
    def check_click(self,cursor:Cursor):
        mouse_pos_section = self._mouse_within_bounds(cursor)
        if mouse_pos_section == 1:
            self._categories.check_click(cursor,self._categories_scroll,self._tile_panel_scroll)
        elif mouse_pos_section == 2:
            pass 
        elif mouse_pos_section == 3:
            pass 

    def update(self,cursor:Cursor):
        self._categories.check_hover(cursor,self._categories_scroll,self._tile_panel_scroll)
