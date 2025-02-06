import pygame 
import platform
from os import environ
from moderngl import create_context
from screeninfo import get_monitors

from editor_scripts.systems import InputHandler
from editor_scripts.resource_manager import ResourceManager
from editor_scripts.interface import EditorInterface

class Editor():
    def __init__(self):
        pygame.init()
        self._initalize_game_settings() 
        self._initialize_game_systems()


    def _initialize_game_systems(self):
        # for the editor you need : 
        # the background, tilemap, entities (but their physics aren't updated)
        # lights, and the tile panel. 

        self._resource_manager = ResourceManager.get_instance(self._ctx)
        self._editor_interface = EditorInterface.get_instance()
        self._input_handler = InputHandler(self._editor_context)

    def _initalize_game_settings(self):
        
        self._editor_context = {
            "camera_offset" : [0,0],
            "screen_shake": [0,0],
            "true_res" : (0,0),
            "screen_res": (0,0),
            "display_scale_ratio": 4
        }

        # private members 
        self._dt :float = 0
        self._time_accumulator:float = 0
        self._movement_input:list[bool,bool] = [False,False]

        self._system_display_info = self._get_system_display_info()
        self._set_initial_display_settings()
        self._configure_pygame()

       # create moderngl context
        self._ctx = create_context()


    def _get_system_display_info(self):
        system_info = {}

        primary_monitor = get_monitors()[0]
        system_info["resolution"] = (primary_monitor.width-50, primary_monitor.height-50)


        if platform.system() == "Windows":
            system_info['os'] = "Windows"
            import ctypes
            # Constants for system DPI 
            LOGPIXELSX = 88
            h_dc = ctypes.windll.user32.GetDC(0)
            dpi_x = ctypes.windll.gdi32.GetDeviceCaps(h_dc,LOGPIXELSX)
            ctypes.windll.user32.ReleaseDC(0,h_dc)

            # Calculate scale percentage
            system_info["scale_percentage"] = (dpi_x/96) * 100 

        elif platform.system() == "Darwin":
            system_info['os'] = 'Mac'
            import Quartz
            main_display_id = Quartz.CGMainDisplayID()
            scale_factor = Quartz.CGDisplayPixelsHigh(main_display_id) / Quartz.CGDisplayBounds(main_display_id).size.height
            system_info['scale_percentage'] = scale_factor * 100 
        else: 
            raise NotImplementedError("This Game Only runs on windows and macOS.")

        return system_info
    

    def _set_initial_display_settings(self):
        environ['SDL_VIDEO_CENTERED'] = '1'

        self._editor_context["screen_res"] = self._system_display_info['resolution']
        
        #TODO : you need to create a way to calculate native_res depending on selected resolution and scaling. 
        self._editor_context["display_scale_ratio"] = 4.0 
        self._editor_context["true_res"]= (int(self._editor_context["screen_res"][0]/self._editor_context["display_scale_ratio"]),\
                                         int(self._editor_context["screen_res"][1]/self._editor_context["display_scale_ratio"]))
    
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
            self._editor_context["screen_res"], pygame.HWSURFACE | pygame.OPENGL | pygame.DOUBLEBUF) 

    def _update_render(self):

        self._dt = min(self._clock.tick() / 1000.0,0.1)
        self._time_accumulator += self._dt
        
        pygame.display.flip()

    def start(self):
        self._dt = self._clock.tick() / 1000.0
        self._time_accumulator += self._dt 

        while(True):
            self._input_handler.handle_inputs()
            self._update_render() 
        

editor = Editor()
editor.start()