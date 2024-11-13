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

        # grass manager 
        self.gm = GrassManager(self.render_engine,self,'data/images/tiles/new_live_grass',tile_size=self.Tilemap.tile_size,stiffness=600,\
                               max_unique=5,place_range=[1,1],burn_spread_speed=3,burn_rate=1.2)

        # player 
        self.player = PlayerEntity(self,(74,10),(14,16))
        self.player.set_accel_rate(0.7)
        self.player.set_default_speed(2.2)
        self.player_movement_input = [False,False] 
   
  
        # other tracking variables
        self.frame_count = 0
        self.mouse_pressed = [False,False] 
        self.shift_pressed = False
        self.reset = True 
        
        """ initialize private  members""" 
        
        # game object containers 
        self._rot_func_t = 0
        self._enemies = []
        self._bullets_on_screen  = []
        self._enemy_bullets = []
        self._collectable_items = []

        # particles and effects containers 

        
        self._scroll = [0,0]
      
        self._dt = 0
        self._prev_frame_time= time.time()
        self._qtree_x_slack = 50
        self._qtree_y_slack = 50
        self._NODE_CAPACITY =4
        
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
        #self._screen_size = (700,550)

        #TODO : you need to create a way to calculate native_res depending on selected resolution and scaling. 
        self._screen_to_native_ratio = 4.5 
        self._native_res = (int(self._screen_size[0]/self._screen_to_native_ratio),int(self._screen_size[1]/self._screen_to_native_ratio))

    def _setup_engine_and_render_surfs(self):
        self.render_engine = LightingEngine(self,screen_res=self._screen_size,screen_to_native_ratio = self._screen_to_native_ratio,native_res=self._native_res,lightmap_res=self._native_res)

        self._background_surf_dim = self._foreground_surf_dim = self.buffer_surf_dim =  self._native_res 
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
                
                if event.key == pygame.K_n:
                   for _ in range(10):
                    self.gm.place_tile((74+_,11),10,[0,1,2,3,4])
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

        #----------------------------quadtree update - needed for collision detection between moving entities
        boundary = Rectangle(Vector2(render_scroll[0]- self._qtree_x_slack,render_scroll[1]- self._qtree_y_slack),\
                                Vector2(self._native_res[0] +self._qtree_x_slack*2,self._native_res[1] +self._qtree_y_slack*2))
        quadtree = QuadTree(self._NODE_CAPACITY, boundary)

        x_lower = boundary.position.x
        x_higher = x_lower + boundary.scale.x
        y_lower = boundary.position.y
        y_higher = y_lower + boundary.scale.y
        #-------------------------------

        self.render_engine.clear(0,0,0,255)

        #print(self.backgrounds['test_background'].bg_layers[0].width)
        
        self.render_engine.render_background_view(
            self.backgrounds['new_building'], render_scroll
        )

        self.render_engine.render_tilemap(
            self.Tilemap,render_scroll
        )

        
        # TODO: render enemies to background layer with draw shader, but also 
        # passing normal map data to achieve dynamic lights with lightmap data

        for i in range(len(self._enemies) - 1, -1, -1):
                enemy = self._enemies[i]
                
                if (enemy.pos[0] >= x_lower and enemy.pos[0] <= x_higher) and (enemy.pos[1] >= y_lower and enemy.pos[1] <= y_higher):
                    kill = enemy.update(self.Tilemap, self.player.pos, self._dt, (0, 0))
                    quadtree.insert(enemy)

                    # TODO: Handle enemy collision and push-back logic here.

                    enemy.render(self.render_engine, offset=render_scroll)
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
                collectable_item.render(self.render_engine, offset=render_scroll)
        

        for i in range(len(self._bullets_on_screen) - 1, -1, -1):
                        bullet = self._bullets_on_screen[i]

                        kill = bullet.update_pos(self.Tilemap)
                        if kill:
                            del self._bullets_on_screen[i]
                            continue    

                        if (bullet.pos[0] >= x_lower and bullet.pos[0] <= x_higher) and (bullet.pos[1] >= y_lower and bullet.pos[1] <= y_higher):
                            bullet.render(self.render_engine, offset=render_scroll)

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

        #TODO: implement rendering for particles 
        #
        #
        self.player.accelerate(self.player_movement_input)
        self.player.update_pos(self.Tilemap,quadtree,[50,50],self.frame_count)
        self.player.render(self.render_engine,render_scroll)

        rot_function = lambda x, y: int(math.sin(self._rot_func_t/60 + x/100)*7)
        self._rot_func_t += self._dt * 100
        self.gm.update_render(quadtree,self._native_res,self._dt,render_scroll,rot_function=rot_function)



        self.render_engine.render(self._ambient_node_ptr.range,render_scroll, (0,0))
        
        pygame.display.flip()
        fps = self._clock.get_fps()
        print(fps)
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
