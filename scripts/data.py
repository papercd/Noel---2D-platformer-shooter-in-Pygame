from collections import namedtuple
from dataclasses import dataclass 
from typing import NamedTuple
from my_pygame_light2d.light import PointLight
from pygame.rect import Rect
from numpy import int16, int32,uint8, uint16 ,uint32,float32,array



RGBA_tuple = namedtuple('RGBA_tuple',['r','g','b','a'])
TileTexcoordsKey = namedtuple('TileTexcoordsKey',['type','relative_pos_ind','variant'])
TileColorKey = namedtuple('TileColorKey',['type','relative_pos_ind','variant','side'])
#TileInfo = namedtuple('TileInfo',['type','relative_pos_ind','variant','tile_pos','tile_size','atl_pos'])
#LightInfo = namedtuple('LightInfo',['type','relative_pos_ind','variant','tile_pos','tile_size','rect','radius','power','colorValue','atl_pos'])
AnimationData = namedtuple('AnimationData',['state','n_textures','img_dur','halt','loop'])
DoorInfo = namedtuple('DoorInfo', ['type','relative_pos_ind','variant','tile_pos','tile_size','rect','atl_pos'])

SparkData = namedtuple('SparkData',['pos','decay_factor','angle','speed','scale','color','speed_factor'])
CollideParticleData = namedtuple('CollideParticleData',['size','pos','angle','speed','color','life','gravity_factor'])
FireParticleData = namedtuple('FireParticleData',['x','y','size','density','rise','rise_angle','spread','wind','damage'])
AnimationParticleData = namedtuple('AnimationParticleData',['type','pos','velocity','angle','flipped','source'])



class TileInfo(NamedTuple):
    type: str 
    relative_pos_ind : uint16 
    variant : uint16 
    tile_pos : tuple[int32,int32]
    tile_size : tuple[int32,int32]
    atl_pos : tuple[uint32,uint32]

class LightInfo(NamedTuple):
    type : str 
    relative_pos_ind: uint16
    variant: uint16 
    tile_pos : tuple[int32,int32]
    tile_size : tuple[int32,int32]
    rect : Rect
    radius: float
    power: float 
    colorValue : tuple[int,int,int,int]
    atl_pos : tuple[uint32,uint32]

"""

namedtuple data types:

RGBA_tuple 
TileTexcoordsKey 
TileColorKey 
TileInfo  - 'type' : str , 'relative_pos_ind' : uint16 , 'variant' : uint16 , 'tile_pos': tuple[int32,int32], 'tile_size': tuple[int32,int32], 'atl_pos' :tuple[uint32,uint32]
LightInfo 
AnimationData 
DoorInfo 

SparkData 
CollideParticleData 
FireParticleData 
AnimationParticleData 

"""


TEXTURE_BASE_PATH = 'data/images/'
BYTES_PER_TEXTURE_QUAD = 48 
BYTES_PER_POSITION_VEC2 = 8 
PHYSICS_TIMESTEP = float32(1/60)


class Animation: 
    """ Animation class to handle entities' animations update """
    def __init__(self,n_textures:uint16,img_dur:uint16=5,halt:bool = False,loop :bool =True):
        self._n_textures:uint16 = n_textures
        self._img_dur:uint16 = img_dur
        self._halt:bool = halt
        self._loop:bool = loop

        self.finished:bool= False
        self.accum_time = array([0],dtype=float32)
        self.frame= array([0],dtype=uint16)

    @property 
    def n_textures(self)->uint16:
        return self._n_textures

    def set_new_data(self,animation_data:AnimationData):
        self._n_textures = animation_data.n_textures
        self._img_dur = animation_data.img_dur
        self._halt = animation_data.halt
        self._loop = animation_data.loop

        self.finished = False
        self.accum_time[0] = float(0)
        self.frame[0] = uint16(0)

    def reset(self):
        self.frame[0] = uint16(0)
        self.finished= False
    
    def copy(self):
        return Animation(self._n_textures,self._img_dur,self._halt,self._loop)
    
    def update(self,dt:float32):

        dt = min(dt, 2 * PHYSICS_TIMESTEP)

        self.accum_time[0] += dt 
        if self.accum_time >= PHYSICS_TIMESTEP: 
            if self._halt: 
                self.frame[0] = min(self.frame[0]+uint16(1),self._img_dur * self._n_textures-uint16(1))
                if self.frame[0] == self._img_dur * self._n_textures-uint16(1) : self.finished= True 
            else: 
                if self._loop:
                    self.frame[0] = (self.frame[0]+uint16(1)) % (self._img_dur * self._n_textures)
                else: 
                    self.frame[0] = min(self.frame[0]+uint16(1),self._img_dur *self._n_textures-uint16(1))
                    if self.frame[0] >= self._img_dur *self._n_textures-uint16(1):
                        self.finished= True 
            self.accum_time -= PHYSICS_TIMESTEP


    def curr_frame(self) -> uint16:
        return self.frame[0]//self._img_dur


