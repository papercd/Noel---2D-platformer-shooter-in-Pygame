from collections import namedtuple
from dataclasses import dataclass 
from my_pygame_light2d.light import PointLight


RGBA_tuple = namedtuple('RGBA_tuple',['r','g','b','a'])
TileTexcoordsKey = namedtuple('TileTexcoordsKey',['type','relative_pos_ind','variant'])
TileColorKey = namedtuple('TileColorKey',['type','relative_pos_ind','variant','side'])
TileInfo = namedtuple('TileInfo',['type','relative_pos_ind','variant','tile_pos','tile_size','atl_pos'])
LightInfo = namedtuple('LightInfo',['type','relative_pos_ind','variant','tile_pos','tile_size','rect','radius','power','colorValue','atl_pos'])
AnimationData = namedtuple('AnimationData',['state','n_textures','img_dur','halt','loop'])
DoorInfo = namedtuple('DoorInfo', ['type','relative_pos_ind','variant','tile_pos','tile_size','rect','atl_pos'])

SparkData = namedtuple('SparkData',['pos','decay_factor','angle','speed','scale','color','speed_factor'])
CollideParticleData = namedtuple('CollideParticleData',['size','pos','angle','speed','color','life','gravity_factor'])
FireParticleData = namedtuple('FireParticleData',['x','y','size','density','rise','rise_angle','spread','wind','damage'])
AnimationParticleData = namedtuple('AnimationParticleData',['type','pos','velocity','angle','flipped','source'])


TEXTURE_BASE_PATH = 'data/images/'
TIME_FOR_ONE_LOGICAL_STEP= 1/60


class Animation: 
    """ Animation class to handle entities' animations update """
    def __init__(self,n_textures:int,img_dur:int=5,halt:bool = False,loop :bool =True):
        self._loop= loop
        self._halt = halt
        self._img_dur = img_dur
        self.finished = False 
        self.accum_time = 0
        self.frame = 0
        self.count = n_textures 

    def set_new_data(self,animation_data:AnimationData):
        self._loop = animation_data.loop
        self._halt = animation_data.halt
        self._img_dur = animation_data.img_dur
        self.finished= False 
        self.frame = 0
        self.count = animation_data.n_textures

    def reset(self):
        self.frame = 0
        self.finished= False
    
    def copy(self):
        return Animation(self.count,self._img_dur,self._halt,self._loop)
    
    def update(self,dt):

        dt = min(dt, 2 * TIME_FOR_ONE_LOGICAL_STEP)

        self.accum_time += dt 
        if self.accum_time >= TIME_FOR_ONE_LOGICAL_STEP: 
            if self._halt: 
                self.frame = min(self.frame+1,self._img_dur * self.count -1)
                if self.frame == self._img_dur * self.count -1 : self.finished= True 
            else: 
                if self._loop:
                    self.frame = (self.frame+1) % (self._img_dur * self.count)
                else: 
                    self.frame = min(self.frame+1,self._img_dur *self.count -1)
                    if self.frame >= self._img_dur *self.count -1:
                        self.finished= True 
            self.accum_time -= TIME_FOR_ONE_LOGICAL_STEP


    def curr_frame(self) -> int:
        return int(self.frame/self._img_dur)


class DoorAnimation(Animation):
    """ Animation class for the special case for doors. """
    def __init__(self, n_textures, img_dur = 5):
        self.opened = False 
        super().__init__(n_textures, img_dur, True,False)

    def reset(self):
        self.frame = 0 if self.opened else self._img_dur * self.count -1
        self.finished= False 
    
    def open(self,is_open = False):
        self.opened = is_open
        self.frame = 0 if self.opened else self._img_dur * self.count -1 

    def update(self):
        if self.opened: 
            self.frame = min(self.frame+1,self._img_dur * self.count -1)
            if self.frame == self._img_dur * self.count - 1 : self.finished= True 
        else: 
            self.frame = max(0,self.frame-1) 
            if self.frame == 0 : self.finished= True 
    


