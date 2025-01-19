t """
Noel: game made in pygame, a module for 2d game development in python.

pygame is definitely too slow to make a high-end, sophisticated game. Reasons?

Firstly, python itself is too slow compared to C++ or C#, which are the main languages 

used for game development. Interpreted languges in general have issues with performance which is a tradeoff for

their flexibility. It is definitely easier to code game mechanics in python, but performnace does lack a lot. 

another reason for why pygame is slow is because it does not support gpu processing. If you want to integrate gpu processing

for rendering, you need to use other libraraaaies from graphics API's like opengl. 


I've found a lighting module for pygame that uses shadow Casting, and integrated it into my game's system.

The lighting module also has its own method for rendering sprites, as it utilizes moderngl's functions which are separate from 

pygame. This has required me to restructure the game's rendering system completely during the midst of development, but it turned 

out to be a good investment of my time as the game's aesthetics has improved alot with the implementation of lights and shadows. 

It's not a complex lighting system, but it does its job well. 


the game itself started as an extension from a tutorial video I've watched on youtube made by a pygame specialist named 

"DafluffyPotato". it was a 6 hour tutorial that showed how to create the most basic framework for a platformer game 

that included a collision detection methpod, a rendering system, and an entities handling system. He had his own way of creating a game 

loop that can handle collision detection between entities, how to create camera movement, how to create an animation system, and so

on. He also had an editor script that was used to save and read information onto a json file. After following through his tutorial 

and understanding how it works together, I wanted to try and create a more sophisticated game with more core game mechanics, that was 

visually pleasing. 

The things that I've implemented or added onto his code is as follows: 

1. a resource management system (a gameassets class) to manage assets such as sprites or animations 

2. a weapons system 

3. an inventory system to hold weapons and items 

4. the lighting system (not implemented by me, more of an integration)

5. the new editor script with a tileset viewing panel, and extra options such as creating different sections with different ambient lighting

6. improved? collision detection system with the usage of a quadtree instead of brute-force collision detection with simple for-loops

7. numbers and characters are rendering with sprites to replace pygame's inconvienient conventional methods 

8. gameStateManager system to handle different game states.


I don't know what kind of game this is going to end up to be, I'm either thinking of making in a pvp shooter, 

or a wave-based survival game with different and stronger enemies that spawn each wave. 


"""


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
        pygame.mouse.set_visible(False)
        self.cursor = Cursor(self,(50,50),(4,4),'default')

        # player 
        self.player = PlayerEntity(self,(50,50),(14,16))
        self.player.set_accel_rate(0.7)
        self.player.set_default_speed(2.2)
        self.player_movement_input = [False,False] 
    
        # HUD
        self.inven_on = True
        self.HUD = HUD(self.player,self.general_sprites['health_UI'],self._foreground_surf_dim)
        
        # grass manager
        self.gm = GrassManager(self,'data/images/tiles/new_live_grass',tile_size=self.Tilemap.tile_size,stiffness=600,\
                               max_unique = 5,place_range=[1,1],burn_spread_speed= 3,burn_rate= 1.2)
       
        
        # other tracking variables
        self.frame_count = 0
        self.mouse_pressed = [False,False] 
        self.shift_pressed = False
        self.reset = True 
        
        """ initialize private members""" 
        
        # game object containers 
        self._collectable_items = []
        self._bullets_on_screen = []
        self._enemies = []
        self._enemy_bullets = []
 
        # particles and effects containers 
        self._particles = []
        self._fire_particles = []
        self._non_animated_particles = []
        self._sparks = []

        # dash variables
        self._boost_ready = False 
        self._timer = 0
        self._time_increment = False

        # other tracking variables 
        self._logo_time_speed_factor= 1
        
        self._scroll = [0,0]
        self._menu_scroll_up = False 
        self._menu_scroll_down = False 
      
        self._dt = 0
        self._prev_frame_time= time.time()
        self._rot_func_t = 0
     
        self._screen_shake = 0

        # quadtree settings 
        self._NODE_CAPACITY = 4
        self._qtree_x_slack = 300
        self._qtree_y_slack = 300

        # gamestate var, start screen ui, ambient light node pointer 
        self._curr_gameState = GameState.StartSequence
        self._start_screen_ui = startScreenUI(self._screen_size)
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
        self._screen_size = self._system_display_info['resolution']

        #TODO : you need to create a way to calculate native_res depending on selected resolution and scaling. 
        self._screen_to_native_ratio = 4.5 
        self._native_res = (int(self._screen_size[0]/self._screen_to_native_ratio),int(self._screen_size[1]/self._screen_to_native_ratio))

    def _setup_engine_and_render_surfs(self):
        self.lights_engine = LightingEngine(screen_res=self._screen_size,native_res=self._native_res,lightmap_res=self._native_res)

        self._background_surf_dim = self._foreground_surf_dim = self.buffer_surf_dim = (int(self._screen_size[0]/self._screen_to_native_ratio),int(self._screen_size[1]/self._screen_to_native_ratio))
        self.buffer_surf = pygame.Surface(self.buffer_surf_dim,pygame.SRCALPHA)
        self.background_surf = pygame.Surface(self._background_surf_dim,pygame.SRCALPHA)
        self.foreground_surf = pygame.Surface(self._foreground_surf_dim,pygame.SRCALPHA)

        # testing custom shaders 
        self.test_shader = self.lights_engine.load_shader_from_path('vertex.glsl','fog_fragment.glsl')

    def _load_game_assets(self):
        self.game_assets = GameAssets()
        self.general_sprites = self.game_assets.general_sprites
        self.interactable_obj_sprites = self.game_assets.interactable_obj_sprites
        self.enemy_sprites = self.game_assets.enemies

        self._window_icon = self.general_sprites['player']
        self._pygame_logo = self.general_sprites['start_logo']
        self._pygame_logo_center_offset = (-4/self._screen_to_native_ratio ,35/self._screen_to_native_ratio)
        self._pygame_logo_dim = self._pygame_logo.get_size()
        self._pygame_logo_ratio = self._pygame_logo_dim[0] /self._pygame_logo_dim[1]
        self._pygame_logo = pygame.transform.smoothscale(self._pygame_logo.convert_alpha(),(self._native_res[0]//2,  (self._native_res[0]//2) / self._pygame_logo_ratio))
        self._pygame_logo_dim = self._pygame_logo.get_size()
        pygame.display.set_icon(self._window_icon)

        self.weapons = {
            'laser_weapon': Wheelbot_weapon(self,Animation(load_images('entities/enemy/Wheel_bot/charge_weapon',background='transparent'),img_dur=5,loop=True),"A Laser weapon."),
            'ak' : AK_47(self,load_image('weapons/ak_holding.png',background='transparent'),load_image('weapons/ak_47_img.png',background='transparent'),load_image('weapons/shrunk/ak_47.png',background='transparent'),"The staple AK-47."),
            'flamethrower' : Flamethrower(self,load_image('weapons/flamethrower_holding.png',background='transparent'),load_image('weapons/flamethrower_img.png',background='transparent'),load_image('weapons/shrunk/flamethrower_img.png',background='transparent'),"Splits powerful flames."),
            'rocket_launcher' : Rocket_launcher(self,load_image('weapons/rocket_launcher_holding.png',background='transparent'),load_image('weapons/rocket_launcher_img.png',background='transparent'),load_image('weapons/shrunk/rocket_launcher.png',background='transparent')," "),
            'shotgun' : Shotgun(self,load_image('weapons/shotgun_holding.png',background='transparent'),load_image('weapons/shotgun_img.png',background='transparent'),load_image('weapons/shrunk/shotgun.png',background='transparent')," ")
        }

        
        self.bullets = {
            'rifle_small' : load_image('bullets/rifle/small.png',background='transparent'),
            'laser_weapon' : Animation(load_images('bullets/laser_weapon/new',background='transparent'),img_dur= 5, loop = True),
            'shotgun' : load_image('bullets/shotgun/small.png',background='transparent'),
            'rocket_launcher' : load_image('bullets/rocket_launcher/0.png',background='transparent'),
        }

        self.backgrounds = {
            'building' : Background(self,load_images('backgrounds/building',background= 'transparent')),
            'new_building' : Background(self,load_images('backgrounds/new_building',background='transparent'))
        }


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

        self._collectable_items = []
        self._bullets_on_screen = []
        self._enemy_bullets = []
        self._particles = []
        self._fire_particles = []
        self._non_animated_particles = []
        self._enemies = []
        self._sparks = []

        self.lights_engine.lights = self.Tilemap.load_map_return_lights(map_file_name)

        self.Tilemap.extract_game_objs()

        self._ambient_node_ptr = self.Tilemap.ambientNodes.set_ptr(self.player.pos[0])
        self.lights_engine.set_ambient(*self._ambient_node_ptr.colorValue)
       

    def _show_start_sequence(self):
        
        self._logo_time = 0

        while self._logo_time <600 :
            
            
            self._logo_time += 1*self._logo_time_speed_factor
            
            self._handle_events()
            
            self.lights_engine.clear(0,0,0,255)
            self.background_surf.fill((0,0,0))
            self.foreground_surf.fill((0,0,0))
        

            blackout_surf = pygame.Surface(self._screen_size)
            blackout_surf = blackout_surf.convert()
            blackout_surf.fill((0,0,0,0))


            if self._logo_time <= 300 :
    
                blackout_surf.set_alpha(smoothclamp(255-self._logo_time,0,255))
            else: 
                 blackout_surf.set_alpha(255-min(255,smoothclamp_decreasing(self._logo_time,0,600)))
            
            
            self.foreground_surf.blit(self._pygame_logo,(self._native_res[0]//4 + self._pygame_logo_center_offset[0], self._native_res[1]//2 - self._pygame_logo_dim[1]//2 - self._pygame_logo_center_offset[1]))
            self.foreground_surf.blit(blackout_surf,(0,0))
            self.cursor.update_render(self.foreground_surf)

            tex = self.lights_engine.surface_to_texture(self.foreground_surf)
            
            self.lights_engine.render_texture(
                tex, Layer_.FOREGROUND,
                pygame.Rect(0,0,tex.width ,tex.height),
                pygame.Rect(0,0,tex.width,tex.height)
            )
            tex.release()

            self.lights_engine.render(self._ambient_node_ptr.range,(0,0), (0,0))
            
            
            pygame.display.flip()
            fps = self._clock.get_fps()
            pygame.display.set_caption(f'Noel - FPS: {fps:.2f}')
            self._clock.tick(60)
        
        self._scroll[0] = (self.player.rect().centerx - self._background_surf_dim[0] /2)
        self._scroll[1] = (self.player.rect().centery - self._background_surf_dim[1] /2)
        """
        self.start_sequence_time = 255 
        scroll_increment_x = (self.player.rect().centerx - self.background_surf_dim[0] /2)
        scroll_increment_y =  (self.player.rect().centery - self.background_surf_dim[1] /2)

        start_scroll = self.scroll.copy() 

        while self.start_sequence_time > 0: 
            self.start_sequence_time -= 1
            self._handle_events()
            
            self.scroll[0] = start_scroll[0] +  scroll_increment_x * (smoothclamp_decreasing(self.start_sequence_time,0,255) / 255)
            self.scroll[1] = start_scroll[1] +  scroll_increment_y * (smoothclamp_decreasing(self.start_sequence_time,0,255) / 255)

            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))
        

            boundary = Rectangle(Vector2(render_scroll[0]- self.qtree_x_slack,render_scroll[1]- self.qtree_y_slack),\
                                 Vector2(self.background_surf_dim[0] +self.qtree_x_slack*2,self.background_surf_dim[1] +self.qtree_y_slack*2))
            quadtree = QuadTree(self.NODE_CAPACITY, boundary)

            self.lights_engine.clear(0,0,0,255)
            self.background_surf.fill((155,155,155))
            self.foreground_surf.fill((0,0,0,0))

            blackout_surf = pygame.Surface(self.screen_size)
            blackout_surf = blackout_surf.convert()
            blackout_surf.fill((0,0,0,0))
            blackout_surf.set_alpha(self.start_sequence_time)

            self.backgrounds['building'].render(self.background_surf,render_scroll)

            self.Tilemap.render(self.background_surf,render_scroll)
            self.lights_engine.hulls = self.Tilemap.update_shadow_objs(self.background_surf,render_scroll)


            self.player.update_pos(self.Tilemap,quadtree,self.cursor.pos,self.frame_count)
            self.player.render(self.background_surf,render_scroll)
            self.background_surf.blit(blackout_surf,(0,0))
            
            self.cursor.update_render(self.foreground_surf)
            


            tex = self.lights_engine.surface_to_texture(self.background_surf)

            self.lights_engine.render_texture_with_trans(
                tex, Layer_.BACKGROUND,
                position= (0,0)
            )
      
            tex.release()

            tex = self.lights_engine.surface_to_texture(self.foreground_surf)
        
            self.lights_engine.render_texture(
                tex, Layer_.FOREGROUND,
                pygame.Rect(0,0,tex.width ,tex.height),
                pygame.Rect(0,0,tex.width,tex.height)
            )
            tex.release()

            self.lights_engine.render(self.ambient_node_ptr.range,render_scroll, (0,0))


            pygame.display.flip()
            fps = self.clock.get_fps()
            pygame.display.set_caption(f'Noel - FPS: {fps:.2f}')
            self.clock.tick(60)

        """
        self._curr_gameState = GameState.MainMenu


    
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
        if self._curr_gameState == GameState.StartSequence:
            for event in pygame.event.get():
                self._handle_common_events(event)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self._logo_time_speed_factor = 7
                        self._logo_time = max(300,self._logo_time)
                        self.start_sequence_time = 0
                        break 
					
        elif self._curr_gameState == GameState.MainMenu:
            for event in pygame.event.get():
                self._handle_common_events(event)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self.start_sequence_time = 0
                    if event.key == pygame.K_p:
                        self._load_map_init_game_env('test.json')
                        self._scroll[0]= (self.player.rect().centerx - self._background_surf_dim[0] /2)
                        self._scroll[1]=  (self.player.rect().centery - self._background_surf_dim[1] /2) - 20 
                        self._curr_gameState = GameState.GameLoop
                        break
                    if event.key == pygame.K_w: 
                        self._menu_scroll_up = True 
                    if event.key == pygame.K_UP: 
                        self._menu_scroll_up = True
                    if event.key == pygame.K_s:
                        self._menu_scroll_down = True
                    if  event.key == pygame.K_DOWN: 
                        self._menu_scroll_down = True
                    if event.key == pygame.K_SPACE:
                        self.menu_select = True 
                    if event.key == pygame.K_KP_ENTER:
                        self.menu_select = True 
                
                if event.type == pygame.KEYUP: 
                    if event.key == pygame.K_w: 
                        self._menu_scroll_up = False
                    if event.key == pygame.K_UP: 
                        self._menu_scroll_up = False
                    if event.key == pygame.K_s:
                        self._menu_scroll_down = False
                    if  event.key == pygame.K_DOWN: 
                        self._menu_scroll_down = False
                    if event.key == pygame.K_SPACE:
                        self.menu_select = False
                    if event.key == pygame.K_KP_ENTER:
                        self.menu_select = False
                        
        elif self._curr_gameState == GameState.GameLoop:
            
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

            for event in pygame.event.get():
                self._handle_common_events(event)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_z:
                        print(self._screen_size)
                        print(self.gm.grass_tiles)
                    if event.key == pygame.K_m:
                        self.gm.burn_tile((74,11))

                    if event.key == pygame.K_o:
                        for _ in range(9):
                            glass_ = glass([80 * 16 +8, 3 *16 +2],2.5,10,math.radians(random.randint(50,130)),180)
                            self._sparks.append(glass_)
                        pass 
                    if event.key == pygame.K_n:
                        self.Tilemap.tilemap[f"80;3"] = Light("lights","0;0",(80,3),radius=356 ,power = 1\
                                                      )
                        
                        light = PointLight([80*16+8,3*16+2],power =1, radius = 356)
                        self.Tilemap.tilemap[f"80;3"].light_ptr = light 
                        self.lights_engine.lights.append(light)
                        for _ in range(20):
                            self.gm.place_tile((74+_,11),10,[0,1,2,3,4])
                        
                    if event.key == pygame.K_LSHIFT:
                        self.shift_pressed = True 
                        if self.inven_on: 
                            self.player.running = True 
            
                    if event.key == pygame.K_SPACE: 
                        self.player.interact()

                    if event.key == pygame.K_x:
                        new_shotgun =  self.weapons['shotgun'].copy()
                        new_shotgun.magazine = 100

                        self.HUD.Items_list[2][1].add_item(new_shotgun)

                    if event.key == pygame.K_b: 
                        new_rocket_launcher = self.weapons['rocket_launcher'].copy()
                        new_rocket_launcher.magazine = 100

                        self.HUD.Items_list[2][1].add_item(new_rocket_launcher) 

                    if event.key == pygame.K_v: 
                        new_flamethrower = self.weapons['flamethrower'].copy()
                        new_flamethrower.magazine = 1000 

                        self.HUD.Items_list[2][1].add_item(new_flamethrower)

                    if event.key == pygame.K_f:
                        new_ak = self.weapons['ak'].copy()
                        new_ak.magazine = 1000
                        self.HUD.Items_list[2][1].add_item(new_ak)


                    if event.key == pygame.K_c:
                        self.HUD.Items_list[0][1].add_item(  Item(random.choice(list(ITEMS.keys())), 1))
                    if event.key == pygame.K_e:
                        self.inven_on = not self.inven_on

                    if event.key == pygame.K_q: 

                        self.HUD.Items_list[2][1].remove_current_item() 

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
                    if event.key == pygame.K_g: 
                        self.player.toggle_rapid_fire()
				
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
        
        if self._curr_gameState == GameState.GameLoop:
            
            #parameters related to render update 
           # self.prev_cursor_pos = self.cursor.pos
            self._dt = time.time() - self._prev_frame_time
            self._prev_frame_time = time.time()
            self._screen_shake = max(0,self._screen_shake -1)
        
            #timer update for acceleration and dash timings  - have dash implemented, unsure 
            #if it should be kept 
                
            self._timer += self._time_increment

            if self._timer > 20:
                self.boost_ready = False 
                self._time_increment = False 
                self._timer = 0

            #frame counter update needed for weapon fire rate implementation 
            self.frame_count = (self.frame_count+1) % 360 

            #render scroll update (camera scroll)
            self._scroll[0] += (self.player.rect().centerx - self._background_surf_dim[0] /2 - self._scroll[0])/20
            self._scroll[1] += (self.player.rect().centery - self._background_surf_dim[1] /2 - self._scroll[1])/20
            render_scroll = (int(self._scroll[0]), int(self._scroll[1]))
            
            #----------------------------quadtree update - needed for collision detection between moving entities
            boundary = Rectangle(Vector2(render_scroll[0]- self._qtree_x_slack,render_scroll[1]- self._qtree_y_slack),\
                                 Vector2(self._background_surf_dim[0] +self._qtree_x_slack*2,self._background_surf_dim[1] +self._qtree_y_slack*2))
            quadtree = QuadTree(self._NODE_CAPACITY, boundary)

            x_lower = boundary.position.x
            x_higher = x_lower + boundary.scale.x
            y_lower = boundary.position.y
            y_higher = y_lower + boundary.scale.y
            #-------------------------------

            #clearing lighting engine texture and render surfaces 
            self.lights_engine.clear(0,0,0,255)
            self.background_surf.fill((0,0,0))
            self.foreground_surf.fill((0,0,0,0))
            self.buffer_surf.fill((0,0,0,0))


            #background and tilemap render
            self.backgrounds['building'].render(self.background_surf,render_scroll)
            self.Tilemap.render(self.background_surf,render_scroll)

            #ambient lighting update - ambient node (node that contains the ambient lighting info in the current domain)
            if self.player.pos[0] < self._ambient_node_ptr.range[0]:
                if self._ambient_node_ptr.prev: 
                    self._ambient_node_ptr = self._ambient_node_ptr.prev
                    if isinstance(self._ambient_node_ptr,interpolatedLightNode):
                        print("check")
                        self.lights_engine.set_ambient(self._ambient_node_ptr.get_interpolated_RGBA(self.player.pos[0]))
                    else:
                        self.lights_engine.set_ambient(*self._ambient_node_ptr.colorValue) 

            elif self.player.pos[0] > self._ambient_node_ptr.range[1]:
                if self._ambient_node_ptr.next: 
                    self._ambient_node_ptr = self._ambient_node_ptr.next
                    if isinstance(self._ambient_node_ptr,interpolatedLightNode):
                        print("check")
                        self.lights_engine.set_ambient(self._ambient_node_ptr.get_interpolated_RGBA(self.player.pos[0]))
                    else:
                        self.lights_engine.set_ambient(*self._ambient_node_ptr.colorValue) 
            else: 
                if isinstance(self._ambient_node_ptr,interpolatedLightNode):
                    self.lights_engine.set_ambient(self._ambient_node_ptr.get_interpolated_RGBA(self.player.pos[0]))



            
            #shadow casting hulls update
            self.lights_engine.hulls = self.Tilemap.update_shadow_objs(self.background_surf,render_scroll)
            

            for i in range(len(self._enemies) - 1, -1, -1):
                enemy = self._enemies[i]
                
                if (enemy.pos[0] >= x_lower and enemy.pos[0] <= x_higher) and (enemy.pos[1] >= y_lower and enemy.pos[1] <= y_higher):
                    kill = enemy.update(self.Tilemap, self.player.pos, self._dt, (0, 0))
                    quadtree.insert(enemy)

                    # TODO: Handle enemy collision and push-back logic here.

                    enemy.render(self.background_surf, offset=render_scroll)
                    if kill:
                        del self._enemies[i]  # Removes the enemy without needing a list copy.
     


            for i in range(len(self._collectable_items) - 1, -1, -1):
                collectable_item = self._collectable_items[i]

                if (collectable_item.life <= 0 or 
                    (collectable_item.pos[0] + collectable_item.size[0] <= x_lower or collectable_item.pos[0] >= x_higher) or 
                    (collectable_item.pos[1] + collectable_item.size[1] <= y_lower or collectable_item.pos[1] >= y_higher)):
                    
                    del self._collectable_items[i]
                    continue

                collectable_item.update_pos(self.Tilemap)
                quadtree.insert(collectable_item)
                collectable_item.render(self.background_surf, offset=render_scroll)

            
                
            for i in range(len(self._bullets_on_screen) - 1, -1, -1):
                bullet = self._bullets_on_screen[i]

                kill = bullet.update_pos(self.Tilemap)
                if kill:
                    del self._bullets_on_screen[i]
                    continue    

                if (bullet.pos[0] >= x_lower and bullet.pos[0] <= x_higher) and (bullet.pos[1] >= y_lower and bullet.pos[1] <= y_higher):
                    bullet.render(self.background_surf, offset=render_scroll)

                xx, yy = bullet.pos[0], bullet.pos[1]
                r = max(bullet.size) * 3  # Adjust range radius for rectangular particles
                rangeRect = Rectangle(Vector2(xx - r / 2, yy - r / 2), Vector2(r, r))

                nearby_entities = quadtree.queryRange(rangeRect, "enemy")
                for entity in nearby_entities:
                    if entity.state != 'death' and bullet.collide(entity):
                        bullet.dead = True
                        entity.hit(bullet.damage)
                        
                        # Set up for collision particle effect
                        og_end_point_vec = pygame.math.Vector2((6, 0)).rotate(bullet.angle)
                        center_pos = [bullet.pos[0] + bullet.sprite.get_width() / 2, bullet.pos[1] + bullet.sprite.get_height() / 2]
                        end_point = [
                            center_pos[0] + og_end_point_vec[0] - (bullet.sprite.get_width() / 2 if bullet.velocity[0] >= 0 else 0),
                            center_pos[1] + og_end_point_vec[1]
                        ]

                        collide_particle = Particle(self, 'bullet_collide/rifle', end_point, 'player')
                        rotated_collide_particle_images = [pygame.transform.rotate(image, 180 + bullet.angle) for image in collide_particle.animation.images]
                        collide_particle.animation.images = rotated_collide_particle_images
                        self._particles.append(collide_particle)
                        
                        # Ensure bullet is removed if still in list
                        if i < len(self._bullets_on_screen) and self._bullets_on_screen[i] == bullet:
                            del self._bullets_on_screen[i]

            """
            for bullet in self.bullets_on_screen.copy():
                                            
                        kill = bullet.update_pos(self.Tilemap)
                        if kill: 
                            
                            self.bullets_on_screen.remove(bullet)
                            continue    

                        if (bullet.pos[0] >= x_lower and bullet.pos[0] <= x_higher) and (bullet.pos[1] >= y_lower and bullet.pos[1] <= y_higher) :
                            bullet.render(self.background_surf,offset = render_scroll)

                        xx, yy = bullet.pos[0],bullet.pos[1]
                        r = max(bullet.size) * 3  # Adjust range radius for rectangular particles

                        rangeRect = Rectangle(Vector2(xx - r / 2, yy - r / 2), Vector2(r, r))
                        
                        nearby_entities = quadtree.queryRange(rangeRect,"enemy")
                        for entity in nearby_entities:
                            
                                if  entity.state != 'death' and bullet.collide(entity) :
                                    bullet.dead = True
                                    entity.hit(bullet.damage)
                                    og_end_point_vec = pygame.math.Vector2((6,0))
                                    og_end_point_vec.rotate(bullet.angle)

                                    center_pos = [bullet.pos[0]+bullet.sprite.get_width()/2, bullet.pos[1] + bullet.sprite.get_height()/2]
                                    end_point = [center_pos[0]+og_end_point_vec[0]- (bullet.sprite.get_width()/2 if bullet.velocity[0] >=0 else 0),center_pos[1] + og_end_point_vec[1]] 
                                    collide_particle = Particle(self,'bullet_collide/rifle',end_point,'player'/
                                    rotated_collide_particle_images = [pygame.transform.rotate(image,180+bullet.angle) for image in collide_particle.animation.copy().images]
                                    collide_particle.animation.images = rotated_collide_particle_images

                                    self.particles.append(collide_particle)
                                    if bullet in self.bullets_on_screen:
                                        self.bullets_on_screen.remove(bullet)
            """
                                    
            
            # Process enemy bullets
            for i in range(len(self._enemy_bullets) - 1, -1, -1):
                bullet = self._enemy_bullets[i]
                kill = bullet.update_pos(self.Tilemap)
                bullet.render(self.background_surf, offset=render_scroll)
                if kill:
                    del self._enemy_bullets[i]

            # Process particles
            for i in range(len(self._particles) - 1, -1, -1):
                particle = self._particles[i]
                if particle is None:
                    del self._particles[i]
                    continue

                kill = particle.update()
                particle.render(self.background_surf, offset=render_scroll)
                if particle.type == 'leaf':
                    particle.pos[0] += math.sin(particle.animation.frame * 0.035) * 0.3
                if particle.source == 'player' and particle.type.startswith('smoke'):
                    if self.player.cur_weapon_node:
                        particle.pos = self.player.cur_weapon_node.weapon.opening_pos
                if kill:
                    del self._particles[i]

            self.player.accelerate(self.player_movement_input)
            self.player.update_pos(self.Tilemap,quadtree,self.cursor.pos,self.frame_count)
            self.player.render(self.background_surf,render_scroll)

            #------------------------grass update and rendering
            

            # Define the rotation function with a bit of randomness for a more natural sway

            rot_function = lambda x, y: int(math.sin(self._rot_func_t/60 + x/100)*7)
            
            if not self.player.crouch: 
                self.gm.apply_force((self.player.pos[0]+ self.player.size[0]//2, self.player.pos[1]+ self.player.size[1]//2),self.Tilemap.tile_size//4,self.Tilemap.tile_size*3.4//7)
            self.gm.update_render(quadtree,self.background_surf,self._dt,offset=render_scroll,rot_function= rot_function)
            self._rot_func_t += self._dt * 100
            #----------------------------------


            particles_to_remove = []

            for i, particle in enumerate(self._fire_particles):
                kill = particle.update_pos(self.Tilemap, self.frame_count)
                
                if kill:
                    particles_to_remove.append(particle)  # Mark particle for removal
                    continue

                particle.render(self.buffer_surf, offset=render_scroll)

                if i % 4 == 0:
                    xx, yy = particle.pos[0], particle.pos[1]
                    r = particle.r * 3
                    
                    rangeCircle = Circle(Vector2(xx, yy), r)
                    
                    # Query for nearby entities
                    nearby_entities = quadtree.queryRange(rangeCircle, "enemy")
                  
                    for entity in nearby_entities:
                        if entity.state != 'death' and particle.collide(entity):
                            entity.hit(particle.damage)

            # Remove particles outside the loop to avoid modifying the list during iteration
            for particle in particles_to_remove:
                self._fire_particles.remove(particle)

            # Process sparks
            for i in range(len(self._sparks) - 1, -1, -1):
                spark = self._sparks[i]
                kill = spark.update(self.Tilemap, self._dt * 30)
                if kill:
                    del self._sparks[i]
                    continue

                spark.render(self.background_surf, render_scroll)

            # Blit buffer surface to background surface
            self.background_surf.blit(self.buffer_surf, (0, 0))
            
            # Process non-animated particles
            for i in range(len(self._non_animated_particles) - 1, -1, -1):
                particle = self._non_animated_particles[i]
                if particle is None:
                    del self._non_animated_particles[i]
                    continue

                kill = particle.update(self._dt)
                particle.render(self.background_surf, offset=render_scroll)
                if kill:
                    del self._non_animated_particles[i]

           

            #HUD rendering 
            self.HUD.render(self.foreground_surf,self.cursor,offset=(0,0),closing = self.inven_on)
            
            #cursor update and render 
            self.cursor.update_render(self.foreground_surf)
            screenshake_offset = (random.random()* self._screen_shake - self._screen_shake /2, random.random()* self._screen_shake - self._screen_shake /2)

            #using lighting engine to turn pg surf into moderngl texture, then render.
            tex = self.lights_engine.surface_to_texture(self.background_surf)
      
            self.lights_engine.render_texture_with_trans(
                tex, Layer_.BACKGROUND,
                position= (-screenshake_offset[0],-screenshake_offset[1]),
            )
           
            tex.release()

            tex = self.lights_engine.surface_to_texture(self.foreground_surf)
            self.lights_engine.render_texture(
                tex, Layer_.FOREGROUND,
                pygame.Rect(0,0,tex.width ,tex.height),
                pygame.Rect(0,0,tex.width,tex.height)
            )
            tex.release()

            self.lights_engine.render(self._ambient_node_ptr.range,render_scroll, screenshake_offset)

            pygame.display.flip()
            fps = self._clock.get_fps()
            pygame.display.set_caption(f'Noel - FPS: {fps:.2f}')
            self._clock.tick(60)

        if self._curr_gameState == GameState.MainMenu:

            #render scroll update
            self._scroll[0] += (self.player.rect().centerx - self._background_surf_dim[0] /2 - self._scroll[0])/20
            self._scroll[1] += (self.player.rect().centery - self._background_surf_dim[1] /2 - self._scroll[1])/20
            render_scroll = (int(self._scroll[0]), int(self._scroll[1]))
            
            #------------------------ quadtree update 
            boundary = Rectangle(Vector2(render_scroll[0]- self._qtree_x_slack,render_scroll[1]- self._qtree_y_slack),\
                                 Vector2(self._background_surf_dim[0] +self._qtree_x_slack*2,self._background_surf_dim[1] +self._qtree_y_slack*2))
            quadtree = QuadTree(self._NODE_CAPACITY, boundary)
            #------------------------------------------

            #lighting engine texture and surface clearance 
            self.lights_engine.clear(0,0,0,255)
            self.background_surf.fill((155,155,155))
            self.foreground_surf.fill((0,0,0,0))
            self.buffer_surf.fill((0,0,0,0))

            #rendering background and tilemap 
            self.backgrounds['building'].render(self.background_surf,render_scroll)
            self.Tilemap.render(self.background_surf,render_scroll)

            #rendering main menu ui - buttons (options,start game, etc)
            self._start_screen_ui.update(self.cursor)
            self._start_screen_ui.render(self.foreground_surf,(0,0))

            #update shadow casting hulls 
            self.lights_engine.hulls = self.Tilemap.update_shadow_objs(self.background_surf,render_scroll)
            
            #update player's movement - doesn't move in this state but still needs to be called to 
            #render idle animation 
            self.player.update_pos(self.Tilemap,quadtree,self.cursor.pos,self.frame_count)
            self.player.render(self.background_surf,render_scroll)

            #cursor update and render 
            self.cursor.update_render(self.foreground_surf)

            #using lighting engine to render final 
            tex = self.lights_engine.surface_to_texture(self.background_surf)

            self.lights_engine.render_texture_with_trans(
                tex, Layer_.BACKGROUND,
                position= (0,0) 
            
            )

            tex.release()

            tex = self.lights_engine.surface_to_texture(self.foreground_surf)
            self.lights_engine.render_texture(
                tex, Layer_.FOREGROUND,
                pygame.Rect(0,0,tex.width ,tex.height),
                pygame.Rect(0,0,tex.width,tex.height)
            )
            tex.release()
            
            self.lights_engine.render(self._ambient_node_ptr.range,render_scroll, (0,0))
            
            pygame.display.flip()
            fps = self._clock.get_fps()
            pygame.display.set_caption(f'Noel - FPS: {fps:.2f}')
            self._clock.tick(60)
            pass
    


    # public methods 
    def add_bullet(self,bullet):
        self._bullets_on_screen.append(bullet)
    
    def add_collectable_item(self,item):
        self._collectable_items.append(item)

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
        self._load_map_init_game_env('start_screen.json')
        #print(self.screen_info_obj.current_h,self.screen_info_obj.current_w)

        self._show_start_sequence()
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
