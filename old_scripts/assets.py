import os 
import pygame 
from OpenGL.GL import glBlitNamedFramebuffer, GL_COLOR_BUFFER_BIT, GL_NEAREST, glGetUniformBlockIndex, glUniformBlockBinding
import numpy as np 
import moderngl
from scripts.utils import Animation
from scripts.background import Background

BASE_PATH = 'data/images/'
class GameAssets:
    def __init__(self,context):
        
        self.ctx =context 

        self.general_sprites = {}
        self.enemies = {}
        self.backgrounds = {}

        self.interactable_obj_sprites = {}
        self.load_assets()

    def _load_texture(self,path) -> moderngl.Texture:
        """
        load a texture from a path. 
        
        returns a moderngl.Texture 

        """ 
        img = pygame.image.load(BASE_PATH + path).convert_alpha()
        return self._surface_to_texture(img)
    
    def _load_textures(self,path):
        """
        load textures from a file.

        returns a list of moderngl.Textures 

        """
        textures = []

        for file_name in sorted(os.listdir(BASE_PATH+path)):
            textures.append(self._load_texture(path+'/' + file_name))
        return textures
    
    def _surface_to_texture(self,img : pygame.Surface)-> moderngl.Texture:
        """
        Convert a pygame.Surface to a moderngl.Texture.

        Args:
            sfc (pygame.Surface): Surface to convert.

        Returns:
            moderngl.Texture: Converted texture.
        """

        img_flip = pygame.transform.flip(img, False, True)
        img_data = pygame.image.tostring(img_flip, "RGBA")

        tex = self.ctx.texture(img.get_size(), components=4, data=img_data)
        tex.filter = (moderngl.NEAREST, moderngl.NEAREST)
        return tex

    def _load_animation_textures(self,animation_paths):
        return {
        key: Animation(self._load_textures(path), img_dur=dur, loop=loop, halt=halt)
        for key, (path, dur, loop, halt) in animation_paths.items()
        }
    
    def _load_textures_from_path_dict(self,paths):
        return {key: self._load_texture(path ) for key, (path) in paths.items()}


    def _load_textures_from_dict_multiple(self,paths):
        return {key: self._load_textures(path) for key, (path) in paths.items()}

    def _load_tile_textures(self,paths):
        return {path: self._retrieve_textures_from_path(f'tiles/{path}') for path in paths}


    def _retrieve_textures_from_path(self,path):
        list_of_lists = []
        for dir in sorted(os.listdir(BASE_PATH + path)):
            dir_check = dir.split('.')
            if len(dir_check) > 1:
                
                list_of_lists.append(self._load_texture(path +'/'+dir))
            else: 
                new_list = self._retrieve_textures_from_path(path +'/' + dir)
                list_of_lists.append(new_list)
        return list_of_lists


          

    def load_assets(self):
        self.general_sprites.update(self.load_grass_textures())
        self.general_sprites.update(self.load_building_textures())
        self.general_sprites.update(self.load_entity_textures())
        self.general_sprites.update(self.load_cursor_textures())
        self.general_sprites.update(self.load_cloud_textures())
        self.general_sprites.update(self.load_ui_textures())
        self.general_sprites.update(self.load_particle_textures())
        self.backgrounds.update(self.load_background_objects())
        self.enemies.update(self.load_enemy_textures())

        self.interactable_obj_sprites.update(self.load_interactable_textures())

    def load_grass_textures(self):
        return self._load_tile_textures(['grass', 'new_live_grass'] )

    def load_building_textures(self):
        building_paths = [
            'building_0', 'building_1', 'building_2', 'building_3', 'building_4',
            'building_5', 'building_back', 'building_decor', 'lights', 'building_stairs',
            'building_door_0','dungeon_back','trap_door'
        ]
        return self._load_tile_textures(building_paths)

    def load_entity_textures(self):
        player_animations = {
            'player/holding_gun/idle': ('entities/player/holding_gun/idle', 6, True, False),
            'player/holding_gun/run': ('entities/player/holding_gun/run',  4, True, False),
            'player/holding_gun/jump_up': ('entities/player/holding_gun/jump/up' , 5, True, False),
            'player/holding_gun/jump_down': ('entities/player/holding_gun/jump/down' , 5, True, True),
            'player/holding_gun/land': ('entities/player/holding_gun/land',  2, False, False),
            'player/holding_gun/slide': ('entities/player/slide',  5, True, False),
            'player/holding_gun/wall_slide': ('entities/player/wall_slide',  4, True, False),
            'player/holding_gun/walk': ('entities/player/holding_gun/walk',  7, True, False),
            'player/holding_gun/crouch': ('entities/player/holding_gun/crouch' , 4, True, False),
            
            'player/idle': ('entities/player/idle',  6, True, False),
            'player/run': ('entities/player/run', 4, True, False),
            'player/jump_up': ('entities/player/jump/up',  5, True, False),
            'player/jump_down': ('entities/player/jump/down' , 5, True, True),
            'player/land': ('entities/player/land',  2, False, False),
            'player/slide': ('entities/player/slide',  5, True, True),
            'player/wall_slide': ('entities/player/wall_slide',  4, True, False),
            'player/crouch': ('entities/player/crouch',  7, False, False),
            
        }
        return {
            'player': self._load_texture('entities/player.png'),
            **self._load_animation_textures(player_animations)
        }

    def load_cursor_textures(self):
        cursor_paths = {
            'cursor/default': ('cursor/default_cursor.png' ),
            'crosshair': ('cursor/crosshair.png'),
            "cursor": ("ui/inventory/cursor.png"),
            "grab": ("ui/inventory/cursor_grab.png"),
            "magnet": ("ui/inventory/cursor_magnet.png"),
            "move": ("ui/inventory/cursor_move.png"),
            "text": ("ui/inventory/cursor_text.png"),           # Added cursor text icon

            "rifle_crosshair": ("cursor/default_cursor.png"),

            
        }
        return self._load_textures_from_path_dict(cursor_paths)

    def load_cloud_textures(self):
        cloud_paths = {
            'clouds': ('clouds/default' ),
            'gray1_clouds': ('clouds/gray1' ),
            'gray2_clouds': ('clouds/gray2' ),
        }
        return self._load_textures_from_dict_multiple(cloud_paths)

    def load_ui_textures(self):
        ui_paths = {
            'health_UI': ('ui/health/0.png'),
            'stamina_UI': ('ui/stamina/0.png' ),
            'start_element' : ('ui/start_ui/start_element.png'),
            'start_logo' : ('ui/start_logo/logo.png'),
        }
        return self._load_textures_from_path_dict(ui_paths)

    def load_particle_textures(self):
        particle_animations_paths = {
            'particle/ball_slinger_attack': ('particles/attack/ball_slinger/normal',6,False,False),
            'particle/ball_slinger_attack_flipped': ('particles/attack/ball_slinger/flipped',6,False,False),
            'particle/box_destroy': ('particles/box' , 3, False, False),
            'particle/box_smoke': ('particles/box_break',  3, False, False),
            'particle/leaf': ('particles/leaf', 20, False, False),
            'particle/jump': ('particles/jump',  2, False, False),
            'particle/dash_left': ('particles/dash/left',  1, False, False),
            'particle/dash_right': ('particles/dash/right',  1, False, False),
            'particle/dash_air': ('particles/dash/air',  2, False, False),
            'particle/land': ('particles/land',  3, False, False),
            'particle/big_land': ('particles/big_land',  2, False, False),
            'particle/shot_muzzle/laser_weapon': ('particles/shot_muzzle/laser_weapon' , 3, False, False),
            'particle/smoke/ak_47': ('particles/shoot/rifle' , 3, False, False),
            'particle/smoke/rocket_launcher' : ('particles/shoot/rocket_launcher',1,False,False),
            'particle/smoke/rifle_small': ('particles/bullet_collide_smoke/rifle/small', 2, False, False),
            'particle/smoke/shotgun' : ('particles/shoot/shotgun', 3,False,False),
            'particle/smoke/laser_weapon': ('particles/shoot/laser_weapon' , 3, False, False),
            'particle/bullet_collide/laser_weapon': ('particles/bullet_collide/laser_weapon' , 2, False, False),
            'particle/bullet_collide/rifle': ('particles/bullet_collide/rifle',  2, False, False),
            'particle/rocket_launcher_smoke' : ('particles/rocket_launcher_smoke',2,False,False),
            'particle/rocket_launcher_collide' : ('particles/rocket_launcher_collide',1,False,False),
        }

        


        return self._load_animation_textures(particle_animations_paths)
    
    def load_background_objects(self):
        backgrounds = {
            'test_background': Background(self._load_textures('backgrounds/building')),
            'new_building' : Background(self._load_textures('backgrounds/new_building'))

        }
        return backgrounds
    
    def load_enemy_textures(self):
            enemy_animations_paths = {
            'Canine/black/idle': ('entities/enemy/Canine/black/idle' , 8, True,False),
            'Canine/black/run': ('entities/enemy/Canine/black/run',  6, True,False),
            'Canine/black/jump_up': ('entities/enemy/Canine/black/jump/up' , 1, False,False),
            'Canine/black/jump_down': ('entities/enemy/Canine/black/jump/down' , 3, False,False),
            'Canine/black/hit': ('entities/enemy/Canine/black/hit',  5, False,False),
            'Canine/black/grounded_death': ('entities/enemy/Canine/black/death/grounded' , 5, False,False),

            'Wheel_bot/idle': ('entities/enemy/Wheel_bot/idle' , 6, True,False),
            'Wheel_bot/move': ('entities/enemy/Wheel_bot/move' , 7, True,False),
            'Wheel_bot/dormant': ('entities/enemy/Wheel_bot/dormant' , 2, True,False),
            'Wheel_bot/alert': ('entities/enemy/Wheel_bot/alert',  4, False,False),
            'Wheel_bot/wake': ('entities/enemy/Wheel_bot/wake',  5, False,False),
            'Wheel_bot/new_charge': ('entities/enemy/Wheel_bot/new_charge' , 3, True,False),
            'Wheel_bot/shoot': ('entities/enemy/Wheel_bot/shoot',  4, False,False),
            'Wheel_bot/hit': ('entities/enemy/Wheel_bot/hit',  4, False,False),
            'Wheel_bot/death': ('entities/enemy/Wheel_bot/death' , 4, False,False),

            'sabre/idle': ('entities/enemy/sabre/idle',  6, True,False),
            'sabre/move': ('entities/enemy/sabre/move',  6, True,False),
            'sabre/dormant': ('entities/enemy/sabre/dormant' , 6, True,False),
            'sabre/wake': ('entities/enemy/sabre/wake',  5, False,False),


            'ball_slinger/idle' : ('entities/enemy/ball_slinger/idle',7,True,False),
            'ball_slinger/move' : ('entities/enemy/ball_slinger/move',6,True,False),
            'ball_slinger/transition' : ('entities/enemy/ball_slinger/transition',6,False,False),
            'ball_slinger/charge' : ('entities/enemy/ball_slinger/charge',6,False,False),
            'ball_slinger/attack' : ('entities/enemy/ball_slinger/attack',6,False,False),
            'ball_slinger/death' : ('entities/enemy/ball_slinger/death',6,False,False),

            'shotguner/idle' : ('entities/enemy/shotgunner/idle',7,True,False),
            'shotguner/move' : ('entities/enemy/shotgunner/move',6,True,False),
		#	'shotguner/shoot' : ('entities/enemy/shotgunner/shoot',6,False,False),
            'shotguner/attack' : ('entities/enemy/shotgunner/attack',6,False,False),
         #   'shotguner/death' : ('entities/enemy/shotgunner/death',6,False,False),
            }
            return self._load_animation_textures(enemy_animations_paths)
    
    # Animation
    def load_interactable_textures(self):
            interactable_animations_paths = {
                 'building_door_0' : ('interactables/building_door/0',5, True,False),
                 'trap_door' : ('interactables/trap_door',5,True,False),

            }
            return self._load_animation_textures(interactable_animations_paths)