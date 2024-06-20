
import pygame

import random
import math
import time
import sys 
from scripts.tilemap import Tilemap
from scripts.utils import load_image,load_images,load_tile_images,Animation, load_sounds
from scripts.entities import PlayerEntity,Canine,Wheel_bot,Sabre,Bullet
from scripts.clouds import Clouds
from scripts.particles import Particle
from scripts.cursor import Cursor
from scripts.weapons import Weapon,Wheelbot_weapon, AK_47,Flamethrower
from scripts.background import Background
from scripts.Pygame_Lights import LIGHT,global_light,pixel_shader
from scripts.indicator import indicator
from scripts.HUD import HUD 
from scripts.grass import *


# ----------------------------------- quadtree imports 
from scripts.quadtree import * 
from scripts.range import * 


#----------------------------------------- imports to integrate shaders 
from array import array
from collections import deque 
import moderngl 


class myGame:
    def __init__(self):
        pygame.init() 
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.display.set_caption('Noel.')
        
        
        self.screen_shake = 0 
        self.screen = pygame.display.set_mode((1040,652),pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.display = pygame.Surface((self.screen.get_width()//2,self.screen.get_height()//2),pygame.SRCALPHA)
        self.bsurf = pygame.Surface((self.screen.get_width()//2,self.screen.get_height()//2),pygame.SRCALPHA)

        self.display_2 = pygame.Surface((self.screen.get_width()//2,self.screen.get_height()//2))
        
        self.NODE_CAPACITY = 2
        self.qtree_x_slack = 300
        self.qtree_y_slack = 300

        """
        self.sfx = {
            'jump': pygame.mixer.Sound(),
            'dash': pygame.mixer.Sound(),
            'run' : pygame.mixer.Sound(),
            'walk': pygame.mixer.Sound(),
            'land': pygame.mixer.Sound(),
        }"""

        self.player_sfx = {
            'run' : load_sounds('data/my_sfx/run'),
            'jump' : load_sounds('data/my_sfx/jump')
        }
       
    
        #make a more efficient way to load assets maybe?

        self.assets = {
            
            'grass' : load_tile_images('tiles/grass',background='transparent'),
            'live_grass': load_tile_images('grass',background='black'),
            #'large_decor' : load_tile_images('tiles/large_decor'),
            #'stone' : load_tile_images('tiles/stone',background='transparent'),
            'box' : load_tile_images('tiles/box',background='transparent'),

            'masks' : load_images('tiles/masks',background='transparent'),
            'building_0' : load_tile_images('tiles/building_0',background='transparent'),
            'building_1' : load_tile_images('tiles/building_1',background='transparent'),
            'building_2' : load_tile_images('tiles/building_2',background='transparent'),
            'building_3' : load_tile_images('tiles/building_3',background='transparent'),
            'building_4' : load_tile_images('tiles/building_4',background='transparent'), 
            'building_5' : load_tile_images('tiles/building_5',background='transparent'), 
            'building_back' : load_tile_images('tiles/building_back',background='transparent'), 
            'building_decor' : load_tile_images('tiles/building_decor',background='transparent'), 
            'lights' : load_tile_images('tiles/light',background='transparent'), 
            'stairs' : load_tile_images('tiles/building_stairs',background='transparent'), 


            'player' : load_image('entities/player.png'),
            'background': load_image('background.png'),
            'test_background' : load_image('test_background.png'),

            'cursor/default' : load_image('cursor/default_cursor.png',background='black'),
            'crosshair' : load_image('cursor/crosshair.png'),


            'clouds': load_images('clouds/default'),
            'gray1_clouds' : load_images('clouds/gray1',background = 'transparent'),
            'gray2_clouds' : load_images('clouds/gray2',background = 'transparent'),
            
            'player/holding_gun/idle' : Animation(load_images('entities/player/holding_gun/idle',background='transparent'), img_dur =6),
            'player/holding_gun/run' : Animation(load_images('entities/player/holding_gun/run',background='transparent'), img_dur =4),

            'player/holding_gun/jump_up' : Animation(load_images('entities/player/holding_gun/jump/up',background='transparent'), img_dur =5),
            'player/holding_gun/jump_down' : Animation(load_images('entities/player/holding_gun/jump/down',background='transparent'), img_dur =5,halt=True),
            'player/holding_gun/land' : Animation(load_images('entities/player/holding_gun/land',background='transparent'), img_dur =2,loop=False),
           

            'player/holding_gun/slide' : Animation(load_images('entities/player/slide',background='transparent'), img_dur =5),
            'player/holding_gun/wall_slide' : Animation(load_images('entities/player/wall_slide',background='transparent'), img_dur =4),
            'player/holding_gun/walk' : Animation(load_images('entities/player/holding_gun/walk',background='transparent'), img_dur =7),


            'health_UI' : load_image('ui/health/0.png',background='transparent'),
            'stamina_UI' : load_image('ui/stamina/0.png',background='transparent'),


            'player/idle' : Animation(load_images('entities/player/idle',background='transparent'), img_dur =6),
            'player/run' : Animation(load_images('entities/player/run',background='transparent'), img_dur =4),

            'player/jump_up' : Animation(load_images('entities/player/jump/up',background='transparent'), img_dur =5),
            'player/jump_down' : Animation(load_images('entities/player/jump/down',background='transparent'), img_dur =5,halt=True),
            'player/land' : Animation(load_images('entities/player/land',background='transparent'), img_dur =2,loop=False),
           

            'player/slide' : Animation(load_images('entities/player/slide',background='transparent'), img_dur =5,halt = True),
            'player/wall_slide' : Animation(load_images('entities/player/wall_slide',background='transparent'), img_dur =4),
            

            'particle/box_destroy' : Animation(load_images('particles/box',background='transparent'),img_dur= 3,loop= False),
            'particle/box_smoke' : Animation(load_images('particles/box_break',background='black'),img_dur= 3,loop= False),
            
            'particle/leaf':Animation(load_images('particles/leaf'),img_dur =20,loop=False),
            'particle/jump':Animation(load_images('particles/jump',background= 'black'),img_dur= 2, loop= False),
            'particle/dash_left' : Animation(load_images('particles/dash/left',background='black'),img_dur=1,loop =False),
            'particle/dash_right' : Animation(load_images('particles/dash/right',background='black'),img_dur=1,loop =False),
            'particle/dash_air' : Animation(load_images('particles/dash/air',background='black'),img_dur=2,loop =False),
            'particle/land' : Animation(load_images('particles/land',background='transparent'),img_dur=3,loop =False),
            'particle/big_land' : Animation(load_images('particles/big_land',background='transparent'),img_dur=2,loop =False),
            
            'particle/shot_muzzle/laser_weapon' : Animation(load_images('particles/shot_muzzle/laser_weapon',background='transparent'),img_dur=3,loop =False),

            'particle/smoke/rifle' : Animation(load_images('particles/shoot/rifle',background='transparent'),img_dur=3,loop=False),

            'particle/smoke/rifle_small' : Animation(load_images('particles/bullet_collide_smoke/rifle/small',background='black'),img_dur=2,loop=False),

            'particle/smoke/laser_weapon' : Animation(load_images('particles/shoot/laser_weapon',background='transparent'),img_dur=3,loop=False),

            'particle/bullet_collide/laser_weapon' :Animation(load_images('particles/bullet_collide/laser_weapon',background='transparent'),img_dur=2,loop=False),
            'particle/bullet_collide/rifle' :Animation(load_images('particles/bullet_collide/rifle',background='transparent'),img_dur=2,loop=False),



        } 

        self.enemies = {
            'Canine/black/idle' : Animation(load_images('entities/enemy/Canine/black/idle',background='transparent'),img_dur= 8),
            'Canine/black/run' : Animation(load_images('entities/enemy/Canine/black/run',background= 'transparent'),img_dur= 6),
            'Canine/black/jump_up': Animation(load_images('entities/enemy/Canine/black/jump/up',background= 'transparent'),img_dur= 1,loop = False),
            'Canine/black/jump_down': Animation(load_images('entities/enemy/Canine/black/jump/down',background= 'transparent'),img_dur= 3,loop = False),
            'Canine/black/hit': Animation(load_images('entities/enemy/Canine/black/hit',background= 'transparent'),img_dur= 5,loop=False),
            'Canine/black/grounded_death': Animation(load_images('entities/enemy/Canine/black/death/grounded',background= 'transparent'),img_dur= 5,loop=False),

            'Wheel_bot/idle': Animation(load_images('entities/enemy/Wheel_bot/idle',background='transparent'),img_dur= 6),
            'Wheel_bot/move': Animation(load_images('entities/enemy/Wheel_bot/move',background='transparent'),img_dur= 7),
            'Wheel_bot/dormant': Animation(load_images('entities/enemy/Wheel_bot/dormant',background='transparent'),img_dur=2,loop=True),
            'Wheel_bot/alert': Animation(load_images('entities/enemy/Wheel_bot/alert',background='transparent'),img_dur=4,loop=False),
            'Wheel_bot/wake': Animation(load_images('entities/enemy/Wheel_bot/wake',background='transparent'),img_dur=5,loop=False),
            'Wheel_bot/new_charge': Animation(load_images('entities/enemy/Wheel_bot/new_charge',background='transparent'),img_dur=3,loop=True),
            'Wheel_bot/shoot': Animation(load_images('entities/enemy/Wheel_bot/shoot',background='transparent'),img_dur=4,loop=False),
            'Wheel_bot/hit': Animation(load_images('entities/enemy/Wheel_bot/hit',background='transparent'),img_dur=4,loop=False),
            'Wheel_bot/death': Animation(load_images('entities/enemy/Wheel_bot/death',background='transparent'),img_dur=4,loop=False),



            #fix the img durations and loop variables accordingly 
            'sabre/idle':  Animation(load_images('entities/enemy/sabre/idle',background='transparent'),img_dur= 6),
            'sabre/move':  Animation(load_images('entities/enemy/sabre/move',background='transparent'),img_dur= 6),
            'sabre/dormant':  Animation(load_images('entities/enemy/sabre/dormant',background='transparent'),img_dur= 6,loop=True),
            'sabre/wake': Animation(load_images('entities/enemy/sabre/wake',background='transparent'),img_dur=5,loop=False),
            #'sabre/attack_1': Animation(load_images('entities/enemy/sabre/attack_1',background='transparent'),img_dur=5,loop=False),
            #'sabre/attack_2': Animation(load_images('entities/enemy/sabre/attack_1',background='transparent'),img_dur=5,loop=False),
            #'sabre/hit': Animation(load_images('entities/enemy/sabre/hit',background='transparent'),img_dur=5,loop=False),
            #'sabre/death': Animation(load_images('entities/enemy/sabre/death',background='transparent'),img_dur=5,loop=False),


        }


        self.weapons = {
            'laser_weapon': Wheelbot_weapon(self,Animation(load_images('entities/enemy/Wheel_bot/charge_weapon',background='transparent'),img_dur=5,loop=True)),
            'ak' : AK_47(self,load_image('weapons/ak_holding.png',background='transparent'),load_image('weapons/ak_47_img.png',background='transparent')),
            'flamethrower' : Flamethrower(self,load_image('weapons/flamethrower_holding.png',background='transparent'),load_image('weapons/flamethrower_img.png',background='transparent')),
        }

        
        self.bullets = {
            'rifle_small' : load_image('bullets/rifle/small.png',background='transparent'),
            'laser_weapon' : Animation(load_images('bullets/laser_weapon/new',background='transparent'),img_dur= 5, loop = True)
        }

        self.backgrounds = {
            'start' : Background(self,load_images('backgrounds/start',background='transparent')),
            'building' : Background(self,load_images('backgrounds/building',background='transparent')),
        }
        

        self.bullets_on_screen = []
        self.enemy_bullets = []
        self.particles = []
        self.physical_particles = []
        self.non_animated_particles = []
        self.leaf_spawners = []
        self.existing_enemies = []
        self.sparks = []

        self.Tilemap = Tilemap(self,tile_size=16,offgrid_layers=2)
        self.Tilemap.load('map.json')


        self.lights = {}
        self.temp_lights = []
        self.shadow_objects = [] 

        
        for light in self.Tilemap.extract([('lights','0;0'),('lights','1;0'),('lights','2;0'),('lights','3;0'),('lights','4;0')],keep=True):
            self.lights[(light.pos[0]*self.Tilemap.tile_size + 8,light.pos[1]*self.Tilemap.tile_size)] =LIGHT(370,pixel_shader(370,(255,255,255),1.5,True, 270, 90)) 
            
            
        for key in self.Tilemap.tilemap:
            split_key = key.split(";")
            tile = self.Tilemap.tilemap[key]
            if tile.type != "spawners":
                self.shadow_objects.append(pygame.Rect(int(split_key[0]) * self.Tilemap.tile_size,int(split_key[1]) * self.Tilemap.tile_size,16,16))
      

        self.PLAYER_DEFAULT_SPEED = 2
        self.player_cur_vel = 0
        self.accel_decel_rate = 0.34
        self.accelerated_movement = 0

        self.player = PlayerEntity(self,(50,50),(14,16))
        self.player_movement = [False,False]
        self.scroll = [0,0]

        #dash variables
        self.boost_ready = False 
        self.timer = 0
        self.time_increment = False

        #cursor object 
        pygame.mouse.set_visible(False)
        self.cursor = Cursor(self,(50,50),(4,4),'default')

        #weapon equip
        
        self.frame_count = 0
        self.reset = True 
        

        # ------------------- ak bullet loading and equip
        ak_47 = self.weapons['ak'].copy()
        for i in range(0,1005):
            test_shell_image = self.bullets['rifle_small'].copy()
            test_shell = Bullet(self,[0,0],test_shell_image.get_size(),test_shell_image,'rifle_small').copy()
            ak_47.load(test_shell)

        flamethrower = self.weapons['flamethrower'].copy()
        for i in range(0,1005):
            flamethrower.magazine.append(0)

        self.player.equip_weapon(flamethrower)
        self.player.equip_weapon(ak_47)

        # ----------------------



        self.inven_on = False 
        self.HUD = HUD(self.player,self.assets['health_UI'],self.display.get_size())
        
        
        #extract grasstiles and place them down using the grassManager.
        self.gm = GrassManager('data/images/grass',tile_size=self.Tilemap.tile_size,stiffness=600,max_unique = 5,place_range=[1,1])
        self.grass_locations = []

        
        for grass in self.Tilemap.extract([('live_grass','0;0'),('live_grass','1;0'),('live_grass','2;0'),('live_grass','3;0'),('live_grass','4;0'),('live_grass','5;0')]):
            self.grass_locations.append((grass.pos[0], grass.pos[1]))

        for loc in self.grass_locations:
            self.gm.place_tile(loc,14,[0,3,4])
    

    
        #spawner order: 0 : player, 1: canine: 2: wheel bot 
        
        for spawner in self.Tilemap.extract([('spawners','0;0'),('spawners','1;0'),('spawners','2;0'),('spawners','3;0')]):   
            if spawner.variant == '0;0':
                
                self.player.pos = [spawner.pos[0] * self.Tilemap.tile_size, spawner.pos[1] * self.Tilemap.tile_size]
            elif spawner.variant == '1;0': 

                #canine wwww
                self.existing_enemies.append(Canine(self,(spawner.pos[0] * self.Tilemap.tile_size,spawner.pos[1] * self.Tilemap.tile_size),(34,23),'black'))
            
        
            elif spawner.variant == '2;0':
                
                #wheelbot 
                self.existing_enemies.append(Wheel_bot(self,(spawner.pos[0] * self.Tilemap.tile_size,spawner.pos[1] * self.Tilemap.tile_size),(20,22)))

            elif spawner.variant == '3;0':
                self.existing_enemies.append(Sabre(self,(spawner.pos[0] * self.Tilemap.tile_size,spawner.pos[1] * self.Tilemap.tile_size),(30,27)))
       
        self.dt = 0
        self.start = time.time()
        self.rot_func_t = 0
        self.main_offset = None 

    def run(self):
        

        while True: 

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
            self.scroll[0] += (self.player.rect().centerx - self.display.get_width() /2 - self.scroll[0])/20
            self.scroll[1] += (self.player.rect().centery - self.display.get_height() /2 - self.scroll[1])/20
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))
            





            #----------------------------quadtree stuff 
            boundary = Rectangle(Vector2(render_scroll[0]- self.qtree_x_slack,render_scroll[1]- self.qtree_y_slack),Vector2(self.display.get_width() +self.qtree_x_slack*2,self.display.get_height() +self.qtree_y_slack*2))
            quadtree = QuadTree(self.NODE_CAPACITY, boundary)

            x_lower = boundary.position.x
            x_higher = x_lower + boundary.scale.x
            y_lower = boundary.position.y
            y_higher = y_lower + boundary.scale.y
            #-------------------------------


            for rect in self.leaf_spawners:
                if random.random() * 399999 < rect.width * rect.height: 
                    pos = (rect.x +random.random()* rect.width,rect.y + random.random() * rect.height)
                    self.particles.append(Particle(self,'leaf',pos,'tree',velocity=[random.randrange(-100,100)/1000,0.3], frame = random.randint(0,20)))

        
            
            self.display.fill((155,155,155))
            self.bsurf.fill((0,0,0,0))
            self.backgrounds['building'].render(self.display,render_scroll)
           
         


            self.Tilemap.render(self.display,render_scroll)

            

            #Global lighting ----------------
            
            lights_display = pygame.Surface(self.display.get_size()) 
            lights_display.blit(global_light(self.display.get_size(),100), (0,0))
            # ----------------
            

            for enemy in self.existing_enemies.copy():
                
                if (enemy.pos[0] >= x_lower and enemy.pos[0] <= x_higher) and (enemy.pos[1] >= y_lower and enemy.pos[1] <= y_higher) :
                    #if the enemy is within the boundaries of the quadtree, update it. 
                    kill = enemy.update(self.Tilemap,self.player.pos,self.dt,(0,0))
                    quadtree.insert(enemy)
                    enemy.render(self.display,offset = render_scroll)
                    if kill:
                        self.existing_enemies.remove(enemy)
            
            
           
            keys = pygame.key.get_pressed()




            if keys[pygame.K_LSHIFT]:
                self.player.running = True 
            else: 
                self.player.running = False
            
        

            for bullet in self.bullets_on_screen.copy():
                if (bullet.pos[0] >= x_lower and bullet.pos[0] <= x_higher) and (bullet.pos[1] >= y_lower and bullet.pos[1] <= y_higher) :
                    
                        kill = bullet.update_pos(self.Tilemap)
                        if kill: 
                            self.bullets_on_screen.remove(bullet)
                            #bullets_to_remove.append(bullet)
                            continue 
                        
                        #quadtree.insert(bullet)
                        bullet.light.main([],lights_display,bullet.center[0],bullet.center[1],render_scroll)
                        bullet.render(self.display,offset = render_scroll)

                        xx, yy = bullet.pos[0],bullet.pos[1]
                        r = max(bullet.size) * 3  # Adjust range radius for rectangular particles

                        rangeRect = Rectangle(Vector2(xx - r / 2, yy - r / 2), Vector2(r, r))
                        
                        nearby_entities = quadtree.queryRange(rangeRect)
                        for entity in nearby_entities:
                            
                            #if bullet != entity and entity.type != "bullet" and entity.state != 'death':
                                if  entity.state != 'death' and bullet.collide(entity) :
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
                bullet.render(self.display,offset=render_scroll)
                bullet.light.main([],lights_display,bullet.center[0],bullet.center[1],render_scroll)
                if kill: 
                    self.enemy_bullets.remove(bullet)

            for particle in self.particles.copy():
                if particle == None: 
                    self.particles.remove(particle)
                else:
                    kill =particle.update()
                    particle.render(self.display,offset = render_scroll)
                    if particle.type =='leaf':
                        particle.pos[0] += math.sin(particle.animation.frame * 0.035) * 0.3
                    if particle.source =='player' and particle.type[0:5] == 'smoke':
                        particle.pos = self.player.cur_weapon.opening_pos
                    if kill: 
                        self.particles.remove(particle)
            
    

            for i, particle in enumerate(self.physical_particles.copy()):
                    
                    kill = particle.update_pos(self.Tilemap,self.frame_count)
                    if kill: 
                        self.physical_particles.remove(particle)
                        continue 
                    if particle.life >= 17:
                        particle.light.main([],lights_display,particle.x,particle.y,render_scroll)
                    particle.render(self.bsurf,offset = render_scroll)

                    if i % 4 == 0:
                        xx, yy = particle.pos[0],particle.pos[1]
                        r = particle.r * 3 
                        
                        rangeCircle = Circle(Vector2(xx, yy), r)

                        nearby_entities = quadtree.queryRange(rangeCircle)

                        for entity in nearby_entities:
                            if  entity.state != 'death' and particle.collide(entity):
                                entity.hit(particle.damage)

                    
            self.display.blit(self.bsurf,(0,0))

            for particle in self.non_animated_particles.copy():
                if particle == None: 
                    self.non_animated_particles.remove(particle)
                else: 
                    kill = particle.update(self.dt)
                    particle.render(self.display,offset =render_scroll)
                    if kill:
                        self.non_animated_particles.remove(particle)

            for spark in self.sparks.copy():
                if spark == None: 
                    self.sparks.remove(spark)
                else: 
                    kill = spark.update()
                    spark.render(self.display,offset = render_scroll)
                    if kill:
                        self.sparks.remove(spark)

            self.player.update_pos(self.Tilemap,self.cursor.pos,self.frame_count,(self.player_cur_vel,0))
            
            self.player.render(self.display,render_scroll)

            #------------------------grass renderer stuff

            rot_function = lambda x, y: int(math.sin(self.rot_func_t / 60 + x / 100) * 7)

            self.gm.update_render(self.display,self.dt,offset=render_scroll,rot_function= rot_function)

            #----------------------------------


           #lighting ------------------

            
            for key in self.lights: 
                if  (key[0] >= render_scroll[0] - 200 and key[0] <= self.display.get_width() + render_scroll[0] + 200)  and (key[1] >= render_scroll[1] - 200 and key[1] <= self.display.get_height() + render_scroll[1]+ 200 ):
                    light = self.lights[key]

                    light.main([],lights_display,key[0],key[1],render_scroll)

            for light in self.temp_lights.copy():
                if light[1] != 0:
                    light[1] -= 1 
                    light[0].main([],lights_display,light[2][0],light[2][1],render_scroll) 
                else: 
                    self.temp_lights.remove(light)

            
            self.display.blit(lights_display,( 0, 0),special_flags= pygame.BLEND_RGB_MULT)

           

            
            #rapid fire and single fire toggle 
            if pygame.mouse.get_pressed()[0]:
                if self.inven_on and (self.HUD.inven_list[0].position[0] <= self.cursor.pos[0] <= self.HUD.inven_list[0].position[0] + self.HUD.inven_list[0].box_size[0]*2) and (self.HUD.inven_list[0].position[1] <= self.cursor.pos[1] <= self.HUD.inven_list[0].position[1] + self.HUD.inven_list[0].box_size[1]//4):
                    """
                    if self.main_offset == None : 
                        self.main_offset = (self.cursor.pos[0] - self.HUD.inven_list[0].position[0],self.cursor.pos[1] - self.HUD.inven_list[0].position[1])
                    
                    self.HUD.inven_list[0].position[0] = self.cursor.pos[0] - self.main_offset[0]
                    self.HUD.inven_list[0].position[1] = self.cursor.pos[1] - self.main_offset[1]
                    
                    """

                    #self.HUD.inven_list[0].position[0] -= offset[0]
                    #self.HUD.inven_list[0].position[1] -= offset[1]
                
                elif self.player.weapon_toggle_state():
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
             



            
            
            display_mask = pygame.mask.from_surface(self.display)
            display_sillhouette = display_mask.to_surface(setcolor=(0,0,0,180),unsetcolor=(0,0,0,0))

            for offset in [(-1,0),(1,0),(0,-1),(0,1)]:
                self.display_2.blit(display_sillhouette,offset)
           

           


           

           
            pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN, pygame.KEYUP])
            
                        
            for event in pygame.event.get():
                if event.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode((event.w,event.h),pygame.RESIZABLE) 

                #We need to define when the close button is pressed on the window. 
                
                if event.type == pygame.QUIT: 
                    #then pygame is closed, and the system is closed. 
                    pygame.quit() 
                    sys.exit() 

                if event.type == pygame.MOUSEWHEEL:
                    
                    self.player.change_weapon(event.y)
                    
                
                #define when the right or left arrow keys are pressed, the corresponding player's movement variable varlues are changed. 
                if event.type == pygame.KEYDOWN: 
                    if event.key == pygame.K_i:
                        self.inven_on = not self.inven_on

                    if event.key == pygame.K_a: 
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

                        
                        self.player_movement[0] = True

                    if event.key == pygame.K_d: 
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
                        self.player_movement[1] = True
                        
                    if event.key == pygame.K_w:
                        
                        self.player.player_jump() 
                    if event.key == pygame.K_s: 
                        self.player.slide = True 
                    if event.key == pygame.K_g: 
                        self.player.toggle_rapid_fire()

                        
                #define when the right or left arrow keys are then lifted, the corresponding player's movement variable values are changed back to false.
                if event.type == pygame.KEYUP: 
                    if event.key == pygame.K_w: 
                        self.player.jump_cut()
                    if event.key == pygame.K_a: 
                        self.player_movement[0] = False
                    if event.key == pygame.K_d:
                        self.player_movement[1] = False 
                    if event.key == pygame.K_s: 
                        self.player.slide =False 

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
            
            
            if self.inven_on:
                self.HUD.render_inven(self.cursor,self.display,(0,0))
            
            self.HUD.render(self.display,self.cursor,offset=(0,0))

            self.cursor.update(keys)
            self.cursor.render(self.display)

            self.display_2.blit(self.display,(0,0))
            self.rot_func_t += self.dt * 100
            
            screenshake_offset = (random.random()* self.screen_shake - self.screen_shake /2, random.random()* self.screen_shake - self.screen_shake /2)

            self.screen.blit(pygame.transform.scale(self.display_2,self.screen.get_size()),screenshake_offset)
            pygame.display.update()

            #self.dt = self.clock.tick(60) / 1000
            self.clock.tick(60)

myGame().run()