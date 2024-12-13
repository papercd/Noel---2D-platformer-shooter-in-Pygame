from scripts.new_entities import Player,AKBullet
from my_pygame_light2d.light import PointLight
from math import atan2,degrees,cos,sin,radians
from scripts.entitiesManager import EntitiesManager

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
    def __init__(self, name , fire_rate:int, damage:int ,knock_back:int, size: tuple[int,int]):
        super().__init__(name, 1, stackable = False) 
        self._type = "weapon"
        self._fire_rate = fire_rate
        self._damage = damage 
        self._knockback_power =knock_back 

        self._size = size

        self._angle_opening = 0
        self._flipped = False
        self._can_RF = self._name in WPNS_WITH_RF
        self._rapid_fire_toggled = False 
        self._knockback = [0,0]

        self._opening_pos = [0,0]
        self._pivot,self._pivot_to_opening_offset = WPNS_PIVOT_N_PIVOT_TO_OPENING_OFFSET[self._name]

        self.target_pos= None
        self._holder = None
        self.magazine = 0 

    def copy(self):
        new_weapon = Weapon(self._name,self._fire_rate,self._damage)
        new_weapon.magazine = self.magazine
        return new_weapon

    def toggle_rapid_fire(self):
        if self._can_RF:
            self._rapid_fire_toggled = not self._rapid_fire_toggled

    def update(self,target_pos,holder_entity,camera_scroll):
        if self._knockback[0] < 0: 
            self._knockback[0] = min(self._knockback[0] + 1.45, 0)
        if self._knockback[0] > 0 :
            self._knockback[0] = max(self._knockback[0] -1.45, 0)

        if self._knockback[1] < 0: 
            self._knockback[1] = min(self._knockback[1] + 1.45, 0)
        if self._knockback[1] > 0 :
            self._knockback[1] = max(self._knockback[1] -1.45, 0)

        self.target_pos=target_pos 
        # first decide on which side the cursor is on 
        if self.target_pos[0] < holder_entity.pos[0]+ holder_entity._sprite_size[0]//2 - camera_scroll[0]:
            self._flipped = True
            pivot = (holder_entity.right_anchor[0] -1, holder_entity.right_anchor[1])
        else: 
            self._flipped = False
            pivot = holder_entity.left_anchor
        
        dx,dy = (self.target_pos[0] +camera_scroll[0] - (holder_entity.pos[0]+pivot[0] + self._pivot_to_opening_offset[0]),\
                 self.target_pos[1] +camera_scroll[1]-  (holder_entity.pos[1]+pivot[1] + self._pivot_to_opening_offset[1]))
        
        self._angle_opening = degrees(atan2(-dy,dx))

        self._opening_pos[0] = holder_entity.pos[0]+pivot[0] + self._pivot_to_opening_offset[0] + cos(radians(-self._angle_opening)) * self._size[0] 
        self._opening_pos[1] = holder_entity.pos[1]+ pivot[1] + self._pivot_to_opening_offset[1] + sin(radians(-self._angle_opening)) * self._size[1] 

        if isinstance(holder_entity,Player):
            if holder_entity.state == 'slide' or holder_entity.state == 'wall_slide':
                self._flipped = holder_entity.flip 

    def shoot(self):
        pass
    

class AK47(Weapon):
    def __init__(self):
        super().__init__('ak47',5,15,12,(18,9))
        self._rapid_fire_toggled = True 
        
    def copy(self):
        new_weapon = AK47()
        new_weapon.magazine = self.magazine
        return new_weapon
    

    def shoot(self,render_engine):
        # create a new bullet, make a system of some kind handle bullet update. 
        em = EntitiesManager.get_instance()
        vel = (cos(radians(-self._angle_opening))*self._knockback_power,sin(radians(-self._angle_opening))*self._knockback_power)
        bullet  = AKBullet(self._opening_pos.copy(),self._damage,-self._angle_opening,vel)
        bullet.pos[0] -= bullet.size[0] //2 
        bullet.pos[1] -= bullet.size[1] //2 

        bullet._center[0] -= bullet.size[0] //2
        bullet._center[1] -= bullet.size[1] //2 
        
        light =  PointLight(self._opening_pos,power = 1.0,radius = 8,life = 2)
        light.set_color(253,108,50)
        light.cast_shadows = False
        render_engine.lights.append(light)
        
        light = PointLight(self._opening_pos,power = 0.7 ,radius = 24,life = 2)
        light.set_color(248,129,153)
        light.cast_shadows = False
        render_engine.lights.append(light)

        light = PointLight(self._opening_pos,power = 0.6,radius = 40,life = 2)
        light.set_color(248,129,153)
        light.cast_shadows = False
        render_engine.lights.append(light)





        em.add_bullet(bullet)
        self._knockback = [-vel[0]/2,-vel[1]/2]

class Flamethrower(Weapon):
    def __init__(self):
        super().__init__('flamethrower',5,30,4,(24,8))

    def copy(self):
        new_weapon = Flamethrower()
        new_weapon.magazine = self.magazine
        return new_weapon

class Shotgun(Weapon):
    def __init__(self):
        super().__init__()


class RocketLauncher(Weapon):
    def __init__(self):
        super().__init__()    