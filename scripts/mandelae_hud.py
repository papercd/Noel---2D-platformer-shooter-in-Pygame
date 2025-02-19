from scripts.new_resource_manager import ResourceManager
from scripts.new_entities_manager import EntitiesManager
from scripts.new_cursor import Cursor

from numpy import float32,array,uint32

from scripts.data import TRUE_RES_TO_HEALTH_BAR_TOPLEFT_RATIO_MANDELAE,TRUE_RES_TO_STAMINA_BAR_TOPLEFT_RATIO_MANDELAE,TRUE_RES_TO_WEAPON_DISPLAY_TOPLEFT_RATIO_MANDELAE,\
                         TRUE_RES_TO_HEALTH_BAR_WIDTH_RATIO_MANDELAE,TRUE_RES_TO_STAMINA_BAR_WIDTH_RATIO_MANDELAE,TRUE_RES_TO_WEAPON_DISPLAY_DIM_RATIO_MANDELAE,TRUE_RES_TO_HEALTH_STAMINA_BAR_HEIGHT_RATIO_MANDELAE
                   

class HUD: 

    def __init__(self,game_context)->None: 
        self._ref_rm = ResourceManager.get_instance()
        self._ref_em = EntitiesManager.get_instance()

        self._game_ctx = game_context
         
        #self.inven_open_state = False
        #self.inven_open_time = array([0],dtype = float64) 
        #self.max_inven_open_time = 30 * PHYSICS_TIMESTEP
        self.cursor = Cursor()

        self._create_display_elements()
        

    def _create_display_elements(self)->None: 

        true_res_array_float32 = self._game_ctx["true_res"].astype(float32)

        # the health bar,
        self.health_bar_topleft = tuple((true_res_array_float32 * array(TRUE_RES_TO_HEALTH_BAR_TOPLEFT_RATIO_MANDELAE,dtype = float32)).astype(uint32)) 
        self.heatlh_bar_dimensions = tuple((true_res_array_float32 * array([TRUE_RES_TO_HEALTH_BAR_WIDTH_RATIO_MANDELAE,TRUE_RES_TO_HEALTH_STAMINA_BAR_HEIGHT_RATIO_MANDELAE],dtype = float32)).astype(uint32)) 

        # the energy (mouse cursor) bar,
        self.energy_bar_topelft = tuple((true_res_array_float32 * array(TRUE_RES_TO_STAMINA_BAR_TOPLEFT_RATIO_MANDELAE,dtype = float32)).astype(uint32)) 
        self.energy_bar_dimensions = tuple((true_res_array_float32 * array([TRUE_RES_TO_STAMINA_BAR_WIDTH_RATIO_MANDELAE,TRUE_RES_TO_HEALTH_STAMINA_BAR_HEIGHT_RATIO_MANDELAE],dtype = float32)).astype(uint32)) 

        # the weapon display 
        self.weapon_display_topleft = tuple((true_res_array_float32 * array(TRUE_RES_TO_WEAPON_DISPLAY_TOPLEFT_RATIO_MANDELAE,dtype = float32)).astype(uint32)) 
        self.weapon_display_dimensions = tuple((true_res_array_float32 * array(TRUE_RES_TO_WEAPON_DISPLAY_DIM_RATIO_MANDELAE,dtype = float32)).astype(uint32)) 

        self._precompute_hud_display_elements_vertices()


    def _precompute_hud_display_elements_vertices(self)->None: 

        # health bar container vertices
        self.health_bar_vertices_bytes = self._create_hud_element_vertices(self.health_bar_topleft,self.heatlh_bar_dimensions) 

        # energy bar container vertices 
        self.energy_bar_vertices_bytes = self._create_hud_element_vertices(self.energy_bar_topelft,self.energy_bar_dimensions) 


    def _create_hud_element_vertices(self,topleft:tuple[uint32,uint32],dimensions:tuple[uint32,uint32])->bytes: 

        x = 2. * (topleft[0])/ self._game_ctx['true_res'][0]- 1.
        y = 1. - 2. * (topleft[1])/ self._game_ctx['true_res'][1]
        w = 2. * dimensions[0] / self._game_ctx['true_res'][0]
        h = 2. * dimensions[1] /self._game_ctx['true_res'][1]

        return array([(x, y - h),(x + w, y - h),(x,y),
                         (x,y),(x + w, y - h),(x+w,y)],dtype= float32).tobytes()


