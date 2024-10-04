import pygame 
import random 
import math 

from scripts.fire import Flame_particle
from scripts.particles import Particle,non_animated_particle
from scripts.Pygame_Lights import LIGHT ,pixel_shader
from scripts.entities import Bullet, shotgun_Bullet, RocketShell
from my_pygame_light2d.light import PointLight

WEAPONS_WITH_KNOCKBACK = {'rifle'}
WEAPONS_THAT_CAN_RAPID_FIRE = {'rifle','weapon'}

class Weapon:
    def __init__(self,game,type,name,sprite,fire_rate,power,image,shrunk_image,img_pivot,description,pivot_to_opening_offset = (0,0)):  
        self.game = game
        self.type = type 

        self.sprite = sprite 
        self.sprite_buffer = sprite

        self.img_pivot = img_pivot
        self.image = image
        self.shrunk_image = shrunk_image
        self.mpos = [0,0]
        self.pivot_to_opening_offset =  pivot_to_opening_offset
        self.sprite_width_discrepency = 0


        self.flipped = False 
        self.rapid_firing = False 
        self.power=power
        self.knockback = [0,0]
        self.fire_rate = fire_rate
        self.magazine = 0
        
        self.angle_opening = 0
        self.opening_pos = [0,0]

        #testing 
        self.amount = 1
        self.name = name
        self.stackable = False
        self.description = description
    



    def draw(self,x,y,surf,scale):
        offset = (17- self.image.get_width()//2, 7 - self.image.get_height()//2 )
        #image = pygame.transform.scale(self.image,(16 * scale,16*scale))
        surf.blit(self.image,(x+offset[0],y+offset[1]))

    def get_description(self):
        return self.description


    def get_name(self):
        return self.name

    def toggle_rapid_fire(self):
        if self.type in WEAPONS_THAT_CAN_RAPID_FIRE:
            self.rapid_firing = not self.rapid_firing

    
    def rotate(self,surface, angle, pivot, offset):
        rotated_image = pygame.transform.rotozoom(surface, -angle, 1)  
        rotated_offset = offset.rotate(angle)  
        rect = rotated_image.get_rect(center=pivot+rotated_offset)
        return rotated_image, rect  
    

    def equip(self,holder_entity):
        self.holder = holder_entity

    def load(self,bullet):
        self.magazine.append(bullet)

    def shoot(self,j= 0,d_mouse_pos = [0,0]):
        if self.magazine: 
            bullet = self.magazine.pop()
            if bullet: 
                #then you shoot the bullet.
                bullet.damage = self.power // 2 
                bullet.angle= self.angle_opening
                #rotate the bullet sprite around the center
                """
                bulletdisplay = pygame.Surface((bullet.sprite.get_width(),bullet.sprite.get_height()),pygame.SRCALPHA)
                bulletdisplay,bullet_rect = self.rotate(bulletdisplay,self.angle_opening,bullet.center,self.render_offset)
                """
                bullet.sprite = pygame.transform.rotate(bullet.sprite,bullet.angle)
                bullet.velocity = [math.cos(math.radians(-bullet.angle)) * self.power ,math.sin(math.radians(-bullet.angle))*self.power]  

                

                if bullet.velocity[0] > 0 :
                    
                    bullet.pos = self.opening_pos.copy()
                    bullet.pos[0] -= bullet.velocity[0]
                    bullet.pos[1] += (0 if bullet.velocity[1] <0 else -bullet.velocity[1])
                    bullet.flip = False 
                else: 
                    bullet.pos = self.opening_pos.copy()
                    if bullet.velocity[1] > 0 :
                        bullet.pos[1] -= bullet.velocity[1]
                    bullet.flip = True 



                self.game.bullets_on_screen.append(bullet)
                
                self.knockback = [-bullet.velocity[0]/2,-bullet.velocity[1]/2]
                
                #append the shooting particles here instead of doing it in the entity class 
                
               
                return bullet
            
        return False 
            
            


        
    def copy(self):
        new_weapon = Weapon(self.game,self.type,self.name,self.sprite,self.fire_rate,self.power,self.image,self.shrunk_image,self.img_pivot,self.description)
        new_weapon.magazine = self.magazine.copy()
        return new_weapon
        
    def update(self,cursor_pos):
        self.mpos = cursor_pos

    def render(self,surf,offset = (0,0),set_angle = None):
        #save surf to use when passing it to bullet 
        
        self.surf = surf 

        #you need to define the anchor point positions for every state of the player. 

        left_and_right_anchors = {  True: {"idle": {"left": (2,6), "right": (13,6)}, "walk": {"left": (2,6), "right": (13,6)},'run' :{"left": (1,6), "right": (8,5)} 
                                           ,'jump_up' :{"left": (0,4), "right": (9,4)},'jump_down' :{"left": (3,5), "right": (10,4)}
                                           ,'slide' :{ "left" : (11,9) ,"right": (11,9)} , 'wall_slide' : {"left": (4,5), "right": (8,5)},'land' :{ "left" : (2,6) ,"right": (8,5)} , 
                                           'crouch' :{ "left" : (2,8) ,"right": (13,8)}
                                           },
                                    False: {"idle": {"left": (2,6), "right": (13,6)},"walk": {"left": (2,6), "right": (13,6)}, 'run' :{"left": (7,5), "right": (14,6)} 
                                           ,'jump_up' :{"left": (6,4), "right": (15,5)},'jump_down' :{"left": (2,4), "right": (7,5)}
                                           ,'slide' :{ "left": (4,9), "right": (4,9) }, 'wall_slide': {'left' : (7,5), 'right' : (11,5)},'land' :{ "left" : (6,5) ,"right": (13,6)} ,
                                           'crouch' :{ "left" : (2,8) ,"right": (14,8)} 
                                           },
        }

        #get the anchors. 

        self.left_anchor = left_and_right_anchors[self.holder.flip][self.holder.state]["left"]
        self.right_anchor = left_and_right_anchors[self.holder.flip][self.holder.state]["right"]
       
        rotate_cap_left = False
        rotate_cap_right = False

        
        if self.holder.state == 'slide' or self.holder.state == 'wall_slide':
            
            if self.holder.flip:
                rotate_cap_left = True 
            else: 
                rotate_cap_right = True 
            
            pass 
        #get the angle, the pivot, and offset
        if self.flipped: 
            self.pivot = [self.holder.pos[0]+self.right_anchor[0]-offset[0]-1,self.holder.pos[1]+self.right_anchor[1] -offset[1]]
            self.render_offset = pygame.math.Vector2(-self.sprite_buffer.get_rect().centerx + self.img_pivot[0],self.sprite_buffer.get_rect().centery - self.img_pivot[1] )       
        else: 
            self.pivot = [self.holder.pos[0]+self.left_anchor[0]-offset[0]+1,self.holder.pos[1]+self.left_anchor[1] -offset[1]]
            self.render_offset = pygame.math.Vector2(self.sprite_buffer.get_rect().centerx - self.img_pivot[0], self.sprite_buffer.get_rect().centery - self.img_pivot[1])

       
        dx, dy = self.mpos[0] - (self.pivot[0] + self.pivot_to_opening_offset[0]), self.mpos[1]- (self.pivot[1] +self.pivot_to_opening_offset[1]) 
      
        angle = math.degrees(math.atan2(-dy,dx)) 
        sprite_width = self.sprite_buffer.get_width() - self.sprite_width_discrepency
        
        #separate angle varialble for the gun's opening - to apply angle cap and to pass onto firing bullet 
        self.angle_opening = angle 

        #flip transition lag exists. If it happens, don't blit the gun, and turn off the shooting function. 
        blitz = False

        #based on the angle, flip the sprite.If you are sliding, cap the angle. 
        if (angle > 90 and angle <= 180) or (angle < -90 and angle >= -180):
            if rotate_cap_right:
                if self.flipped:
                    self.sprite_buffer = pygame.transform.flip(self.sprite_buffer,True,False)
                    self.flipped = False
                    blitz = True 
                if (angle > 90 and angle <= 180):
                    angle = -82
                elif (angle < -90 and angle >= -180):
                    angle = 83
                self.angle_opening = -angle 
            else: 
                if self.flipped != True: 
                    self.sprite_buffer = pygame.transform.flip(self.sprite_buffer,True,False)
                    self.flipped = True 
                    blitz = True 
                angle += 180    
                angle = -angle
        else: 
            if rotate_cap_left:
                if self.flipped == False: 
                    self.sprite_buffer = pygame.transform.flip(self.sprite_buffer,True,False)
                    self.flipped = True
                    blitz = True 
                if (angle >0 and angle <= 90) : 
                    angle = 65
                elif (angle <= 0 and angle >= -90):
                    angle =  -72
                self.angle_opening = 180-angle 
            else: 
                if self.flipped != False: 
                    self.sprite_buffer = pygame.transform.flip(self.sprite_buffer,True,False)
                    self.flipped = False  
                    blitz = True 
                angle = -angle

        #if self.flipped: sprite_buffer = pygame.transform.flip(sprite_buffer,True,False)
        weapon_display = pygame.Surface((self.sprite_buffer.get_width(),self.sprite_buffer.get_height()),pygame.SRCALPHA)
        weapon_display.blit(self.sprite_buffer,(0,0))
        rotated_image,rect = self.rotate(weapon_display,angle if set_angle == None else set_angle,self.pivot,self.render_offset)

        #the gun's opening position  
        #self.opening_pos[0] = self.pivot[0] + math.cos(math.radians(-self.angle_opening)) * sprite_width
        #self.opening_pos[1] = self.pivot[1] + math.sin(math.radians(-self.angle_opening)) * sprite_width
       
        self.opening_pos[0] = self.pivot[0] + self.pivot_to_opening_offset[0] + offset[0]+ math.cos(math.radians(-self.angle_opening)) * sprite_width
        self.opening_pos[1] = self.pivot[1] + self.pivot_to_opening_offset[1] + offset[1]+ math.sin(math.radians(-self.angle_opening)) * sprite_width
        
        #if self.type in WEAPONS_WITH_KNOCKBACK:
        if self.knockback[0] < 0: 
            self.knockback[0] = min(self.knockback[0] + 1.45, 0)
        if self.knockback[0] > 0 :
            self.knockback[0] = max(self.knockback[0] -1.45, 0)

        if self.knockback[1] < 0: 
            self.knockback[1] = min(self.knockback[1] + 1.45, 0)
        if self.knockback[1] > 0 :
            self.knockback[1] = max(self.knockback[1] -1.45, 0)

        #testSurf = pygame.Surface((2,2))

        if not blitz: 
            #surf.blit(testSurf,(self.opening_pos[0]-offset[0],self.opening_pos[1]-offset[1]))
            surf.blit(rotated_image,(rect.topleft[0] + self.knockback[0],rect.topleft[1] + self.knockback[1]))
         

class AK_47(Weapon):
    def __init__(self,game,sprite,image,shrunk_image,description): 
        super().__init__(game,'weapon','ak_47',sprite,5,15,image,shrunk_image,(2,2),description)

    def copy(self):
        new_ak = AK_47(self.game,self.sprite,self.image,self.shrunk_image,self.description)
        new_ak.magazine = self.magazine
        return new_ak

    def shoot(self,j= 0,d_mouse_pos = [0,0]):
        if self.magazine: 
            self.magazine -= 1 
            bullet_image = self.game.bullets['rifle_small'].copy()
            bullet = Bullet(self.game,[0,0],bullet_image.get_size(),bullet_image,'rifle_small')
    
            #then you shoot the bullet.
            bullet.damage = self.power // 2 
            bullet.angle= self.angle_opening
            #rotate the bullet sprite around the center
            """
            bulletdisplay = pygame.Surface((bullet.sprite.get_width(),bullet.sprite.get_height()),pygame.SRCALPHA)
            bulletdisplay,bullet_rect = self.rotate(bulletdisplay,self.angle_opening,bullet.center,self.render_offset)
            """
            bullet.sprite = pygame.transform.rotate(bullet.sprite,bullet.angle)
            bullet.velocity = [math.cos(math.radians(-bullet.angle)) * self.power ,math.sin(math.radians(-bullet.angle))*self.power]  

            

            if bullet.velocity[0] > 0 :
                
                bullet.pos = self.opening_pos.copy()
                bullet.pos[0] -= bullet.velocity[0]
                bullet.pos[1] += (0 if bullet.velocity[1] <0 else -bullet.velocity[1])
                bullet.flip = False 
            else: 
                bullet.pos = self.opening_pos.copy()
                if bullet.velocity[1] > 0 :
                    bullet.pos[1] -= bullet.velocity[1]
                bullet.flip = True 



            self.game.bullets_on_screen.append(bullet)
            
            self.knockback = [-bullet.velocity[0]/2,-bullet.velocity[1]/2]
            
            #append the shooting particles here instead of doing it in the entity class 
            
            """
            self.game.temp_lights.append([LIGHT(30,pixel_shader(30,(253,178,50),1,False)),3,self.opening_pos])
            self.game.temp_lights.append([LIGHT(60,pixel_shader(60,(248,229,153),1,True,self.angle_opening,360)),3,self.opening_pos])
            self.game.temp_lights.append([LIGHT(50,pixel_shader(50,(248,229,153),1,True,180+self.angle_opening,360)),3,self.opening_pos])
            """
            
            light =  PointLight(self.opening_pos,power = 1.0,radius = 8,life = 2)
            light.set_color(253,108,50)
            light.cast_shadows = False
            self.game.lights_engine.lights.append(light)
            
            light = PointLight(self.opening_pos,power = 0.7 ,radius = 24,life = 2)
            light.set_color(248,129,153)
            light.cast_shadows = False
            self.game.lights_engine.lights.append(light)

            light = PointLight(self.opening_pos,power = 0.6,radius = 40,life = 2)
            light.set_color(248,129,153)
            light.cast_shadows = False
            self.game.lights_engine.lights.append(light)


            light = PointLight(self.opening_pos,power = 1.0,radius = 20, illuminator= bullet, life = bullet.frames_flown)
            light.cast_shadows = False
            self.game.lights_engine.lights.append(light)
            
            shot_particle = Particle(self.game,'smoke'+'/'+self.name,self.opening_pos.copy(),self.holder.type,velocity=[0,0],frame=0)
            rotated_shot_particle_images = [pygame.transform.rotate(image,bullet.angle) for image in shot_particle.animation.copy().images]
            shot_particle.animation.images = rotated_shot_particle_images

            self.game.particles.append(shot_particle)
            #add non animated particles here to polish as well 
            colors = [(253,245,216),(117,116,115),(30,30,30)]
            for i in range(random.randint(6,13)):
                normal =[-bullet.velocity[1],bullet.velocity[0]] 
                factor = random.random()
                up_down = random.randint(-10,10)
                
                shot_muzzle_particle = non_animated_particle(self.opening_pos.copy(),random.choice(colors),[bullet.velocity[0]*20*factor + normal[0]* factor*up_down,bullet.velocity[1]*20*factor +normal[1]* factor*up_down],self.game.Tilemap,life = random.randint(1,5))
                self.game.non_animated_particles.append(shot_muzzle_particle)
                

class Flamethrower(Weapon):
    def __init__(self,game,sprite,image,shrunk_image,description):
        super().__init__(game,'weapon', 'flamethrower' ,sprite,1,5,image,shrunk_image,(2,2),description)
        self.rapid_firing = True
        self.size = self.sprite.get_size()
    def copy(self):
        new_flamethrower =  Flamethrower(self.game,self.sprite,self.image,self.shrunk_image,self.description)
        new_flamethrower.magazine = self.magazine
        return new_flamethrower
    
    def toggle_rapid_fire(self):
        self.rapid_firing = not self.rapid_firing 
        

    def shoot(self,j= 0,d_mouse_pos = [0,0]):
        if self.magazine > 0 :
            self.magazine -= 1 
            # -------------   predetermined particle parameters 
            size = 6
            density = 4
            rise = 3.1
            spread = 1.8
            wind = 0
            #---------------
            ox,oy = self.mpos[0],self.mpos[1]
            mx,my = d_mouse_pos[0],d_mouse_pos[1]

            dist = math.sqrt((mx-ox)**2+(my-oy)**2)
            #a = math.atan2(my-oy, mx-ox)
            for d in range(0, int(dist), 10):
                #_x = mx+math.cos(a)*d
                #_y = my+math.sin(a)*d
                
                for _ in range(round(density)): 
                    flame_particle= Flame_particle(self.opening_pos[0], self.opening_pos[1],size,density,rise,self.angle_opening,spread,wind,self.power)
                    
                    light = PointLight((self.opening_pos[0], self.opening_pos[1]),power = 0.12,radius = 42,illuminator=flame_particle,life = flame_particle.maxlife)
                    light.set_color(255,35,19)
                    light.cast_shadows = False
                    self.game.lights_engine.lights.append(light)
                    
                    self.game.physical_particles.append(flame_particle)
            else:
                for _ in range(round(density)): 
                    flame_particle= Flame_particle(self.opening_pos[0], self.opening_pos[1],size,density,rise,self.angle_opening,spread,wind,self.power)

                    light = PointLight((self.opening_pos[0], self.opening_pos[1]),power = 0.11,radius = 42,illuminator=flame_particle,life = flame_particle.maxlife)
                    light.set_color(255,35,19)
                    light.cast_shadows = False

                    self.game.lights_engine.lights.append(light)


                    self.game.physical_particles.append(flame_particle)

            self.knockback = [ - 4 * math.cos(math.radians(self.angle_opening)), 4* math.sin(math.radians(self.angle_opening))]
        
        
           
            
class Rocket_launcher(Weapon):
    def __init__(self,game,sprite,image,shrunk_image,description):
        super().__init__(game,'weapon','rocket_launcher',sprite,120,30,image,shrunk_image,(6,6),description)
        self.rapid_firing = False
        self.pivot_to_opening_offset = (0,-3)
        self.sprite_width_discrepency = 4
        self.prev_shot_time = 0
        self.cooldown = 45

    def copy(self):
        new_rocket_launcher = Rocket_launcher(self.game,self.sprite,self.image,self.shrunk_image,self.description)
        new_rocket_launcher.magazine = self.magazine
        
        return new_rocket_launcher

    def toggle_rapid_fire(self):
        pass 

    def shoot(self,j= 0,d_mouse_pos = [0,0]):
        if j >= self.prev_shot_time:
            if self.prev_shot_time + self.cooldown < j: 
                can_shoot = True 
            else: 
                can_shoot = False 
            
        else: 
            if 360 - self.prev_shot_time + j > self.cooldown:
                can_shoot = True 
            else: 
                can_shoot = False 

        if self.magazine > 0 and can_shoot:
            self.prev_shot_time = j
            self.magazine -= 1
            bullet_image = self.game.bullets['rocket_launcher'].copy()
            bullet = RocketShell(self.game,self.opening_pos.copy(),bullet_image.get_size(),bullet_image,'rocket_launcher')

            bullet.angle = self.angle_opening 
            bullet.sprite = pygame.transform.rotate(bullet.sprite,bullet.angle)
            bullet.velocity =  [math.cos(math.radians(-bullet.angle)) * self.power/1.3 ,math.sin(math.radians(-bullet.angle))*self.power/1.3]  
            
            
            if bullet.velocity[0] > 0 :
                
                bullet.pos = self.opening_pos.copy()
                bullet.pos[0] -= bullet.velocity[0]
                bullet.pos[1] += (0 if bullet.velocity[1] <0 else -bullet.velocity[1])
                bullet.flip = False 
            else: 
                bullet.pos = self.opening_pos.copy()
                
                if bullet.velocity[1] > 0 :
                    bullet.pos[1] -= bullet.velocity[1]
                bullet.flip = True 
            

            self.game.bullets_on_screen.append(bullet)

            self.knockback = [-bullet.velocity[0]/2,-bullet.velocity[1]/2]


            
            



class Shotgun(Weapon):
    def __init__(self,game,sprite,image,shrunk_image,description):
        super().__init__(game,'weapon','shotgun',sprite,50,14,image,shrunk_image,(3,0),description)
        self.rapid_firing = False
        self.cooldown = 14
        self.prev_shot_time = 0

    def copy(self):
        new_shotgun = Shotgun(self.game,self.sprite,self.image,self.shrunk_image,self.description)
        new_shotgun.magazine = self.magazine

        return new_shotgun 

    def toggle_rapid_fire(self):
        pass 

    def shoot(self,j= 0,d_mouse_pos = [0,0]):
        if j >= self.prev_shot_time:
            if self.prev_shot_time + self.cooldown < j: 
                can_shoot = True 
            else: 
                can_shoot = False 
            
        else: 
            if 360 - self.prev_shot_time + j > self.cooldown:
                can_shoot = True 
            else: 
                can_shoot = False 


        if self.magazine > 0 and can_shoot:

            self.prev_shot_time = j
            self.magazine -= 1
            bullet_image = self.game.bullets['shotgun'].copy()  
            knockback = [0,0]
            for i in range(-2,3):
                
                bullet = shotgun_Bullet(self.game, [0,0], bullet_image.get_size(), bullet_image,'shotgun')
                bullet.damage = self.power//2
                bullet.angle = self.angle_opening - i*3
                bullet.sprite = pygame.transform.rotate(bullet.sprite, bullet.angle)
                bullet.velocity =  bullet.velocity = [math.cos(math.radians(-bullet.angle)) * self.power ,math.sin(math.radians(-bullet.angle))*self.power ]  
                if i == 0:
                    knockback = [-bullet.velocity[0] * 1.5/2 , -bullet.velocity[1]* 1.5/2]
                if bullet.velocity[0] > 0 :
                
                    bullet.pos = self.opening_pos.copy()
                    bullet.pos[0] -= bullet.velocity[0]
                    bullet.pos[1] += (0 if bullet.velocity[1] <0 else -bullet.velocity[1])
                    bullet.flip = False 
                else: 
                    bullet.pos = self.opening_pos.copy()
                    if bullet.velocity[1] > 0 :
                        bullet.pos[1] -= bullet.velocity[1]
                    bullet.flip = True 

                
                light = PointLight(self.opening_pos,power = 0.5, radius = 20, illuminator= bullet, life = bullet.frames_flown)
                light.cast_shadows = False
                self.game.lights_engine.lights.append(light)

                self.game.bullets_on_screen.append(bullet)
            self.knockback = knockback
            
            """"""
            light =  PointLight(self.opening_pos,power = 1.1,radius = 12,life = 2)
            light.set_color(253,108,50)
            light.cast_shadows = False
            self.game.lights_engine.lights.append(light)
            
            light = PointLight(self.opening_pos,power = 0.8 ,radius = 28,life = 2)
            light.set_color(248,129,153)
            light.cast_shadows = False
            self.game.lights_engine.lights.append(light)

            light = PointLight(self.opening_pos,power = 0.7,radius = 44,life = 2)
            light.set_color(248,129,153)
            light.cast_shadows = False
            self.game.lights_engine.lights.append(light)

            shot_particle = Particle(self.game,'smoke'+'/'+self.name,self.opening_pos.copy(),self.holder.type,velocity=[0,0],frame=0)
            rotated_shot_particle_images = [pygame.transform.rotate(image,bullet.angle) for image in shot_particle.animation.copy().images]
            shot_particle.animation.images = rotated_shot_particle_images

            self.game.particles.append(shot_particle)

            colors = [(253,245,216),(117,116,115),(30,30,30)]
            for i in range(random.randint(8,15)):
                normal =[-bullet.velocity[1],bullet.velocity[0]] 
                factor = random.random()
                up_down = random.randint(-10,10)
                
                shot_muzzle_particle = non_animated_particle(self.opening_pos.copy(),random.choice(colors),[bullet.velocity[0]*20*factor + normal[0]* factor*up_down,bullet.velocity[1]*20*factor +normal[1]* factor*up_down],self.game.Tilemap,life = random.randint(1,5))
                self.game.non_animated_particles.append(shot_muzzle_particle)
                
           
        pass 
    

    
class Wheelbot_weapon(Weapon):
    def __init__(self,game,animation,description):
        self.game = game 
        self.type = 'weapon'
        self.animation = animation 
        self.img_pivot = [(2,8),(3,8)]
        self.flipped = False 
        self.rapid_firing = False 
        self.power = 6 
        self.knockback = [0,0]
        self.fire_rate = 0
        self.opening_pos = [0,0]
        self.magazine = []
        self.player_pos = [0,0]
        self.pivot =[]
        self.description = description
    
    def copy(self):
        return Wheelbot_weapon(self.game,self.animation.copy(),self.description) 
        
    def update(self,player_pos):
        self.animation.update()
        self.player_pos = player_pos

        

    def shoot(self,j= 0,d_mouse_pos = [0,0]):
        
        #bullet = tile_ign_Bullet(self.game,self.opening_pos.copy(),self.game.bullets[self.type].get_size(),self.game.bullets[self.type].copy(),self.type)
        bullet = self.magazine.pop()
        if bullet: 

            #bullet positioning is specific to the bullet sprite. 
            pos = self.opening_pos.copy()

            bullet.damage = self.power *6// 2 
            bullet.angle= self.angle_opening
            bullet.velocity = [math.cos(math.radians(self.angle_opening if not self.holder.flip else self.angle_opening+180)) * self.power ,math.sin(math.radians(self.angle_opening if not self.holder.flip else self.angle_opening+180))*self.power]  
            bullet.flip = True if bullet.velocity[0] < 0 else False 
            bullet.pos = pos 
           

            new_animation_imgs = [pygame.transform.flip(pygame.transform.rotate(img,bullet.angle),True if self.holder.flip else False, True if not self.holder.flip else False) for img in bullet.animation.copy().images]
            bullet.animation.images = new_animation_imgs
            
            bullet.pos[1] -= bullet.animation.img().get_height()/2 
            bullet.pos[0] -= (bullet.animation.img().get_width()-3 if bullet.velocity[0]< 0 else 5)

            

            self.game.enemy_bullets.append(bullet)
            self.knockback = [-bullet.velocity[0]*2,-bullet.velocity[1]*2]
            
        #add the shooting particles first 
            pos = self.opening_pos.copy()
            
            shot_particle = Particle(self.game,'smoke' +'/'+ 'laser_weapon',pos,self.holder.type)
            """
            shot_particle_og_width = shot_particle.animation.img().get_width() 
           
            shot_particle.pos[0] += 0.5*(shot_particle_og_width * math.cos(math.radians(self.angle_opening)) if bullet.velocity[0] >= 0 else -shot_particle_og_width * math.cos(math.radians(self.angle_opening)))
            shot_particle.pos[1] += 0.5*(shot_particle_og_width * math.sin(math.radians(self.angle_opening)) if bullet.velocity[0] >= 0 else -shot_particle_og_width * math.sin(math.radians(self.angle_opening)))
            """
            rotated_shot_particle_images =  [pygame.transform.flip(img,True,False) for img in [pygame.transform.rotate(image,self.angle_opening) for image in shot_particle.animation.copy().images]] if self.holder.flip else [pygame.transform.flip(pygame.transform.rotate(image,self.angle_opening+180),True,False) for image in shot_particle.animation.copy().images]
            shot_particle.animation.images = rotated_shot_particle_images

            shot_muzzle = Particle(self.game,'shot_muzzle' + '/' + 'laser_weapon',pos,self.holder.type)
            shot_muzzle_og_width = shot_muzzle.animation.img().get_width()
            
            shot_muzzle.pos[0] += 0.4*(shot_muzzle_og_width * math.cos(math.radians(self.angle_opening)) if bullet.velocity[0] >= 0 else -shot_muzzle_og_width * math.cos(math.radians(self.angle_opening)))
            shot_muzzle.pos[1] += 0.4*(shot_muzzle_og_width * math.sin(math.radians(self.angle_opening)) if bullet.velocity[0] >= 0 else -shot_muzzle_og_width * math.sin(math.radians(self.angle_opening)))

            rotated_shot_muzzle_particle_images =  [pygame.transform.flip(img,True,False) for img in [pygame.transform.rotate(image,self.angle_opening) for image in shot_muzzle.animation.copy().images]] if self.holder.flip else [pygame.transform.flip(pygame.transform.rotate(image,self.angle_opening+180),True,False) for image in shot_muzzle.animation.copy().images]
            shot_muzzle.animation.images = rotated_shot_muzzle_particle_images 

            self.game.particles.append(shot_muzzle)
            self.game.particles.append(shot_particle)

            light = PointLight(bullet.pos,power = 1.0,radius = 52,illuminator=bullet,life = 300)
            light.set_color(268,45,84)
            light.cast_shadows = False
            self.game.lights_engine.lights.append(light)

            


            """
            self.game.temp_lights.append([LIGHT(40,pixel_shader(40,(162,46,229),1.2,False)),4,self.opening_pos])
            self.game.temp_lights.append([LIGHT(150,pixel_shader(150,(137,31,227),1.5,True,(180-self.angle_opening if self.holder.flip else -self.angle_opening),40)),5,self.opening_pos])
            self.game.temp_lights.append([LIGHT(170,pixel_shader(170,(122,23,225),1.5,True,(180-self.angle_opening if self.holder.flip else -self.angle_opening),50)),6,self.opening_pos])

            """
            
            colors = [(253,245,216),(117,116,115),(30,30,30)]
            for i in range(random.randint(6,13)):
                normal =[-bullet.velocity[1],bullet.velocity[0]] 
                factor = random.random()
                up_down = random.randint(-10,10)
                
                shot_muzzle_particle = non_animated_particle(self.opening_pos.copy(),random.choice(colors),[bullet.velocity[0]*20*factor + normal[0]* factor*up_down,bullet.velocity[1]*20*factor +normal[1]* factor*up_down],self.game.Tilemap,life = random.randint(1,5))
                self.game.non_animated_particles.append(shot_muzzle_particle)
            
        
             
    def render(self,surf,offset = (0,0),set_angle = None):
        #save surf to use when passing it to bullet 
        self.surf = surf 

        img_pivot = self.img_pivot[0] if int(self.animation.frame / self.animation.img_dur) in [0,2] else self.img_pivot[1]

        #get the angle, the pivot, and offset
        if self.holder.flip: 
            self.sprite = pygame.transform.flip(self.animation.img(),True,False)
            self.right_anchor = (12,10)
            self.pivot = [self.holder.pos[0]+self.right_anchor[0]-offset[0],self.holder.pos[1]+self.right_anchor[1] -offset[1]]
            self.render_offset = pygame.math.Vector2(-self.sprite.get_rect().centerx + img_pivot[0],self.sprite.get_rect().centery - img_pivot[1] )       
        else: 
            self.sprite = self.animation.img()
            self.left_anchor = (8,10)
            self.pivot = [self.holder.pos[0]+self.left_anchor[0]-offset[0],self.holder.pos[1]+self.left_anchor[1] -offset[1]]
            self.render_offset = pygame.math.Vector2(self.sprite.get_rect().centerx - img_pivot[0], self.sprite.get_rect().centery - img_pivot[1])

        """
        mpos = pygame.mouse.get_pos()
        mpos = ((mpos[0]/2),(mpos[1]/2))

        dx,dy = mpos[0] - self.pivot[0], mpos[1]- self.pivot[1]
        """
        
        self.player_pos = (self.player_pos[0]-offset[0]+8,self.player_pos[1]-offset[1]+8)
        dx,dy = self.player_pos[0] - self.pivot[0], self.player_pos[1]- self.pivot[1]
       
        if self.holder.flip: 
            dx = -dx
        else:
            dy = -dy

        
        angle = math.degrees(math.atan2(-dy,dx)) 
       

        sprite_width = self.sprite.get_width()

        

        
        #separate angle varialble for the gun's opening - to apply angle cap and to pass onto firing bullet 
        self.angle_opening = angle 

        #flip transition lag exists. If it happens, don't blit the gun, and turn off the shooting function. 
        blitz = False
        """
        #based on the angle, flip the sprite.If you are sliding, cap the angle. 
        if (angle > 90 and angle <= 180) or (angle < -90 and angle >= -180):
            if rotate_cap_right:
                if self.flipped:
                    self.sprite = pygame.transform.flip(self.sprite,True,False)
                    self.flipped = False
                    blitz = True 
                if (angle > 90 and angle <= 180):
                    angle = -82
                elif (angle < -90 and angle >= -180):
                    angle = 83
                self.angle_opening = -angle 
            else: 
                if self.flipped != True: 
                    self.sprite = pygame.transform.flip(self.sprite,True,False)
                    self.flipped = True 
                    blitz = True 
                angle += 180    
                angle = -angle
        else: 
            if rotate_cap_left:
                if self.flipped == False: 
                    self.sprite = pygame.transform.flip(self.sprite,True,False)
                    self.flipped = True
                    blitz = True 
                if (angle >0 and angle <= 90) : 
                    angle = 65
                elif (angle <= 0 and angle >= -90):
                    angle =  -72
                self.angle_opening = 180-angle 
            else: 
                if self.flipped != False: 
                    self.sprite = self.sprite = pygame.transform.flip(self.sprite,True,False)
                    self.flipped = False  
                    blitz = True 
                angle = -angle
        """

        weapon_display = pygame.Surface((self.sprite.get_width(),self.sprite.get_height()),pygame.SRCALPHA)
        weapon_display.blit(self.sprite,(0,0))
        rotated_image,rect = self.rotate(weapon_display,angle,self.pivot,self.render_offset)

        #the gun's opening position  
        #self.opening_pos[0] = self.pivot[0] + math.cos(math.radians(-self.angle_opening)) * sprite_width
        #self.opening_pos[1] = self.pivot[1] + math.sin(math.radians(-self.angle_opening)) * sprite_width

       

        self.opening_pos[0] = self.pivot[0] + offset[0]+ math.cos(math.radians(self.angle_opening +180 if self.holder.flip else self.angle_opening)) * sprite_width
        self.opening_pos[1] = self.pivot[1]-3 + offset[1]+ math.sin(math.radians(-self.angle_opening if self.holder.flip else self.angle_opening)) * sprite_width
        
        if self.knockback[0] < 0: 
            self.knockback[0] = min(self.knockback[0] + 1.45, 0)
        if self.knockback[0] > 0 :
            self.knockback[0] = max(self.knockback[0] -1.45, 0)

        if self.knockback[1] < 0: 
            self.knockback[1] = min(self.knockback[1] + 1.45, 0)
        if self.knockback[1] > 0 :
            self.knockback[1] = max(self.knockback[1] -1.45, 0)
        
        #testSurf = pygame.Surface((2,2))

        if not blitz: 
            #surf.blit(testSurf,(self.opening_pos[0]-offset[0],self.opening_pos[1]-offset[1]))
            outline = pygame.mask.from_surface(rotated_image)
            for offset_ in [(-1,0),(1,0),(0,-1),(0,1)]:
                surf.blit(outline.to_surface(unsetcolor=(255,255,255,0),setcolor=(0,0,0,255)),(rect.topleft[0]+ self.knockback[0]+offset_[0],rect.topleft[1]+self.knockback[1]+offset_[1]))
            surf.blit(rotated_image,(rect.topleft[0] + self.knockback[0],rect.topleft[1] + self.knockback[1]))















        """
        #save surf to use when passing it to bullet 
        self.surf = surf 

        #you need to define the anchor point positions for every state of the player. 
 

        
        
       
        
        rotate_cap_left = False
        rotate_cap_right = False

        
        if self.holder.state == 'slide' or self.holder.state == 'wall_slide':
            if self.holder.flip:
                rotate_cap_left = True 
            else: 
                rotate_cap_right = True 
        
        
        #get the angle, the pivot, and offset
        img_pivot = self.img_pivot[0] if int(self.animation.frame / self.animation.img_dur) in [0,2] else self.img_pivot[1]
        
        if self.holder.flip: 
      
            self.sprite = pygame.transform.flip(self.animation.img(),True,False)
            self.right_anchor = (12,9)
            self.pivot = [self.holder.pos[0]+self.right_anchor[0]-offset[0]-1,self.holder.pos[1]+self.right_anchor[1] -offset[1]]
            self.render_offset = pygame.math.Vector2(-self.animation.img().get_rect().centerx + img_pivot[0],self.animation.img().get_rect().centery - img_pivot[1] )       
        else:
            self.sprite = self.animation.img()
            self.left_anchor = (6,10)
            self.pivot = [self.holder.pos[0]+self.left_anchor[0]-offset[0]+1,self.holder.pos[1]+self.left_anchor[1] -offset[1]]
            self.render_offset = pygame.math.Vector2(self.animation.img().get_rect().centerx - img_pivot[0], self.animation.img().get_rect().centery - img_pivot[1])

        dx,dy = self.player_pos[0] - self.pivot[0], self.player_pos[1]- self.pivot[1]
        angle = math.degrees(math.atan2(-dy,dx)) 
       
        b = 90 - math.acos(3/math.hypot(self.player_pos[0] - self.pivot[0], self.player_pos[1] - self.pivot[1]))

        angle = angle - b 

        
        sprite_width = self.animation.img().get_width()

        
        
        #separate angle varialble for the gun's opening - to apply angle cap and to pass onto firing bullet 
        self.angle_opening = angle 

        #flip transition lag exists. If it happens, don't blit the gun, and turn off the shooting function. 
        blitz = False

        #based on the angle, flip the sprite.If you are sliding, cap the angle. 
        
        if (angle > 90 and angle <= 180) or (angle < -90 and angle >= -180):
            
            if rotate_cap_right:
                if self.flipped:
                    self.sprite = pygame.transform.flip(self.sprite,True,False)
                    self.flipped = False
                    blitz = True 
                if (angle > 90 and angle <= 180):
                    angle = -82
                elif (angle < -90 and angle >= -180):
                    angle = 83
                self.angle_opening = -angle 
            else: 
            
            if self.flipped != True: 
                self.sprite = pygame.transform.flip(self.animation.img(),True,False)
                self.flipped = True 
                blitz = True 
            angle += 180    
            angle = -angle
        else:
             
            if rotate_cap_left:
                if self.flipped == False: 
                    self.sprite = pygame.transform.flip(self.sprite,True,False)
                    self.flipped = True
                    blitz = True 
                if (angle >0 and angle <= 90) : 
                    angle = 65
                elif (angle <= 0 and angle >= -90):
                    angle =  -72
                self.angle_opening = 180-angle 
            else: 
            
            if self.flipped != False: 
                self.sprite = pygame.transform.flip(self.animation.img(),True,False)
                self.flipped = False  
                blitz = True 
            angle = -angle
        

        weapon_display = pygame.Surface((self.sprite.get_width(),self.sprite.get_height()),pygame.SRCALPHA)
        weapon_display.blit(self.sprite,(0,0))

        
            
        rotated_image,rect = self.rotate(weapon_display,angle,self.pivot,self.render_offset)

        #the gun's opening position  
        #self.opening_pos[0] = self.pivot[0] + math.cos(math.radians(-self.angle_opening)) * sprite_width
        #self.opening_pos[1] = self.pivot[1] + math.sin(math.radians(-self.angle_opening)) * sprite_width
       
        
        self.opening_pos[0] = self.pivot[0] + offset[0]+ math.cos(math.radians(-self.angle_opening)) * sprite_width
        self.opening_pos[1] = self.pivot[1] + offset[1]+ math.sin(math.radians(-self.angle_opening)) * sprite_width
       
        
        if self.knockback[0] < 0: 
            self.knockback[0] = min(self.knockback[0] + 1.45, 0)
        if self.knockback[0] > 0 :
            self.knockback[0] = max(self.knockback[0] -1.45, 0)

        if self.knockback[1] < 0: 
            self.knockback[1] = min(self.knockback[1] + 1.45, 0)
        if self.knockback[1] > 0 :
            self.knockback[1] = max(self.knockback[1] -1.45, 0)
        

        print(angle)
        testSurf = pygame.Surface((2,2))

        if not blitz: 
            surf.blit(testSurf,(self.opening_pos[0]-offset[0],self.opening_pos[1]-offset[1]))
           
            surf.blit(rotated_image,(rect.topleft[0] ,rect.topleft[1] ))
            #surf.blit(testSurf,(rect.topleft[0] ,rect.topleft[1] ))
         

        """