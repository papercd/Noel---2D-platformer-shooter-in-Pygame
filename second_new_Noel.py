import pygame 
import platform
import importlib
from os import environ
from numpy import array,float32,float64,int32,uint8,uint16,bool_

from moderngl import create_context
from screeninfo import get_monitors

import scripts.data
import scripts.second_HUD
import scripts.systems

from scripts.second_HUD import HUD
from scripts.game_state import GameState
from scripts.data import PHYSICS_TIMESTEP
from scripts.new_resource_manager import ResourceManager
from scripts.new_entities_manager import EntitiesManager
from scripts.systems import PhysicsSystem,RenderSystem,InputHandler,StateSystem
from scripts.new_tilemap import Tilemap

class Noel():
    def __init__(self):
        pygame.init()
        self._initalize_game_settings() 
        self._initialize_game_systems()


    def _initialize_game_systems(self):
        
        self._resource_manager = ResourceManager.get_instance(self._ctx,self._game_context)
        self._entities_manager = EntitiesManager.get_instance()

        self._physics_system = PhysicsSystem()
        self._state_system = StateSystem()  
        self._render_system = RenderSystem(self._ctx,self._game_context)
        self._input_handler = InputHandler(self._game_context)

        self._tilemap = Tilemap(self._game_context,self._resource_manager.get_tilemap_json('test1.json'))
        self._hud = HUD(self._game_context)

        self._entities_manager.set_initial_player_position(self._tilemap.initial_player_position)
        self._physics_system.attatch_tilemap(self._tilemap)
        self._input_handler.attatch_hud(self._hud)
        self._render_system.attatch_hud(self._hud)
        self._render_system.attatch_tilemap(self._tilemap)
        self._render_system.attatch_background(self._resource_manager.backgrounds['start'])

  

    def _hot_reload(self)->None: 
        # reload systems module
        importlib.reload(scripts.data)
        importlib.reload(scripts.second_HUD)
        importlib.reload(scripts.systems)

        from scripts.second_HUD import HUD
        from scripts.systems import PhysicsSystem, StateSystem,RenderSystem, InputHandler 
        # reinitialize systems
        self._physics_system = PhysicsSystem()
        self._physics_system.attatch_tilemap(self._tilemap)
        
        self._state_system = StateSystem()

        self._hud = HUD(self._game_context["true_res"],self._game_context["display_scale_ratio"])

        self._render_system = RenderSystem(self._ctx,self._game_context['display_scale_ratio'],self._game_context['screen_res'],\
                                           self._game_context['true_res'])
        self._input_handler = InputHandler(self._game_context)
        
        self._input_handler.attatch_hud(self._hud)
        self._render_system.attatch_hud(self._hud)
        self._render_system.attatch_background(self._resource_manager.backgrounds['start'])
        self._render_system.attatch_tilemap(self._tilemap)
    

    def _initalize_game_settings(self):
        
        # game context is a set of game's system values that 
        # other systems have access to 
        self._game_context = {
            "camera_offset" : array([0,0],dtype=int32),
            "screen_shake": array([0,0],dtype = int32),
            "gamestate" : GameState.GameLoop,
            "true_res" : array([0,0],dtype=uint16),
            "screen_res": array([0,0],dtype= uint16),
            "display_scale_ratio": uint8(1)
        }

        # private members 
        self._float_camera_offset_buffer = array([0,0],dtype = float64)
        self._frame_count = array([0],dtype = uint16) 
        self._dt = array([0],dtype = float32) 
        #self._grass_rotation_function_time = float32(0)
        self._time_accumulator = array([0],dtype= float32)
        self._movement_input = [False,False]

        self._system_display_info = self._get_system_display_info()
        self._set_initial_display_settings()
        self._configure_pygame()

       # create moderngl context
        self._ctx = create_context()


    def _get_system_display_info(self):
        system_info = {}

        primary_monitor = get_monitors()[0]
        system_info["resolution"] = (primary_monitor.width, primary_monitor.height)


        if platform.system() == "Windows":
            import ctypes
            # Constants for system DPI 
            LOGPIXELSX = 88
            h_dc = ctypes.windll.user32.GetDC(0)
            dpi_x = ctypes.windll.gdi32.GetDeviceCaps(h_dc,LOGPIXELSX)
            ctypes.windll.user32.ReleaseDC(0,h_dc)

            # Calculate scale percentage
            system_info["scale_percentage"] = (dpi_x/96) * 100 

        elif platform.system() == "Darwin":
            import Quartz
            main_display_id = Quartz.CGMainDisplayID()
            scale_factor = Quartz.CGDisplayPixelsHigh(main_display_id) / Quartz.CGDisplayBounds(main_display_id).size.height
            system_info['scale_percentage'] = scale_factor * 100 
        else: 
            raise NotImplementedError("This Game Only runs on windows and macOS.")

        return system_info
    

    def _set_initial_display_settings(self):
        environ['SDL_VIDEO_CENTERED'] = '1'

        self._game_context["screen_res"][0] = uint16(self._system_display_info['resolution'][0])
        self._game_context["screen_res"][1] = uint16(self._system_display_info['resolution'][1])

        #TODO : you need to create a way to calculate native_res depending on selected resolution and scaling. 
        self._game_context["display_scale_ratio"] =  uint8(4)

        self._game_context["true_res"][0] = uint16(self._game_context["screen_res"][0] / uint16(self._game_context["display_scale_ratio"]))
        self._game_context["true_res"][1] = uint16(self._game_context["screen_res"][1] / uint16(self._game_context["display_scale_ratio"]))

    
    def _configure_pygame(self):
        # Check that pygame has been initialized
        assert pygame.get_init(), 'Error: Pygame is not initialized.'

        # setup sound mixer 
        pygame.mixer.pre_init(44100, -16, 2, 512)

        # setup clock 
        self._clock = pygame.time.Clock()
        # change cursor to invisible 
        pygame.mouse.set_visible(False)

        # Set OpenGL version to 4.3 core
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 4)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(
            pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)

        # Configure pygame display
        self._pygame_display = pygame.display.set_mode(
            self._game_context["screen_res"], pygame.HWSURFACE | pygame.OPENGL | pygame.DOUBLEBUF)

    def _update_render(self):

        self._frame_count[0] = (self._frame_count[0]+uint16(1)) % uint16(360)
        self._render_system.clear(0,0,0,0)
        self._dt[0] = min(float32(self._clock.tick() / 1000),float32(0.1))
        self._time_accumulator[0] += self._dt[0]

        if self._game_context['gamestate']== GameState.GameLoop: 
          
            player_position = self._entities_manager.player_physics_comp.position

            self._float_camera_offset_buffer[0] += 3*self._dt[0]*(player_position[0] + int32(self._game_context["true_res"][0]) // -2 - self._game_context['camera_offset'][0])
            self._float_camera_offset_buffer[1] += 3*self._dt[0]*(player_position[1] + int32(self._game_context["true_res"][1]) // -2 - self._game_context['camera_offset'][1])

            # cast the camera offset to be an integer 
            self._game_context['camera_offset'][0] = int32(self._float_camera_offset_buffer[0])
            self._game_context['camera_offset'][1] = int32(self._float_camera_offset_buffer[1])        


            while self._time_accumulator[0] >= PHYSICS_TIMESTEP:
                self._physics_system.process(PHYSICS_TIMESTEP)
                self._state_system.process(PHYSICS_TIMESTEP)
                self._time_accumulator[0] -= PHYSICS_TIMESTEP
            
            interpolation_delta = self._time_accumulator[0] / PHYSICS_TIMESTEP

            self._render_system.process(self._game_context,interpolation_delta,self._dt[0])
          
            pygame.display.flip()
            #fps = self._clock.get_fps()
            #print(fps)

    def start(self):
        self._dt[0] = float32(self._clock.tick() / 1000)
        self._time_accumulator[0] += self._dt[0] 
        while(True):
            self._input_handler.process(self._hot_reload)
            self._update_render() 
        

game = Noel()
game.start()