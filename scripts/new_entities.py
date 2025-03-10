from pygame import Rect
from scripts.data import AnimationParticleData,CollideParticleData,SPARK_COLORS,SparkData ,TIME_FOR_ONE_LOGICAL_STEP,PlayerAnimationDataCollection
from scripts.utils import get_rotated_vertices, SAT
from random import choice as random_choice,random,randint,choice
from my_pygame_light2d.light import PointLight 
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scripts.data import Animation,TileInfo
    from scripts.new_tilemap import Tilemap
    from scripts.new_particles import ParticleSystem
    from scripts.entitiesManager import EntitiesManager

class PhysicsEntity: 
    def __init__(self,type:str,pos:list[float,float],size:tuple[int,int]):

        self._type = type 
        self._size = size       
        self._on_ramp = False        
        self._collisions = {'up': False, 'down': False, 'left': False, 'right': False}
        self._state = ''
        self._flip = False

        self.velocity = [0, 0]
        self.anim_offset = (0, 0)
        self.set_state('idle')
        self.cut_movement_input = False
        self.frame_data = 1
        self.pos = pos

    @property
    def state(self)->str: 
        return self._state

    @property
    def size(self)->tuple[int,int]:
        return self._size

    @property 
    def type(self)->str: 
        return self._type

    def set_state(self,state:str)->None:
        if state != self._state: 
            self.frame_data = 0
            self._state= state 

    def _collision_rect(self) -> Rect:
        return Rect(*self.pos,*self.size)


    def collide(self,other:"PhysicsEntity"):
        return self._collision_rect().colliderect(other._collision_rect())
    

    def accelerate(self,dir,dt):
        pass
    

    def update(self,tilemap:"Tilemap",dt,anim_offset = (0,0))->None:
        self.frame_data += 1 
        self._collisions = {'up': False, 'down': False, 'left': False, 'right': False}


        if self.velocity[0] > 0:
            self._flip = False
        if self.velocity[0] < 0 :
            self._flip = True 


        scaled_dt = dt * 60 
        # gravity 
        gravity = 0.26
        
        self._on_ramp = 0
        self.velocity[1] = min(6, self.velocity[1] + gravity * scaled_dt)

        frame_movement = (self.velocity[0] *scaled_dt ,self.velocity[1] * scaled_dt) if not self.cut_movement_input else \
                            (self.velocity[0] *scaled_dt, self.velocity[1] *scaled_dt)
        self.pos[0] += frame_movement[0] if not self.cut_movement_input else 0 
        self_rect = self._collision_rect()
        for rect_tile in tilemap.phy_rects_around((self.pos[0] + anim_offset[0], self.pos[1] + anim_offset[1]),self.size):
            tile_type = rect_tile[1].type
            if self_rect.colliderect(rect_tile[0]) and tile_type.split('_')[1] != 'stairs':
                if tile_type.split('_')[1] == 'door':
                    if  rect_tile[1].open:
                        continue
                    else:

                        # if you close the door on youself (trap door and vertical door)
                        if rect_tile[1].trap: 
                            continue 
                        else: 
                            if frame_movement[0] > 0 :
                                self._collisions['right'] = True
                                
                                self_rect.right = rect_tile[0].left
                            elif frame_movement[0] < 0:
                                self._collisions['left'] = True
                                
                                self_rect.left = rect_tile[0].right
                            else: 
                                if self_rect.centerx -rect_tile[0].centerx <0:
                                    self._collisions['right'] = True
                                    self_rect.right = rect_tile[0].left
                                    
                                else:
                                    self._collisions['left'] = True 
                                    self_rect.left = rect_tile[0].right 
                                
                            self.pos[0] =self_rect.x - anim_offset[0]
                            
                else:

                    if frame_movement[0] > 0:
                        self._collisions['right'] = True
                        
                        self_rect.right = rect_tile[0].left
                    elif frame_movement[0] < 0:
                        self._collisions['left'] = True
                        
                        self_rect.left = rect_tile[0].right
                        
                    else: 
                        if self_rect.centerx -rect_tile[0].centerx <0:
                            self._collisions['right'] = True
                            self_rect.right = rect_tile[0].left
                            
                        else:
                            self._collisions['left'] = True 
                            self_rect.left = rect_tile[0].right 
                        
                    self.pos[0] =self_rect.x - anim_offset[0]
        
        self.pos[1] +=frame_movement[1] if self.velocity[1] <0 else frame_movement[1] * 1.2
        self_rect = self._collision_rect()
        for rect_tile in tilemap.phy_rects_around((self.pos[0] +anim_offset[0] ,self.pos[1] +anim_offset[1]), self.size):
            tile_type = rect_tile[1].type
            if tile_type == 'lights':
                continue
            if self_rect.colliderect(rect_tile[0]):
                if tile_type.split('_')[1] != 'stairs':
                    if tile_type.split('_')[1] == 'door' and  rect_tile[1].open:
                        continue 
                    

                    if frame_movement[1] > 0:
                        self._collisions['down'] = True
                        self.velocity[1] = gravity * scaled_dt 
                        self._on_ramp = 0
                        self_rect.bottom = rect_tile[0].top
                        
                    elif frame_movement[1] < 0:
                        self._collisions['up'] = True
                        self.velocity[1] = 0
                        self_rect.top = rect_tile[0].bottom
                    self.pos[1] = self_rect.y - anim_offset[1]
                else:
                    variant = rect_tile[1].variant.split(';')[0]
                    pos_height = 0
                    rel_x = rect_tile[0].x - self_rect.right if variant in ('0', '2') else rect_tile[0].right - self_rect.left

                    if variant == '0':
                        if -16 <= rel_x < 0:
                            pos_height = max(0, -rel_x - self.size[0] // 4)
                    elif variant == '2':
                        if rel_x < 0:
                            pos_height = min(tilemap.tile_size, -rel_x + (tilemap.tile_size- self.size[0] // 4))
                    elif variant == '1':
                        if rel_x > 0:
                            pos_height = max(0, rel_x - self.size[0] // 4)
                    elif variant == '3':
                        if 0 < rel_x <= tilemap.tile_size:
                            pos_height = min(tilemap.tile_size, rel_x + (tilemap.tile_size- self.size[0] // 4))

                    target_y = rect_tile[0].y +tilemap.tile_size- pos_height
                    if self_rect.bottom > target_y:
                        self._on_ramp = 1 if variant == '0' else -1
                        self_rect.bottom = target_y
                        self.pos[1] = self_rect.y -anim_offset[1]
                        self._collisions['down'] = True



class CollectableItem(PhysicsEntity):
    def __init__(self, item, pos, size,life = 200)->None:
        super().__init__("collectableItem", pos, size)
        self.item = item 
        self.life = life
        self.dead = False


    def _collision_rect(self):
        return Rect(self.pos[0]+self.size[0]//2,self.pos[1]+self.size[1]//2,
                    self.size[0],self.size[1])
    
    def update(self, tilemap, dt, anim_offset=(0, 0)):
        self.life -= dt * 60 
        if self.life <= 0: 
            self.dead = True 
        super().update(tilemap, dt, anim_offset)

        return self.dead
    
class Player(PhysicsEntity):
    def __init__(self, pos: list[float], size: tuple[int, int])->None:
        self._animation_data_collection = PlayerAnimationDataCollection
        self._cur_animation = self._animation_data_collection.get_animation_data('idle')
        super().__init__('player', pos, size)
        self._sprite_size = (16,16)
        self._accel_rate = 0
        self._default_speed = 0
        self._curr_speed = 0
        self._knockback_reduction_factor = (5,9)

        self.recov_rate = 0.6
        self.stamina = 100
        self.health = 200
        self.fatigued =False

        self.jump_count = 2
        self.wall_slide = False
        self.crouch = False 
        self.on_wall = self._collisions['left'] or self._collisions['right']
        self.air_time = 0
        self.on_ladder = False

        self.changing_done = False 
        self.change_weapon_inc = False 
        self.holding_gun = False 
        self.running = False 
        self.y_inertia = 0
        self.hard_land_recovery_time = 0

        self.cursor_pos = [0,0]
        self.curr_weapon_node = None

        self.left_and_right_anchors = {  True: {"idle": {"left": (2,6), "right": (13,6)}, "walk": {"left": (2,6), "right": (13,6)},'run' :{"left": (1,6), "right": (8,5)} 
                                           ,'jump_up' :{"left": (0,4), "right": (9,4)},'jump_down' :{"left": (3,5), "right": (10,4)}
                                           ,'slide' :{ "left" : (11,9) ,"right": (11,9)} , 'wall_slide' : {"left": (4,5), "right": (8,5)},'land' :{ "left" : (2,6) ,"right": (8,5)} , 
                                           'crouch' :{ "left" : (2,8) ,"right": (13,8)},'sprint' : {'left': (1,6),'right':(8,5)}
                                           },
                                    False: {"idle": {"left": (2,6), "right": (13,6)},"walk": {"left": (2,6), "right": (13,6)}, 'run' :{"left": (7,5), "right": (14,6)} 
                                           ,'jump_up' :{"left": (6,4), "right": (15,5)},'jump_down' :{"left": (5,4), "right": (12,5)}
                                           ,'slide' :{ "left": (4,9), "right": (4,9) }, 'wall_slide': {'left' : (7,5), 'right' : (11,5)},'land' :{ "left" : (6,5) ,"right": (13,6)} ,
                                           'crouch' :{ "left" : (2,8) ,"right": (14,8)},'sprint': {'left': (7,5),'right':(14,6)} 
                                           },
        }
        self.left_anchor = None 
        self.right_anchor = None
        

    @property
    def knockback_reduction_factor(self)->tuple[int,int]:
        return self._knockback_reduction_factor

    @property
    def sprite_size(self)->tuple[int,int]:
        return self._sprite_size

    @property 
    def flip(self)->bool: 
        return self._flip
    
    @property 
    def cur_animation(self)->"Animation": 
        return self._cur_animation


    def set_default_speed(self,speed):
        self._default_speed = speed
        self._curr_speed = speed

    def set_accel_rate(self,accel_rate):
        self._accel_rate = accel_rate

    def _collision_rect(self) -> Rect:
        return Rect(self.pos[0] +3, self.pos[1] + 1 ,10,15)


    def accelerate(self, direction, dt):
        max_speed = 1.3 * self._curr_speed
        acceleration = self._accel_rate * dt * 60

        # Gradual acceleration based on direction
        if direction > 0:  # Move right
            if self.velocity[0] < 0:  # Transition from leftward velocity
                self.velocity[0] += acceleration # Reduce transition step
            else:  # Normal rightward acceleration
                self.velocity[0] += acceleration
        elif direction < 0:  # Move left
            if self.velocity[0] > 0:  # Transition from rightward velocity
                self.velocity[0] -= acceleration   # Reduce transition step
            else:  # Normal leftward acceleration
                self.velocity[0] -= acceleration
        else:  # No input, apply deceleration
            if self.velocity[0] > 0:
                self.velocity[0] = max(0, self.velocity[0] - acceleration)  # Decelerate rightward
            elif self.velocity[0] < 0:
                self.velocity[0] = min(0, self.velocity[0] + acceleration)  # Decelerate leftward

        # Clamp velocity to maximum speed
        self.velocity[0] = max(-max_speed, min(max_speed, self.velocity[0]))

            
    
    def set_state(self,state):
        if state != self._state: 
            self._state = state
            self._cur_animation.reset()
            self._cur_animation = self._animation_data_collection.get_animation_data(state)
     

    def jump_cut(self):
        if not self.on_ladder: 
            if self.velocity[1] < 0: 
                if self.velocity[1] > -4.2:
                    if self.air_time >0 and self.air_time <= 7.2 * TIME_FOR_ONE_LOGICAL_STEP:
                        self.velocity[1] = -2.28
                    if self.air_time >7.2 * TIME_FOR_ONE_LOGICAL_STEP and self.air_time <=11 * TIME_FOR_ONE_LOGICAL_STEP:
                        self.velocity[1] = -2.0


    def jump(self,particle_system: "ParticleSystem"):
        WALL_JUMP_SPEED = 2.2
        JUMP_SPEED =4.4

        if self.wall_slide: 
                self.jump_count = 1
                
                if self._collisions['left']:
                    
                    self.velocity[0] =  WALL_JUMP_SPEED
                if self._collisions['right']:
                    
                    self.velocity[0] = -WALL_JUMP_SPEED
                
                self.velocity[1] = -JUMP_SPEED
                particle_data = AnimationParticleData('jump',[self.pos[0] + self.size[0]//2 ,self.pos[1]+self.size[1]],[0,0.1],0,False,'player')
                particle_system.add_particle(particle_data)

        if self.jump_count == 2:
            if self._state == 'jump_down':
                self.jump_count -=2

                self.velocity[1] = -JUMP_SPEED
                particle_data = AnimationParticleData('jump',[self.pos[0] + self.size[0]//2 ,self.pos[1]+self.size[1]],[0,0.1],0,False,'player')
                particle_system.add_particle(particle_data)

            else: 
                self.jump_count -=1

                self.velocity[1] = -JUMP_SPEED
            
        elif self.jump_count ==1: 
            self.jump_count -=1
            self.velocity[1] = -JUMP_SPEED

            particle_data = AnimationParticleData('jump',[self.pos[0] + self.size[0]//2 ,self.pos[1]+self.size[1]],[0,0.1],0,False,'player')
            particle_system.add_particle(particle_data)


    def toggle_rapid_fire(self)->None: 
        if self.curr_weapon_node and self.curr_weapon_node.weapon: 
            self.curr_weapon_node.weapon.toggle_rapid_fire()

    def prompt_weapon_reset(self)->None: 
        if self.curr_weapon_node and self.curr_weapon_node.weapon: 
            self.curr_weapon_node.weapon.reset_shot()

    def shoot_weapon(self,engine_lights:list["PointLight"],entities_manager:"EntitiesManager",\
                     particle_system:"ParticleSystem")->None: 
        if self.curr_weapon_node and self.curr_weapon_node.weapon: 
            weapon = self.curr_weapon_node.weapon
            weapon.shoot(engine_lights,entities_manager,particle_system)


    def update(self,tilemap:"Tilemap",particle_system:"ParticleSystem",cursor_pos,movement_input,camera_scroll,game_context,dt):
        self.accelerate(movement_input[1]- movement_input[0],dt)
        self._cur_animation.update(dt)
        self.cursor_pos = cursor_pos
        

        self._curr_speed = self._default_speed

        
        if self.fatigued: 
            self.recov_rate = 0.3
            self._curr_speed = self._default_speed * 0.8
            if self.stamina >= 80:
                self.fatigued = False 
        else: 
            self.recov_rate = 0.6
            if self.running: 
                if self.stamina >= 10:
                    #then you can run. 
                    if self.velocity[0]!= 0:
                        self.stamina -= 1.2 * dt
                        self._curr_speed = self._default_speed * 1.7
                else: 
                    self._curr_speed = self._default_speed * 0.8
                    self.fatigued = True 
            else: 
                if self.stamina < 10: 
                    self._curr_speed = self._default_speed * 0.8
                    self.fatigued = True 
        
        """
        if self.hard_land_recovery_time > 0 :
            self.velocity[0] *= (20 - self.hard_land_recovery_time)/20 
            self.velocity[1] *= (20 - self.hard_land_recovery_time)/20 
            self.hard_land_recovery_time -= dt
        """

        super().update(tilemap,dt*1.1,anim_offset= (3,1))
        self.left_anchor = self.left_and_right_anchors[self._flip][self._state]["left"]
        self.right_anchor = self.left_and_right_anchors[self._flip][self._state]["right"]

        """
        r = max(self.size) * 2

        rangeRect = Rectangle(Vector2(self.pos[0] - self.size[0]//2 - r /2 ,self.pos[1]  - r /2 ), Vector2(r,r))

        self.nearest_collectable_item = quadtree.queryRange(rangeRect,"item")
        """
        #every frame, the stamina is increased by 0.7


        self.stamina = min(100, self.stamina + self.recov_rate * dt)
        self.air_time +=dt 
        
        """
        self.changing_done = min(2,self.change_weapon_inc + self.changing_done)
        if self.changing_done == 2:
             
            self.change_weapon(self.change_scroll)
        """     
        if self.velocity[1] >0 :
            self.y_inertia +=  dt * 60
        else:
            self.y_inertia = 0

        self.cut_movement_input = False 


        if self._collisions['down']:
    
            if self.y_inertia > 10:

                self.set_state('land')


                entry_pos = (self._collision_rect().centerx,self._collision_rect().bottom)
                for offset in range(-tilemap.tile_size, tilemap.tile_size, 4):
                    if tilemap.solid_check((entry_pos[0]+offset,entry_pos[1])):
                        color = tilemap.get_at((entry_pos[0]+offset,entry_pos[1]),side ='top')



                offsets = [(-2,0),(-1,0), (0,0), (1,0),(2,0)]                
                for i in range(max(8,int(self.y_inertia)//2)):
                    offset = random_choice(offsets)
                    random_factor = random()
                    particle_data = CollideParticleData((1,1), [entry_pos[0] - offset[0],entry_pos[1] - 2] ,\
                                                        -90 + randint(-88,88), 2.4+random_factor,color,life= 40 + 20 * random_factor , gravity_factor= 1)
                    particle_system.add_particle(particle_data)
        


            if self.y_inertia > 25 and self.y_inertia <50:
                particle_data = AnimationParticleData('land',[self.pos[0] +8,self.pos[1]+14],velocity=[0,0],angle=0,flipped=False,source='player')
                particle_system.add_particle(particle_data)
                self.hard_land_recovery_time = 7 *TIME_FOR_ONE_LOGICAL_STEP 
                game_context['screen_shake'] = max(game_context['screen_shake'],7)
                #self.set_state('land')
                
                
            elif self.y_inertia >= 50:
                particle_data = AnimationParticleData('big_land',[self.pos[0] +7,self.pos[1]+7],velocity=[0,0],angle=0,flipped=False,source='player')
                particle_system.add_particle(particle_data)
                self.hard_land_recovery_time = 20 *TIME_FOR_ONE_LOGICAL_STEP 
                game_context['screen_shake'] = max(game_context['screen_shake'],16)
            self.jump_count =2 
            self.air_time = 0
            
            
        self.wall_slide = False
        self.on_wall = self._collisions['left'] or self._collisions['right']

        if self.on_wall and self.air_time > 4 * TIME_FOR_ONE_LOGICAL_STEP:
            self.wall_slide = True 
            self.velocity[1] = min(self.velocity[1],0.5)
            if self._collisions['right']:
                self._flip = False
            else:
                self._flip = True 
            
            self.set_state('wall_slide')
            self.y_inertia = 0
       
        if not self.wall_slide: 
            if self.air_time > 4 * TIME_FOR_ONE_LOGICAL_STEP:
                self.boost_on_next_tap = False 
                if self.velocity[1] < 0:
                    self.y_inertia = 0
                    self.set_state('jump_up')
                elif self.velocity[1] >0 :
                    self.set_state('jump_down')
               
            elif self.velocity[0]!= 0:
                if self._state == 'land':
                    if self._cur_animation.done == True: 
                        if self.fatigued: 
                            self.set_state('walk')
                        else: 
                            if self.running: 
                                self.set_state('sprint')
                            else: 
                                self.set_state('run')
                else: 
                   
                    if self.fatigued: 
                        self.set_state('walk')
                    else: 
                        if self.running: 
                            cur_frame = None
                            if self._state == 'run':
                                cur_frame = self._cur_animation.frame 
                            self.set_state('sprint')
                            if cur_frame:
                                self._cur_animation.frame = (cur_frame -1) % self._cur_animation._count
                        else:    
                            cur_frame = None 
                            if self._state == 'sprint':
                                cur_frame = self._cur_animation.frame
                            self.set_state('run')
                            if cur_frame:
                                self._cur_animation.frame = (cur_frame - 1) % self._cur_animation._count
                    """
                    anim_frame = self.animation.frame / self.animation.img_dur
                    if anim_frame == 0 or anim_frame == 3:
                        self.game.player_sfx['run'][str(random.randint(0,7))].play()
                    """
                if self.crouch and movement_input[1] - movement_input[0] != 0:
                    self.cut_movement_input = True
                    self.set_state('slide')
                self.y_inertia = 0
                    
            else: 
                self.y_inertia = 0
                if self._state == 'land':
                    if self._cur_animation.done == True: 
                        self.set_state('idle') 
                else: 
                    if self.crouch: 
                        self.set_state('crouch')
                        pass 
                    else: 
                        self.set_state('idle')
        """
        print(self.state)
        print(self.air_time)
        print(self._collisions['down'])
        """
        # update the weapon

        if self.curr_weapon_node and self.curr_weapon_node.weapon: 

            self.holding_gun = True
            self.curr_weapon_node.weapon.update(self.cursor_pos,self,camera_scroll,dt)
        else: 
            self.holding_gun = False 
        
        #testing weapon rendering  
        """
        if self.cur_weapon_node:
            self.cur_weapon_node.update(self.d_cursor_pos)
        """
        """
        if self.cur_weapon_node:
            self.cur_weapon_node.weapon.update(self.d_cursor_pos)
        """


class Bullet(PhysicsEntity):
    def __init__(self,life:int,pos: list[float], size: tuple[int, int],angle:int):
        super().__init__('Bullet', pos, size)
        self._angle = angle
        self._life= life
        self._max_life = life 
        self.dead = False
        self.center = [self.pos[0]+self.size[0]//2,self.pos[1] +self.size[1]//2]
        self.interpolate_pos = True
    
    @property
    def angle(self): 
        return self._angle
    
    @property
    def flip(self)->bool:
        return self._flip

    def _create_collision_effects(self,tilemap:"Tilemap",rect_tile:tuple[Rect,"TileInfo"],ps:"ParticleSystem",engine_lights:list["PointLight"]): 
        if rect_tile[1].type == "lights":
            print("add light collision later")
        else: 
            num_sparks = randint(2,5)
            for i in range(num_sparks):
                speed = randint(1,3)
                angle = int(self.angle)
                angle =  randint(180-angle -30,180-angle +30)
                color = choice(SPARK_COLORS)         
                spark_data = SparkData(self.center.copy(),1.2,angle,speed,1.5,color,9)
                light = self._create_light()
                """
                light = PointLight()
                light.cast_shadows = False 
                engine_lights.append(light)
                """
                # pass light to particle system to bind spark object as illuminator for light 
                ps.add_particle(spark_data,light)
                engine_lights.append(light)

    def _create_light(self):
        light = PointLight(self.center.copy(),power = 1,radius = 5,life= 70)
        light.set_color(255,255,255)
        light.cast_shadows = False
        return light


    def adjust_pos(self,adjustment)->None: 
        self.pos[0] -= adjustment[0] 
        self.pos[1] -= adjustment[1]
        self.center[0] -= adjustment[0] 
        self.center[1] -= adjustment[1]

    def adjust_flip(self,adjustment:bool) ->None: 
        self._flip = adjustment

    def update(self,tilemap:"Tilemap",ps: "ParticleSystem",engine_lights:list["PointLight"],dt:float)->None:
        self._life-= dt * 60
        if self._life <= 0:
            self.dead = True
            return True

        scaled_dt = dt * 60
        steps =4 

        # devide one movement into steps, and if bullet collides in
        # one sub step move the bullet up to that step 
  
        for step in range(steps):
            self.cur_physics_step = step
            self.pos[0] += scaled_dt*self.velocity[0]/steps
            # need a different way to find the center 
            self.center[0] += scaled_dt*self.velocity[0] /steps

            rotated_bullet_rect = get_rotated_vertices(self.center,*self.size,self._angle) 

            for rect_tile in tilemap.phy_rects_around(self.pos, self.size):
                if SAT(rect_tile,rotated_bullet_rect):
                #if entity_rect.colliderect(rect_tile[0]):
                    #self.handle_tile_collision(tilemap,rect_tile)
                    if step != 0:
                        self.pos[1] += scaled_dt*self.velocity[1]/steps
                        self.center[1] += scaled_dt*self.velocity[1]/steps
                        self.interpolate_pos = False
                        return False
                    self._create_collision_effects(tilemap,rect_tile,ps,engine_lights)
                    self.dead = True
                    return True 
            
            self.pos[1] += scaled_dt* self.velocity[1]/steps
            self.center[1] += scaled_dt* self.velocity[1]/steps
            
            rotated_bullet_rect = get_rotated_vertices(self.center,*self.size,self._angle)
            
            for rect_tile in tilemap.phy_rects_around(self.pos, self.size):
                if SAT(rect_tile,rotated_bullet_rect):
                #if entity_rect.colliderect(rect_tile[0]):
                    #self.handle_tile_collision(tilemap,rect_tile)
                    if step != 0: 
                        self.interpolate_pos =False
                        return False
                    self._create_collision_effects(tilemap,rect_tile,ps,engine_lights)
                    self.dead = True
                    return True 
        return False



class AKBullet(Bullet):
    def __init__(self, pos: list[float],damage,angle,velocity):
        super().__init__(60,pos, (16,5),angle)
        self._damage = damage
        self._type = 'ak47'
        self.velocity = velocity
