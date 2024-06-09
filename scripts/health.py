import pygame
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

    def render(self,surf,offset = (0,0)):
        #calculate health ratio 
        ratio = self.hp/ self.max_hp
        pygame.draw.rect(surf,"black",(self.x-offset[0],self.y-offset[1],self.w,self.h))
        pygame.draw.rect(surf,"red",(self.x-offset[0],self.y-offset[1],self.w*ratio,self.h))

class HealthBar(Bar):
    
    def __init__(self,x,y,w,h,max_hp):
        super().__init__(x,y,w,h,max_hp)
        self.mid_cur = self.cur_resource
        self.last_cur = self.cur_resource
        self.shake = 0 
    

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
        
        

    def render(self,surf,offset = (0,0)):
        #calculate health ratio 
       
       
        ratio = self.cur_resource/ self.max_resource
        ratio_mid = self.mid_cur / self.max_resource
        ratio_last = self.last_cur / self.max_resource

        shake_offset = (0,0)
        if self.shake:
            shake_offset = (random()* self.shake - self.shake/2,random()* self.shake - self.shake/2)
        
            

        pygame.draw.rect(surf,(0,0,0,0),(self.x-offset[0] ,self.y-offset[1],self.w,self.h))

        pygame.draw.rect(surf,(173,106,29,255),(self.x-offset[0]- shake_offset[0],self.y-offset[1]- shake_offset[1],self.w*ratio_last,self.h))
        pygame.draw.rect(surf,(225,69,29,255),(self.x-offset[0]- shake_offset[0],self.y-offset[1]- shake_offset[1],self.w*ratio_mid,self.h))
        pygame.draw.rect(surf,(119,48,48,255),(self.x-offset[0]- shake_offset[0],self.y-offset[1]- shake_offset[1],self.w*ratio,self.h))
        

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
        pygame.draw.rect(surf,(0,0,0,0),(self.x-offset[0],self.y-offset[1],self.w,self.h))
        pygame.draw.rect(surf,(61,44,116,255),(self.x-offset[0],self.y-offset[1],self.w*ratio,self.h))