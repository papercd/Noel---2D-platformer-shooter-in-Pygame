from scripts.data import ITEM_DESCRIPTIONS

from numpy import uint16,uint32,int16,float64,array

class Item:
    def __init__(self,name,count:uint16 = uint16(1),stackable = True):
        self._name = name 
        self._type = "item"
        self._rarity = "common"
        self._stackable = stackable
        self.count = array([count],dtype = uint16)

    def copy(self):
        return Item(self.name,self.count,self._stackable)

    @property
    def stackable(self):
        return self._stackable

    @property 
    def type(self):
        return self._type 

    @property 
    def description(self):
        return ITEM_DESCRIPTIONS[self._name]

    @property 
    def name(self):
        return self._name


class Weapon(Item): 
    def __init__(self, size:tuple[uint16,uint16], origin_offset:tuple[int16,int16],
                 name:str, count:uint16 = uint16(1),fire_rate:array = array([0],dtype = float64),stackable=False):
        super().__init__(name, count, stackable)
        
        self.magazine = array(0,dtype = uint32)
        self._size = size
        self._type = 'weapon'
        self.origin_offset_from_center = origin_offset 
        self.fire_rate = fire_rate
        self.power = uint16(1)
        self.bullet_speed = uint32(1000)

    @property 
    def size(self): 
        return self._size

    def copy(self):
        weapon = Weapon(self.name)
        weapon.magazine[0] = self.magazine[0]
        return weapon


class AK47(Weapon):
    def __init__(self):
        super().__init__((uint16(18),uint16(9)),(int16(-7),int16(-2)),'ak47', uint16(1),array([1/12],dtype= float64) , False)

    def copy(self)->"AK47": 
        new_ak = AK47()
        new_ak.magazine = self.magazine
        return new_ak

class FlameThrower(Weapon):
    def __init__(self):
        super().__init__((uint16(24),uint16(8)),(int16(-10),int16(-2)),'flamethrower', uint16(1), False) 

    def copy(self)->"FlameThrower":
        new_flamethrower = FlameThrower()
        new_flamethrower.magazine = self.magazine 
        return new_flamethrower
        