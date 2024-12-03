ITEM_DESCRIPTIONS = {
    "amethyst_arrow" : "Arrow made with dirty amethyst."
}

WPNS_WITH_RF = {
    "ak47"
}

WPNS_PIVOT_N_PIVOT_TO_OPENING_OFFSET ={
    "ak47" : ((2,2),(0,0))
}

class Item:
    def __init__(self,name,count = 1,stackable = True):
        self._name = name 
        self._type = "item"
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
    def __init__(self, name , fire_rate:int, damage:int):
        super().__init__(name, 1, stackable = False) 
        self._type = "weapon"
        self._fire_rate = fire_rate
        self._damage = damage 

        self._angle_opening = 0
        self._flipped = False
        self._can_RF = self._name in WPNS_WITH_RF
        self._rapid_fire_toggled = False 
        self._knockback = [0,0]

        self._holder = None
        self.magazine = 0 

    def copy(self):
        new_weapon = Weapon(self._name,self._fire_rate,self._damage)
        new_weapon.magazine = self.magazine
        return new_weapon

    def toggle_rapid_fire(self):
        if self._can_RF:
            self._rapid_fire_toggled = not self._rapid_fire_toggled

    def equip(self,holder_entity):
        self._holder = holder_entity

    def shoot(self):
        pass 

    

class AK47(Weapon):
    def __init__(self):
        super().__init__()

class Flamethrower(Weapon):
    def __init__(self):
        super().__init__()


class Shotgun(Weapon):
    def __init__(self):
        super().__init__()


class RocketLauncher(Weapon):
    def __init__(self):
        super().__init__()    