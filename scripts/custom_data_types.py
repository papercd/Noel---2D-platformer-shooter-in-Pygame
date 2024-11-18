from collections import namedtuple

TileInfo = namedtuple('TileInfo',['type','variant','tile_pos','atl_pos'])
LightInfo = namedtuple('LightInfo',['type','variant','tile_pos','radius','power','colorValue','atl_pos'])
AnimationData = namedtuple('AnimationData',['state','n_textures','img_dur','halt','loop'])
DoorInfo = namedtuple('DoorInfo', ['type','variant','tile_pos','size','atl_pos'])


class Animation: 
    """ Animation class to handle entities' animations update """
    def __init__(self,n_textures:int,img_dur:int=5,halt:bool = False,loop :bool =True):
        self._count = n_textures 
        self._loop= loop
        self._halt = halt
        self._img_dur = img_dur
        self.done = False 
        self.frame = 0


    def reset(self):
        self.frame = 0
        self.done = False
    
    def copy(self):
        return Animation(self._count,self._img_dur,self._halt,self._loop)
    
    def update(self):
        if self._halt: 
             self.frame = min(self.frame+1,self._img_dur * self._count -1)
        else: 
            if self._loop:
                self.frame = (self.frame+1) % (self._img_dur * self._count)
            else: 
                self.frame = min(self.frame+1,self._img_dur *self._count -1)
                if self.frame >= self._img_dur *self._count -1:
                    self.done = True 


    def curr_frame(self) -> int:
        """
        Returns the current frame of the animation. 
        """
        return int(self.frame/self._img_dur)


class DoorAnimation(Animation):
    """ Animation class for the special case for doors. """
    def __init__(self, n_textures, img_dur = 5):
        self.closed = False 
        super().__init__(n_textures, img_dur, True,False)

    def reset(self):
        self.frame = 0 if not self.closed else self._img_dur * self._count -1
        self.done = False 
    
    def open(self,is_open = False):
        self.closed = is_open
        self.frame = 0 if not self.closed else self._img_dur * self._count -1 

    def update(self):
        if not self.closed: 
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

