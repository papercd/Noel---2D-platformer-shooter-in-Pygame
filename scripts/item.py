from scripts.new_entities import Player
from math import atan2,degrees

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
    "ak47" : ((2,2),(0,0))
}

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
        
        self._pivot,self._pivot_to_opening_offset = WPNS_PIVOT_N_PIVOT_TO_OPENING_OFFSET[self._name]

        self.cursor_pos = None
        self._holder = None
        self.magazine = 0 

    def copy(self):
        new_weapon = Weapon(self._name,self._fire_rate,self._damage)
        new_weapon.magazine = self.magazine
        return new_weapon

    def toggle_rapid_fire(self):
        if self._can_RF:
            self._rapid_fire_toggled = not self._rapid_fire_toggled

    def update(self,cursor_pos,holder_entity,camera_scroll):
        self.cursor_pos = cursor_pos
        dx,dy = (self.cursor_pos[0]+camera_scroll[0] - (holder_entity.pos[0]+self._pivot[0] + self._pivot_to_opening_offset[0]),\
                 self.cursor_pos[1] +camera_scroll[1]- (holder_entity.pos[1]+self._pivot[1] + self._pivot_to_opening_offset[1]))
        self._angle_opening = atan2(-dy,dx)
        print(degrees(self._angle_opening))

        if 90 < self._angle_opening <= 180   or -180 <= self._angle_opening  <-90 : 
            self._flipped = True
        else: 
            self._flipped = False

        

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