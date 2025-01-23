import pygame 
import platform
import importlib
from os import environ
from moderngl import create_context
from screeninfo import get_monitors

import scripts.data
import scripts.second_HUD
import scripts.systems

from scripts.game_state import GameState
from scripts.data import TIME_FOR_ONE_LOGICAL_STEP
from scripts.new_resource_manager import ResourceManager
from scripts.new_entities_manager import EntitiesManager
from scripts.systems import PhysicsSystem,RenderSystem,InputHandler,StateSystem
from scripts.new_tilemap import Tilemap

class Noel():
    def __init__(self):
        pygame.init()
        self._initalize_game_settings() 

        

        # TODO : think adding a game context to the main game structure would benefit 
        # the readability of the code. Refactor. 

        self._frame_count:int = 0
        self._camera_offset:list[int,int] = [0,0]
        self._dt :float = 0
        self._grass_rotation_function_time:float = 0
        self._time_accumulator:float = 0
        self._prev_frame_time :float = 0
        self._scroll:list[int,int] = [1000,0]
        self._movement_input:list[bool,bool] = [False,False]

        self._initialize_game_objects()
        self._bind_objects_to_render_engine()


    def _initialize_game_objects(self):
        
        self._resource_manager = ResourceManager.get_instance(self._ctx,self._game_context['true_res'])
        self._tilemap = Tilemap(self._resource_manager.tilemap_jsons['test1.json'])
        self._entities_manager = EntitiesManager.get_instance()


        self._physics_system = PhysicsSystem()
        self._physics_system.attatch_tilemap(self._tilemap)

        self._state_system = StateSystem()  

        self._render_system = RenderSystem(self._ctx,self._game_context["display_scale_ratio"],self._game_context['screen_res'],\
                                           self._game_context['true_res'])
        
        self._input_handler = InputHandler(self._game_context)

 
        self._render_system.attatch_tilemap(self._tilemap)
        self._render_system.attatch_background(self._resource_manager.backgrounds['start'])


       

    def _hot_reload(self)->None: 
        # reload systems module
        importlib.reload(scripts.data)
        importlib.reload(scripts.second_HUD)
        importlib.reload(scripts.systems)

    
        from scripts.systems import PhysicsSystem, StateSystem,RenderSystem, InputHandler 
        # reinitialize systems
        self._physics_system = PhysicsSystem()
        self._physics_system.attatch_tilemap(self._tilemap)
        
        self._state_system = StateSystem()
        self._render_system = RenderSystem(self._ctx,self._game_context['display_scale_ratio'],self._game_context['screen_res'],\
                                           self._game_context['true_res'])
        self._input_handler = InputHandler(self._game_context)
        
        self._render_system.attatch_background(self._resource_manager.backgrounds['start'])
        self._render_system.attatch_tilemap(self._tilemap)
        """
        self.resource_manager = ResourceManager.get_instance(self._ctx)
        self.particle_system = ParticleSystem.get_instance(self._ctx) 
        self.entities_manager = EntitiesManager.get_instance(

        self._tilemap = Tilemap()
        self._tilemap.load_map('test1.json')  

        self._grass_manager = GrassManager.get_instance(self.resource_manager.get_ga_of_name('test_grass'),self._tilemap.tile_size,stiffness=600,\
                                           max_unique=5,place_range=[1,1],burn_spread_speed=3,burn_rate=1.2)

        self.render_engine = RenderEngine(self._ctx,self._game_context["screen_res"],\
                                          self._game_context["display_scale_ratio"],self._game_context["true_res"])
        self.player = Player([900,11],(14,16)) 
        self.player.set_accel_rate(1)
        self.player.set_default_speed(2.3)
        self._hud = HUD(self.player,self._game_context["true_res"])
        """

    def _bind_objects_to_render_engine(self):
        """
        self.render_engine.bind_tilemap(self._tilemap)
        self.render_engine.bind_background('building')
        self.render_engine.bind_hud(self._hud)
        self.render_engine.lights = self._tilemap.lights
        """
    """
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
        importlib.reload(scripts.resourceManager)

        # import changed classes
        from my_pygame_light2d.engine import RenderEngine
        from scripts.new_HUD import HUD
        from scripts.new_grass import GrassManager
        from scripts.new_particles import ParticleSystem
        from scripts.new_entities import Player
        from scripts.new_tilemap import Tilemap
        from scripts.resourceManager import ResourceManager

        # reinitialize singletons

        self.resource_manager = ResourceManager.get_instance(self._ctx)
        self.particle_system = ParticleSystem.get_instance(self._ctx) 
        self.entities_manager = EntitiesManager.get_instance()

        # explicitly reinitialize objects       
        self._tilemap = Tilemap()
        self._tilemap.load_map('test1.json')  

        self._grass_manager = GrassManager.get_instance(self.resource_manager.get_ga_of_name('test_grass'),self._tilemap.tile_size,stiffness=600,\
                                           max_unique=5,place_range=[1,1],burn_spread_speed=3,burn_rate=1.2)

        self.render_engine = RenderEngine(self._ctx,self._game_context["screen_res"],\
                                          self._game_context["display_scale_ratio"],self._game_context["true_res"])


        # Update cursor's position
        
        cursor_topleft = pygame.mouse.get_pos()
        cursor_topleft =  (
            cursor_topleft[0] / self._game_context["display_scale_ratio"] + self._scroll[0],
            cursor_topleft[1] / self._game_context["display_scale_ratio"] + self._scroll[1],
        )

        # Reinitialize Player with updated cursor position
        self.player = Player(list(cursor_topleft), (14, 16))
        self.player.set_accel_rate(1)
        self.player.set_default_speed(2.3)

        # reinitialize hud
        self._hud = HUD(self.player,self._game_context["true_res"])

        # rebind objects to render engine
        self._bind_objects_to_render_engine()
    """

    def _initalize_game_settings(self):
        self._game_context = {
            "screen_shake":0,
            "gamestate" : GameState.GameLoop,
            "true_res" : (0,0),
            "screen_res": (0,0),
            "display_scale_ratio": 4
        }

        self._system_display_info = self._get_system_display_info()
        self._set_initial_display_settings()
        self._configure_pygame()

       # create moderngl context
        self._ctx = create_context()


    def _get_system_display_info(self):
        system_info = {}
        # primary monitor set to second monitor for hot reloading
        primary_monitor = get_monitors()[1]
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

        self._target_min_fps = 60

        self._game_context["screen_res"] =self._system_display_info['resolution']
        

        #TODO : you need to create a way to calculate native_res depending on selected resolution and scaling. 
        self._game_context["display_scale_ratio"] = 4.0 
        self._game_context["true_res"]= (int(self._game_context["screen_res"][0]/self._game_context["display_scale_ratio"]),\
                                         int(self._game_context["screen_res"][1]/self._game_context["display_scale_ratio"]))
    
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
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 4)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(
            pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)

        # Configure pygame display
        self._pygame_display = pygame.display.set_mode(
            self._game_context["screen_res"], pygame.HWSURFACE | pygame.OPENGL | pygame.DOUBLEBUF)

    

        """
        
        self._hud.cursor.topleft= pygame.mouse.get_pos()
        self._hud.cursor.topleft= ((self._hud.cursor.topleft[0]//self._game_context["display_scale_ratio"]),\
                                   (self._hud.cursor.topleft[1]//self._game_context["display_scale_ratio"]))
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
        """
                          
        """
            if self._hud.cursor.pressed[0]:
                if not self._hud.cursor.interacting:
                    self.player.shoot_weapon(self.render_engine.lights,self.entities_manager,self.particle_system)
            else: 
                if not self._hud.cursor.interacting: 
                    self.player.prompt_weapon_reset()
          
            for event in pygame.event.get():
                self._handle_common_events(event)
                if event.type == pygame.MOUSEWHEEL:
                    print(" ")
                    self._hud.change_weapon(event.y)
                if event.type ==pygame.KEYDOWN:
                    
                    if event.key == pygame.K_F5:
                        self._hot_reload()
                    if event.key == pygame.K_n:  
                        for _ in range(20):
                            self._grass_manager.place_tile((74+_,11),10,[0,1,2,3,4])
                    if event.key == pygame.K_q:
                        self._hud.remove_current_weapon(self.entities_manager)
                    if event.key == pygame.K_e:
                        self._hud.set_inven_open_state(not self._hud.inven_open_state)
                    if event.key == pygame.K_a:
                        self.movement_input[0] = True
                    if event.key == pygame.K_d:
                        self.movement_input[1] = True 
                    if event.key == pygame.K_g: 
                        self.player.toggle_rapid_fire()

                    if event.key == pygame.K_x: 
                        for row in self._hud._inven_list[0]._cells: 
                            for cell in row:
                                if cell._item: 
                                    print(cell._item.count)
                    if event.key == pygame.K_f: 
                        # change these later to be instantiated with their own sdclass names 
                        self._hud.add_item(AK47())
                    if event.key == pygame.K_v: 
                        self._hud.add_item(Flamethrower())
                    if event.key == pygame.K_c:
                        # testing adding items to item inventory 
                        self._hud.add_item(Item(choice(list(ITEM_ATLAS_POSITIONS_AND_SIZES.keys()))))
                        pass 
                    if event.key == pygame.K_w: 
                        self.player.jump(self.particle_system)
                    if event.key == pygame.K_s:
                        self.player.crouch = True
                    if event.key == pygame.K_LSHIFT:
                        self.player.running = True
                        self._hud.cursor.special_actions = True 
                if event.type == pygame.KEYUP: 
                    if event.key == pygame.K_a:
                        self.movement_input[0] = False 
                    if event.key == pygame.K_d: 
                        self.movement_input[1] = Fals
                    if event.key == pygame.K_w:
                        self.player.jump_cut()
                    if event.key == pygame.K_s: 
                        self.player.crouch = False
                    if event.key == pygame.K_LSHIFT:
                        self.player.running = False
                        self._hud.cursor.special_actions = False 
            """
    

    def _update_render(self):
        self._frame_count = (self._frame_count+1) %360
        self._render_system.clear(0,0,0,0)
        self._dt = min(self._clock.tick() / 1000.0,0.1)
        self._time_accumulator += self._dt

        if self._game_context['gamestate']== GameState.GameLoop:  
           
            self._camera_offset[0] += 3*self._dt*(self._entities_manager.player_position[0] - self._game_context["true_res"][0] /2 - self._camera_offset[0])
            self._camera_offset[1] += 3*self._dt*(self._entities_manager.player_position[1] - self._game_context["true_res"][1] /2 - self._camera_offset[1])

            integer_camera_offset = (int(self._camera_offset[0]), int(self._camera_offset[1]))

            while self._time_accumulator >= TIME_FOR_ONE_LOGICAL_STEP:
                self._physics_system.process(TIME_FOR_ONE_LOGICAL_STEP)
                self._state_system.process(TIME_FOR_ONE_LOGICAL_STEP)
                self._time_accumulator -= TIME_FOR_ONE_LOGICAL_STEP
            
            interpolation_delta = self._time_accumulator / TIME_FOR_ONE_LOGICAL_STEP

            self._render_system.process(integer_camera_offset,interpolation_delta,self._dt)

            """
           
            self._game_context['screen_shake'] = max(0,self._game_context['screen_shake'] -self._dt*60)
            screen_shake_buffer = self._game_context['screen_shake']

            
            self._scroll[1] += 2.5*self._dt*(self.player.pos[1] +self.player.size[1]/2 - self._game_context["true_res"][1] /2 - self._scroll[1])

            camera_scroll = (int(self._scroll[0]), int(self._scroll[1]))
           
            self.render_engine.hulls = self._tilemap._hull_grid.query(camera_scroll[0]-self._tilemap.tile_size * 10 ,camera_scroll[1]- self._tilemap.tile_size * 10,camera_scroll[0] \
                                                             + self._game_context["true_res"][0]+self._tilemap.tile_size * 10 ,camera_scroll[1]+ self._game_context["true_res"][1]+ self._tilemap.tile_size * 10)



            # updates that require  physics are done in fixed time steps 
            while self._accumulator >= TIME_FOR_ONE_LOGICAL_STEP: 

                self.entities_manager.update(self._tilemap,self.particle_system,self.render_engine.lights,TIME_FOR_ONE_LOGICAL_STEP)
                self.particle_system.update(self._tilemap,self._grass_manager,TIME_FOR_ONE_LOGICAL_STEP)

                rot_func = lambda x,y : int(sin(self._rot_func_t / 60 + x/100)* 7) 
                if not self.player.crouch: 
                    self._grass_manager.apply_force((self.player.pos[0] + self.player.size[0]//2,self.player.pos[1] + self.player.size[1]//2),\
                                                    self._tilemap.tile_size//4,self._tilemap.tile_size*4//7)
                self._grass_manager.update(self._game_context["true_res"],TIME_FOR_ONE_LOGICAL_STEP,camera_scroll,rot_function= rot_func)
                self.player.update(self._tilemap,self.particle_system,self._hud.cursor.topleft,\
                                self.movement_input,camera_scroll,self._game_context,TIME_FOR_ONE_LOGICAL_STEP)
                self._accumulator -= TIME_FOR_ONE_LOGICAL_STEP
            
            self._tilemap.update_ambient_node_ptr(self.player.pos)
            self._hud.update(self._dt)

            #self._accumulator = min(self._accumulator,TIME_FOR_ONE_LOGICAL_STEP)
            interpolation_alpha = self._accumulator / TIME_FOR_ONE_LOGICAL_STEP

            self.render_engine.bind_player(self.player)
            self.render_engine.bind_hud(self._hud)


            self.render_engine.render_background_scene_to_fbo(camera_scroll,interpolation_alpha,infinite=False)
            self.render_engine.render_foreground_scene_to_fbo()
            

            screenshake_offset = (random() * screen_shake_buffer - screen_shake_buffer/2,
                                  random() * screen_shake_buffer - screen_shake_buffer/2)
            self.render_engine.render_scene_with_lighting(camera_scroll,interpolation_alpha, screenshake_offset)
            """
            pygame.display.flip()
            fps = self._clock.get_fps()
            print(fps)

    def start(self):
        self._dt = self._clock.tick() / 1000.0
        self._time_accumulator += self._dt 
        while(True):
            # hot reload
            hot_reload = self._input_handler.process(self._dt)
            self._update_render() 

            if hot_reload: 
                self._hot_reload()
        


game = Noel()
game.start()