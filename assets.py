from scripts.utils import *

class GameAssets:
    def __init__(self):
        self.general_sprites = {}
        self.enemies = {}

        self.interactable_obj_sprites = {}
        self.load_assets()

    def load_assets(self):
        self.general_sprites.update(self.load_grass_assets())
        self.general_sprites.update(self.load_building_assets())
        self.general_sprites.update(self.load_entity_assets())
        self.general_sprites.update(self.load_cursor_assets())
        self.general_sprites.update(self.load_cloud_assets())
        self.general_sprites.update(self.load_ui_assets())
        self.general_sprites.update(self.load_particle_assets())
        self.enemies.update(self.load_enemy_assets())

        self.interactable_obj_sprites.update(self.load_interactable_assets())

    def load_grass_assets(self):
        return load_tile_assets(['grass', 'live_grass'], background='transparent')

    def load_building_assets(self):
        building_paths = [
            'building_0', 'building_1', 'building_2', 'building_3', 'building_4',
            'building_5', 'building_back', 'building_decor', 'lights', 'building_stairs',
            'building_door_0','dungeon_back','trap_door'
        ]
        return load_tile_assets(building_paths, background='transparent')

    def load_entity_assets(self):
        player_animations = {
            'player/holding_gun/idle': ('entities/player/holding_gun/idle', 'transparent', 6, True, False),
            'player/holding_gun/run': ('entities/player/holding_gun/run', 'transparent', 4, True, False),
            'player/holding_gun/jump_up': ('entities/player/holding_gun/jump/up', 'transparent', 5, True, False),
            'player/holding_gun/jump_down': ('entities/player/holding_gun/jump/down', 'transparent', 5, True, True),
            'player/holding_gun/land': ('entities/player/holding_gun/land', 'transparent', 2, False, False),
            'player/holding_gun/slide': ('entities/player/slide', 'transparent', 5, True, False),
            'player/holding_gun/wall_slide': ('entities/player/wall_slide', 'transparent', 4, True, False),
            'player/holding_gun/walk': ('entities/player/holding_gun/walk', 'transparent', 7, True, False),
            'player/holding_gun/crouch': ('entities/player/holding_gun/crouch', 'transparent', 4, True, False),
            
            'player/idle': ('entities/player/idle', 'transparent', 6, True, False),
            'player/run': ('entities/player/run', 'transparent', 4, True, False),
            'player/jump_up': ('entities/player/jump/up', 'transparent', 5, True, False),
            'player/jump_down': ('entities/player/jump/down', 'transparent', 5, True, True),
            'player/land': ('entities/player/land', 'transparent', 2, False, False),
            'player/slide': ('entities/player/slide', 'transparent', 5, True, True),
            'player/wall_slide': ('entities/player/wall_slide', 'transparent', 4, True, False),
            'player/crouch': ('entities/player/crouch', 'transparent', 7, False, False),
            
        }
        return {
            'player': load_image('entities/player.png'),
            **load_animation_assets(player_animations)
        }

    def load_cursor_assets(self):
        cursor_paths = {
            'cursor/default': ('cursor/default_cursor.png', 'black'),
            'crosshair': ('cursor/crosshair.png', 'black')
        }
        return load_image_assets(cursor_paths)

    def load_cloud_assets(self):
        cloud_paths = {
            'clouds': ('clouds/default', 'transparent'),
            'gray1_clouds': ('clouds/gray1', 'transparent'),
            'gray2_clouds': ('clouds/gray2', 'transparent'),
        }
        return load_image_assets_multiple(cloud_paths)

    def load_ui_assets(self):
        ui_paths = {
            'health_UI': ('ui/health/0.png', 'transparent'),
            'stamina_UI': ('ui/stamina/0.png', 'transparent'),
            'start_element' : ('ui/start_ui/start_element.png','transparent'),
            'start_logo' : ('ui/start_logo/logo.png','transparent'),
        }
        return load_image_assets(ui_paths)

    def load_particle_assets(self):
        particle_animations = {
            'particle/ball_slinger_attack': ('particles/attack/ball_slinger/normal','transparent',6,False,False),
            'particle/ball_slinger_attack_flipped': ('particles/attack/ball_slinger/flipped','transparent',6,False,False),
            'particle/box_destroy': ('particles/box', 'transparent', 3, False, False),
            'particle/box_smoke': ('particles/box_break', 'black', 3, False, False),
            'particle/leaf': ('particles/leaf', 'black', 20, False, False),
            'particle/jump': ('particles/jump', 'black', 2, False, False),
            'particle/dash_left': ('particles/dash/left', 'black', 1, False, False),
            'particle/dash_right': ('particles/dash/right', 'black', 1, False, False),
            'particle/dash_air': ('particles/dash/air', 'black', 2, False, False),
            'particle/land': ('particles/land', 'transparent', 3, False, False),
            'particle/big_land': ('particles/big_land', 'transparent', 2, False, False),
            'particle/shot_muzzle/laser_weapon': ('particles/shot_muzzle/laser_weapon', 'transparent', 3, False, False),
            'particle/smoke/ak_47': ('particles/shoot/rifle', 'transparent', 3, False, False),
            'particle/smoke/rocket_launcher' : ('particles/shoot/rocket_launcher','transparent',1,False,False),
            'particle/smoke/rifle_small': ('particles/bullet_collide_smoke/rifle/small', 'black', 2, False, False),
            'particle/smoke/shotgun' : ('particles/shoot/shotgun', 'transparent',3,False,False),
            'particle/smoke/laser_weapon': ('particles/shoot/laser_weapon', 'transparent', 3, False, False),
            'particle/bullet_collide/laser_weapon': ('particles/bullet_collide/laser_weapon', 'transparent', 2, False, False),
            'particle/bullet_collide/rifle': ('particles/bullet_collide/rifle', 'transparent', 2, False, False),
            'particle/rocket_launcher_smoke' : ('particles/rocket_launcher_smoke','transparent',2,False,False),
            'particle/rocket_launcher_collide' : ('particles/rocket_launcher_collide','transparent',1,False,False),
        }

        


        return load_animation_assets(particle_animations)
    
    def load_enemy_assets(self):
            enemy_animations = {
            'Canine/black/idle': ('entities/enemy/Canine/black/idle', 'transparent', 8, True,False),
            'Canine/black/run': ('entities/enemy/Canine/black/run', 'transparent', 6, True,False),
            'Canine/black/jump_up': ('entities/enemy/Canine/black/jump/up', 'transparent', 1, False,False),
            'Canine/black/jump_down': ('entities/enemy/Canine/black/jump/down', 'transparent', 3, False,False),
            'Canine/black/hit': ('entities/enemy/Canine/black/hit', 'transparent', 5, False,False),
            'Canine/black/grounded_death': ('entities/enemy/Canine/black/death/grounded', 'transparent', 5, False,False),

            'Wheel_bot/idle': ('entities/enemy/Wheel_bot/idle', 'transparent', 6, True,False),
            'Wheel_bot/move': ('entities/enemy/Wheel_bot/move', 'transparent', 7, True,False),
            'Wheel_bot/dormant': ('entities/enemy/Wheel_bot/dormant', 'transparent', 2, True,False),
            'Wheel_bot/alert': ('entities/enemy/Wheel_bot/alert', 'transparent', 4, False,False),
            'Wheel_bot/wake': ('entities/enemy/Wheel_bot/wake', 'transparent', 5, False,False),
            'Wheel_bot/new_charge': ('entities/enemy/Wheel_bot/new_charge', 'transparent', 3, True,False),
            'Wheel_bot/shoot': ('entities/enemy/Wheel_bot/shoot', 'transparent', 4, False,False),
            'Wheel_bot/hit': ('entities/enemy/Wheel_bot/hit', 'transparent', 4, False,False),
            'Wheel_bot/death': ('entities/enemy/Wheel_bot/death', 'transparent', 4, False,False),

            'sabre/idle': ('entities/enemy/sabre/idle', 'transparent', 6, True,False),
            'sabre/move': ('entities/enemy/sabre/move', 'transparent', 6, True,False),
            'sabre/dormant': ('entities/enemy/sabre/dormant', 'transparent', 6, True,False),
            'sabre/wake': ('entities/enemy/sabre/wake', 'transparent', 5, False,False),


            'ball_slinger/idle' : ('entities/enemy/ball_slinger/idle','transparent',7,True,False),
            'ball_slinger/move' : ('entities/enemy/ball_slinger/move','transparent',6,True,False),
            'ball_slinger/transition' : ('entities/enemy/ball_slinger/transition','transparent',6,False,False),
            'ball_slinger/charge' : ('entities/enemy/ball_slinger/charge','transparent',6,False,False),
            'ball_slinger/attack' : ('entities/enemy/ball_slinger/attack','transparent',6,False,False),
            'ball_slinger/death' : ('entities/enemy/ball_slinger/death','transparent',6,False,False),

            'shotguner/idle' : ('entities/enemy/shotgunner/idle','transparent',7,True,False),
            'shotguner/move' : ('entities/enemy/shotgunner/move','transparent',6,True,False),
		#	'shotguner/shoot' : ('entities/enemy/shotgunner/shoot','transparent',6,False,False),
            'shotguner/attack' : ('entities/enemy/shotgunner/attack','transparent',6,False,False),
         #   'shotguner/death' : ('entities/enemy/shotgunner/death','transparent',6,False,False),

            
            
            
            

            
            }
            return load_animation_assets(enemy_animations)
    
    # Animation
    def load_interactable_assets(self):
            interactable_animations = {
                 'building_door_0' : ('interactables/building_door/0','transparent',5, True,False),
                 'trap_door' : ('interactables/trap_door','transparent',5,True,False),

            }
            return load_animation_assets(interactable_animations)