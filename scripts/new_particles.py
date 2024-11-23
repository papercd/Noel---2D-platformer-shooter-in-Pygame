

class PhysicalParticle: 
    def __init__(self,size,pos:list[int,int],angle:float,speed,color,life = 60,gravity_factor =1):
        self._size = size 
        self._pos = pos
        self._angle  =angle 
        self._speed = speed
        self._life = life 
        self._gravity_factor = gravity_factor

        