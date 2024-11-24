from pygame import Rect
from scripts.new_tilemap import Tilemap
from scripts.new_particles import ParticleSystem
from scripts.custom_data_types import AnimationParticleData,Animation
from scripts.animationData import PlayerAnimationDataCollection
from random import choice as random_choice


class PhysicsEntity: 
    def __init__(self,type:str,pos:list[float,float],size:tuple[int,int]):
        
        self.collisions = {'up': False, 'down': False, 'left': False, 'right': False}
        self.type = type 
        self.pos = pos
        self.size = size
        self.velocity = [0, 0]
        self.state = ''
        self.anim_offset = (0, 0)
        self.flip = False
        self.set_state('idle')
        self.cut_movement_input = False
        self.on_ramp = False 
        self.frame_data = 0


    def set_state(self,state):
        if state != self.state: 
            self.frame_data = 0
            self.state= state 

    def _collision_rect(self) -> Rect:
        return Rect(*self.pos,*self.size)


    def collide(self,other):
        return self._collision_rect().colliderect(other._collision_rect())
    

    def update(self,tilemap:Tilemap,movement = (0,0),anim_offset = (0,0)):
        self.frame_data += 1 
        self.collisions = {'up': False, 'down': False, 'left': False, 'right': False}
        
        if movement[0] > 0:
            self.flip = False
        if movement[0] < 0 :
            self.flip = True 


        # gravity 
        self.velocity[1] = min(5, self.velocity[1] + 0.26)

        # air resistance 
        if self.velocity[0] < 0:
            self.velocity[0] = min(self.velocity[0] + 0.21, 0)
        elif self.velocity[0] > 0:
            self.velocity[0] = max(self.velocity[0] - 0.21, 0)

        frame_movement = (movement[0] + self.velocity[0], movement[1] + self.velocity[1]) if not self.cut_movement_input else self.velocity
        
        self.pos[0] += frame_movement[0]
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
                                self.collisions['right'] = True
                                
                                self_rect.right = rect_tile[0].left
                            elif frame_movement[0] < 0:
                                self.collisions['left'] = True
                                
                                self_rect.left = rect_tile[0].right
                            else: 
                                if self_rect.centerx -rect_tile[0].centerx <0:
                                    self.collisions['right'] = True
                                    self_rect.right = rect_tile[0].left
                                    
                                else:
                                    self.collisions['left'] = True 
                                    self_rect.left = rect_tile[0].right 
                                
                            self.pos[0] =self_rect.x - anim_offset[0]
                            
                else:
                    if frame_movement[0] > 0:
                        self.collisions['right'] = True
                        
                        self_rect.right = rect_tile[0].left
                    elif frame_movement[0] < 0:
                        self.collisions['left'] = True
                        
                        self_rect.left = rect_tile[0].right
                        
                    else: 
                        if self_rect.centerx -rect_tile[0].centerx <0:
                            self.collisions['right'] = True
                            self_rect.right = rect_tile[0].left
                            
                        else:
                            self.collisions['left'] = True 
                            self_rect.left = rect_tile[0].right 
                        
                    self.pos[0] =self_rect.x - anim_offset[0]
        
        self.pos[1] +=frame_movement[1]
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
                        self.collisions['down'] = True
                        self.on_ramp = 0
                        self_rect.bottom = rect_tile[0].top
                        
                    elif frame_movement[1] < 0:
                        self.collisions['up'] = True
                        self_rect.top = rect_tile[0].bottom
                    self.velocity[1] = 0
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
                        self.on_ramp = 1 if variant == '0' else -1
                        self_rect.bottom = target_y
                        self.pos[1] = self_rect.y -anim_offset[1]
                        self.collisions['down'] = True
 


