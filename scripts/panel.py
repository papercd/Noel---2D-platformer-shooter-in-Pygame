import pygame 

from scripts.alphabet import alphabets 
from scripts.numbers import numbers 
from scripts.utils import load_images


class inven_panel: 
    def __init__(self,topleft,player_ent):
        self.topleft = topleft

        self.done_expanding = 0

        self.player = player_ent 

        self.TL_cur_weapon_frame = load_images("indicator/cur_weapon_indicator")

        self.ammo_indicator = numbers(0)

        self.display_weapons = []
    

    def render(self,surf,offset = (0,0),expanded= False):
        

        #instead of having one panel to print all the weapons, you are going to have like a rotation 
        if not expanded: 
            self.done_expanding = max(0,self.done_expanding-1)
        else: 
            self.done_expanding = min(4,self.done_expanding+1)

        
        if self.player.cur_weapon_node: 
            if self.player.cur_weapon_node.prev: 

                org_image_size = self.player.cur_weapon_node.prev.weapon.weapon_img.get_size()
                display_img = self.player.cur_weapon_node.prev.weapon.shrunk_weapon_img
                display_img.set_alpha(185* (self.done_expanding/4))
                display_offset = (org_image_size[0]/2 - display_img.get_width()/2,-14* ((6-self.player.changing_done)/6) +org_image_size[1]/2 - display_img.get_height()/2  )
                surf.blit(display_img,(self.topleft[0] - offset[0] + display_offset[0],self.topleft[1] - offset[1] + display_offset[1]))

            surf.blit(self.player.cur_weapon_node.weapon.weapon_img,(self.topleft[0] - offset[0] ,self.topleft[1] - offset[1]))
  
            
            new_mag_count = len(self.player.cur_weapon_node.weapon.magazine)
        
            shot = new_mag_count != self.ammo_indicator.number
            self.ammo_indicator.change_number(new_mag_count)
            self.ammo_indicator.render(self.topleft[0] - offset[0] ,self.topleft[1] - offset[1] - (2 if shot else 0),surf)

            if self.player.cur_weapon_node.next:
                org_image_size = self.player.cur_weapon_node.next.weapon.weapon_img.get_size()
                display_img = self.player.cur_weapon_node.next.weapon.shrunk_weapon_img
                display_img.set_alpha(185* (self.done_expanding/4))
                display_offset = (org_image_size[0]/2 - display_img.get_width()/2,14* ((6-self.player.changing_done)/6) +org_image_size[1]/2 - display_img.get_height()/2  )
                surf.blit(display_img,(self.topleft[0] - offset[0] + display_offset[0],self.topleft[1] - offset[1] + display_offset[1]))


        change_offset = [(0,0),(-1,-1),(-2,-2)]
        surf.blit(self.TL_cur_weapon_frame[self.player.changing_done//3],(self.topleft[0] - offset[0] + change_offset[self.player.changing_done//3][0]-1,self.topleft[1] - offset[1]+change_offset[self.player.changing_done//3][1] -3 ))




class tile_panel:

    def __init__(self,topleft,x_bound,tiles):

        self.tile_dict = tiles 
        self.selected_tile_panel = None 

        self.topleft = topleft
        self.tile_panels = []
        self.x_range = x_bound

        self.cur_category = None 
        self.categories = []
        
        self.category_gui = self.create_category_gui(tiles) 

        self.category_gui_scroll = 0
        self.tile_panel_scroll = 0
        
        self.indicator_labels = (alphabets('stick_grid'),alphabets('on_grid'),alphabets('auto_random'),
                                 alphabets('selec_box'),alphabets('box_del_option'),alphabets('flipped'),alphabets('mark'))

        self.indicators = [False,False,False,False,2,False]
        

        self.fill_tile_panels(tiles) 
    

    def create_category_gui(self,tiles):
        y_pos = 3
        for key in tiles: 
            self.categories.append([alphabets(key),False,y_pos,False])
            y_pos += 6
         

    def fill_tile_panels(self,tiles,category = None):
        self.tile_panels.clear()
        #tiles is a dictionary that contains lists of images.
       
        for key in tiles:
            
            if category: 
                if key == category: 
                    tile_list = tiles[key] 
                else: 
                    continue 
            else: 
                tile_list = tiles[key]

            longest_length = 0
            tile_rel_pos = 0
            for list_or_img in tile_list:
                
                if isinstance(list_or_img,list):
                    tile_res_pos_list = []

                    for tile_variant ,img in enumerate(list_or_img) :
                        if img.get_height() > longest_length:
                            longest_length = img.get_height() 
                        if tile_res_pos_list:
                            last_tile_panel = tile_res_pos_list[-1]
                            pot_pos = [0,0]
                                
                            pot_x = last_tile_panel[0][0] + last_tile_panel[1][0] +3
                            pot_y =last_tile_panel[0][1] 
                            if pot_x + img.get_width() > self.x_range or key != last_tile_panel[3]:
                                #if the blit position of the tile panel exceeds the x range of the entire panel,
                                #move onto new line. 
                                pot_pos = [3,pot_y + longest_length + 2]
                                longest_length = img.get_height() 
                                #this needs to be dynamic. change later. 


                            else: 
                                pot_pos = [pot_x,pot_y]
                        else: 
                            if self.tile_panels:
                                last_tile_panel = self.tile_panels[-1]
                            
                                if isinstance(last_tile_panel,list) and isinstance(last_tile_panel[-1],list):
                                    last_tile_panel = last_tile_panel[-1]
                                
                                pot_pos = [0,0]
                                
                                pot_x = last_tile_panel[0][0] + last_tile_panel[1][0] +3
                                pot_y =last_tile_panel[0][1] 
                                if pot_x + img.get_width() > self.x_range or key != last_tile_panel[3]:
                                    #if the blit position of the tile panel exceeds the x range of the entire panel,
                                    #move onto new line. 
                                    pot_pos = [3,pot_y + longest_length + 2 + 6* (key != last_tile_panel[3])]
                                    longest_length = img.get_height() 
                                    #this needs to be dynamic. change later. 


                                else: 
                                    pot_pos = [pot_x,pot_y]
                            
                            else: 
                                pot_pos = [3,3]

                        tile_panel_att  = [pot_pos,img.get_size(),img.copy(),key,False,(tile_rel_pos,tile_variant)]
                        tile_res_pos_list.append(tile_panel_att)
                        #self.tile_panels.append(tile_panel_att)
                    self.tile_panels.append(tile_res_pos_list)
                else: 
                    
                    if list_or_img.get_height() > longest_length:
                            longest_length = list_or_img.get_height() 
                    

                    if self.tile_panels:
                        last_tile_panel = self.tile_panels[-1]
                        if isinstance(last_tile_panel,list) and isinstance(last_tile_panel[-1],list):
                            last_tile_panel = last_tile_panel[-1]
                        pot_pos = [0,0]
                        
                        pot_x = last_tile_panel[0][0] + last_tile_panel[1][0] +3
                        pot_y =last_tile_panel[0][1] 
                        if pot_x + list_or_img.get_width() > self.x_range or key != last_tile_panel[3]:
                            #if the blit position of the tile panel exceeds the x range of the entire panel,
                            #move onto new line. 
                            pot_pos = [3,pot_y + longest_length + 2+6* (key != last_tile_panel[3])]
                            longest_length = list_or_img.get_height() 
                            #this needs to be dynamic. change later. 


                        else: 
                            pot_pos = [pot_x,pot_y]
                            
                    else: 
                        pot_pos = [3,3]

                    tile_panel_att  = [pot_pos,list_or_img.get_size(),list_or_img.copy(),key,False,(tile_rel_pos,0)]
                    self.tile_panels.append(tile_panel_att)

                tile_rel_pos +=1 
                   
    
    def check_scroll(self,up_down,mpos,surf,lshift_pressed,variant_change):

        if variant_change and self.selected_tile_panel:
            
           

            if self.cur_category:

                tile_res_and_var = self.selected_tile_panel[5]

                tile_panel_list =  self.tile_dict[self.selected_tile_panel[3]]

                tile_panel_list_list = tile_panel_list[tile_res_and_var[0]]
                if not isinstance(tile_panel_list_list,pygame.surface.Surface):
                    total_variants = len(tile_panel_list_list)
                
                    if total_variants != 1:
                        #if there is more than one variant, then change the variant. 

                        #deselect first 

                        self.selected_tile_panel[4] = False 

                        self.selected_tile_panel = self.tile_panels[tile_res_and_var[0]][min(total_variants-1,tile_res_and_var[1] + 1) if up_down == 1 else max(0,tile_res_and_var[1] - 1)] 

                        self.selected_tile_panel[4] = True 
                
            else: 
                running_sum_tile_res_pos = 0 
                for key in self.tile_dict:
                    if key != self.selected_tile_panel[3]:
                        tile_list = self.tile_dict[key]
                        res_pos_count = len(tile_list)
                        running_sum_tile_res_pos += res_pos_count
                    else: 
                        break 
                
                tile_res_and_var = self.selected_tile_panel[5]

                tile_panel_list = self.tile_panels[running_sum_tile_res_pos + tile_res_and_var[0]]

                if isinstance(tile_panel_list,list) and isinstance(tile_panel_list[-1],list):
                    
                    total_variants = len(tile_panel_list)

                    if total_variants != 1:

                        self.selected_tile_panel[4] = False 

                        self.selected_tile_panel = self.tile_panels[running_sum_tile_res_pos + tile_res_and_var[0]][min(total_variants-1,tile_res_and_var[1] + 1) if up_down == 1 else max(0,tile_res_and_var[1] - 1)] 

                        self.selected_tile_panel[4] = True 
                
                
                


                
            


        
        #check category panel scroll 
        if (mpos[0] >= 0 and mpos[0] <= self.x_range )and (mpos[1]>= 0 and mpos[1] <= surf.get_height()/5):

            if lshift_pressed:
                
                if self.cur_category:
                    cur_category_index = self.categories.index(self.cur_category) 
                    
                    if up_down == 1:
                        cur_category_index = min(len(self.categories)-1, cur_category_index + 1)
                    else: 
                        cur_category_index = max(0,cur_category_index -1)
                   
                    self.cur_category[3] = False 
                    self.cur_category = self.categories[cur_category_index]
                    self.cur_category[3] = True
                    self.fill_tile_panels(self.tile_dict,self.cur_category[0].text) 
                    

            else:          
                if self.categories[-1][2]  >= 5 and up_down == -1:
                    #and self.categories[-1][2] < surf.get_height()/5 +5:  
                    for category in self.categories:
                        category[2] +=up_down * 7
                if  self.categories[0][2] <= surf.get_height()/5 -10  and up_down == 1:
                    for category in self.categories:
                        category[2] +=up_down * 7

        #check tile panel scroll 
        else: 
            #if left shift is pressed, that means that the rel tile pos is gonna change. 
            if lshift_pressed:
                if self.selected_tile_panel :
                    

                    if self.cur_category: 
                        if self.cur_category[0].text != self.selected_tile_panel[3]:
                        
                            self.selected_tile_panel[4] = False 
                            self.selected_tile_panel = self.tile_panels[0]
                            if isinstance(self.selected_tile_panel,list) and isinstance(self.selected_tile_panel[-1],list): 
                                self.selected_tile_panel = self.selected_tile_panel[0]


                            self.selected_tile_panel[4] = True 
                    else: 
                        pass

                    #if a tile panel is indeed selected, change the relative pos of the tile. 
                    tile_res_and_var = self.selected_tile_panel[5] 


                    total_tile_res_pos = len(self.tile_dict[self.selected_tile_panel[3]])
                
                    if up_down ==1:
                        new_res_pos = min(total_tile_res_pos -1,tile_res_and_var[0] + 1) 
                    else: 
                        new_res_pos = max(0,tile_res_and_var[0] - 1)
                    
                    
                    self.selected_tile_panel[4] = False 

                    if self.cur_category:
                        
                        self.selected_tile_panel = self.tile_panels[new_res_pos]
                    else: 
                        running_sum_tile_res_pos = 0 
                        for key in self.tile_dict:
                            if key != self.selected_tile_panel[3]:
                                tile_list = self.tile_dict[key]
                                res_pos_count = len(tile_list)
                                running_sum_tile_res_pos += res_pos_count
                            else: 
                                break 
                    
                        self.selected_tile_panel = self.tile_panels[running_sum_tile_res_pos+new_res_pos] 
                        

                    if isinstance(self.selected_tile_panel,list) and isinstance(self.selected_tile_panel[-1],list): 
                        self.selected_tile_panel = self.selected_tile_panel[0]

                    self.selected_tile_panel[4] = True 

                else: 
                    self.selected_tile_panel = self.tile_panels[0]

            if (mpos[0] >= 0 and mpos[0] <= self.x_range )and (mpos[1]>=  surf.get_height()/5 and mpos[1] <= surf.get_height()*4/5):
                
                
                if not lshift_pressed and not variant_change:
                    #panels position scroll when shift is not pressed. 
                    
                    last_tile_panel = self.tile_panels[-1]
                    if isinstance(last_tile_panel,list) and isinstance(last_tile_panel[-1],list):
                        last_tile_panel = last_tile_panel[-1]
                    if last_tile_panel[0][1]  >= 5   and up_down == -1:
                        
                        #and self.categories[-1][2] < surf.get_height()/5 +5:  
                        for tile_panel in self.tile_panels:
                            if isinstance(tile_panel,list) and isinstance(tile_panel[-1],list):
                                for tile_panels_within in tile_panel:
                                    tile_panels_within[0][1] += up_down * 20  
                            else: 
                                tile_panel[0][1] +=up_down * 20
                    first_tile_panel = self.tile_panels[0]
                    if isinstance(first_tile_panel,list) and isinstance(first_tile_panel[-1],list):
                        first_tile_panel = first_tile_panel[0]

                    if  first_tile_panel[0][1] <= surf.get_height()*3/5 -20  and up_down == 1:
                        for tile_panel in self.tile_panels:
                            if isinstance(tile_panel,list) and isinstance(tile_panel[-1],list):
                                for tile_panels_within in tile_panel:
                                    tile_panels_within[0][1] += up_down * 20  
                            else: 
                                tile_panel[0][1] +=up_down * 20

         
    def return_tile_selection(self):
        return self.selected_tile_panel 
        

    def update_indicator_panels(self,auto_random,stick_grid,selection_box_selec,on_grid,sel_box_del_option,flip_tile,mark):

        self.indicators = [stick_grid,on_grid,auto_random,selection_box_selec,sel_box_del_option,flip_tile,mark]
        


    def check_mouse_int(self,mpos):
        #check category panel hover 
        for category in self.categories:
            
            if  (0 <= mpos[0] and mpos[0] <= category[0].length +5  ) and (category[2] <= mpos[1] and mpos[1] <= category[2] + 5 ):
                category[1] = True 
            else: 
                category[1] = False   
        #check tile panel hover
      

    def check_click(self,mpos,surf):
        
        
        exclude = -1
        if (mpos[0] >= 0 and mpos[0] <= self.x_range )and (mpos[1]>= 0 and mpos[1] <= surf.get_height()/5):
            for i, category in enumerate(self.categories):
                if  (0 <= mpos[0] and mpos[0] <= category[0].length ) and (category[2] <= mpos[1] and mpos[1] <= category[2] + 5 ):
                    if self.cur_category:
                        self.cur_category[3] = False 
                    self.cur_category = category
                    self.cur_category[3] = True
                    exclude = i 
                    self.fill_tile_panels(self.tile_dict,self.cur_category[0].text) 
                   
                        
            if exclude == -1:
                if self.cur_category:
                    self.cur_category[3] = False 
                self.cur_category = None  
                self.fill_tile_panels(self.tile_dict) 
            """
            for i, category in enumerate(self.categories):
                if i != exclude:
                    category[3] = False 
            """ 
        elif (mpos[0] >= 0 and mpos[0] <= self.x_range )and (mpos[1]>=  surf.get_height()/5 and mpos[1] <= surf.get_height()*4/5):
            tile_res_pos_ = -1
            variation = -1

            for tile_res_pos,tile_panel in enumerate(self.tile_panels):
                if isinstance(tile_panel,list) and isinstance(tile_panel[-1],list):
                    for var, tile_panel_within in enumerate(tile_panel): 
                        if  (tile_panel_within[0][0] <= mpos[0] and mpos[0] <= tile_panel_within[0][0] + tile_panel_within[1][0] ) and (tile_panel_within[0][1] +surf.get_height()/5 <= mpos[1] and mpos[1] <= tile_panel_within[0][1] + tile_panel_within[1][1] + surf.get_height()/5) :
                            if self.selected_tile_panel:
                                self.selected_tile_panel[4] = False
                            self.selected_tile_panel = tile_panel_within
                            self.selected_tile_panel[4] = True 

                            variation = var  
                            tile_res_pos_ = tile_res_pos
                else: 
                    if  (tile_panel[0][0] <= mpos[0] and mpos[0] <= tile_panel[0][0] + tile_panel[1][0] ) and (tile_panel[0][1] +surf.get_height()/5 <= mpos[1] and mpos[1] <= tile_panel[0][1] + tile_panel[1][1] + surf.get_height()/5) :
                        if self.selected_tile_panel:
                            self.selected_tile_panel[4] = False
                        self.selected_tile_panel = tile_panel
                        self.selected_tile_panel[4] = True 
                        
                        variation = 0
                        tile_res_pos_ = tile_res_pos

            if variation == -1 and tile_res_pos_ == -1:
                if self.selected_tile_panel:
                    self.selected_tile_panel[4] = False     
                self.selected_tile_panel = None 
            """
            for i, tile_panel in enumerate(self.tile_panels):
                if i != exclude_tile:
                    tile_panel[4] = False 
            """
            
                


    def render(self,surf):
        
        pygame.draw.rect(surf,(97,97,97), (0,0,self.x_range,surf.get_height()))

        #render the category GUI first 
        
        for category in self.categories:
            if category[2] >= 0 and category[2] <= surf.get_height()/5 -5:

                category[0].render(surf,6 if category[1] else 3,category[2])
                if category[3]:
                    pygame.draw.rect(surf,(48,130,64),(category[0].length + 6,category[2]+ 2, 5,2))
            
        #render the rect 
        pygame.draw.rect(surf,(48,96,130),(0,0,self.x_range,surf.get_height()/5),2)
        
        
        for tile_panel in self.tile_panels:
            if isinstance(tile_panel,list) and isinstance(tile_panel[-1],list):
                for varition in tile_panel:
                    #print(varition)
                    if (varition[0][1]  >= 0) and (varition[0][1] +varition[1][1] <= surf.get_height()*3/5):
                
                        if varition[4] :
                            pygame.draw.rect(surf,(166,16,16),(varition[0][0]-1,surf.get_height()/5+varition[0][1]-1,varition[1][0]+2,varition[1][1]+2),1)
                        surf.blit(varition[2],(varition[0][0],surf.get_height()/5 + varition[0][1]))

            else: 
                if (tile_panel[0][1]  >= 0) and (tile_panel[0][1] +tile_panel[1][1] <= surf.get_height()*3/5):
                
                    if tile_panel[4] :
                        pygame.draw.rect(surf,(166,16,16),(tile_panel[0][0]-1,surf.get_height()/5+tile_panel[0][1]-1,tile_panel[1][0]+2,tile_panel[1][1]+2),1)
                    surf.blit(tile_panel[2],(tile_panel[0][0],surf.get_height()/5 + tile_panel[0][1]))

        #render the rect 
        pygame.draw.rect(surf,(48,96,130),(0,surf.get_height()/5,self.x_range,surf.get_height()*3/5),2)
        

        #now render the indicator panel GUI 
        for y_pos,label in enumerate(self.indicator_labels):
            label.render(surf,3,surf.get_height()*4/5 + 3 + y_pos*12)
            if self.indicators[y_pos]:
                pygame.draw.rect(surf,(118,66 + (self.indicators[y_pos]-1) * 80 ,138),(label.length + 8,surf.get_height()*4/5 + 5 + y_pos*12,10,2))
            
    
        #render the rect 
        pygame.draw.rect(surf,(48,96,130),(0,surf.get_height()*4/5,self.x_range,surf.get_height()/5),2)