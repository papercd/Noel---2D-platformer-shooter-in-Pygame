from my_pygame_light2d.engine import RenderEngine
from screeninfo import get_monitors
from scripts.new_panel import TilePanel
from scripts.new_tilemap import Tilemap
from scripts.new_cursor import Cursor
from scripts.utils import load_texture
from os import environ,listdir
from json import load as jsLoad
from moderngl import create_context,Texture
import platform 
import sys 
import pygame 
from time import time

TEXTURE_BASE_PATH = 'data/images/'

class Editor: 
    def __init__(self):
        pygame.init()
        self._initalize_game_settings()
        
        self._backgrounds:dict[str,list[Texture]] = self._load_backgrounds(TEXTURE_BASE_PATH + 'backgrounds')


        self._tilemap_jsons = self._load_tilemap_jsons('map_jsons')
        self._atlas_dict = self._create_texture_atlasses()
        self._tilemap = Tilemap(self._atlas_dict['tiles'])
        self._tilemap.load_map(self._tilemap_jsons['test1.json'])

    


        self._dt = 0
        self._prev_frame_time = 0
        self._scroll_speed = 3
        self._scroll_increm = 4
        self._camera_movement = [0,0,0,0]
        self._scroll = [0,0]

        self._main_tile_panel = TilePanel(self._true_res)
        self._cursor = Cursor(self._atlas_dict['cursor'],in_editor= True)

    def _initalize_game_settings(self):
        self._system_display_info = self._set_system_display_info()
        self._set_initial_display_settings()
        self._configure_pygame()

       # create moderngl context
        self._ctx = create_context()
       

       # setup render engine
        self.render_engine = RenderEngine(self,self._ctx,self._screen_res,self._true_to_screen_res_ratio,self._true_res)


    def _set_system_display_info(self):
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
            raise NotImplementedError("The editor only runs on windows and macOS.")

        return system_info
    

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



    def _set_initial_display_settings(self):
        environ['SDL_VIDEO_CENTERED'] = '1'
        self._screen_res = self._system_display_info['resolution']
        
        self._default_true_to_screen_res_ratio = 4 

        #TODO : you need to create a way to calculate native_res depending on selected resolution and scaling. 
        self._true_to_screen_res_ratio = 4 
        self._true_res = (int(self._screen_res[0]/self._true_to_screen_res_ratio),int(self._screen_res[1]/self._true_to_screen_res_ratio))
    
    def _configure_pygame(self):
        # Check that pygame has been initialized
        assert pygame.get_init(), 'Error: Pygame is not initialized. Please ensure you call pygame.init() before using the lighting engine.'

        # setup sound mixer 
        pygame.mixer.pre_init(44100, -16, 2, 512)

        # setup clock 
        self._clock = pygame.time.Clock()

        # change cursor to invisible 
        pygame.mouse.set_visible(False)

        # Set OpenGL version to 3.3 core
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(
            pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)

        # Configure pygame display
        self._pygame_display = pygame.display.set_mode(
            self._screen_res, pygame.HWSURFACE | pygame.OPENGL | pygame.DOUBLEBUF)


    def _load_backgrounds(self,path:str) -> dict[str,list[Texture]]:
        """
        load background textures and create a dictionary with (path,Bacgkround) key-value pair 

        Args: 
            path (str) : the path to your directory containing folders with the background textures. 
        
        Returns: 
            A dictionary with (path, textures) key-value pair 
        """
        
        backgrounds_dict = {}
        
        for folder in listdir(path = path):
            textures = []
            for tex_path in listdir(path= path+'/'+folder):
                tex = load_texture(path+ '/' +folder + '/' + tex_path,self._ctx)
                textures.append(tex)

            backgrounds_dict[folder] = textures
        
        return backgrounds_dict




    def _create_texture_atlasses(self) -> dict[str,Texture]:
        
        dict = {}

        dict['tiles'] = load_texture(TEXTURE_BASE_PATH+ 'tiles/tile_atlas.png',self._ctx)
        dict['entities'] = load_texture(TEXTURE_BASE_PATH + 'entities/entities_atlas.png',self._ctx)
        dict['cursor'] = load_texture(TEXTURE_BASE_PATH +'cursor/cursor_atlas.png',self._ctx)
        dict['text'] = load_texture(TEXTURE_BASE_PATH +'text/text_atl.png',self._ctx)
        return dict


    def _handle_events(self):   
        self._cursor.pos = pygame.mouse.get_pos()
        self._cursor.pos = ((self._cursor.pos[0]/self._true_to_screen_res_ratio),(self._cursor.pos[1]/self._true_to_screen_res_ratio))
        self._cursor.box.x,self._cursor.box.y = self._cursor.pos[0],self._cursor.pos[1]

        events = pygame.event.get()
        for event in events: 
            if event.type == pygame.QUIT: 
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self._main_tile_panel.check_click(self._cursor)
                    self._cursor.pressed[0] = True
                if event.button == 3:
                    self._cursor.pressed[1] = True
            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self._cursor.pressed[0] = False 
                if event.button == 3:
                    self._cursor.pressed[1] = False  
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_a: 
                    self._camera_movement[0] = True 
                if event.key == pygame.K_d: 
                    self._camera_movement[1] = True
                if event.key == pygame.K_w: 
                    self._camera_movement[2] = True 
                if event.key == pygame.K_s: 
                    self._camera_movement[3] = True
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_a: 
                    self._camera_movement[0] =False 
                if event.key == pygame.K_d: 
                    self._camera_movement[1] = False
                if event.key == pygame.K_w: 
                    self._camera_movement[2] = False
                if event.key == pygame.K_s: 
                    self._camera_movement[3] = False
 
                

                
            

    def _update_render(self):
        self._dt = time() - self._prev_frame_time
        self._prev_frame_time = time()
        self.render_engine.set_ambient(255,255,255,255)
        self.render_engine.clear(255,255,255,255)
        
        self._scroll[0] += (self._camera_movement[1] - self._camera_movement[0]) * (self._scroll_speed+self._scroll_increm)
        self._scroll[1] += (self._camera_movement[3] - self._camera_movement[2]) * (self._scroll_speed+self._scroll_increm)

        camera_scroll = (int(self._scroll[0]),int(self._scroll[1]))
        self._cursor.update()

        self._main_tile_panel.update(self._cursor)

        self.render_engine.render_background_only_to_fbo(self._backgrounds['new_building'],camera_scroll)

        self.render_engine.render_tile_panel(self._atlas_dict['text'],self._main_tile_panel)

        self.render_engine.render_foreground_scene_to_fbo(self._cursor)

        self.render_engine.render_scene_with_lighting((float('-inf'),float('inf')),camera_scroll,(0,0))
        pygame.display.flip()
        fps = self._clock.get_fps()
        pygame.display.set_caption(f"Noel - FPS: {fps: .2f}")
        self._clock.tick(60)
        

    def run(self):
        while(True):
            self._handle_events()
            self._update_render()

editor = Editor()
editor.run()




