class DoorAnimation(Animation):
    """ Animation class for the special case for doors. """
    def __init__(self, n_textures, img_dur = 5):
        self.opened = False 
        super().__init__(n_textures, img_dur, True,False)

    def reset(self):
        self.frame = 0 if self.opened else self._img_dur * self._n_textures-1
        self.finished= False 
    
    def open(self,is_open = False):
        self.opened = is_open
        self.frame = 0 if self.opened else self._img_dur * self._n_textures-1 

    def update(self):
        if self.opened: 
            self.frame = min(self.frame+1,self._img_dur * self._n_textures-1)
            if self.frame == self._img_dur * self._n_textures- 1 : self.finished= True 
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
SPRINT_FACTOR = float32(1.4)
WALL_SLIDE_CAP_VELOCITY = 1 * 60 
GRAVITY = 35 * 60   # 20 pixels per second squared
TERMINAL_VELOCITY = float32(10 * 60)     # 20 pixels per second
HORIZONTAL_DECELERATION = int32(35 * 60)    #15 pixels per second squared

ENTITIES_ACCELERATION = {
    'player' : int32(70 * 60) 
}

ENTITIES_JUMP_SPEED = {
    'player' : 350
}

ENTITIES_MAX_HORIZONTAL_SPEED = {
    'player' : int32(240)
}




