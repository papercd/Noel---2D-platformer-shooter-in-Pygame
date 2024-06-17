#the HUD script.
#it will contain the inventory, the health bar, and the stamina bar.
#the inventory will show the currently selected weapon, as well as other weapons. LEFt and right . the middle one is the one selected. 
#show the bullet count for selected bullet, 

#it also needs to be screen adjustable. 
from scripts.indicator import indicator
from scripts.health import HealthBar,StaminaBar 
from pygame.transform import scale 
from scripts.panel import inven_panel
from scripts.inventory import * 


class HUD: 
    def __init__(self,player_entity,bar_UI,display_size):
       
       self.player_entity = player_entity
       self.display_size = display_size 

       self.bar_height = bar_UI.get_height() -4
       
       self.health_bar_width = self.player_entity.health
       self.stamina_bar_width = self.player_entity.stamina

       self.health_bar_UI = scale(bar_UI,(self.health_bar_width + 4,self.bar_height+ 4))
       self.stamina_bar_UI = scale(bar_UI,(self.stamina_bar_width + 4,self.bar_height+ 4))
        
       self.health_bar = HealthBar( 0,0,self.health_bar_width,self.bar_height, self.health_bar_width)
       self.stamina_bar = StaminaBar( 0,0,self.stamina_bar_width,self.bar_height,self.stamina_bar_width) 
       
       self.health_bar_render_position = (self.display_size[0]//12,self.display_size[1] - self.bar_height * 6)
       self.stamina_bar_render_position = (self.display_size[0]//12,self.display_size[1] - self.bar_height * 5 +4)

       #set render position for health and stamina bars 
       self.health_bar.set_pos(self.health_bar_render_position)
       self.stamina_bar.set_pos(self.stamina_bar_render_position)


       #create the inven panel 
       self.inven_panel = inven_panel((self.display_size[0]//12 + self.health_bar.w  + 16, self.display_size[1] - self.bar_height * 6),self.player_entity)

       #create the inventories
       self.inven_list = [
           Inventory("ARMS", 1, 5, self.inven_panel.topleft[0] + 50, self.inven_panel.topleft[1] -22 , 1, 1, bin_active=False),
           Inventory("Small", 1, 3, 700, 400, 1, 99)
       ]
       
       


    def render_inven(self,cursor,surf,offset= [0,0]):
        pass 
    
        #self.inven_list[0].update(surf,0,self.inven_list,cursor,"") 
        


    def render(self,surf,cursor,offset = [0,0]):
        #render character face 


        #render character health and stamina 
        self.health_bar.update(self.player_entity.health)
        self.stamina_bar.update(self.player_entity.stamina)

        surf.blit(self.health_bar_UI,(self.health_bar_render_position[0]- 2, self.health_bar_render_position[1]-2))
        self.health_bar.render(surf,offset)

        surf.blit(self.stamina_bar_UI,(self.stamina_bar_render_position[0]- 2, self.stamina_bar_render_position[1]-2))
        self.stamina_bar.render(surf,offset)
        
        #render health and stamina indicator 
        """
        health_ind = indicator(int(self.health_bar.cur_resource),int(self.health_bar.max_resource))
        health_ind.render(self.health_bar.x + self.health_bar.w //2 ,self.health_bar.y-1,surf)
        
        #render the stamina bar indicator 
        stamina_ind = indicator(int(self.stamina_bar.cur_resource),int(self.stamina_bar.max_resource))
        stamina_ind.render(self.stamina_bar.x+self.stamina_bar.w//2,self.stamina_bar.y-1,surf)
        """
        #render the weapon panel 
        self.inven_panel.render(surf,offset)

        #render the items
        self.inven_list[0].update(surf,0,self.inven_list,cursor,"")