@dataclass 
class TileInfoDataClass:
    info: namedtuple

@dataclass
class DoorTileInfoWithAnimation(TileInfoDataClass):
    info: DoorInfo
    animation: DoorAnimation 


@dataclass 
class TrapDoorTileInfoWithOpenState(TileInfoDataClass):
    info: DoorInfo
    open: bool 

@dataclass
class RegularTileInfo(TileInfoDataClass):
    info: TileInfo
    

@dataclass 
class LightTileInfo(TileInfoDataClass):
    info: LightInfo
    refPointLight : PointLight

class AnimationDataCollection:
    def __init__(self,animation_data :list[AnimationData]):
        self.animations = {}
        for animation_datum in animation_data:
            self.animations[animation_datum.state] = Animation(*animation_datum[1:])


    
    def get_animation(self,state:str) -> Animation:
        """
        Returns the animation that corresponds to the entity's state. 

        Args: 
            state (str) : the state of the entity that the animation belongs to. 

        """
        return self.animations[state]



""" Animation Data """
# physics updates are done every 1/60 seconds, the 60 is multiplied to the physics calculations 
# so the number in front of the * corresponds to the unit of distance in pixels.
SPRINT_FACTOR = 1.2
WALL_SLIDE_CAP_VELOCITY = 1 * 60 
GRAVITY = 35 * 60   # 20 pixels per second squared
TERMINAL_VELOCITY = 10 * 60     # 20 pixels per second
HORIZONTAL_DECELERATION = 35 * 60    #15 pixels per second squared
ENTITIES_ACCELERATION = {
    'player' : 70 * 60 
}

ENTITIES_JUMP_SPEED = {
    'player' : 350
}

ENTITIES_MAX_HORIZONTAL_SPEED = {
    'player' : 240
}




ENTITY_ANIMATION_DATA = {
    'player' : (
    AnimationData('idle',4,6,False,True),
    AnimationData('crouch',1,4,True,False),
    AnimationData('jump_up',1,5,True,False),
    AnimationData('jump_down',4,5,True,False),
    AnimationData('land',6,2,False,False),
    AnimationData('run',6,4,False,True),
    AnimationData('slide',1,5,True,False),
    AnimationData('wall_slide',1,4,True,False),
    AnimationData('sprint',6,3,False,True)
    )
}

PARTICLE_ANIMATION_DATA = {
    'jump': AnimationData('jump',9,2,True,False),
    'land': AnimationData('land',4,2,True,False),
    'big_land': AnimationData('big_land',11,2,True,False),
    'ak47_smoke':AnimationData('ak47_smoke',3,3,False,False)
}

PARTICLE_ANIMATION_PIVOTS = {
    'jump':(0,0),
    'land':(0,0),
    'big_land': (0,0),
    'ak47_smoke': (2,4)
}



"""  Texture Data  """


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

