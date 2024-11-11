from scripts.particles import glass
import numpy as np 
import pygame
import random
import math
import time
import sys 
import os 
import platform
from screeninfo import get_monitors
from scripts import * 

from assets import GameAssets
from my_pygame_light2d.engine import LightingEngine, Layer_
from my_pygame_light2d.light import PointLight
from scripts.tilemap import Light
from my_pygame_light2d.hull import Hull
from enum import Enum


class GameState(Enum):
    StartSequence = 0
    MainMenu = 1
    MainMenuSettings = 2
    GameLoop = 3
    PauseMenu = 4
    PauseMenuSettings =5 


class myGame():
    def __init__(self):
        # set display settings, setup lighting engine and load game assets. 
        self._initialize_game_settings()

        
        """ initialize public members """
        
        # tilemap 
        self.Tilemap = Tilemap(self,tile_size=16,offgrid_layers=2)
        
        # cursor 

        # player 
        self.player = PlayerEntity(self,(50,50),(14,16))
        self.player.set_accel_rate(0.7)
        self.player.set_default_speed(2.2)
        self.player_movement_input = [False,False] 
   
  
        # other tracking variables
        self.frame_count = 0
        self.mouse_pressed = [False,False] 
        self.shift_pressed = False
        self.reset = True 
        
        """ initialize private members""" 
        
        # game object containers 
        self._enemies = []
        self._enemy_bullets = []
 
        # particles and effects containers 

        
        self._scroll = [0,0]
      
        self._dt = 0
        self._prev_frame_time= time.time()
     

        self._ambient_node_ptr = self.Tilemap.ambientNodes.set_ptr(self.player.pos[0])  



       
        
        
    def _initialize_game_settings(self):
        pygame.init()
        pygame.mixer.pre_init(44100, -16, 2, 512)
        self._clock = pygame.time.Clock()
        self._system_display_info = self._get_system_display_info()
        self._default_screen_to_native_ratio = 4

        self._set_initial_display_settings()
        self._setup_engine_and_render_surfs()
        self._load_game_assets()

    def _set_initial_display_settings(self):
        os.environ['SDL_VIDEO_CENTERED'] = '1'
        #self._screen_size = self._system_display_info['resolution']
        self._screen_size = (1400,750)

        #TODO : you need to create a way to calculate native_res depending on selected resolution and scaling. 
        self._screen_to_native_ratio = 2.5 
        self._native_res = (int(self._screen_size[0]/self._screen_to_native_ratio),int(self._screen_size[1]/self._screen_to_native_ratio))

    def _setup_engine_and_render_surfs(self):
        self.render_engine = LightingEngine(self,screen_res=self._screen_size,screen_to_native_ratio = self._screen_to_native_ratio,native_res=self._native_res,lightmap_res=self._native_res)

        self._background_surf_dim = self._foreground_surf_dim = self.buffer_surf_dim = (int(self._screen_size[0]/self._screen_to_native_ratio),int(self._screen_size[1]/self._screen_to_native_ratio))
        self.buffer_surf = pygame.Surface(self.buffer_surf_dim,pygame.SRCALPHA)
        self.background_surf = pygame.Surface(self._background_surf_dim,pygame.SRCALPHA)
        self.foreground_surf = pygame.Surface(self._foreground_surf_dim,pygame.SRCALPHA)

        # testing custom shaders 
        self.test_shader = self.render_engine.load_shader_from_path('vertex.glsl','fog_fragment.glsl')

    def _load_game_assets(self):
        self.game_assets = GameAssets()
        self.general_sprites = self.game_assets.general_sprites
        self.interactable_obj_sprites = self.game_assets.interactable_obj_sprites
        self.enemy_sprites = self.game_assets.enemies
        self.backgrounds = self.game_assets.backgrounds

        """

        self._window_icon = self.general_sprites['player']
        self._pygame_logo = self.general_sprites['start_logo']
        self._pygame_logo_center_offset = (-4/self._screen_to_native_ratio ,35/self._screen_to_native_ratio)
        self._pygame_logo_dim = self._pygame_logo.get_size()
        self._pygame_logo_ratio = self._pygame_logo_dim[0] /self._pygame_logo_dim[1]
        self._pygame_logo = pygame.transform.smoothscale(self._pygame_logo.convert_alpha(),(self._native_res[0]//2,  (self._native_res[0]//2) / self._pygame_logo_ratio))
        self._pygame_logo_dim = self._pygame_logo.get_size()
        pygame.display.set_icon(self._window_icon)

        """
        
        
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


    def _load_map_init_game_env(self,map_file_name):

        self.render_engine.lights = self.Tilemap.load_map_return_lights(map_file_name)

        self.Tilemap.extract_game_objs()

        self._ambient_node_ptr = self.Tilemap.ambientNodes.set_ptr(self.player.pos[0])
        self.render_engine.set_ambient(*self._ambient_node_ptr.colorValue)
       
    
    def _handle_common_events(self,event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.quit_game() 
            if event.key == pygame.K_F12:
                pygame.display.toggle_fullscreen()
        if event.type == pygame.QUIT:
                self.quit_game() 

        elif event.type == pygame.MOUSEWHEEL:
            if self._curr_gameState == GameState.GameLoop:
                self.player.change_weapon(event.y)
                
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.mouse_pressed[0] = True
            elif event.button == 3:
                self.mouse_pressed[1] = True  

        elif event.type == pygame.MOUSEBUTTONUP: 
            if event.button == 1:
                self.mouse_pressed[0] = False
            elif event.button == 3:
                self.mouse_pressed[1] = False 
		 
	
    def _handle_events(self):
        """
        if self.mouse_pressed[0]:
            if not self.cursor.interacting:
                if self.player.return_weapon_toggle_state():
                    self.player.shoot_weapon(self.frame_count)
                else: 
                    if self.reset:  
                        
                        self.player.shoot_weapon(self.frame_count)
                        self.reset = False
        else: 
            self.reset = True 

        """
        for event in pygame.event.get():
            self._handle_common_events(event)
            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_a: 
                    """
                    if self.player.flip: 
                        if self._timer >=0 and self._timer < 20:
                            if self._boost_ready:
                                self._boost_ready = False 
                                self.player.dash()
                            else: 
                                self._boost_ready = True 
                    else: 
                        self._boost_ready = True 
                    self._timer = 0
                    self._time_increment = True

                    """
                    
                    self.player_movement_input[0] = True

                if event.key == pygame.K_d: 
                    """
                    if not self.player.flip:
                        if self._timer >=0 and self._timer < 20:
                            if self._boost_ready: 
                                self._boost_ready = False 
                                self.player.dash()
                            else: 
                                self._boost_ready = True 
                    else: 
                        self.boost_ready = True 
                    self._timer = 0
                    self._time_increment = True 

                    """
                    self.player_movement_input[1] = True
                    
                if event.key == pygame.K_w:
                    
                    self.player.player_jump() 
                if event.key == pygame.K_s: 
                    self.player.crouch = True  
            
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_LSHIFT:
                    self.shift_pressed = False 
                    self.player.running = False 
                if event.key == pygame.K_w: 
                    self.player.jump_cut()
                if event.key == pygame.K_a: 
                    self.player_movement_input[0] = False
                if event.key == pygame.K_d:
                    self.player_movement_input[1] = False 
                if event.key == pygame.K_s: 
                    self.player.crouch =False 
                
            

        
    def _update_render(self):
        
        
        #parameters related to render update 
        # self.prev_cursor_pos = self.cursor.pos
        self._dt = time.time() - self._prev_frame_time
        self._prev_frame_time = time.time()

        
        #timer update for acceleration and dash timings  - have dash implemented, unsure 
        #if it should be kept 
            

        #render scroll update (camera scroll)
        self._scroll[0] += (self.player.rect().centerx - self._background_surf_dim[0] /2 - self._scroll[0])/20
        self._scroll[1] += (self.player.rect().centery - self._background_surf_dim[1] /2 - self._scroll[1])/20
        render_scroll = (int(self._scroll[0]), int(self._scroll[1]))

        self.render_engine.clear(0,0,0,255)

        #print(self.backgrounds['test_background'].bg_layers[0].width)
        
        self.render_engine.render_background_view(
            self.backgrounds['test_background'], render_scroll
        )

        self.render_engine.render_tilemap(
            self.Tilemap,render_scroll
        )

        self.render_engine.render(self._ambient_node_ptr.range,(0,0), (0,0))
        
        pygame.display.flip()
        fps = self._clock.get_fps()
        pygame.display.set_caption(f'Noel - FPS: {fps:.2f}')
        self._clock.tick(60)

    # public methods 
    def add_bullet(self,bullet):
        self._bullets_on_screen.append(bullet)
    
    def add_enemy(self,enemy):
        self._enemies.append(enemy)

    def add_particle(self,particle):
        self._particles.append(particle)

    def add_fire_particle(self,fire_particle):
        self._fire_particles.append(fire_particle)

    def add_non_anim_particle(self,non_anim_particle):
        self._non_animated_particles.append(non_anim_particle)

    def add_spark(self,spark):
        self._sparks.append(spark)

    def add_screen_shake(self,magnitude):
        self._screen_shake = max(magnitude,self._screen_shake)
        pass 

    def start_game(self):
        self._load_map_init_game_env('test.json')

        while(True):
            self._handle_events()
            self._update_render()
    
    

    def quit_game(self): 
        pygame.quit()
        quit()

    def run(self):
        pass

game = myGame()
game.start_game()
