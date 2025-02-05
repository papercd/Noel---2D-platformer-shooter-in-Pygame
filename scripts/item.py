from scripts.data import ITEM_DESCRIPTIONS

class Item:
    def __init__(self,name,count = 1,stackable = True):
        self._name = name 
        self._type = "item"
        self._rarity = "common"
        self._stackable = stackable
        if not stackable: 
            self.count = 1
        else: 
            self.count = count

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
    def __init__(self, size, origin,name, count=1, stackable=False):
        super().__init__(name, count, stackable)
        self.magazine = 0
        self.size = size
        self.origin = origin 
        self._type = 'weapon'
        

    def copy(self):
        weapon = Weapon(self.name)
        weapon.magazine = self.magazine
        return weapon


class AK47(Weapon):
    def __init__(self):
        super().__init__((18,9),(2,2),'ak47', 1, False)

    def copy(self)->"AK47": 
        new_ak = AK47()
        new_ak.magazine = self.magazine
        return new_ak

class FlameThrower(Weapon):
    def __init__(self):
        super().__init__((24,8),(2,2),'flamethrower', 1, False) 

    def copy(self)->"FlameThrower":
        new_flamethrower = FlameThrower()
        new_flamethrower.magazine = self.magazine 
        return new_flamethrower
        