ENTITY_ANIMATION_DATA = {
    'player' : (
    AnimationData('idle',uint16(4),uint16(6),False,True),
    AnimationData('crouch',uint16(1),uint16(4),True,False),
    AnimationData('jump_up',uint16(1),uint16(5),True,False),
    AnimationData('jump_down',uint16(4),uint16(5),True,False),
    AnimationData('land',uint16(6),uint16(2),False,False),
    AnimationData('run',uint16(6),uint16(4),False,True),
    AnimationData('slide',uint16(1),uint16(5),True,False),
    AnimationData('wall_slide',uint16(1),uint16(4),True,False),
    AnimationData('sprint',uint16(6),uint16(3),False,True)
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
    "building_0" : (uint32(0),uint32(0)),
    'building_1' : (uint32(0),uint32(160)),
    'trap_door' : (uint32(48),uint32(208)),
    'building_2' : (uint32(0),uint32(320)),
    'building_3' : (uint32(0),uint32(384)),
    'building_4' : (uint32(0),uint32(448)),
    'building_5' : (uint32(0),uint32(528)),
    'building_door' : (uint32(48),uint32(256)),
    'dungeon_back' : (uint32(0),uint32(656)),
    'building_stairs': (uint32(48),uint32(0)),
    'building_back': (uint32(48),uint32(80)),
    'spawners' : (uint32(80),uint32(0)),
    'lights':(uint32(128),uint32(0)),
    'grass' : (uint32(0),uint32(816))
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
    'ak47': {"normal": ((uint32(0),uint32(0)),(uint32(31),uint32(12))),"holding":((uint32(56),uint32(0)),(uint32(18),uint32(9)))},
    'flamethrower': {"normal": ((uint32(0),uint32(12)),(uint32(32),uint32(9))),"holding":((uint32(57),uint32(12)),(uint32(24),uint32(8)))}
}

UI_WEAPON_ATLAS_POSITIONS_AND_SIZES = {
    'ak47' : ((384,92),(31,12)),
    'flamethrower' : ((416,92),(31,12))
}

ITEM_ATLAS_POSITIONS_AND_SIZES={
  "ak47" : ((uint32(0),uint32(0)),(uint32(31),uint32(12))),
  "rocket_launcher" : ((uint32(21),uint32(21)), (uint32(32), uint32(9))),
  "shotgun" : ((uint32(0),uint32(12)), (uint32(32), uint32(9)))
}

"""
  "amethyst_arrow": ((uint32(381),uint32(0)),(uint32(16),uint32(16))),
    "amethyst_clump" : ((uint32(397),uint32(0)),(uint32(16),uint32(16))),
    "arrow": ((uint32(413),uint32(0)),(uint32(16),uint32(16))),
    "string":((uint32(429),uint32(0)),(uint32(16),uint32(16)))
"""

UI_ATLAS_POSITIONS_AND_SIZES = {
    "health_bar" : ((uint32(0),uint32(0)),(uint32(204),uint32(8))),
    "stamina_bar" : ((uint32(0),uint32(0)),(uint32(204),uint32(8))),
    "item_slot" : {True:((uint32(20),uint32(8)),(uint32(24),uint32(24))),False:((uint32(0),uint32(8)),(uint32(20),uint32(20)))},
    "weapon_slot" : {True:((uint32(82),uint32(9)),(uint32(45),uint32(24))),False:((uint32(44),uint32(9)),(uint32(38),uint32(18)))},
    "background" : ((uint32(204),uint32(0)),(uint32(176),uint32(93))),
    "cursor" : {
        "default" : ((uint32(0),uint32(32)),(uint32(9),uint32(10))),
        "grab" :  ((uint32(9),uint32(32)),(uint32(9),uint32(10))),
        "magnet" :  ((uint32(18),uint32(32)),(uint32(9),uint32(10))),
        "move" :  ((uint32(27),uint32(32)),(uint32(9),uint32(10))),
        "crosshair" :  ((uint32(36),uint32(32)),(uint32(10),uint32(10)))
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
                "idle": (uint32(0),uint32(0)),
                "crouch" : (uint32(0),uint32(16)),
                "jump_up": (uint32(0),uint32(32)),
                "jump_down": (uint32(0),uint32(48)),
                "land": (uint32(0),uint32(80)),
                "run": (uint32(0),uint32(96)),
                "slide": (uint32(0),uint32(112)),
                "wall_slide": (uint32(0),uint32(128)),
                "sprint": (uint32(0),uint32(144))

                },
                True: {
                "idle": (uint32(96),uint32(0)),
                "crouch" : (uint32(96),uint32(16)),
                "jump_up": (uint32(96),uint32(32)),
                "jump_down": (uint32(96),uint32(48)),
                "land": (uint32(96),uint32(80)),
                "run": (uint32(96),uint32(96)),
                "slide": (uint32(96),uint32(112)),
                "wall_slide": (uint32(96),uint32(128)),
                "sprint": (uint32(96),uint32(144))
                }                        
                },  
}
     
"""
"ak47": (0,0),
"rocket_launcher": (0,0),
"shotgun" : (0,0)
"""


ENTITY_SIZES = {
    "player" : (uint32(16),uint32(16)),
    "items":{
        "ak47" : (uint32(16),uint32(5)),
        "rocket_launcher" : (uint32(16),uint32(5)),
        "shotgun" : (uint32(16),uint32(5))
    }
}

IRREGULAR_TILE_SIZES = {
    "spawners": (int32(48),int32(32)),
    "building_door": (int32(18),int32(32))

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


PLAYER_LEFT_AND_RIGHT_ANCHOR_OFFSETS = {

    True: {"idle": {False: (-6,-2), True: (5,-2)}, "walk": {False: (-6,-2), True: (5,-2)},'run' :{False: (-7,-2), True: (0,-3)} 
            ,'jump_up' :{False: (-6,-3), True: (1,-4)},'jump_down' :{False: (-5,-3), True: (2,-4)}
            ,'slide' :{ False : (3,1) ,True: (3,1)} , 'wall_slide' : {False: (-4,-3), True: (0,-3)},'land' :{ False : (-6,-2) ,True: (0,-3)} , 
            'crouch' :{ False : (-6,0) ,True: (5,0)},'sprint': {False : (-6,-2),True:(-1,-3)}
            },
    False: {"idle": {False: (-6,-2), True: (5,-2)},"walk": {False: (-6,-2), True: (5,-2)}, 'run' :{False: (-1,-3), True: (6,-2)} 
            ,'jump_up' :{False: (-2,-4), True: (7,-3)},'jump_down' :{False: (-2,-4), True: (6,-3)}
            ,'slide' :{ False: (-4,1), True: (-4,1) }, 'wall_slide': {False : (-1,-3), True : (3,-3)},'land' :{ False : (-2,-3) ,True: (5,-2)} ,
            'crouch' :{ False : (-6,0) ,True: (6,0)},'sprint' : {False: (-1,-3), True: (5,-2)} 
    }
}


"""  Grass Data  """

GRASS_ASSET_ATLAS_POS_AND_INFO = {
  

    "test_grass" : ((8,6,6,6,3,6),(11,26),(153,46,17))
}




"""  Tile Data """

PHYSICS_APPLIED_TILE_TYPES = {'grass','stone','box','building_0','building_1','building_2','building_3','building_4','building_5','building_stairs','building_door','trap_door',\
                              'ladder'}

LIGHT_POSITION_OFFSET_FROM_TOPLEFT= (7,3)
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

    'grass' : {
        0: ((1,0),(0,1)),
        1: ((1,0),(0,1),(-1,0)),
        2: ((-1,0),(0,1)),
        3: ((-1,0),(0,1),(0,-1)),
        4: ((-1,0),(0,-1)),
        5: ((1,0),(0,-1),(-1,0)),
        6: ((1,0),(0,-1)),
        7: ((1,0),(0,1),(0,-1)),
        8: ((1,0),(-1,0),(0,1),(0,-1)),
    }
 
}



