from scripts.new_entities import Player,AKBullet
from my_pygame_light2d.light import PointLight
from math import atan2,degrees,cos,sin,radians
from scripts.custom_data_types import AnimationParticleData,CollideParticleData
from typing import TYPE_CHECKING
from random import randint,random,choice

TIME_FOR_LOGICAL_FRAME = 0.015969276428222656


if TYPE_CHECKING:
    from scripts.new_particles import ParticleSystem
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

MUZZLE_PARTICLE_COLORS = {
    'ak47' : ((238,208,88),(117,116,115),(30,30,30))
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
        self._knockback = [0,0]

        self._opening_pos = [0,0]
        self._smoke_pos = [0,0]
        self._pivot,self._pivot_to_opening_offset = WPNS_PIVOT_N_PIVOT_TO_OPENING_OFFSET[self._name]

        self._holder = None
        self.magazine = 0 
        self.target_pos= None
        self.rapid_fire_toggled = False 
        self.shot = False
        self.accum_time = 0
    @property 
    def angle_opening(self):
        return self._angle_opening

    @property
    def size(self)->tuple[int,int]:
        return self._size

    @property
    def opening_pos(self):
        return self._opening_pos

    @property 
    def knockback(self):
        return self._knockback
    
    @property
    def pivot(self):
        return self._pivot
    
    @property
    def flipped(self)-> bool: 
        return self._flipped

    def copy(self):
        new_weapon = Weapon(self._name,self._fire_rate,self._damage)
        new_weapon.magazine = self.magazine
        return new_weapon

    def toggle_rapid_fire(self):
        if self._can_RF:
            self._rapid_fire_toggled = not self._rapid_fire_toggled
            self.accum_time = 0

    def update(self,target_pos,holder_entity,camera_scroll,dt):
        self.accum_time += min(dt, 2 * TIME_FOR_LOGICAL_FRAME)
        self.accum_time = min(self.accum_time, (self._fire_rate+1) * TIME_FOR_LOGICAL_FRAME)

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

        rotation_offset = (cos(radians(-self._angle_opening)) * self._size[0],sin(radians(-self._angle_opening)) * self._size[0])

        self._opening_pos[0] = holder_entity.pos[0]+pivot[0] + self._pivot_to_opening_offset[0] + rotation_offset[0]
        self._opening_pos[1] = holder_entity.pos[1]+ pivot[1] + self._pivot_to_opening_offset[1] + rotation_offset[1]
        self._smoke_pos[0] = self._opening_pos[0] - rotation_offset[0] //4
        self._smoke_pos[1] = self._opening_pos[1] - rotation_offset[1] //4


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
    
    def _create_light(self,pos,power,radius,color,life,cast_shadows = False,illuminator = None)->PointLight: 
        light = PointLight(pos, power=power, radius=radius, life=life, illuminator=illuminator)
        light.set_color(*color)
        light.cast_shadows = cast_shadows
        return light

    def reset_shot(self)->None: 
        self.shot = False 

    def shoot(self,engine_lights:list["PointLight"],em:"EntitiesManager",ps:"ParticleSystem")-> None:
        #TODO: change the frame count system to a dt-based system later, when integrating dt. 
        
        if self._rapid_fire_toggled: 
            if self.accum_time >= TIME_FOR_LOGICAL_FRAME * self._fire_rate: 
                self._emit_bullet(engine_lights,em,ps)
                self.accum_time -= TIME_FOR_LOGICAL_FRAME * self._fire_rate
        else: 
            if not self.shot :
                self._emit_bullet(engine_lights,em,ps)
                self.shot = True 
        


    def _emit_bullet(self,engine_lights:list["PointLight"],em:"EntitiesManager",ps:"ParticleSystem")->None: 
        vel = (cos(radians(-self._angle_opening))*self._knockback_power*1.5,sin(radians(-self._angle_opening))*self._knockback_power*1.5)
        bullet  = AKBullet(self._opening_pos.copy(),self._damage,-self._angle_opening,vel)
        bullet.adjust_pos((vel[0]/2+bullet.size[0]//2,vel[1]/2+bullet.size[1]//2))
        flip = vel[0] <=0
        bullet.adjust_flip(flip)
        
        engine_lights.append(self._create_light(self._opening_pos, 1.0, 8, (253, 108, 50), 2))
        engine_lights.append(self._create_light(self._opening_pos, 0.7, 24, (248, 129, 153), 2))
        engine_lights.append(self._create_light(self._opening_pos, 0.6, 40, (248, 129, 153), 2))
        engine_lights.append(self._create_light(self._opening_pos, 1.0, 20, (255, 255, 255), bullet._time_flown, illuminator=bullet))


        particle_data = AnimationParticleData('ak47_smoke',self._smoke_pos,[0,0],-self._angle_opening,flip,'weapon')
        ps.add_particle(particle_data)
        for _ in range(randint(6,13)):
            speed_factor = random()
            randomize_angle = randint(-30,30)
            color = choice(MUZZLE_PARTICLE_COLORS['ak47'])
            life = randint(1,8)


            particle_data = CollideParticleData((1,1),self._smoke_pos.copy(),-(self._angle_opening + randomize_angle),\
                                                5*speed_factor,color,life,1) 
            ps.add_particle(particle_data)

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