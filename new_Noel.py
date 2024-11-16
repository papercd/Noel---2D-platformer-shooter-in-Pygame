import pygame 
import platform
from os import environ,listdir
from json import load  as jsLoad

from scripts.background import Background
from scripts.new_tilemap import Tilemap
from scripts.layer import Layer_
from scripts.utils import load_texture 
from time import time
from enum import Enum
from my_pygame_light2d.engine import RenderEngine
from moderngl import create_context,Texture
from screeninfo import get_monitors
from scripts.gameSceneManager import GameSceneManager

class GameState(Enum): 
    StartSequence = 0
    MainMenu = 1
    MainMenuSettings =2
    GameLoop = 3
    PauseMenu = 4 
    PauseMenuSettings =5


TEXTURE_BASE_PATH = 'data/images/'

class Noel():
    def __init__(self):
        pygame.init()
        self._initalize_game_settings() 

        
        #TODO: HANDLE updates and rendering depending on gamestate 
        self._curr_gameState = GameState.GameLoop
        self._dt = 0
        self._prev_frame_time = 0



        self._backgrounds:dict[str,Background] = self._load_backgrounds(TEXTURE_BASE_PATH+'backgrounds')
        self._tilemap_jsons = self._load_tilemap_jsons('map_jsons')
    
        self.Tilemap = Tilemap(self._tilemap_jsons['test.json'])




    def _initalize_game_settings(self):
        self._system_display_info = self._get_system_display_info()
        self._set_initial_display_settings()
        self._configure_pygame()

       # create moderngl context
        self._ctx = create_context()
       
       # load game assets 
        self.atlas_dict  =  self._create_atlasses()
        """
        self.game_assets = GameAssets(self._ctx)
        self.general_sprites = self.game_assets.general_sprites
        self.interactable_obj_sprites = self.game_assets.interactable_obj_sprites
        self.enemy_sprites = self.game_assets.enemies
        """

       # setup render engine 
        self.render_engine = RenderEngine(self,self._ctx,self._screen_res,self._true_to_screen_res_ratio,self._true_res)


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
        self._screen_res = self._system_display_info['resolution']
        
        self._default_true_to_screen_res_ratio = 4 

        #TODO : you need to create a way to calculate native_res depending on selected resolution and scaling. 
        self._true_to_screen_res_ratio = 4.5 
        self._true_res = (int(self._screen_res[0]/self._true_to_screen_res_ratio),int(self._screen_res[1]/self._true_to_screen_res_ratio))
    
    def _configure_pygame(self):
        # Check that pygame has been initialized
        assert pygame.get_init(), 'Error: Pygame is not initialized. Please ensure you call pygame.init() before using the lighting engine.'

        # setup sound mixer 
        pygame.mixer.pre_init(44100, -16, 2, 512)

        # setup clock 
        self._clock = pygame.time.Clock()

        # Set OpenGL version to 3.3 core
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(
            pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)

        # Configure pygame display
        self._pygame_display = pygame.display.set_mode(
            self._screen_res, pygame.HWSURFACE | pygame.OPENGL | pygame.DOUBLEBUF)

    def _create_atlasses(self) -> dict[str,Texture]:
        """
        Create a dictionary for the atlasses (texture map) you want to use. 
        
        Access the atlass with the name of the atlass type (str) ex: 'tiles', 'spawners'

        """
        dict = {}
        
        # load tile atlas 
        dict['tiles'] = load_texture(TEXTURE_BASE_PATH + 'tiles/tile_atlas.png',self._ctx)

        
        return dict


    def _load_backgrounds(self,path:str) -> dict[str,Background]:
        """
        load background textures and create a dictionary with (path,Bacgkround) key-value pair 

        Args: 
            path (str) : the path to your directory containing folders with the background textures. 
        
        Returns: 
            A dictionary with (path, Background) key-value pair 
        """
        
        backgrounds_dict = {}
        
        for folder in listdir(path = path):
            textures = []
            for tex_path in listdir(path= path+'/'+folder):
                tex = load_texture(path+ '/' +folder + '/' + tex_path,self._ctx)
                textures.append(tex)

            backgrounds_dict[folder] = Background(textures)
        
        return backgrounds_dict


    def _load_tilemap_jsons(self,tilemaps_path:str):
        """
        load tilemap json files to create list of tilemap data

        Args: 
            tilemaps_path (str) : the path to your directory containing json files for different maps 

        Returns: 
            A dictionary with (filename, tilemap data) key-value pair 
        """
        tilemap_data_dict = {}

        for file_name in listdir(path = tilemaps_path):
            f = open(tilemaps_path+'/'+file_name,'r')
            tilemap_data = jsLoad(f)
            tilemap_data_dict[file_name] = tilemap_data

        return tilemap_data_dict

    def _load_tilemap(self,json_file_name:str) -> Tilemap:
        """
        create and return a Tilemap object from the json file specified by the file name. 
       
        Args: 
            json_file_name (str) : the name of the json file to read from. 

        Returns: 
            a Tilemap object 
        """ 
        return Tilemap(self._tilemap_jsons[json_file_name])
        
    
    def _handle_common_events(self,event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.quit_game() 
            if event.key == pygame.K_F12:
                pygame.display.toggle_fullscreen()
        if event.type == pygame.QUIT:
                self.quit_game() 


    def _handle_events(self):
        if self._curr_gameState == GameState.GameLoop:
            for event in pygame.event.get():
                self._handle_common_events(event)
                if event.type ==pygame.KEYDOWN:
                    pass 
                    



    def _update_render(self):
        
        self._dt = time() - self._prev_frame_time
        self._prev_frame_time = time()
        self.render_engine.set_ambient(255,255,255,255)
        if self._curr_gameState == GameState.GameLoop:

            self.render_engine.clear(0,0,0,255)

            self.render_engine.render_background_view(self._backgrounds['start'])

            #self.render_engine.render_tilemap(self._curr_tilemap,(0,0))

            self.render_engine.render((0,0),(0,0),(0,0))
            #self.render_engine.render_game_scene(self._curr_game_scene)
            
            pygame.display.flip()
            fps = self._clock.get_fps()
            pygame.display.set_caption(f"Noel - FPS: {fps: .2f}")
            self._clock.tick(60)
            

    def quit_game(self):
        pygame.quit()
        
        #TODO: release render engine
        quit()


    def start(self):
        while(True):
            self._handle_events()
            self._update_render() 

        





game = Noel()
game.start()