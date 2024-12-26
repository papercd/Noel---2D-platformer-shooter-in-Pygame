from collections import namedtuple

TileInfo = namedtuple('TileInfo',['type','variant','tile_pos','tile_size','atl_pos'])
LightInfo = namedtuple('LightInfo',['type','variant','tile_pos','tile_size','rect','radius','power','colorValue','atl_pos'])
AnimationData = namedtuple('AnimationData',['state','n_textures','img_dur','halt','loop'])
DoorInfo = namedtuple('DoorInfo', ['type','variant','tile_pos','tile_size','rect','atl_pos'])

SparkData = namedtuple('SparkData',['pos','decay_factor','angle','speed','scale','color','speed_factor'])
CollideParticleData = namedtuple('CollideParticleData',['size','pos','angle','speed','color','life','gravity_factor'])
FireParticleData = namedtuple('FireParticleData',['x','y','size','density','rise','rise_angle','spread','wind','damage'])
AnimationParticleData = namedtuple('AnimationParticleData',['type','pos','velocity','angle','flipped','source'])


TIME_FOR_ONE_LOGICAL_STEP= 0.016666666666

class Animation: 
    """ Animation class to handle entities' animations update """
    def __init__(self,n_textures:int,img_dur:int=5,halt:bool = False,loop :bool =True):
        self._count = n_textures 
        self._loop= loop
        self._halt = halt
        self._img_dur = img_dur
        self.done = False 
        self.accum_time = 0
        self.frame = 0

    def set_new_data(self,animation_data:AnimationData):
        self._count = animation_data.n_textures
        self._loop = animation_data.loop
        self._halt = animation_data.halt
        self._img_dur = animation_data.img_dur
        self.done = False 
        self.frame = 0

    def reset(self):
        self.frame = 0
        self.done = False
    
    def copy(self):
        return Animation(self._count,self._img_dur,self._halt,self._loop)
    
    def update(self,dt):
        dt = min(dt, 2 * TIME_FOR_ONE_LOGICAL_STEP)

        self.accum_time += dt 
        if self.accum_time >= TIME_FOR_ONE_LOGICAL_STEP: 
            if self._halt: 
                self.frame = min(self.frame+1,self._img_dur * self._count -1)
                if self.frame == self._img_dur * self._count -1 : self.done = True 
            else: 
                if self._loop:
                    self.frame = (self.frame+1) % (self._img_dur * self._count)
                else: 
                    self.frame = min(self.frame+1,self._img_dur *self._count -1)
                    if self.frame >= self._img_dur *self._count -1:
                        self.done = True 
            self.accum_time -= TIME_FOR_ONE_LOGICAL_STEP

    def curr_frame(self) -> int:
        """
        Returns the current frame of the animation. 
        """
        return int(self.frame/self._img_dur)


class DoorAnimation(Animation):
    """ Animation class for the special case for doors. """
    def __init__(self, n_textures, img_dur = 5):
        self.opened = False 
        super().__init__(n_textures, img_dur, True,False)

    def reset(self):
        self.frame = 0 if self.opened else self._img_dur * self._count -1
        self.done = False 
    
    def open(self,is_open = False):
        self.opened = is_open
        self.frame = 0 if self.opened else self._img_dur * self._count -1 

    def update(self):
        if self.opened: 
            self.frame = min(self.frame+1,self._img_dur * self._count -1)
            if self.frame == self._img_dur * self._count - 1 : self.done  = True 
        else: 
            self.frame = max(0,self.frame-1) 
            if self.frame == 0 : self.done = True 
    


class AnimationDataCollection:
    def __init__(self,animation_data :list[AnimationData]):
        self.animations = {}
        for animation_datum in animation_data:
            self.animations[animation_datum.state] = Animation(*animation_datum[1:])


    
    def get_animation_data(self,state:str) -> Animation:
        """
        Returns the animation that corresponds to the entity's state. 

        Args: 
            state (str) : the state of the entity that the animation belongs to. 

        """
        return self.animations[state]



""" Animation Data """

PLAYER_ANIMATION_DATA = [
    AnimationData('idle',4,6,False,True),
    AnimationData('crouch',1,4,True,False),
    AnimationData('jump_up',1,5,True,False),
    AnimationData('jump_down',4,5,True,False),
    AnimationData('land',6,2,False,False),
    AnimationData('run',6,4,False,True),
    AnimationData('slide',1,5,True,False),
    AnimationData('wall_slide',1,4,True,False),
    AnimationData('sprint',6,3,False,True)
]

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

PlayerAnimationDataCollection = AnimationDataCollection(PLAYER_ANIMATION_DATA)  


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


