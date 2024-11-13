import pygame
from my_pygame_light2d.engine import Layer_
from random import random

class Bar():
    def __init__(self,x,y,w,h,max_resource):
        self.x = x
        self.y = y
        self.w = w
        self.h = h 
        self.cur_resource = max_resource
        self.max_resource = max_resource
    
    def update_render_pos(self,x,y):
        self.x = x
        self.y = y

    def render(self,render_engine_ref,offset = (0,0)):
        #calculate health ratio 
        ratio = self.hp/ self.max_hp

        back_buffer_surf = pygame.Surface(self.w,self.h)
        front_buffer_surf = pygame.Surface(self.w*ratio, self.h)
        pygame.draw.rect(back_buffer_surf,"black",(0,0))
        pygame.draw.rect(front_buffer_surf,"red",(0,0))

        back_tex = render_engine_ref.surface_to_texture(back_buffer_surf)
        front_tex = render_engine_ref.surface_to_texture(front_buffer_surf)

        render_engine_ref.render_texture(
            back_tex,Layer_.BACKGROUND,
            dest = pygame.Rect(self.x-offset[0],self.y-offset[1],back_tex.width,back_tex.height),
            source = pygame.Rect(0,0,back_tex.width,back_tex.height)
        )
        back_tex.release()
        
        render_engine_ref.render_texture(
            front_tex,Layer_.BACKGROUND,
            dest = pygame.Rect(self.x-offset[0],self.y-offset[1],front_tex.width,front_tex.height),
            source = pygame.Rect(0,0,front_tex.width,front_tex.height)
        )
        back_tex.release()
        front_tex.release()

class HealthBar(Bar):
    
    def __init__(self,x,y,w,h,max_hp,last_shake=False):
        super().__init__(x,y,w,h,max_hp)
        self.mid_cur = self.cur_resource
        self.last_cur = self.cur_resource
        self.shake = 0 
        self.last_shake = last_shake
    

    #here you are going to have three separate bars, one that decreases immediately, and two others that decreases slower than the previous one, and blit them onto one another, and make them a different color. 
    #the fast one will be red, #the 
    def set_pos(self,pos):
        self.x = pos[0]
        self.y=  pos[1]

    

    def update(self,health):
        self.shake = max(0,self.shake -1)
        health_dec = min(7,self.cur_resource - health)
        self.shake = max(health_dec,self.shake)

        self.cur_resource = health
        if int(self.mid_cur) > self.cur_resource:
            self.mid_cur -= 2*(self.mid_cur-self.cur_resource )/4
        
        if int(self.last_cur) > self.cur_resource:
            
            self.last_cur -= (self.last_cur-self.cur_resource )/4
        
    def _render_surface_as_texture(self,surf,render_engine,offset = (0,0)):
        # convert surface into moderngl.Texture using render engine
        tex = render_engine.surface_to_texture(surf)

        # render created surface onto background layer
        render_engine.render_texture(
            tex,Layer_.BACKGROUND,
            dest = pygame.Rect(self.x-offset[0],self.y-offset[1],tex.width,tex.height),
            source = pygame.Rect(0,0,tex.width,tex.height)
        )

        # release texture 
        tex.release()


    def render(self,render_engine_ref,offset = (0,0)):
        #calculate health ratio 
       
       
        ratio = self.cur_resource/ self.max_resource
        ratio_mid = self.mid_cur / self.max_resource
        ratio_last = self.last_cur / self.max_resource

        shake_offset = (0,0)
        if self.shake:
            shake_offset = (random()* self.shake - self.shake/2,random()* self.shake - self.shake/2)
        
        first_surf_buffer = pygame.Surface((self.w,self.h))
        second_surf_buffer = pygame.Surface((self.w*ratio_last,self.h))
        third_surf_buffer = pygame.Surface((self.w*ratio_mid,self.h))
        fourth_surf_buffer = pygame.Surface((self.w*ratio,self.h))

        pygame.draw.rect(first_surf_buffer,(0,0,0,255),(0,0,self.w,self.h))
        pygame.draw.rect(second_surf_buffer,(173,106,29,255),(0,0,self.w*ratio_last,self.h))
        pygame.draw.rect(third_surf_buffer,(225,69,29,255),(0,0,self.w*ratio_mid,self.h))
        pygame.draw.rect(fourth_surf_buffer,(119,48,48,255),(0,0,self.w*ratio,self.h))

        self._render_surface_as_texture(first_surf_buffer,render_engine_ref,offset)
        self._render_surface_as_texture(first_surf_buffer,render_engine_ref,(offset[0] + shake_offset[0],offset[1] + shake_offset[1]))
        self._render_surface_as_texture(first_surf_buffer,render_engine_ref,(offset[0] + shake_offset[0],offset[1] + shake_offset[1]))
        self._render_surface_as_texture(first_surf_buffer,render_engine_ref,(offset[0] + shake_offset[0],offset[1] + shake_offset[1]))
        
        """
        pygame.draw.rect(first_surf_buffer,(0,0,0,255),(self.x-offset[0] - (shake_offset[0] if self.last_shake else 0) ,self.y-offset[1]- (shake_offset[1] if self.last_shake else 0),self.w,self.h))
        pygame.draw.rect(second_surf_buffer,(173,106,29,255),(self.x-offset[0]- shake_offset[0],self.y-offset[1]- shake_offset[1],self.w*ratio_last,self.h))
        pygame.draw.rect(third_surf_buffer,(225,69,29,255),(self.x-offset[0]- shake_offset[0],self.y-offset[1]- shake_offset[1],self.w*ratio_mid,self.h))
        pygame.draw.rect(fourth_surf_buffer,(119,48,48,255),(self.x-offset[0]- shake_offset[0],self.y-offset[1]- shake_offset[1],self.w*ratio,self.h))
        """


class StaminaBar(Bar):
    def __init__(self,x,y,w,h,max_stamina):
        super().__init__(x,y,w,h,max_stamina)

    def set_pos(self,pos):
        self.x = pos[0]
        self.y=  pos[1]

    def update(self,stamina):
        self.cur_resource = stamina 
        pass 

    def render(self,surf,offset = (0,0)):
        #calculate health ratio 
        ratio = self.cur_resource/ self.max_resource
        pygame.draw.rect(surf,(0,0,0,255),(self.x-offset[0],self.y-offset[1],self.w,self.h))
        pygame.draw.rect(surf,(61,44,116,255),(self.x-offset[0],self.y-offset[1],self.w*ratio,self.h))