"""  HUD positioning numbers  """

INVENTORY_CELL_EXPANSION_RATIO = 1/16

SPACE_BETWEEN_INVENTORY_ELEMENTS = uint32(5)
SPACE_BETWEEN_INVENTORY_CELLS = uint32(10)
ITEM_TRUE_DIMENSIONS = (16,16)
TEXT_TRUE_DIMENSIONS = (16,16)

HEALTH_BAR_TRUE_DIMENSIONS = (1,1)
STAMINA_BAR_TRUE_DIMENSIONS = (1,1)

TRUE_RES_TO_HEALTH_BAR_WIDTH_RATIO = float32(1/3)
TRUE_RES_TO_STAMINA_BAR_WIDTH_RATIO =  float32(1 / 4)

TRUE_RES_TO_HEALTH_STAMINA_BAR_HEIGHT_RATIO = float32(1.2/40)
TRUE_RES_TO_HEALTH_BAR_TOPLEFT_RATIO = (float32(1/12),float32(9/10))
TRUE_RES_TO_WEAPON_INVEN_DIM_RATIO = (float32(5/12),float32(1/12))
TRUE_RES_TO_OPAQUE_ITEM_INVEN_DIM_RATIO = (float32(5/12),float32(1/12))
TRUE_RES_TO_HIDDEN_ITEM_INVEN_DIM_RATIO = (float32(5/12),float32(1/12))
TRUE_RES_TO_CURRENT_WEAPON_DISPLAY_DIM_RATIO = (float32(1/7),float32(1/12))



""" MANDELAE hud positioning numbers """

TRUE_RES_TO_HEALTH_BAR_TOPLEFT_RATIO_MANDELAE = (float32(8/16),float32(8/10))
TRUE_RES_TO_STAMINA_BAR_TOPLEFT_RATIO_MANDELAE = (float32(8/16),float32(8.3/10))

TRUE_RES_TO_HEALTH_BAR_WIDTH_RATIO_MANDELAE = float32(1/5)
TRUE_RES_TO_STAMINA_BAR_WIDTH_RATIO_MANDELAE =  float32(1/6)

TRUE_RES_TO_WEAPON_DISPLAY_TOPLEFT_RATIO_MANDELAE = (float32(13/32),float32(16/20))
TRUE_RES_TO_WEAPON_DISPLAY_DIM_RATIO_MANDELAE = (float32(2/32),float32(1/20))

TRUE_RES_TO_HEALTH_STAMINA_BAR_HEIGHT_RATIO_MANDELAE = float32(1/44)

""" MANDELAE data """
HEALTH_BAR_FULL_COLOR = array([72,12,12,255],dtype = int16)
HEALTH_BAR_DEPLETED_COLOR = array([116,81,81,255],dtype = int16)

ENERGY_BAR_FULL_COLOR = array([14,45,55,255],dtype = int16) 
ENERGY_BAR_DEPLETED_COLOR = array([61,99,126,255],dtype = int16) 

CURSOR_ENERGY_INITIAL_EXPENDITURE_RATE = float32(40)
CURSOR_ENERGY_RECHARGE_RATE = float32(10)