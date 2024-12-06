import pygame 
import platform
import importlib
from os import environ,listdir
from json import load  as jsLoad
from scripts.utils import load_texture 
from time import time
from enum import Enum
from moderngl import create_context,Texture
from screeninfo import get_monitors

# testing 
from scripts.atlass_positions import ITEM_ATLAS_POSITIONS
import random

import scripts 
import my_pygame_light2d.engine

from scripts.item import Item,Weapon
from scripts.lists import interpolatedLightNode

from scripts.new_HUD import HUD
from scripts.new_grass import GrassManager
from scripts.new_particles import ParticleSystem
from scripts.new_cursor import Cursor 
from scripts.new_entities import Player
from scripts.new_tilemap import Tilemap
from my_pygame_light2d.engine import RenderEngine



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
        self._frame_count = 0
        self._dt = 0
        self._prev_frame_time = 0
        self.scroll = [0,0]
        self._player_movement_input = [0,0]

        self._backgrounds:dict[str,list[Texture]] = self._load_backgrounds(TEXTURE_BASE_PATH+'backgrounds')
        self._tilemap_jsons = self._load_tilemap_jsons('map_jsons')
        self._atlas_dict = self._create_texture_atlasses()

        self._initialize_game_objects()
        self._bind_objects_to_render_engine()


    def _initialize_game_objects(self):
        self._tilemap = Tilemap(self._atlas_dict['tiles'])
        self._tilemap.load_map(self._tilemap_jsons['test1.json'])  

        

        self.particle_system = ParticleSystem.get_instance(self._atlas_dict['particles']) 
        self.player = Player([74,11],(14,16)) 
        self.player.set_accel_rate(0.7)
        self.player.set_default_speed(2.2)

    
        self._grass_manager = GrassManager()
        self._hud = HUD(self._atlas_dict['UI_and_items'],self.player,self._true_res)

    def _bind_objects_to_render_engine(self):
        self.render_engine.bind_tilemap(self._tilemap)
        self.render_engine.bind_entities_atlas(self._atlas_dict['entities'])
        self.render_engine.bind_background(self._backgrounds['start'])
        self.render_engine.bind_hud(self._hud)
        self.render_engine.lights = self._tilemap.lights
    

    def _hot_reload(self):
        # import changed modules
        importlib.reload(scripts.new_HUD)
        importlib.reload(scripts.new_grass)
        importlib.reload(scripts.new_particles)
        importlib.reload(scripts.new_cursor)
        importlib.reload(scripts.new_entities)
        importlib.reload(scripts.new_tilemap)
        importlib.reload(scripts.new_inventory)
        importlib.reload(my_pygame_light2d.engine)
        

        # import changed classes
        from my_pygame_light2d.engine import RenderEngine
        from scripts.new_HUD import HUD
        from scripts.new_grass import GrassManager
        from scripts.new_particles import ParticleSystem
        from scripts.new_entities import Player
        from scripts.new_tilemap import Tilemap

        # reinitialize render engine 
        self.render_engine = RenderEngine(self._ctx,self._screen_res,self._true_to_screen_res_ratio,self._true_res)

        # explicitly reinitialize objects       
        self._tilemap = Tilemap(self._atlas_dict['tiles'])
        self._tilemap.load_map(self._tilemap_jsons['test1.json'])  

        self.particle_system = ParticleSystem.get_instance(self._atlas_dict['particles']) 
        self._grass_manager = GrassManager()
        
        # Update cursor's position
        
        cursor_topleft = pygame.mouse.get_pos()
        cursor_topleft =  (
            cursor_topleft[0] / self._true_to_screen_res_ratio + self.scroll[0],
            cursor_topleft[1] / self._true_to_screen_res_ratio + self.scroll[1],
        )

        # Reinitialize Player with updated cursor position
        self.player = Player(list(cursor_topleft), (14, 16))
        self.player.set_accel_rate(0.7)
        self.player.set_default_speed(2.2)

        # reinitialize hud
        self._hud = HUD(self._atlas_dict['UI_and_items'],self.player,self._true_res)

        # rebind objects to render engine
        self._bind_objects_to_render_engine()


    def _initalize_game_settings(self):
        self._system_display_info = self._get_system_display_info()
        self._set_initial_display_settings()
        self._configure_pygame()

       # create moderngl context
        self._ctx = create_context()
       

       # setup render engine and background buffer surface 
        self._background_buffer_srf = pygame.Surface(self._true_res)
        self.render_engine = RenderEngine(self._ctx,self._screen_res,self._true_to_screen_res_ratio,self._true_res)


    def _get_system_display_info(self):
        system_info = {}
        # primary monitor set to second monitor for hot reloading
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
        self._screen_res =self._system_display_info['resolution']
        #self._screen_res = (1440,950)
        
        self._default_true_to_screen_res_ratio = 3.5 

        #TODO : you need to create a way to calculate native_res depending on selected resolution and scaling. 
        self._true_to_screen_res_ratio = 4 
        self._true_res = (int(self._screen_res[0]/self._true_to_screen_res_ratio),int(self._screen_res[1]/self._true_to_screen_res_ratio))
    
    def _configure_pygame(self):
        # Check that pygame has been initialized
        assert pygame.get_init(), 'Error: Pygame is not initialized.'

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

    def _create_texture_atlasses(self) -> dict[str,Texture]:
        
        dict = {}

        dict['text'] = load_texture(TEXTURE_BASE_PATH + 'text/text_atl.png',self._ctx)
        dict['tiles'] = load_texture(TEXTURE_BASE_PATH+ 'tiles/tile_atlas.png',self._ctx)
        dict['entities'] = load_texture(TEXTURE_BASE_PATH + 'entities/entities_atlas.png',self._ctx)
        dict['cursor'] = load_texture(TEXTURE_BASE_PATH +'cursor/cursor_atlas.png',self._ctx)
        dict['particles'] = load_texture(TEXTURE_BASE_PATH + 'particles/animation_atlas.png',self._ctx)
        dict['UI_and_items'] = load_texture(TEXTURE_BASE_PATH + 'ui/ui_atlas.png',self._ctx)
        dict['items'] = load_texture(TEXTURE_BASE_PATH +'items/item_atlas.png',self._ctx)
        dict['weapons'] = load_texture(TEXTURE_BASE_PATH + 'weapons/weapon_atlas.png',self._ctx)

        return dict

    
    def _handle_common_events(self,event):
        
        self._hud.cursor.topleft= pygame.mouse.get_pos()
        self._hud.cursor.topleft= ((self._hud.cursor.topleft[0]/self._true_to_screen_res_ratio),(self._hud.cursor.topleft[1]/self._true_to_screen_res_ratio))
        self._hud.cursor.box.x,self._hud.cursor.box.y = self._hud.cursor.topleft[0] , self._hud.cursor.topleft[1]
        

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.quit_game() 
            if event.key == pygame.K_F12:
                pygame.display.toggle_fullscreen()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self._hud.cursor.pressed[0] = True 
            elif event.button == 3:
                self._hud.cursor.pressed[1] = True 
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self._hud.cursor.pressed[0] = False 
            elif event.button == 3:
                self._hud.cursor.pressed[1] = False 
 

        if event.type == pygame.QUIT:
                self.quit_game() 


    def _handle_events(self):
        if self._curr_gameState == GameState.GameLoop:
            for event in pygame.event.get():
                self._handle_common_events(event)
                if event.type ==pygame.KEYDOWN:
                    if event.key == pygame.K_F5:
                        self._hot_reload()
                    if event.key == pygame.K_e:
                        self._hud.set_inven_open_state(not self._hud.inven_open_state)
                    if event.key == pygame.K_a:
                        self._player_movement_input[0] = True 
                    if event.key == pygame.K_x: 
                        for row in self._hud._inven_list[0]._cells: 
                            for cell in row:
                                if cell._item: 
                                    print(cell._item.count)
                    if event.key == pygame.K_f: 
                        self._hud.add_item(Weapon('ak47',5,10))
                    if event.key == pygame.K_c:
                        # testing adding items to item inventory 
                        self._hud.add_item(Item(random.choice(list(ITEM_ATLAS_POSITIONS.keys()))))
                        pass 
                    if event.key == pygame.K_w: 
                        self.player.jump()
                    if event.key == pygame.K_s:
                        self.player.crouch = True
                    if event.key == pygame.K_d:
                        self._player_movement_input[1] = True 
                    if event.key == pygame.K_LSHIFT:
                        self.player.running = True
                        self._hud.cursor.special_actions = True 
                if event.type == pygame.KEYUP: 
                    if event.key == pygame.K_w:
                        self.player.jump_cut()
                    if event.key == pygame.K_a: 
                        self._player_movement_input[0] = False 
                    if event.key == pygame.K_d: 
                        self._player_movement_input[1] = False 
                    if event.key == pygame.K_s: 
                        self.player.crouch = False
                    if event.key == pygame.K_LSHIFT:
                        self.player.running = False
                        self._hud.cursor.special_actions = False 
    



    def _update_render(self):
        self._frame_count = (self._frame_count+1) %360
        self._dt = time() - self._prev_frame_time
        self._prev_frame_time = time()
        self.render_engine.set_ambient(255,255,255, 25)
        self.render_engine.clear(0,0,0,255)

        if self._curr_gameState == GameState.GameLoop:  
            
            self.scroll[0] += (self.player.pos[0]+ self.player.size[0]/2 - self._true_res[0] /2 - self.scroll[0])/20
            self.scroll[1] += (self.player.pos[1] +self.player.size[1]/2 - self._true_res[1] /2 - self.scroll[1])/20

            camera_scroll = (int(self.scroll[0]), int(self.scroll[1]))
            
            self.render_engine.hulls = self._tilemap._hull_grid.query(camera_scroll[0]-self._tilemap.tile_size * 10 ,camera_scroll[1]- self._tilemap.tile_size * 10,camera_scroll[0] \
                                                             + self._true_res[0]+self._tilemap.tile_size * 10 ,camera_scroll[1]+ self._true_res[1]+ self._tilemap.tile_size * 10)


            self.particle_system.update(self._tilemap,self._grass_manager)
            self.player.update(self._tilemap,self._hud.cursor.topleft,self._player_movement_input,self._frame_count)
            self.render_engine.bind_player(self.player)
            self._hud.update()
            self.render_engine.bind_hud(self._hud)
            self._tilemap.update_ambient_node_ptr(self.player.pos)
            self.render_engine.render_background_scene_to_fbo(camera_scroll,infinite=False)
            self.render_engine.render_foreground_scene_to_fbo()
            

            self.render_engine.render_scene_with_lighting(camera_scroll,(0,0))
            
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