BULLET_ATLAS_POSITIONS_AND_SIZES = {
    'ak47' : ((0,0),(16,5)),
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
    "big_land" :((0,26),(60,20)),
    'ak47_smoke':((0,46),(16,9))
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

ENTITY_SIZES = {
    "player" : (16,16)
}

IRREGULAR_TILE_SIZES = {
    "spawners": (48,32),
    "building_door": (18,32)

}

""" Particle Data """

SPARK_COLORS = ((253,128,70),(244,160,86) ,(189,84,55))

MUZZLE_PARTICLE_COLORS = {
    'ak47' : ((238,208,88),(117,116,115),(30,30,30))
}



"""  Item Data  """


ITEM_DESCRIPTIONS = {
    "amethyst_arrow" : "Arrow made with dirty amethyst.",
    "amethyst_clump" : "",
    "arrow": "",
    "string": "",
    "ak47": "A powerful weapon that shoots bullets.",
    "flamethrower": "Does more damage to soft enemies."

}

ITEM_RARITY = {
    "common" : 0,
    "rare" : 1,
    "epic" : 2,
    "legendary" : 3
}

WPNS_WITH_RF = {
    "ak47"
}

WPNS_PIVOT_N_PIVOT_TO_OPENING_OFFSET ={
    "ak47" : ((2,2),(0,0)),
    'flamethrower' : ((2,2),(0,0))
}


"""  Grass Data  """

GRASS_ASSET_ATLAS_POS_AND_INFO = {
  

    "test_grass" : ((8,6,6,6,3,6),(11,26),(153,46,17))
}




"""  Tile Data """

PHYSICS_APPLIED_TILE_TYPES = {'grass','stone','box','building_0','building_1','building_2','building_3','building_4','building_5','building_stairs','building_door','trap_door',\
                              'ladder'}

HULL_OUTER_EDGE_OFFSET = 4 
HULL_AXIS_TO_OFFSET_EVEN_POS= [ ((0,2),(1,1)),((1,2),(-1,1)),((1,3),(-1,-1)),((0,3),(1,-1))]
HULL_AXIS_TO_OFFSET_ODD_POS = [(2,1),(1,-1),(3,-1),(0,1)]
OPEN_SIDE_OFFSET_TO_AXIS_NUM = {(1,0):1,(-1,0):0,(0,1):3,(0,-1):2}
TILE_COLOR_SAMPLE_POS_TO_DIM_RATIO= {
    'regular' :{
     "top": (0.5,1),
    "left": (0,0.5),
    "right": (1,0.5),
    "bottom": (0.5,0),
   
    },
    'door':
    {

    },
    'stairs': (0.5,0.3125)

    
}


TILE_NEIGHBOR_MAP = {
    "building_0" : 
    {
        0 : ((1,0),(0,1)),
        1 : ((1,0),(0,1),(-1,0)),
        2 : ((-1,0),(0,1)),
        3 : ((-1,0),(0,1),(0,-1)),
        4 : ((-1,0),(0,-1)),
        5 : ((1,0),(0,-1),(-1,0)),
        6 : ((1,0),(0,-1)),
        7 : ((1,0),(0,1),(0,-1)),
        8 : ((1,0),(-1,0),(0,1),(0,-1)),
    },

    'building_1': 
    {
        0: ((1,0),(0,1)),
        1: ((1,0),(0,1),(-1,0)),
        2: ((-1,0),(0,1)) ,
        3: ((-1,0),(0,-1),(0,1)),
        4: ((-1,0),(0,-1)),
        5: ((-1,0),(0,-1),(1,0)),
        6: ((1,0),(0,-1)),
        7: ((1,0),(0,-1),(0,1)),
        8: ((1,0),(-1,0),(0,1),(0,-1))
     },
     

    'building_2': {
        0: ((0,1)),
        1:((0,-1),(0,1)),
        2:((0,-1)),
     },
    
    'building_3' : {
        0:((1,0)),
        1:((-1,0),(1,0)),
        2:((-1,0)),
    },

    'building_4': {
        0: ((1,0),(0,1)),
        1:((-1,0),(0,1)),
        2:((0,-1),(-1,0)),
        3:((0,-1),(1,0)),
    },
 
}



"""  HUD positioning numbers  """

SPACE_BETWEEN_INVENTORY_ELEMENTS = 5

ITEM_TRUE_DIMENSIONS = (16,16)
TEXT_TRUE_DIMENSIONS = (16,16)

HEALTH_BAR_TRUE_DIMENSIONS = (1,1)
STAMINA_BAR_TRUE_DIMENSIONS = (1,1)

TRUE_RES_TO_HEALTH_BAR_WIDTH_RATIO = 1 / 3
TRUE_RES_TO_STAMINA_BAR_WIDTH_RATIO =  1 / 4

TRUE_RES_TO_HEALTH_STAMINA_BAR_HEIGHT_RATIO = 1 / 40

# closed items rows, cols (2,5)
# showing items rows, cols (1,5)
# weapon rows, cols (1,4)



