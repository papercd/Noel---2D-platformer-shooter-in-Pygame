from collections import namedtuple

TileInfo = namedtuple('TileInfo',['type','variant','tile_pos','tile_size','atl_pos'])
LightInfo = namedtuple('LightInfo',['type','variant','tile_pos','tile_size','rect','radius','power','colorValue','atl_pos'])
AnimationData = namedtuple('AnimationData',['state','n_textures','img_dur','halt','loop'])
DoorInfo = namedtuple('DoorInfo', ['type','variant','tile_pos','tile_size','rect','atl_pos'])

SparkData = namedtuple('SparkData',['pos','decay_factor','angle','speed','scale','color','speed_factor'])
CollideParticleData = namedtuple('CollideParticleData',['size','pos','angle','speed','color','life','gravity_factor'])
FireParticleData = namedtuple('FireParticleData',['x','y','size','density','rise','rise_angle','spread','wind','damage'])
AnimationParticleData = namedtuple('AnimationParticleData',['type','pos','velocity','angle','flipped','source'])

SPARK_COLORS = ((253,128,70),(244,160,86) ,(189,84,55))

TIME_FOR_ONE_LOGICAL_FRAME = 0.015969276428222656
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
        dt = min(dt, 2 * TIME_FOR_ONE_LOGICAL_FRAME)

        self.accum_time += dt 
        if self.accum_time >= TIME_FOR_ONE_LOGICAL_FRAME: 
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
            self.accum_time -= TIME_FOR_ONE_LOGICAL_FRAME 

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

