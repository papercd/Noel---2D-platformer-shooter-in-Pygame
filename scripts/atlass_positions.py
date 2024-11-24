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

CURSOR_ATLAS_POSITIONS = {
    "default" : ((0,0),(9,10)),
    "grab" :  ((9,0),(9,10)),
    "magnet" :  ((18,0),(9,10)),
    "move" :  ((27,0),(9,10)),
    "crosshair" :  ((36,0),(10,10))
}

TEXT_DIMENSIONS = {
    "CAPITAL" : (6,7),
    "LOWER": (5,5),
    "UNDERSCORE" : (5,5),
    "NUMBERS" : (5,5)
    
}
TEXT_ATLAS_POSITIONS = {
    "CAPITAL" : (0,5),
    "LOWER" : (0,0),
    "UNDERSCORE" : (130,0),
    "NUMBERS":(0,12)

}

UI_ATLAS_POSITIONS = {
    "health_bar" : (0,0),
    "stamina_bar" : (0,0)
}

PARTICLE_ATLAS_POSITIONS_AND_SIZES ={
    "jump" : ((0,0),(30,15)),
    "land" : ((0,11),(48,11)),
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
                "wall_slide": (0,128)
                },
                True: {

                }                        
                } 

}

IRREGULAR_TILE_SIZES = {
    "spawners": (48,32),
    "building_door": (18,32)

}

