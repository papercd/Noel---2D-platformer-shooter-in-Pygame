"""
Noel: game made in pygame, a module for 2d game development in python.

pygame is definitely too slow to make a high-end, sophisticated game. Reasons?

Firstly, python itself is too slow compared to C++ or C#, which are the main languages 

used for game development. Interpreted languges in general have issues with performance which is a tradeoff for

their flexibility. It is definitely easier to code game mechanics in python, but performnace does lack a lot. 

another reason for why pygame is slow is because it does not support gpu processing. If you want to integrate gpu processing

for rendering, you need to use other libraraaaies from graphics API's like opengl. 


I've found a lighting module for pygame that uses rayCasting, and integrated it into my game's system.

The lighting module also has its own method for rendering sprites, as it utilizes moderngl's functions which are separate from 

pygame. This has required me to restructure the game's rendering system completely during the midst of development, but it turned 

out to be a good investment of my time as the game's aesthetics has improved alot with the implementation of lights and shadows. 

It's not a complex lighting system, but it does its job well. 


the game itself started as an extension from a tutorial video I've watched on youtube made by a pygame specialist named 

"DafluffyPotato". it was a 6 hour tutorial that showed how to create the most basic framework for a platformer game 

that included a collision detection method, a rendering system, and an entities handling system. He had his own way of creating a game 

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



import numpy as np 
import pygame
import random
import math
import time
import sys 


from scripts import * 
from assets import GameAssets

#import pygame_light2d as pl2d 
#from pygame_light2d import LightingEngine, PointLight, Hull

#----------------------------------------- imports to integrate shaders 


from my_pygame_light2d.engine import LightingEngine, Layer_
from my_pygame_light2d.light import PointLight
from my_pygame_light2d.hull import Hull
from enum import Enum


class GameState(Enum):
    StartSequence = 0
    MainMenu = 1
    MainMenuSettings = 2
    GameLoop = 3
    PauseMenu = 4
    PauseMenuSettings =5 


class myGame:
    def __init__(self):
        pygame.init() 
        pygame.mixer.pre_init(44100, -16, 2, 512)

        
        self.clock = pygame.time.Clock()
        self.screen_size = (1440,900)
        self.native_res = (int(self.screen_size[0]/2.5),int(self.screen_size[1]/2.5))
       
        self.lights_engine = LightingEngine(screen_res=self.screen_size,native_res=self.native_res,lightmap_res=self.native_res)
        
        
        self.buffer_surf = pygame.Surface((int(self.screen_size[0]/2.5),int(self.screen_size[1]/2.5)),pygame.SRCALPHA)
        self.background_surf = pygame.Surface((int(self.screen_size[0]//2.5),int(self.screen_size[1]/2.5)),pygame.SRCALPHA)
        self.foreground_surf = pygame.Surface((int(self.screen_size[0]//2.5),int(self.screen_size[1]//2.5)),pygame.SRCALPHA)

        """
        self.test_shader = self.lights_engine.load_shader_from_path('vertex.glsl','fog_fragment.glsl')
        self.pixel_exp_shader = self.lights_engine.load_shader_from_path('vertex.glsl','exp_fragment.glsl')
        self.sparks_shader = self.lights_engine.load_shader_from_path('vertex.glsl','sparks.glsl')
        self.dithering_shader = self.lights_engine.load_shader_from_path('vertex.glsl','dithering.glsl')

        """
        
        self.game_assets = GameAssets()
        self.general_sprites = self.game_assets.general_sprites
        self.interactable_obj_sprites = self.game_assets.interactable_obj_sprites
        self.enemies = self.game_assets.enemies
        
        #game objects using assets 

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

        #tile map 
        self.Tilemap = Tilemap(self,tile_size=16,offgrid_layers=2)
        
        #cursor object 
        pygame.mouse.set_visible(False)
        self.cursor = Cursor(self,(50,50),(4,4),'default')

        #player 
        self.PLAYER_DEFAULT_SPEED = 2.2
        self.player_cur_vel = 0
        self.accel_decel_rate = 0.7
        self.accelerated_movement = 0

        self.player = PlayerEntity(self,(50,50),(14,16))
        self.player_movement = [False,False]

        #HUD
        self.inven_on = True
        self.HUD = HUD(self.player,self.general_sprites['health_UI'],self.foreground_surf.get_size())
        
        #grass manager
        self.gm = GrassManager('data/images/tiles/live_grass',tile_size=self.Tilemap.tile_size,stiffness=600,max_unique = 5,place_range=[1,1])

        #game object containers 
        self.collectable_items = []
        self.bullets_on_screen = []
        self.existing_enemies = []
        self.enemy_bullets = []
        
        #particles and effects containers 
        self.particles = []
        self.physical_particles = []
        self.non_animated_particles = []
        self.leaf_spawners = []
        self.sparks = []
        self.grass_locations = []

        #light objs containers  
        self.lights = {}
        self.temp_lights = []
        self.shadow_objects = [] 


        #dash variables
        self.boost_ready = False 
        self.timer = 0
        self.time_increment = False

        #other tracking variables
        self.frame_count = 0
        self.mouse_pressed = [False,False] 
        self.shift_pressed = False
        self.reset = True 
        
        self.scroll = [0,0]
        self.menu_scroll_up = False 
        self.menu_scroll_down = False 
      
        self.dt = 0
        self.start = time.time()
        self.running_time = time.time()
        self.rot_func_t = 0
        self.main_offset = None 
     
        self.screen_shake = 0

        #quadtree settings 
        self.NODE_CAPACITY = 4
        self.qtree_x_slack = 300
        self.qtree_y_slack = 300


        self.curr_gameState = GameState.MainMenu
        self.start_screen_ui = startScreenUI(self.screen_size)
        self.ambient_node_ptr = self.Tilemap.ambientNodes.set_ptr(self.player.pos[0])


    
    def load_map_init_game_env(self,map_file_name):

        self.collectable_items = []
        self.bullets_on_screen = []
        self.enemy_bullets = []
        self.particles = []
        self.physical_particles = []
        self.non_animated_particles = []
        self.leaf_spawners = []
        self.existing_enemies = []
        self.sparks = []
        self.grass_locations = []

        self.lights_engine.lights = self.Tilemap.load(map_file_name)
        
        #locate grass tiles from map and extract them into the grass obj
        #container

        for grass in self.Tilemap.extract([('live_grass','0;0'),('live_grass','1;0'),('live_grass','2;0'),('live_grass','3;0'),('live_grass','4;0'),('live_grass','5;0')]):
            self.grass_locations.append((grass.pos[0], grass.pos[1]))
        
        for loc in self.grass_locations:
            self.gm.place_tile(loc,14,[0,3,4])

        #extract enemies from tilemap and add them into the enemy container 

        for spawner in self.Tilemap.extract([('spawners','0;0'),('spawners','1;0'),('spawners','2;0'),('spawners','3;0'),('spawners','4;0')]):   
            if spawner.variant == '0;0':
                
                self.player.pos = [spawner.pos[0] * self.Tilemap.tile_size, spawner.pos[1] * self.Tilemap.tile_size]
                
            elif spawner.variant == '1;0': 
                self.existing_enemies.append(Canine(self,(spawner.pos[0] * self.Tilemap.tile_size,spawner.pos[1] * self.Tilemap.tile_size),(34,23),'black'))
                
        
            elif spawner.variant == '2;0':
                
                self.existing_enemies.append(Wheel_bot(self,(spawner.pos[0] * self.Tilemap.tile_size,spawner.pos[1] * self.Tilemap.tile_size),(20,22)))

            elif spawner.variant == "4;0":
                self.existing_enemies.append(Ball_slinger(self,(spawner.pos[0] *self.Tilemap.tile_size,spawner.pos[1] *self.Tilemap.tile_size), (13,19)))

        self.ambient_node_ptr = self.Tilemap.ambientNodes.set_ptr(self.player.pos[0])
        self.lights_engine.set_ambient(*self.ambient_node_ptr.colorValue)
       

    def start_game(self):
        self.show_start_sequence()
        while(True):
            self.handle_events()
            self.update_render()
    

    def smoothclamp(self,x, mi, mx): 
        return mi + (mx-mi)*(lambda t: np.where(t < 0 , 0, np.where( t <= 1 , 3*t**2-2*t**3, 1 ) ) )( (x-mi)/(mx-mi) )

    def smoothclamp_decreasing(self, x, mi, mx):
        def smoothstep(t):
            return np.where(t < 0, 1, np.where(t <= 1, 1 - (3*t**2 - 2*t**3), 0))
        
        t = (x - mi) / (mx - mi)
        
        return mi + (mx - mi) * smoothstep(t)


    def show_start_sequence(self):
        self.logo_time = 0
        logo = self.general_sprites['start_logo']
        logo_dim = logo.get_size()
        logo_dim_ratio = logo_dim[0] / logo_dim[1]
        
        scaled_logo = pygame.transform.smoothscale(logo.convert_alpha(),(self.native_res[0]//2,  (self.native_res[0]//2) / logo_dim_ratio))
        print(self.native_res)


        while self.logo_time <600 :
            
            
            self.logo_time += 1
            
            self.handle_events()

            self.lights_engine.clear(0,0,0,255)
            self.background_surf.fill((0,0,0))
            self.foreground_surf.fill((0,0,0))
        
            #(self.screen_size[0] // 2 - logo_dim[0]//2, self.screen_size[1] // 2 - logo_dim[1]//2)

            blackout_surf = pygame.Surface(self.screen_size)
            blackout_surf = blackout_surf.convert()
            blackout_surf.fill((0,0,0,0))


            if self.logo_time <= 300 :
                
                blackout_surf.set_alpha(self.smoothclamp(255-self.logo_time,0,255))
            else: 
               
                blackout_surf.set_alpha(255-min(255,self.smoothclamp_decreasing(self.logo_time,0,600)))
            
            
            
            #self.foreground_surf.blit(logo,(0,0))
            self.foreground_surf.blit(scaled_logo,(self.native_res[0]//4, self.native_res[1]//2 - scaled_logo.get_height()//2))
            
            self.foreground_surf.blit(blackout_surf,(0,0))
            self.cursor.update(self.foreground_surf)

            tex = self.lights_engine.surface_to_texture(self.foreground_surf)

            tex = self.lights_engine.surface_to_texture(self.foreground_surf)
            
            self.lights_engine.render_texture(
                tex, Layer_.FOREGROUND,
                pygame.Rect(0,0,tex.width ,tex.height),
                pygame.Rect(0,0,tex.width,tex.height)
            )
            tex.release()


            tex.release()
            self.lights_engine.render(self.ambient_node_ptr.range,(0,0), (0,0))
            
            
            pygame.display.flip()
            #pygame.display.update()
            fps = self.clock.get_fps()
            pygame.display.set_caption(f'Noel - FPS: {fps:.2f}')
            self.clock.tick(60)

        
        self.start_sequence_time = 255 

        self.load_map_init_game_env('start_screen.json')
        scroll_increment_x = (self.player.rect().centerx - self.background_surf.get_width() /2)
        scroll_increment_y =  (self.player.rect().centery - self.background_surf.get_height() /2)
        while self.start_sequence_time > 0: 
            self.start_sequence_time -= 1
            self.handle_events()

            self.scroll[0] += scroll_increment_x /255
            self.scroll[1] += scroll_increment_y /255
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))
        

            boundary = Rectangle(Vector2(render_scroll[0]- self.qtree_x_slack,render_scroll[1]- self.qtree_y_slack),Vector2(self.background_surf.get_width() +self.qtree_x_slack*2,self.background_surf.get_height() +self.qtree_y_slack*2))
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


            self.player.update_pos(self.Tilemap,quadtree,self.cursor.pos,self.frame_count,(self.player_cur_vel,0))
            self.player.render(self.background_surf,render_scroll)
            self.background_surf.blit(blackout_surf,render_scroll)
            
            self.cursor.update(self.foreground_surf)
            


            tex = self.lights_engine.surface_to_texture(self.background_surf)

            self.lights_engine.render_texture_with_trans(
                tex, Layer_.BACKGROUND,
                position= (0,0)
            )
            """
            self.lights_engine.render_texture(
                tex, Layer_.BACKGROUND,
                pygame.Rect(-screenshake_offset[0] ,-screenshake_offset[1],tex.width ,tex.height),
                pygame.Rect(0,0,tex.width,tex.height)
            )"""
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
            #pygame.display.update()
            fps = self.clock.get_fps()
            pygame.display.set_caption(f'Noel - FPS: {fps:.2f}')
            self.clock.tick(60)

        self.curr_gameState = GameState.MainMenu

         

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_game() 
            
            elif event.type == pygame.MOUSEWHEEL:
                if self.curr_gameState == GameState.GameLoop:
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

            elif event.type == pygame.KEYDOWN:
                if self.curr_gameState == GameState.GameLoop:
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
                        """
                        i = 0
                        while i <1000:
                            test_shell_image = self.bullets['rifle_small'].copy()
                            test_shell = Bullet(self,[0,0],test_shell_image.get_size(),test_shell_image,'rifle_small')
                            new_ak.load(test_shell)
                            i+=1 
                        """
                        new_ak.magazine = 1000
                        self.HUD.Items_list[2][1].add_item(new_ak)


                    if event.key == pygame.K_c:
                        #self.HUD.Items_list[0][1].add_item(Item("glass",1))
                        self.HUD.Items_list[0][1].add_item(  Item(random.choice(list(ITEMS.keys())), 1))
                    if event.key == pygame.K_e:
                        self.inven_on = not self.inven_on

                    if event.key == pygame.K_q: 
                        self.HUD.Items_list[2][1].remove_current_item() 

                    if event.key == pygame.K_a: 
                        """
                        if self.player.flip: 
                            if self.timer >=0 and self.timer < 20:
                                if self.boost_ready:
                                    self.boost_ready = False 
                                    self.player.dash()
                                else: 
                                    self.boost_ready = True 
                        else: 
                            self.boost_ready = True 
                        self.timer = 0
                        self.time_increment = True

                        """
                        self.player_movement[0] = True

                    if event.key == pygame.K_d: 
                        """
                        if not self.player.flip:
                            if self.timer >=0 and self.timer < 20:
                                if self.boost_ready: 
                                    self.boost_ready = False 
                                    self.player.dash()
                                else: 
                                    self.boost_ready = True 
                        else: 
                            self.boost_ready = True 
                        self.timer = 0
                        self.time_increment = True 

                        """
                        self.player_movement[1] = True
                        
                    if event.key == pygame.K_w:
                        
                        self.player.player_jump() 
                    if event.key == pygame.K_s: 
                        self.player.crouch = True  
                    if event.key == pygame.K_g: 
                        self.player.toggle_rapid_fire()
                
                elif self.curr_gameState == GameState.MainMenu:

                    if event.key == pygame.K_RETURN:
                        self.start_sequence_time = 0
                    if event.key == pygame.K_p:

                        self.load_map_init_game_env('start_screen.json')

                        self.curr_gameState = GameState.GameLoop

                    if event.key == pygame.K_w: 
                        self.menu_scroll_up = True 
                    if event.key == pygame.K_UP: 
                        self.menu_scroll_up = True
                    if event.key == pygame.K_s:
                        self.menu_scroll_down = True
                    if  event.key == pygame.K_DOWN: 
                        self.menu_scroll_down = True

                    if event.key == pygame.K_SPACE:
                        self.menu_select = True 
                    if event.key == pygame.K_KP_ENTER:
                        self.menu_select = True 

                elif self.curr_gameState == GameState.StartSequence: 
                    if event.key ==pygame.K_RETURN:
                        self.start_sequence_time = 0
                    
                

            elif event.type == pygame.KEYUP: 
                if self.curr_gameState == GameState.GameLoop:
                    if event.key == pygame.K_LSHIFT:
                        self.shift_pressed = False 
                        self.player.running = False 
                    if event.key == pygame.K_w: 
                        self.player.jump_cut()
                    if event.key == pygame.K_a: 
                        self.player_movement[0] = False
                    if event.key == pygame.K_d:
                        self.player_movement[1] = False 
                    if event.key == pygame.K_s: 
                        self.player.crouch =False 

                elif self.curr_gameState == GameState.MainMenu:
                    if event.key == pygame.K_p: 
                        self.curr_gameState = GameState.GameLoop
                    if event.key == pygame.K_w: 
                        self.menu_scroll_up = False
                    if event.key == pygame.K_UP: 
                        self.menu_scroll_up = False
                    if event.key == pygame.K_s:
                        self.menu_scroll_down = False
                    if  event.key == pygame.K_DOWN: 
                        self.menu_scroll_down = False
                    if event.key == pygame.K_SPACE:
                        self.menu_select = False
                    if event.key == pygame.K_KP_ENTER:
                        self.menu_select = False

        
            
    
    def update_render(self):
        
        if self.curr_gameState == GameState.GameLoop:
            
        
            pygame.mixer.music.load('data/music/Abstraction - Patreon Goal Reward Loops/Patreon Goal Reward Loops - Track 05.wav')
            pygame.mixer.music.set_volume(0.3)
            #pygame.mixer.music.play(loops=-1)
             
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
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LSHIFT]:
                self.player.running = True 
            else: 
                self.player.running = False
            """
            #rapid fire and single fire toggle 
            """
            if pygame.mouse.get_pressed()[0]:
                if not self.cursor.interacting:
                    
                    if self.player.weapon_toggle_state():
                        #then you shoot. 
                        self.player.shoot_weapon(self.frame_count)
                    else:
                        #you shoot, once. 
                        if self.reset == True: 
                            self.player.shoot_weapon(self.frame_count)
                            self.reset = False 
                
            elif pygame.mouse.get_pressed()[0] == False:
                #self.main_offset = None 
                self.reset = True 
            """

            self.prev_cursor_pos = self.cursor.pos
            self.dt = time.time() - self.start
            self.start = time.time()
            self.screen_shake = max(0,self.screen_shake -1)
        
            #frame counter for acceleration and dash timings 
                
            self.timer += self.time_increment

            if self.timer > 20:
                self.boost_ready = False 
                self.time_increment = False 
                self.timer = 0


            self.frame_count = (self.frame_count+1) % 360 
            self.scroll[0] += (self.player.rect().centerx - self.background_surf.get_width() /2 - self.scroll[0])/20
            self.scroll[1] += (self.player.rect().centery - self.background_surf.get_height() /2 - self.scroll[1])/20
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))
            

            #----------------------------quadtree stuff 
            boundary = Rectangle(Vector2(render_scroll[0]- self.qtree_x_slack,render_scroll[1]- self.qtree_y_slack),Vector2(self.background_surf.get_width() +self.qtree_x_slack*2,self.background_surf.get_height() +self.qtree_y_slack*2))
            quadtree = QuadTree(self.NODE_CAPACITY, boundary)

            x_lower = boundary.position.x
            x_higher = x_lower + boundary.scale.x
            y_lower = boundary.position.y
            y_higher = y_lower + boundary.scale.y
            #-------------------------------



            #print(self.player.interactables)


            """


            for rect in self.leaf_spawners:
                if random.random() * 399999 < rect.width * rect.height: 
                    pos = (rect.x +random.random()* rect.width,rect.y + random.random() * rect.height)
                    self.particles.append(Particle(self,'leaf',pos,'tree',velocity=[random.randrange(-100,100)/1000,0.3], frame = random.randint(0,20)))

            """

            self.lights_engine.clear(0,0,0,255)
            self.background_surf.fill((155,155,155))
            self.foreground_surf.fill((0,0,0,0))
            self.buffer_surf.fill((0,0,0,0))

            self.backgrounds['building'].render(self.background_surf,render_scroll)

            #self.backgrounds['new_building'].render(selaaaaaf.background_surf,render_scroll)
        
        


            self.Tilemap.render(self.background_surf,render_scroll)



            # this part where you set the ambient node pointer should be in the update function. 

            if self.player.pos[0] < self.ambient_node_ptr.range[0]:
                if self.ambient_node_ptr.prev: 
                    self.ambient_node_ptr = self.ambient_node_ptr.prev
                    self.lights_engine.set_ambient(*self.ambient_node_ptr.colorValue) 
            elif self.player.pos[0] > self.ambient_node_ptr.range[1]:
                if self.ambient_node_ptr.next: 
                    self.ambient_node_ptr = self.ambient_node_ptr.next
                    self.lights_engine.set_ambient(*self.ambient_node_ptr.colorValue)




            #Global lighting ----------------
            """
            self.shadow_objects = self.Tilemap.update_shadow_objs(self.display,render_scroll)
            """
            #self.lights_display.fill((128,128,128,128))
            #self.lights_display.blit(global_light(self.background_swurf.get_size(),100), (0,0))
            
            self.lights_engine.hulls = self.Tilemap.update_shadow_objs(self.background_surf,render_scroll)
            
            # ----------------
            

            for enemy in self.existing_enemies.copy():
                
                if (enemy.pos[0] >= x_lower and enemy.pos[0] <= x_higher) and (enemy.pos[1] >= y_lower and enemy.pos[1] <= y_higher) :
                    #if the enemy is within the boundaries of the quadtree, update it. 
                    kill = enemy.update(self.Tilemap,self.player.pos,self.dt,(0,0))
                    quadtree.insert(enemy)

                    # If an enemy collides with another enemy, it should push itself away. To avoid too much overlap.
                    

                    enemy.render(self.background_surf,offset = render_scroll)
                    if kill:
                        self.existing_enemies.remove(enemy)
            


            for collectable_item in self.collectable_items.copy():
                if collectable_item.life <= 0 or (collectable_item.pos[0] + collectable_item.size[0] <= x_lower or \
                                                  collectable_item.pos[0] >= x_higher) or (collectable_item.pos[1] + collectable_item.size[1] <= y_lower or \
                                                  collectable_item.pos[1] >= y_higher)  :
                    self.collectable_items.remove(collectable_item)
                    continue 
                collectable_item.update_pos(self.Tilemap)
                quadtree.insert(collectable_item)
                collectable_item.render(self.background_surf,offset = render_scroll)

                
            
            
            for bullet in self.bullets_on_screen.copy():
                #if (bullet.pos[0] >= x_lower and bullet.pos[0] <= x_higher) and (bullet.pos[1] >= y_lower and bullet.pos[1] <= y_higher) :
                    
                        kill = bullet.update_pos(self.Tilemap)
                        if kill: 
                            
                            self.bullets_on_screen.remove(bullet)
                            #bullets_to_remove.append(bullet)
                            continue    

                        if (bullet.pos[0] >= x_lower and bullet.pos[0] <= x_higher) and (bullet.pos[1] >= y_lower and bullet.pos[1] <= y_higher) :

                            #quadtree.insert(bullet)
                            #bullet.light.main([]d,self.lights_display,bullet.center[0],bullet.center[1],render_scroll)
                        
                            bullet.render(self.background_surf,offset = render_scroll)

                            xx, yy = bullet.pos[0],bullet.pos[1]
                            r = max(bullet.size) * 3  # Adjust range radius for rectangular particles

                            rangeRect = Rectangle(Vector2(xx - r / 2, yy - r / 2), Vector2(r, r))
                            
                            nearby_entities = quadtree.queryRange(rangeRect,"enemy")
                            for entity in nearby_entities:
                                
                                #if bullet != entity and entity.type != "bullet" and entity.state != 'death':
                                    if  entity.state != 'death' and bullet.collide(entity) :
                                        bullet.dead = True
                                        entity.hit(bullet.damage)
                                        og_end_point_vec = pygame.math.Vector2((6,0))
                                        og_end_point_vec.rotate(bullet.angle)

                                        center_pos = [bullet.pos[0]+bullet.sprite.get_width()/2, bullet.pos[1] + bullet.sprite.get_height()/2]
                                        end_point = [center_pos[0]+og_end_point_vec[0]- (bullet.sprite.get_width()/2 if bullet.velocity[0] >=0 else 0),center_pos[1] + og_end_point_vec[1]] 
                                        collide_particle = Particle(self,'bullet_collide/rifle',end_point,'player')
                                        rotated_collide_particle_images = [pygame.transform.rotate(image,180+bullet.angle) for image in collide_particle.animation.copy().images]
                                        collide_particle.animation.images = rotated_collide_particle_images

                                        self.particles.append(collide_particle)
                                        if bullet in self.bullets_on_screen:
                                            self.bullets_on_screen.remove(bullet)
                                        #bullets_to_remove.append(bullet)
                                    
                                
    
            for bullet in self.enemy_bullets.copy():
                kill = bullet.update_pos(self.Tilemap)
                bullet.render(self.background_surf,offset=render_scroll)
                #bullet.light.main([],self.lights_display,bullet.center[0],bullet.center[1],render_scroll)
                if kill: 
                    self.enemy_bullets.remove(bullet)

            for particle in self.particles.copy():
                if particle == None: 
                    self.particles.remove(particle)
                else:
                    kill =particle.update()
                    particle.render(self.background_surf,offset = render_scroll)
                    if particle.type =='leaf':
                        particle.pos[0] += math.sin(particle.animation.frame * 0.035) * 0.3
                    if particle.source =='player' and particle.type[0:5] == 'smoke':
                        if self.player.cur_weapon_node:
                            particle.pos = self.player.cur_weapon_node.weapon.opening_pos
                    if kill: 
                        self.particles.remove(particle)
            

            for i, particle in enumerate(self.physical_particles.copy()):
                    
                    kill = particle.update_pos(self.Tilemap,self.frame_count)
                    if kill: 
                        self.physical_particles.remove(particle)
                        continue 
                    #if particle.life >= 17:
                        #particle.light.main([],self.lights_display,particle.x,particle.y,render_scroll)
                    particle.render(self.buffer_surf,offset = render_scroll)

                    if i % 4 == 0:
                        xx, yy = particle.pos[0],particle.pos[1]
                        r = particle.r * 3 
                        
                        rangeCircle = Circle(Vector2(xx, yy), r)

                        nearby_entities = quadtree.queryRange(rangeCircle,"enemy")

                        for entity in nearby_entities:
                            if  entity.state != 'death' and particle.collide(entity):
                                entity.hit(particle.damage)

                    
            self.background_surf.blit(self.buffer_surf,(0,0))


            for particle in self.non_animated_particles.copy():
                if particle == None: 
                    self.non_animated_particles.remove(particle)
                else: 
                    kill = particle.update(self.dt)
                    particle.render(self.background_surf,offset =render_scroll)
                    if kill:
                        self.non_animated_particles.remove(particle)

        

            self.player.update_pos(self.Tilemap,quadtree,self.cursor.pos,self.frame_count,(self.player_cur_vel,0))
            self.player.render(self.background_surf,render_scroll)

            #------------------------grass renderer stuff

            rot_function = lambda x, y: int(math.sin(self.rot_func_t / 60 + x / 100) * 7)
            self.gm.update_render(self.background_surf,self.dt,offset=render_scroll,rot_function= rot_function)
            self.rot_func_t += self.dt * 100
            #----------------------------------


        #lighting ------------------

            """
            for key in self.lights: e
                if  (key[0] >= render_scroll[0] - 200 and key[0] <= self.display.get_width() + render_scroll[0] + 200)  and (key[1] >= render_scroll[1] - 200 and key[1] <= self.display.get_height() + render_scroll[1]+ 200 ):
                    light = self.lights[key]


                    light.main(self.shadow_objects,self.lights_display,key[0],key[1],render_scroll)
            
            """
            """
            for light in self.temp_lights.copy():
                if light[1] != 0:
                    light[1] -= 1 
                    #shadow_objs = light[0].filter_tiles(self.Tilemap.tilemap,self.Tilemap.tile_size,key[0],key[1],render_scroll) 
                    light[0].main(self.shadow_objects,self.lights_display,light[2][0],light[2][1],render_scroll) 
                else: 
                    self.temp_lights.remove(light)
            
            """
            #self.background_surf.blit(self.lights_display,( 0, 0),special_flags= pygame.BLEND_RGB_MULT)
            
        
            


            
            """
            display_mask = pygame.mask.from_surface(self.background_surf)
            display_sillhouette = display_mask.to_surface(setcolor=(0,0,0,180),unsetcolor=(0,0,0,0))

            for offset in [(-1,0),(1,0),(0,-1),(0,1)]:
                self.background_surf.blit(display_sillhouette,offset)
        

        """
            #add decel and accel here 
                        
            if(self.player_movement[1]-self.player_movement[0])  >0 :
                #means that the intent of the player movement is to the right.  
                self.player_cur_vel = min( 1.3*self.PLAYER_DEFAULT_SPEED,self.accel_decel_rate + self.player_cur_vel)
                
            elif (self.player_movement[1]-self.player_movement[0]) <0 :
                #means that the intent of the player movement is to the left.  
                self.player_cur_vel = max( -1.3*self.PLAYER_DEFAULT_SPEED,self.player_cur_vel- self.accel_decel_rate )
                
            else: 
                if self.player_cur_vel >= 0 :
                    self.player_cur_vel = max(0,self.player_cur_vel - self.accel_decel_rate)
                    
                else:
                    self.player_cur_vel = min(0,self.player_cur_vel + self.accel_decel_rate)
            
            
            """
            self.HUD.render_expanded(self.cursor,self.display,(0,0),closing = not self.inven_on)
            """
            self.HUD.render(self.foreground_surf,self.cursor,offset=(0,0),closing = self.inven_on)
            self.cursor.update(self.foreground_surf)
            #self.cursor.render(self.display)





            
            """"""

            #print(self.player.pos[0] - render_scroll[0] ,self.cursor.pos[0])
            #print(self.ambient_node_ptr.range[0] - render_scroll[0])

            #self.display_2.blit(self.display,(0,0))
            #print(len(self.lights_engine.hulls))
            screenshake_offset = (random.random()* self.screen_shake - self.screen_shake /2, random.random()* self.screen_shake - self.screen_shake /2)

            
            tex = self.lights_engine.surface_to_texture(self.background_surf)
        

            
            #self.test_shader['iTime'] = self.running_time -time.time()

            self.lights_engine.render_texture_with_trans(
                tex, Layer_.BACKGROUND,
                position= (-screenshake_offset[0],-screenshake_offset[1])
            )
            """
            self.lights_engine.render_texture(
                tex, Layer_.BACKGROUND,
                pygame.Rect(-screenshake_offset[0] ,-screenshake_offset[1],tex.width ,tex.height),
                pygame.Rect(0,0,tex.width,tex.height)
            )"""
            tex.release()

            tex = self.lights_engine.surface_to_texture(self.foreground_surf)
            self.lights_engine.render_texture(
                tex, Layer_.FOREGROUND,
                pygame.Rect(0,0,tex.width ,tex.height),
                pygame.Rect(0,0,tex.width,tex.height)
            )
            tex.release()
            



            self.lights_engine.render(self.ambient_node_ptr.range,render_scroll, screenshake_offset)
            
            #self.screen.blit(pygame.transform.scale(self.display_2,self.screen.get_size()),screenshake_offset)


            pygame.display.flip()
            #pygame.display.update()
            fps = self.clock.get_fps()
            pygame.display.set_caption(f'Noel - FPS: {fps:.2f}')
            self.clock.tick(60)

        if self.curr_gameState == GameState.MainMenu:
            self.scroll[0] += (self.player.rect().centerx - self.background_surf.get_width() /2 - self.scroll[0])/20
            self.scroll[1] += (self.player.rect().centery - self.background_surf.get_height() /2 - self.scroll[1])/20
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))
            
            boundary = Rectangle(Vector2(render_scroll[0]- self.qtree_x_slack,render_scroll[1]- self.qtree_y_slack),Vector2(self.background_surf.get_width() +self.qtree_x_slack*2,self.background_surf.get_height() +self.qtree_y_slack*2))
            quadtree = QuadTree(self.NODE_CAPACITY, boundary)

            self.lights_engine.clear(0,0,0,255)
            self.background_surf.fill((155,155,155))
            self.foreground_surf.fill((0,0,0,0))
            self.buffer_surf.fill((0,0,0,0))

            self.backgrounds['building'].render(self.background_surf,render_scroll)

            self.Tilemap.render(self.background_surf,render_scroll)

            #self.start_screen_ui.update(self.cursor)
            self.start_screen_ui.render(self.foreground_surf,(0,0))

            self.lights_engine.hulls = self.Tilemap.update_shadow_objs(self.background_surf,render_scroll)

            self.player.update_pos(self.Tilemap,quadtree,self.cursor.pos,self.frame_count,(self.player_cur_vel,0))
            self.player.render(self.background_surf,render_scroll)


            self.cursor.update(self.foreground_surf)

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
            #pygame.display.update()
            fps = self.clock.get_fps()
            pygame.display.set_caption(f'Noel - FPS: {fps:.2f}')
            self.clock.tick(60)
            pass

    def quit_game(self): 
        pygame.quit()
        quit()

    def run(self):
        pass

game = myGame()
game.start_game()