class Player(PhysicsEntity):
    def __init__(self, pos: list[float], size: tuple[int, int]):
        self._animation_data_collection = PlayerAnimationDataCollection
        self._cur_animation = self._animation_data_collection.get_animation_data('idle')
        super().__init__('player', pos, size)
        
        self._accel_rate = 0
        self._default_speed = 0

        self.cur_vel = 0 
        self.recov_rate = 0.6
        self.stamina = 100
        self.health = 200
        self.fatigued =False

        self.jump_count = 2
        self.wall_slide = False
        self.crouch = False 
        self.on_wall = self.collisions['left'] or self.collisions['right']
        self.air_time = 0
        self.on_ladder = False

        self.changing_done = False 
        self.change_weapon_inc = False 
        self.holding_gun = False 
        self.running = False 
        self.y_inertia = 0
        self.hard_land_recovery_time = 0

        self.d_cursor_pos = [0,0]


    def set_default_speed(self,speed):
        self._default_speed = speed

    def set_accel_rate(self,accel_rate):
        self._accel_rate = accel_rate

    def _collision_rect(self) -> Rect:
        return Rect(self.pos[0] +3, self.pos[1] + 1 ,10,15)


    def _accelerate(self,movement_input):
        if(movement_input[1]-movement_input[0])  >0 :
            #means that the intent of the player movement is to the right.  
            self.cur_vel = min( 1.3*self._default_speed,self._accel_rate + self.cur_vel)
                
        elif (movement_input[1]-movement_input[0]) <0 :
            #means that the intent of the player movement is to the left.  
            self.cur_vel = max( -1.3*self._default_speed,self.cur_vel- self._accel_rate)
            
        else: 
            if self.cur_vel >= 0 :
                self.cur_vel = max(0,self.cur_vel - self._accel_rate)
                
            else:
                self.cur_vel = min(0,self.cur_vel + self._accel_rate)
    
    def set_state(self,state):
        if state != self.state: 
            self.state = state
            self._cur_animation.reset()
            self._cur_animation = self._animation_data_collection.get_animation_data(state)
     

    def jump_cut(self):
        if not self.on_ladder: 
            if self.velocity[1] < 0: 
                if self.velocity[1] > -4.2:
                    if self.air_time >0 and self.air_time <= 8:
                        self.velocity[1] = -1.2
                    if self.air_time >8 and self.air_time <=11 :
                        self.velocity[1] = -2.2



    def jump(self):
        if self.wall_slide: 
                self.jump_count = 1
                
                if self.collisions['left']:
                    
                    self.velocity[0] =  4.2
                if self.collisions['right']:
                    
                    self.velocity[0] = -4.2
                
                self.velocity[1] =-4.4
                particle_system = ParticleSystem.get_instance()
                particle_data = AnimationParticleData('jump',[self.pos[0] + self.size[0]//2 ,self.pos[1]+self.size[1]],[0,0.1],'player')
                particle_system.add_particle(particle_data)

        if self.jump_count == 2:
            if self.state == 'jump_down':
                self.jump_count -=2

                self.velocity[1] = -4.4
                particle_system = ParticleSystem.get_instance()
                particle_data = AnimationParticleData('jump',[self.pos[0] + self.size[0]//2 ,self.pos[1]+self.size[1]],[0,0.1],'player')
                particle_system.add_particle(particle_data)

            else: 
                self.jump_count -=1

                self.velocity[1] = -4.4    
            
        elif self.jump_count ==1: 
            self.jump_count -=1
            self.velocity[1] = -4.4  

            particle_system = ParticleSystem.get_instance()
            particle_data = AnimationParticleData('jump',[self.pos[0] + self.size[0]//2 ,self.pos[1]+self.size[1]],[0,0.1],'player')
            particle_system.add_particle(particle_data)

    
    # TODO: add weapon rendering later. 

    def update(self,tilemap:Tilemap,cursor_pos,player_movement_input,frame_count):
        self._accelerate(player_movement_input)
        self._cur_animation.update()
        self.time = frame_count
        self.d_cursor_pos = cursor_pos
        new_movement = [self.cur_vel,0]

        if self.fatigued: 
            self.recov_rate = 0.3
            new_movement[0] *= 0.7
            if self.stamina >= 80:
                self.fatigued = False 
        else: 
            self.recov_rate = 0.6
            if self.running: 
                if self.stamina >= 10:
                    #then you can run. 
                    if self.cur_vel != 0:
                        self.stamina -= 1.2
                        new_movement[0] *= 1.4
                else: 
                    new_movement[0] *= 0.7
                    self.fatigued = True 
            else: 
                if self.stamina < 10: 
                    new_movement[0] *= 0.7
                    self.fatigued = True 
        
        if self.hard_land_recovery_time > 0 :
            new_movement[0] *= (20 - self.hard_land_recovery_time)/20 
            new_movement[1] *= (20 - self.hard_land_recovery_time)/20 
            self.hard_land_recovery_time -= 1
            
        super().update(tilemap, new_movement,anim_offset= (3,1))
        """
        r = max(self.size) * 2

        rangeRect = Rectangle(Vector2(self.pos[0] - self.size[0]//2 - r /2 ,self.pos[1]  - r /2 ), Vector2(r,r))

        self.nearest_collectable_item = quadtree.queryRange(rangeRect,"item")
        """
        #every frame, the stamina is increased by 0.7
       
        self.stamina = min(100, self.stamina + self.recov_rate)
        self.air_time +=1
        
        
        self.changing_done = min(2,self.change_weapon_inc + self.changing_done)
        if self.changing_done == 2:
             
            self.change_weapon(self.change_scroll)
                

        if self.velocity[1] >=2:
            self.y_inertia += 1 

       
        self.cut_movement_input = False 


        #add particle spew effect, similar to how you've done it for the bullets when it collides with tiles. 
        #the number of particles that are created should depend on the impact force, which can be a function of y_inertia you've 
        #defined already. 


        #TODO: recover this logic. get rid of breaks. 

        if self.collisions['down']:
            if self.y_inertia > 6:
                self.set_state('land')
            entry_pos = (self._collision_rect().centerx,self._collision_rect().bottom)
            for offset in range(-tilemap.tile_size, tilemap.tile_size, 4):
                if tilemap.solid_check((entry_pos[0]+offset,entry_pos[1])):
                    color = tilemap.get_at((entry_pos[0]+offset,entry_pos[1]),side ='top')



            offsets = [(-2,0),(-1,0), (0,0), (1,0),(2,0)]                
            for i in range(min(8,self.y_inertia//2)):
                offset = random_choice(offsets)
                #self.game.add_non_anim_particle(bullet_collide_particle(random.choice([(1,1),(2,1),(1,2),(3,1),(1,3),(2,2)]), (entry_pos[0] - offset[0],entry_pos[1] ) ,-90 + random.randint(-88,88),2.4+random.random(),color,tile_map,gravity_factor= 1.4 * min(8,self.y_inertia//2)/5))
        


            if self.y_inertia > 12 and self.y_inertia <35:
                
                pass
                """
                land_smoke = Particle(self.game,'land',(self.pos[0] +8,self.pos[1]+14),'player')
                self.game.add_particle(land_smoke)
                self.game.add_screen_shake(5) 
                self.hard_land_recovery_time = 7
                """
                #self.set_state('land')
                

                
                
                
            elif self.y_inertia >= 35:
                pass 
                """
                land_smoke = Particle(self.game,'big_land',(self.pos[0] +7,self.pos[1]+7),'player')
                self.game.add_particle(land_smoke)
                #self.set_state('land')
                self.game.add_screen_shake(16)
                self.animation.img_dur = 5
                self.hard_land_recovery_time = 20
                """

            self.y_inertia = 0
            self.jump_count =2 
            self.air_time = 0
            
            
        self.wall_slide = False
        self.on_wall = self.collisions['left'] or self.collisions['right']


        if self.on_wall and self.air_time > 4:
            self.wall_slide = True 
            self.velocity[1] = min(self.velocity[1],0.5)
            if self.collisions['right']:
                self.flip = False
            else:
                self.flip = True 
            
            self.set_state('wall_slide')
            self.y_inertia = 0
       
        if not self.wall_slide: 
            if self.air_time > 4:
                self.boost_on_next_tap = False 
                if self.velocity[1] < 0:
                    self.y_inertia = 0
                    self.set_state('jump_up')
                elif self.velocity[1] >0 :
                    self.set_state('jump_down')
               
            elif self.cur_vel != 0:
                if self.state == 'land':
                    if self._cur_animation.done == True: 
                        if self.fatigued: 
                            self.set_state('walk')
                        else: 
                            self.set_state('run')
                else: 
                   
                    if self.fatigued: 
                        self.set_state('walk')
                    else: 
                        self.set_state('run')
                    """
                    anim_frame = self.animation.frame / self.animation.img_dur
                    if anim_frame == 0 or anim_frame == 3:
                        self.game.player_sfx['run'][str(random.randint(0,7))].play()
                    """
                if self.crouch and (player_movement_input[0] or player_movement_input[1]) :
                    self.cut_movement_input = True
                    self.set_state('slide')
                self.y_inertia = 0
                    
            else: 
                self.y_inertia = 0
                if self.state == 'land':
                    if self._cur_animation.done == True: 
                        self.set_state('idle') 
                else: 
                    if self.crouch: 
                        self.set_state('crouch')
                        pass 
                    else: 
                        self.set_state('idle')
                
        
        
        #testing weapon rendering  
        """
        if self.cur_weapon_node:
            self.cur_weapon_node.update(self.d_cursor_pos)
        """
        """
        if self.cur_weapon_node:
            self.cur_weapon_node.weapon.update(self.d_cursor_pos)
        """
        