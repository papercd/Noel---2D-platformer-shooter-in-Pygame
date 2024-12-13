TILE_ATLAS_POSITIONS ={
    "building_0" : (0,0),
    'building_1' : (0,160),
    'trap_door' : (48,208),
    'building_2' : (0,320),
    'building_3' : (0,384),
    'building_4' : (0,448),
    'building_5' : (0,528),
    'building_door' : (48,256),
    'dungeon_back' : (0,656),
    'building_stairs': (48,0),
    'building_back': (48,80),
    'spawners' : (80,0),
    'lights':(128,0)
}


TEXT_ATLAS_POSITIONS_AND_SPACE_AND_SIZES = {
    "CAPITAL" : ((0,140),(32,32),(32,32)),
    "LOWER": ((0,108), (32,32),(32,32)),
    "NUMBERS" : ((0,172),(32,32),(32,32))
}


IN_WORLD_WEAPON_ATLAS_POSITIONS_AND_SIZES = {
    'ak47': {"normal": ((0,0),(31,12)),"holding":((56,0),(18,9))},
    'flamethrower': {"normal": ((0,12),(32,9)),"holding":((57,12),(24,8))}
}

UI_WEAPON_ATLAS_POSITIONS_AND_SIZES = {
    'ak47' : ((384,92),(31,12)),
    'flamethrower' : ((415,92),(32,11))
}

ITEM_ATLAS_POSITIONS_AND_SIZES={
    "amethyst_arrow": ((381,0),(16,16)),
    "amethyst_clump" : ((397,0),(16,16)),
    "arrow": ((413,0),(16,16)),
    "string":((429,0),(16,16))

}

"""
 "amethyst_arrow": (381,0),
    "amethyst_clump" : (397,0),
    "arrow": (413,0),
    "string": (429,0)
"""

UI_ATLAS_POSITIONS_AND_SIZES = {
    "health_bar" : ((0,0),(204,8)),
    "stamina_bar" : ((0,0),(204,8)),
    "item_slot" : {True:((20,8),(24,24)),False:((0,8),(20,20))},
    "weapon_slot" : {True:((82,9),(45,24)),False:((44,9),(38,18))},
    "background" : ((204,0),(176,93)),
    "cursor" : {
        "default" : ((0,32),(9,10)),
        "grab" :  ((9,32),(9,10)),
        "magnet" :  ((18,32),(9,10)),
        "move" :  ((27,32),(9,10)),
        "crosshair" :  ((36,32),(10,10))
    }
}

PARTICLE_ATLAS_POSITIONS_AND_SIZES ={
    "jump" : ((0,0),(30,15)),
    "land" : ((0,15),(48,11)),
    "big_land" :((0,26),(60,20))
}


ENTITIES_ATLAS_POSITIONS ={
    "player" : {False:{
                "idle": (0,0),
                "crouch" : (0,16),
                "jump_up": (0,32),
                "jump_down": (0,48),
                "land": (0,80),
                "run": (0,96),
                "slide": (0,112),
                "wall_slide": (0,128),
                "sprint": (0,144)

                },
                True: {
                "idle": (96,0),
                "crouch" : (96,16),
                "jump_up": (96,32),
                "jump_down": (96,48),
                "land": (96,80),
                "run": (96,96),
                "slide": (96,112),
                "wall_slide": (96,128),
                "sprint": (96,144)
                }                        
                } 

}

IRREGULAR_TILE_SIZES = {
    "spawners": (48,32),
    "building_door": (18,32)

}

