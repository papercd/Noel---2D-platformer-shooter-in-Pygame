from scripts.new_resource_manager import ResourceManager
from scripts.new_entities_manager import EntitiesManager
from scripts.new_inventory import WeaponInventory,InventoryEngine

from my_pygame_light2d.color import normalize_color_arguments
from scripts.new_cursor import Cursor

from numpy import float32,ndarray,array,uint32,uint16,int32

from scripts.data import ENERGY_BAR_FULL_COLOR,ENERGY_BAR_DEPLETED_COLOR,HEALTH_BAR_DEPLETED_COLOR, HEALTH_BAR_FULL_COLOR,BYTES_PER_TEXTURE_QUAD,TRUE_RES_TO_HEALTH_BAR_TOPLEFT_RATIO_MANDELAE,TRUE_RES_TO_STAMINA_BAR_TOPLEFT_RATIO_MANDELAE,TRUE_RES_TO_WEAPON_DISPLAY_TOPLEFT_RATIO_MANDELAE,\
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

        # the background 
        self.background_topleft = None 
        self.background_dimensions = None

        # the health bar,
        self.health_bar_topleft = tuple((true_res_array_float32 * array(TRUE_RES_TO_HEALTH_BAR_TOPLEFT_RATIO_MANDELAE,dtype = float32)).astype(uint32)) 
        self.heatlh_bar_dimensions = tuple((true_res_array_float32 * array([TRUE_RES_TO_HEALTH_BAR_WIDTH_RATIO_MANDELAE,TRUE_RES_TO_HEALTH_STAMINA_BAR_HEIGHT_RATIO_MANDELAE],dtype = float32)).astype(uint32)) 

        # the energy (mouse cursor) bar,
        self.energy_bar_topleft = tuple((true_res_array_float32 * array(TRUE_RES_TO_STAMINA_BAR_TOPLEFT_RATIO_MANDELAE,dtype = float32)).astype(uint32)) 
        self.energy_bar_dimensions = tuple((true_res_array_float32 * array([TRUE_RES_TO_STAMINA_BAR_WIDTH_RATIO_MANDELAE,TRUE_RES_TO_HEALTH_STAMINA_BAR_HEIGHT_RATIO_MANDELAE],dtype = float32)).astype(uint32)) 

        # the weapon display 
        self.weapon_display_topleft = tuple((true_res_array_float32 * array(TRUE_RES_TO_WEAPON_DISPLAY_TOPLEFT_RATIO_MANDELAE,dtype = float32)).astype(uint32)) 
        self.weapon_display_dimensions = tuple((true_res_array_float32 * array(TRUE_RES_TO_WEAPON_DISPLAY_DIM_RATIO_MANDELAE,dtype = float32)).astype(uint32)) 

        # the bars 
        """
        self.health_resource_topleft = (self.health_bar_topleft[0]+uint32(1),self.health_bar_topleft[1]+ uint32(1)) 
        self.health_resource_dimensions = (self.heatlh_bar_dimensions[0]-uint32(2),self.heatlh_bar_dimensions[1]-uint32(2)) 

        self.energy_resource_topleft = (self.energy_bar_topleft[0]+uint32(1),self.energy_bar_topleft[1]+ uint32(1)) 
        self.energy_resource_dimensions = (self.energy_bar_dimensions[0]-uint32(2),self.energy_bar_dimensions[1]-uint32(2)) 
        """
        self._precompute_hud_display_elements_vertices()

        self.bars_vertices_and_color_buffer, self.vertices_buffer,self.texcoords_buffer = self._ref_rm.get_hud_diplay_vertices_and_texcoords(quads = 5)

        self._write_initial_state_to_buffers()

        self._inven_list = [
            WeaponInventory(1,1,self.weapon_display_topleft,self.weapon_display_dimensions,uint16(1),uint16(1),False)
        ]

        self._items_engine = InventoryEngine(self._inven_list)

    def _precompute_hud_display_elements_vertices(self)->None: 

        # background vertices 
        self.background_vertices_bytes = None 

        # health bar container vertices
        self.health_bar_vertices_bytes = self._create_hud_element_vertices(self.health_bar_topleft,self.heatlh_bar_dimensions) 

        # energy bar container vertices 
        self.energy_bar_vertices_bytes = self._create_hud_element_vertices(self.energy_bar_topleft,self.energy_bar_dimensions) 

        # weapon display vertices 
        self.weapon_display_vertices_bytes = self._create_hud_element_vertices(self.weapon_display_topleft,self.weapon_display_dimensions)


    def _create_hud_element_vertices(self,topleft:tuple[uint32,uint32],dimensions:tuple[uint32,uint32],asbytes:bool = True)->bytes|ndarray: 

        x = 2. * (topleft[0])/ self._game_ctx['true_res'][0]- 1.
        y = 1. - 2. * (topleft[1])/ self._game_ctx['true_res'][1]
        w = 2. * dimensions[0] / self._game_ctx['true_res'][0]
        h = 2. * dimensions[1] /self._game_ctx['true_res'][1]

        if asbytes: 
            return array([(x, y - h),(x + w, y - h),(x,y),
                            (x,y),(x + w, y - h),(x+w,y)],dtype= float32).tobytes()
        else: 
            return  array([(x, y - h),(x + w, y - h),(x,y),
                            (x,y),(x + w, y - h),(x+w,y)],dtype= float32)

    

    def _create_bar_colors(self,curr_health_to_max_ratio:float,curr_energy_to_max_ratio:float)->None: 
        """
        health - interpolate between red and yellow
        
        stmina - interpolate between blue and light blue

        """
        health_color_diff  = HEALTH_BAR_FULL_COLOR - HEALTH_BAR_DEPLETED_COLOR
        health_color = HEALTH_BAR_DEPLETED_COLOR + health_color_diff * curr_health_to_max_ratio


        energy_color_dif = ENERGY_BAR_FULL_COLOR - ENERGY_BAR_DEPLETED_COLOR
        energy_color = ENERGY_BAR_DEPLETED_COLOR + energy_color_dif * curr_energy_to_max_ratio

        return normalize_color_arguments(*health_color),normalize_color_arguments(*energy_color)

    def _write_initial_state_to_buffers(self)->None: 
        
        buffer_write_offset = 0

        # background 


        # health bar 
        self.vertices_buffer.write(self.health_bar_vertices_bytes,offset = buffer_write_offset)
        self.texcoords_buffer.write(self._ref_rm.ui_element_texcoords_bytes['health_bar'],offset = buffer_write_offset)

        buffer_write_offset += BYTES_PER_TEXTURE_QUAD
 
        # stamina bar 
        self.vertices_buffer.write(self.energy_bar_vertices_bytes,offset = buffer_write_offset)
        self.texcoords_buffer.write(self._ref_rm.ui_element_texcoords_bytes['health_bar'],offset = buffer_write_offset)
        
        buffer_write_offset += BYTES_PER_TEXTURE_QUAD
  
        # weapon display 
        self.vertices_buffer.write(self.weapon_display_vertices_bytes,offset = buffer_write_offset)
        self.texcoords_buffer.write(self._ref_rm.ui_element_texcoords_bytes['weapon_slot'][False],offset = buffer_write_offset)


    def update(self,dt:float32,interpolation_delta, tuple_camera_offset:tuple[int32,int32],cursor_state_change_callback:"function")->None: 
        # update the bar buffer 

        # offsets for health = vertices : 0 , color : 4 * 2 * 6 

        # offsets for stamina = vertices : 4 * 2 * 6 + 4 * 4, color : 4 * 4 * 6 + 4 * 4 

        health_resource_ratio = (self._ref_em.player_state_info_comp.health[0] / self._ref_em.player_state_info_comp.max_health)
        energy_resource_ratio = (self.cursor.energy[0] / self.cursor.max_energy)

        health_resource_bar_width = int((self.heatlh_bar_dimensions[0] - 2) * (health_resource_ratio))
        energy_resource_bar_width = int((self.energy_bar_dimensions[0] - 2) * (energy_resource_ratio))

        health_bar_vertices= self._create_hud_element_vertices((self.health_bar_topleft[0] + 1, self.health_bar_topleft[1] +1),(health_resource_bar_width,self.heatlh_bar_dimensions[1] - 3),False) 
        energy_bar_vertices= self._create_hud_element_vertices((self.energy_bar_topleft[0] + 1, self.energy_bar_topleft[1] +1),(energy_resource_bar_width,self.energy_bar_dimensions[1] - 3),False)

        health_bar_color,energy_bar_color= self._create_bar_colors(health_resource_ratio,energy_resource_ratio) 

        health_bar_color_bytes = health_bar_color.tobytes()
        energy_bar_color_bytes = energy_bar_color.tobytes()

        intermidiate_byte_array = bytearray()

        for i in range(6):
            intermidiate_byte_array.extend(health_bar_vertices[i].tobytes())
            intermidiate_byte_array.extend(health_bar_color_bytes)

        for i in range(6):
            intermidiate_byte_array.extend(energy_bar_vertices[i].tobytes())
            intermidiate_byte_array.extend(energy_bar_color_bytes)

        self.bars_vertices_and_color_buffer.write(intermidiate_byte_array)

        self.cursor.update(dt,cursor_state_change_callback,self._ref_em.player_physics_comp,self._ref_em.player_state_info_comp,tuple_camera_offset)