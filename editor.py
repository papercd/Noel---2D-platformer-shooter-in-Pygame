
import pygame
import sys 
from scripts.tilemap import Tilemap,Tile
from scripts.utils import load_images,load_tile_images
from scripts.panel import tile_panel 
from scripts.Pygame_Lights import LIGHT
from scripts.numbers import numbers
from scripts.alphabet import alphabets
from scripts.grass import * 
from scripts.background import Background

from my_pygame_light2d.engine import LightingEngine, Layer
from my_pygame_light2d.light import PointLight
from my_pygame_light2d.hull import Hull


LIGHTMAP_SCALE = 2.5

#now we need to add in the we have the player, now we need to add in the tiles. Now this is where things get a lot more difficult to follow. 

class Editor:
    def __init__(self):
        pygame.init() 
        pygame.display.set_caption('editor')

        
        self.RENDER_SCALE = 2.5
        self.DEFAULT_LIGHT_RADIUS = 890


        self.screen_res = (1440,900)


        self.lights_engine = LightingEngine(screen_res= self.screen_res,native_res= self.screen_res,lightmap_res= (int(self.screen_res[0] / LIGHTMAP_SCALE) , int(self.screen_res[1] / LIGHTMAP_SCALE) ))
        self.lights_engine.set_ambient(225,225,225,225)

        
        

        self.background_surf = pygame.Surface((int(self.screen_res[0]/self.RENDER_SCALE),int(self.screen_res[1]/self.RENDER_SCALE)),pygame.SRCALPHA)
        self.foreground_surf = pygame.Surface((int(self.screen_res[0]/self.RENDER_SCALE),int(self.screen_res[1]/self.RENDER_SCALE)),pygame.SRCALPHA)


        #self.screen = pygame.display.set_mode((1440,900),pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        

        #so coming back to here, we will define an assets dictionary that contains all of the assets
        #(sprites) that we are going to use to create our game. 

        #Now that we have our load_image function defined, let's load the background into our assets 
        #and have that blitted onto our screen rather than just a gray screen. 


        self.assets = {
           
            
            'box' : load_tile_images('tiles/box'),
            #'stone' : load_tile_images('tiles/stone'),
            'grass' : load_tile_images('tiles/grass'), 
            'building_0' : load_tile_images('tiles/building_0',background='transparent'),
            'building_1' : load_tile_images('tiles/building_1',background='transparent'),
            'building_2' : load_tile_images('tiles/building_2',background='transparent'),
            'building_3' : load_tile_images('tiles/building_3',background='transparent'), 
            'building_4' : load_tile_images('tiles/building_4',background='transparent'), 
            'building_5' : load_tile_images('tiles/building_5',background='transparent'), 
            'building_back' : load_tile_images('tiles/building_back',background='transparent'), 
            'building_decor' : load_tile_images('tiles/building_decor',background='transparent'), 
            'lights' : load_tile_images('tiles/lights',background='transparent'), 
            'building_stairs' : load_tile_images('tiles/building_stairs',background='transparent'), 
            'live_grass': load_tile_images('tiles/live_grass',background='black'),

            #'large_decor' : load_tile_images('tiles/large_decor'),
            'spawners' : load_tile_images('tiles/spawners',background='transparent'),
        } 

        self.backgrounds = {
            'start' : Background(self,load_images('backgrounds/start',background='transparent')),
            'building' : Background(self,load_images('backgrounds/building',background='transparent')),
        }

        self.movement = [False,False,False,False]

        self.Tilemap = Tilemap(self,tile_size=16,offgrid_layers=2)

        self.cur_offgrid_layer = 0

        self.offgrid_layer_ind = alphabets('cur_off_layer')
        self.offgrid_layer_num = numbers(self.cur_offgrid_layer)

        try: 
            self.Tilemap.load('map.json')
        except FileNotFoundError:
            pass
        

        for light in self.Tilemap.extract([('lights','0;0'),('lights','1;0'),('lights','2;0'),('lights','3;0'),('lights','4;0')],keep=True):
            light = PointLight(position=(self.RENDER_SCALE*(light.pos[0]*self.Tilemap.tile_size + 8), (light.pos[1]*self.Tilemap.tile_size)*self.RENDER_SCALE), power=1., radius= self.DEFAULT_LIGHT_RADIUS)
            light.set_color(255, 255, 255, 200)
            self.lights_engine.lights.append(light)

        self.gm = GrassManager('data/images/tiles/live_grass',tile_size=self.Tilemap.tile_size,stiffness=600,max_unique = 5,place_range=[1,1])

        #place down grass tiles 
        for key in self.Tilemap.grass: 
            grass_tile = self.Tilemap.grass[key]
            self.gm.place_tile(grass_tile.pos,12,[0,1,2,3,4])
        self.scroll = [0,0]

        #different variables that we can vary to choose different tiles to set down. 
        self.tile_list = list(self.assets)
       
        self.selected = False 

        self.tile_group = 0 

        self.tile_rel_pos = 0  

        self.tile_variant = 0

        self.change_variant = False 

        self.flip_tile = False 

        self.selection_box_button = False 
        self.selection_box = None 
        self.selection_box_start_pos = [0,0]  
        self.selection_box_dim = [0,0]
        self.selection_box_time = 0
        self.delete_selection_box_content = False 
        self.selection_box_del_option = 2
    
        self.clicking = False 
        self.right_clicking = False 
        #self.offgrid_click_redun = None 

        self.left_shift_pressed = False 
        self.scroll_Fast = False 
        self.stick_to_grid = False 

        #Now we are going to add a toggle button that we are going to use to toggle between off-grid tiles and on-grid tiles. 
        self.on_grid = True 

        self.auto_random = False 

        #tile panel attribute 
        self.main_tile_panel =  tile_panel((0,0),self.foreground_surf.get_width() // 5 ,self.assets)

        #grass manager object for grass rendering when placing down grass tiles '
        
        self.dt = 0

        
    
    def run(self):
        while True: 
            #click_var = self.clicking
            self.background_surf.fill((128,128,128))

            #now we want to be able to move around our camera. with the arrow keys. 

            SCROLL_SPEED =3
            SCROLL_INCREM = self.scroll_Fast * 5

            self.scroll[0] += (self.movement[1] - self.movement[0]) * (SCROLL_SPEED+SCROLL_INCREM)
            self.scroll[1] += (self.movement[3] - self.movement[2]) * (SCROLL_SPEED+SCROLL_INCREM)



            render_scroll = (int(self.scroll[0]),int(self.scroll[1]))

            #render the tilemap on the editor window 
            self.backgrounds['building'].render(self.background_surf,render_scroll)
            self.Tilemap.render(self.background_surf, offset = render_scroll)

            self.gm.update_render(self.background_surf,self.dt,offset=render_scroll)

            #Design a tile panel. The tile panel will look like the following: 
            #It will be on the left side of the screen, and it will be SCROLLABLE. This is to fit all the tiles I add to the assets library. Maybe add a sorting system?
            #then below the tile panel will be a GUI that shows all the different functionalities of the editor. So that I don't forget what I'm on right now at the moment. 

            #render the center indicator 
            center_ind = pygame.Surface((1,1))
            center_ind.fill((222,13,255))
            self.background_surf.blit(center_ind,(435-render_scroll[0],240-render_scroll[1]))
            self.lights_engine.hulls = self.Tilemap.update_shadow_objs(self.background_surf,render_scroll,self.RENDER_SCALE)
        
            #render the autotile random factor panel
            """
            if self.auto_random:
                random_ind = pygame.Surface((16,16))
                random_ind.fill((50,30,255))
                self.display.blit(random_ind,(0,100))
            """

            #display the current tile selected from the tile list. 

            

            cur_tile_panel = self.main_tile_panel.return_tile_selection()
            

            if cur_tile_panel:     
                if isinstance(self.assets[cur_tile_panel[3]][cur_tile_panel[5][0]],list):
                    
                    selected_tile_ = pygame.transform.flip(self.assets[cur_tile_panel[3]][cur_tile_panel[5][0]][cur_tile_panel[5][1]].copy(),self.flip_tile,False) 
                else: 
                    selected_tile_ = pygame.transform.flip(self.assets[cur_tile_panel[3]][cur_tile_panel[5][0]].copy(),self.flip_tile,False)

                self.selected = True 
                
            else: 
                self.selected = False 
            
        
            #make the selected tile partially transparent 
            
            #selected_tile_.set_alpha(100)

            #we need to scale down the mouse position as we scaled up our display on our viewing surface twicefold. 
            mpos = pygame.mouse.get_pos() 
            mpos = (mpos[0]/ self.RENDER_SCALE, mpos[1]/self.RENDER_SCALE)

            
            
            tile_pos = (int((mpos[0]+self.scroll[0])//self.Tilemap.tile_size) ,int((mpos[1]+self.scroll[1])//self.Tilemap.tile_size))
            

            #you want to know where your selected tile is going to be placed. 
            if self.stick_to_grid:
                """
                stick_ind_surf = pygame.Surface((16,16))
                stick_ind_surf.fill((188,3,3))
                self.display.blit(stick_ind_surf,(0,60))
                """
                fin_tile_pos = (tile_pos[0]*self.Tilemap.tile_size - self.scroll[0],tile_pos[1]*self.Tilemap.tile_size - self.scroll[1])
            else: 
                fin_tile_pos = mpos 

            #add he toggle part in 
           

           

            
            if self.selection_box_button:
                """
                selec_ind_surf = pygame.Surface((16,16))
                selec_ind_surf.fill((0,100,255))
                self.display.blit(selec_ind_surf,(0,80))
                """

                if self.clicking:  
                    
                    if self.selection_box_time== 0 :
                        self.selection_box_dim = [0,0]
                        self.selection_box_start_pos = (int((mpos[0]+self.scroll[0])) ,int((mpos[1]+self.scroll[1])))
                    else: 
                        self.selection_box_dim[0] = int((mpos[0]+self.scroll[0])) - self.selection_box_start_pos[0]
                        self.selection_box_dim[1] = int((mpos[1]+self.scroll[1]))  - self.selection_box_start_pos[1]
                        self.selection_box = pygame.Rect(self.selection_box_start_pos[0],self.selection_box_start_pos[1],self.selection_box_dim[0],self.selection_box_dim[1])
                    #here you want to implement the selection box creation. 
                    
                    self.selection_box_time = min(2000,self.selection_box_time+1)
                else: 
                    self.selection_box_time = 0

            else:
                if self.on_grid: 
                    """
                    grid_ind_surf = pygame.Surface((16,16))
                    grid_ind_surf.fill((123,6,6))
                    self.display.blit(grid_ind_surf,(0,28))
                    """
                    if self.selected: 
                            
                        self.background_surf.blit(selected_tile_, fin_tile_pos)

                        #now that we have our mouse position, we are going to place the selected tile into our tilemap. 
                        if self.clicking and (mpos[0] >= self.main_tile_panel.x_range): 
                           
                            #so here check if the position of the click is within the selection box. 
                            if self.selection_box:
                                #if there is a selection box, you are going to check if the click position is within the box. 
                                if int((mpos[0]+self.scroll[0])) >= self.selection_box_start_pos[0] and int((mpos[0]+self.scroll[0])) <= self.selection_box_start_pos[0] + self.selection_box_dim[0]and int((mpos[1]+self.scroll[1])) >= self.selection_box_start_pos[1] and int((mpos[1]+self.scroll[1])) <= self.selection_box_start_pos[1] + self.selection_box_dim[1]:
                                    
                                
                                        x_check = int(self.selection_box_start_pos[0]) % self.Tilemap.tile_size
                                        y_check = int(self.selection_box_start_pos[1]) % self.Tilemap.tile_size
                                        if x_check == 0:
                                            x_shift = 0 
                                        else:
                                            x_shift = self.Tilemap.tile_size - x_check 

                                        if y_check == 0:
                                            y_shift = 0 
                                        else:
                                            y_shift = self.Tilemap.tile_size - y_check 
                                        
                                        new_start_x = int(self.selection_box_start_pos[0]) + x_shift
                                        new_start_y = int(self.selection_box_start_pos[1]) + y_shift 

                                        x_range = (self.selection_box_start_pos[0] + self.selection_box_dim[0] - new_start_x ) // self.Tilemap.tile_size
                                        y_range = (self.selection_box_start_pos[1] + self.selection_box_dim[1] - new_start_y ) // self.Tilemap.tile_size

                                        for x in range(x_range):
                                            for y in range(y_range):
                                                
                                                tile_pos_ = ((new_start_x + x*self.Tilemap.tile_size)//self.Tilemap.tile_size,(new_start_y + y*self.Tilemap.tile_size)//self.Tilemap.tile_size)
                                                self.Tilemap.tilemap[str(tile_pos_[0])+';'+str(tile_pos_[1])] = Tile(cur_tile_panel[3],str(cur_tile_panel[5][0]) + ';' + str(cur_tile_panel[5][1]),tile_pos_)

                                        
                            else:
                                
                                self.Tilemap.tilemap[str(tile_pos[0])+';'+str(tile_pos[1])] = Tile(cur_tile_panel[3],str(cur_tile_panel[5][0]) + ';' + str(cur_tile_panel[5][1]),tile_pos)
                       
                    #now that is nice and all, but now I need to be able to delete tiles from our tilemap. 
                    if self.right_clicking: 
                        click_loc = str(tile_pos[0]) + ';' + str(tile_pos[1])
                        if click_loc in self.Tilemap.tilemap: 
                            del self.Tilemap.tilemap[click_loc]

                else: 
                    #off grid tiles 
                    if self.stick_to_grid:
                        if self.selected:
                            self.background_surf.blit(selected_tile_, fin_tile_pos)
                        if self.clicking and (mpos[0] >= self.main_tile_panel.x_range): 
                            if self.selection_box:
                                #if there is a selection box, you are going to check if the click position is within the box. 
                                if int((mpos[0]+self.scroll[0])) >= self.selection_box_start_pos[0] and int((mpos[0]+self.scroll[0])) <= self.selection_box_start_pos[0] + self.selection_box_dim[0]and int((mpos[1]+self.scroll[1])) >= self.selection_box_start_pos[1] and int((mpos[1]+self.scroll[1])) <= self.selection_box_start_pos[1] + self.selection_box_dim[1]:
                                    
                                
                                        x_check = int(self.selection_box_start_pos[0]) % self.Tilemap.tile_size
                                        y_check = int(self.selection_box_start_pos[1]) % self.Tilemap.tile_size
                                        if x_check == 0:
                                            x_shift = 0 
                                        else:
                                            x_shift = self.Tilemap.tile_size - x_check 

                                        if y_check == 0:
                                            y_shift = 0 
                                        else:
                                            y_shift = self.Tilemap.tile_size - y_check 
                                        
                                        new_start_x = int(self.selection_box_start_pos[0]) + x_shift
                                        new_start_y = int(self.selection_box_start_pos[1]) + y_shift 

                                        x_range = (self.selection_box_start_pos[0] + self.selection_box_dim[0] - new_start_x ) // self.Tilemap.tile_size
                                        y_range = (self.selection_box_start_pos[1] + self.selection_box_dim[1] - new_start_y ) // self.Tilemap.tile_size

                                        for x in range(x_range):
                                            for y in range(y_range):
                                                
                                                tile_pos_ = ((new_start_x + x*self.Tilemap.tile_size)//self.Tilemap.tile_size,(new_start_y + y*self.Tilemap.tile_size)//self.Tilemap.tile_size)
                                                self.Tilemap.offgrid_tiles[self.cur_offgrid_layer][str(tile_pos_[0])+';'+str(tile_pos_[1])] = Tile(cur_tile_panel[3],str(cur_tile_panel[5][0]) + ';' + str(cur_tile_panel[5][1]),tile_pos_)

                                        
                            else:
                                
                                self.Tilemap.offgrid_tiles[self.cur_offgrid_layer][str(tile_pos[0])+';'+str(tile_pos[1])] = Tile(cur_tile_panel[3],str(cur_tile_panel[5][0]) + ';' + str(cur_tile_panel[5][1]),tile_pos)

                        if self.right_clicking: 
                            click_loc = str(tile_pos[0]) + ';' + str(tile_pos[1])

                            if click_loc in self.Tilemap.offgrid_tiles[self.cur_offgrid_layer]: 
                                del self.Tilemap.offgrid_tiles[self.cur_offgrid_layer][click_loc]
                    else: 
                        #decorations 


                        if self.selected:

                            self.background_surf.blit(selected_tile_, fin_tile_pos)

                            #you have to add a check for grass tile placement here. 
                            """
                            if self.main_tile_panel.cur_category[0].text == 'live_grass' :
                                #if you have a live_grass tile panel selected, 
                                if self.clicking and (mpos[0] >= self.main_tile_panel.x_range):
                                    
                                    dup = False 
                                    for tile in self.Tilemap.decorations: 
                                        if  tile.pos == (fin_tile_pos[0] + self.scroll[0],fin_tile_pos[1] + self.scroll[1]) and tile.type == cur_tile_panel[3] and tile.variant == str(cur_tile_panel[5][0]) + ';' + str(cur_tile_panel[5][1]):

                                            dup = True 
                                            break
                                    if not dup: 
                                        self.gm.place_tile(((fin_tile_pos[0] + self.scroll[0] )//self.Tilemap.tile_size,(fin_tile_pos[1] + self.scroll[1] )//self.Tilemap.tile_size),12,[0,1,2,3,4])
                                        self.Tilemap.decorations.append(Tile(cur_tile_panel[3],str(cur_tile_panel[5][0]) + ';' + str(cur_tile_panel[5][1]), (fin_tile_pos[0] + self.scroll[0], fin_tile_pos[1] + self.scroll[1])))
                                 
                            else: 
                            """
                            if self.clicking and (mpos[0] >= self.main_tile_panel.x_range):
                                if self.main_tile_panel.cur_category[0].text == 'live_grass' :
                                    check_loc =(int((fin_tile_pos[0] + self.scroll[0] )//self.Tilemap.tile_size),int((fin_tile_pos[1] + self.scroll[1] )//self.Tilemap.tile_size))
                                    #if ((fin_tile_pos[0] + self.scroll[0] )//self.Tilemap.tile_size,(fin_tile_pos[1] + self.scroll[1] )//self.Tilemap.tile_size) not in self.gm.grass_tiles:
                                    placed = self.gm.place_tile(check_loc,12,[0,1,2,3,4])
                                    #print(check_loc)
                                    if placed: 
                                        self.Tilemap.grass[str(check_loc[0])+';'+str(check_loc[1])] =   Tile(cur_tile_panel[3],str(cur_tile_panel[5][0]) + ';' + str(cur_tile_panel[5][1]),check_loc)
                                        #print(self.Tilemap.grass[str(check_loc[0])+';'+str(check_loc[1])].type,self.Tilemap.grass[str(check_loc[0])+';'+str(check_loc[1])].pos,self.Tilemap.grass[str(check_loc[0])+';'+str(check_loc[1])].variant)

                                else: 
                                    dup = False 
                                    #checking for duplicate placements crude method 
                                    for tile in self.Tilemap.decorations: 
                                        """
                                        print((tile.pos,(fin_tile_pos[0] + self.scroll[0],fin_tile_pos[1] + self.scroll[1])))

                                        print((tile.type,cur_tile_panel[3]))

                                        print((tile.variant, str(cur_tile_panel[5][0]) + ';' + str(cur_tile_panel[5][1])))
                                        """
                                        if  tile.pos == (fin_tile_pos[0] + self.scroll[0],fin_tile_pos[1] + self.scroll[1]) and tile.type == cur_tile_panel[3] and tile.variant == str(cur_tile_panel[5][0]) + ';' + str(cur_tile_panel[5][1]):

                                            dup = True 
                                            break

                                    if not dup: 
                                    
                                        self.Tilemap.decorations.append(Tile(cur_tile_panel[3],str(cur_tile_panel[5][0]) + ';' + str(cur_tile_panel[5][1]), (fin_tile_pos[0] + self.scroll[0], fin_tile_pos[1] + self.scroll[1])))
                                
                                            
                                    
                                 


                        if self.right_clicking: 
                            #you have to add a check for grass tile placement here. 
                            check_loc =(int((fin_tile_pos[0] + self.scroll[0] )//self.Tilemap.tile_size),int((fin_tile_pos[1] + self.scroll[1] )//self.Tilemap.tile_size))

                            if check_loc in self.gm.grass_tiles:
                                del self.Tilemap.grass[str(check_loc[0]) + ';' + str(check_loc[1]) ]
                                del self.gm.grass_tiles[check_loc]


                            for tile in self.Tilemap.decorations.copy():
                            #parse variant attribute from tile object to get subscript 
                                variant_sub = tile.variant.split(';')
                                if isinstance(self.assets[tile.type][int(variant_sub[0])],list):
                                    check_rect = pygame.Rect(tile.pos[0] - self.scroll[0],tile.pos[1] - self.scroll[1], self.assets[tile.type][int(variant_sub[0])][int(variant_sub[1])].get_width(),self.assets[tile.type][int(variant_sub[0])][int(variant_sub[1])].get_width())
                                else: 
                                    check_rect = pygame.Rect(tile.pos[0] - self.scroll[0],tile.pos[1] - self.scroll[1], self.assets[tile.type][int(variant_sub[0])].get_width(),self.assets[tile.type][int(variant_sub[0])].get_height())


                                #check_rect = pygame.Rect(tile.pos[0] - self.scroll[0],tile.pos[1] - self.scroll[1], self.assets_[tile.type][tile.variant].get_width(),self.assets[tile.type][tile.variant].get_height())
                                if check_rect.collidepoint(fin_tile_pos):
                                    self.Tilemap.decorations.remove(tile)






                    """

                    if self.selected:
                        self.display.blit(selected_tile_, fin_tile_pos)

                        if fin_tile_pos not in self.Tilemap.offgrid_tiles_pos: 
                            if self.clicking and (mpos[0] >= self.main_tile_panel.x_range): 
                                self.Tilemap.offgrid_tiles.append(Tile(cur_tile_panel[3],str(cur_tile_panel[5][0]) + ';' + str(cur_tile_panel[5][1]), (fin_tile_pos[0] + self.scroll[0],fin_tile_pos[1] + self.scroll[1])))
                                self.Tilemap.offgrid_tiles_pos[(fin_tile_pos[0] + self.scroll[0],fin_tile_pos[1] + self.scroll[1])] = True 

                        
                        
                        if self.clicking and (mpos[0] >= self.main_tile_panel.x_range): 
                            if not self.offgrid_click_redun:
                                self.Tilemap.offgrid_tiles.append(Tile(cur_tile_panel[3],str(cur_tile_panel[5][0]) + ';' + str(cur_tile_panel[5][1]), (fin_tile_pos[0] + self.scroll[0], fin_tile_pos[1] + self.scroll[1]))) 
                                self.offgrid_click_redun = (fin_tile_pos[0] + self.scroll[0], fin_tile_pos[1] + self.scroll[1])
                            else: 
                                if self.offgrid_click_redun != (fin_tile_pos[0] + self.scroll[0], fin_tile_pos[1] + self.scroll[1]):
                                     self.Tilemap.offgrid_tiles.append(Tile(cur_tile_panel[3],str(cur_tile_panel[5][0]) + ';' + str(cur_tile_panel[5][1]), (fin_tile_pos[0] + self.scroll[0], fin_tile_pos[1] + self.scroll[1]))) 

                        
                                    


                            #self.assets[cur_tile_panel[3]][cur_tile_panel[5][0]][cur_tile_panel[5][1]].copy() 
                    if self.right_clicking: 
                        for tile in self.Tilemap.offgrid_tiles.copy():
                            #parse variant attribute from tile object to get subscript 
                            variant_sub = tile.variant.split(';')
                            if isinstance(self.assets[tile.type][int(variant_sub[0])],list):
                                check_rect = pygame.Rect(tile.pos[0] - self.scroll[0],tile.pos[1] - self.scroll[1], self.assets[tile.type][int(variant_sub[0])][int(variant_sub[1])].get_width(),self.assets[tile.type][int(variant_sub[0])][int(variant_sub[1])].get_width())
                            else: 
                                check_rect = pygame.Rect(tile.pos[0] - self.scroll[0],tile.pos[1] - self.scroll[1], self.assets[tile.type][int(variant_sub[0])].get_width(),self.assets[tile.type][int(variant_sub[0])].get_height())


                            #check_rect = pygame.Rect(tile.pos[0] - self.scroll[0],tile.pos[1] - self.scroll[1], self.assets_[tile.type][tile.variant].get_width(),self.assets[tile.type][tile.variant].get_height())
                            if check_rect.collidepoint(fin_tile_pos):
                                del self.Tilemap.offgrid_tiles_pos[(tile.pos[0],tile.pos[1])]
                                self.Tilemap.offgrid_tiles.remove(tile)   
                    """
 
                
            """
            if self.on_grid: 
                grid_ind_surf = pygame.Surface((16,16))
                grid_ind_surf.fill((123,6,6))
                self.display.blit(grid_ind_surf,(0,28))
                self.display.blit(selected_tile_, fin_tile_pos)

                #now that we have our mouse position, we are going to place the selected tile into our tilemap. 
                if self.clicking: 
                    self.Tilemap.tilemap[str(tile_pos[0])+';'+str(tile_pos[1])] = Tile(self.tile_list_[self.tile_group],str(self.tile_rel_pos) + ';' + str(self.tile_variant),tile_pos)
                 #now that is nice and all, but now I need to be able to delete tiles from our tilemap. 
                if self.right_clicking: 
                    click_loc = str(tile_pos[0]) + ';' + str(tile_pos[1])
                    if click_loc in self.Tilemap.tilemap: 
                        del self.Tilemap.tilemap[click_loc]

            if not self.on_grid: 
                #off grid tiles 
                self.display.blit(selected_tile_, fin_tile_pos)

                if self.clicking: 
                    self.Tilemap.offgrid_tiles.append(Tile(self.tile_list_[self.tile_group],str(self.tile_rel_pos) + ';' + str(self.tile_variant), (fin_tile_pos[0] + self.scroll[0], fin_tile_pos[1] + self.scroll[1]))) 
                if self.right_clicking: 
                    for tile in self.Tilemap.offgrid_tiles.copy():asd
                        #parse variant attribute from tile object to get subscript 
                        variant_sub = tile.variant.split(';')
                        if isinstance(self.assets_[tile.type][int(variant_sub[0])],list):
                            check_rect = pygame.Rect(tile.pos[0] - self.scroll[0],tile.pos[1] - self.scroll[1], self.assets_[tile.type][int(variant_sub[0])][int(variant_sub[1])].get_width(),self.assets_[tile.type][int(variant_sub[0])][int(variant_sub[1])].get_width())
                        else: 
                            check_rect = pygame.Rect(tile.pos[0] - self.scroll[0],tile.pos[1] - self.scroll[1], self.assets_[tile.type][int(variant_sub[0])].get_width(),self.assets_[tile.type][int(variant_sub[0])].get_height())


                        #check_rect = pygame.Rect(tile.pos[0] - self.scroll[0],tile.pos[1] - self.scroll[1], self.assets_[tile.type][tile.variant].get_width(),self.assets[tile.type][tile.variant].get_height())
                        if check_rect.collidepoint(fin_tile_pos):
                            self.Tilemap.offgrid_tiles.remove(tile)
            """
            
        
                
            if self.selection_box:
                if self.delete_selection_box_content:
                                
                    x_check = int(self.selection_box_start_pos[0]) % self.Tilemap.tile_size
                    y_check = int(self.selection_box_start_pos[1]) % self.Tilemap.tile_size
                    if x_check == 0:
                        x_shift = 0 
                    else:
                        x_shift = self.Tilemap.tile_size - x_check 

                    if y_check == 0:
                        y_shift = 0 
                    else:
                        y_shift = self.Tilemap.tile_size - y_check 
                    
                    new_start_x = int(self.selection_box_start_pos[0]) + x_shift
                    new_start_y = int(self.selection_box_start_pos[1]) + y_shift 

                    x_range = (self.selection_box_start_pos[0] + self.selection_box_dim[0] - new_start_x ) // self.Tilemap.tile_size
                    y_range = (self.selection_box_start_pos[1] + self.selection_box_dim[1] - new_start_y ) // self.Tilemap.tile_size

                    for x in range(x_range):
                        for y in range(y_range):
                            
                            tile_pos_ = str((new_start_x + x*self.Tilemap.tile_size)//self.Tilemap.tile_size) + ';' + str((new_start_y + y*self.Tilemap.tile_size)//self.Tilemap.tile_size)
                            
                            if self.selection_box_del_option == 0 :
                                delete_target = [self.Tilemap.tilemap]
        
                            elif self.selection_box_del_option == 1: 
                                delete_target = self.Tilemap.offgrid_tiles
                            else: 
                                delete_target = [self.Tilemap.tilemap]
                                delete_target.append(dict for dict in self.Tilemap.offgrid_tiles)


                            for dicts in delete_target:
                                if tile_pos_ in dicts: 
                                    del dicts[tile_pos_]   

                #blit the selection box. 
                pygame.draw.rect(self.background_surf,(0,100,255),(self.selection_box_start_pos[0]-render_scroll[0],self.selection_box_start_pos[1]-render_scroll[1],self.selection_box_dim[0],self.selection_box_dim[1]),2)
            
            #fix this 
            """
            selec_back_surf = pygame.Surface((16,16))
            selec_back_surf.fill((255,255,255))
            self.display.blit(selec_back_surf,(5,5))
            self.display.blit(selected_tile_,(5,5))
            """
            

            #main tile_panel blit

            #print(mpos)
            self.main_tile_panel.update_indicator_panels(self.auto_random,self.stick_to_grid,self.selection_box_button,self.on_grid,self.selection_box_del_option,self.flip_tile)
            self.main_tile_panel.check_mouse_int(mpos)
            self.main_tile_panel.render(self.foreground_surf)
            #pygame.draw.rect(self.background_surf,(48,96,130),(0,0,self.background_surf.get_width()//5,self.background_surf.get_height()/5),2)
            #layer indication panel blit 
            self.offgrid_layer_ind.render(self.foreground_surf,self.foreground_surf.get_width() - self.offgrid_layer_ind.length *1.5,10)
           
            self.offgrid_layer_num.change_number(self.cur_offgrid_layer)
            self.offgrid_layer_num.render(self.foreground_surf.get_width() -  self.offgrid_layer_num.length * 4 ,10,self.foreground_surf)

    
            for event in pygame.event.get():

                if event.type == pygame.VIDEORESIZE:
                    self.lights_engine.release_objects() 

                    pygame.quit()
                    pygame.init()
                    self.screen_res = (event.w, event.h)
                    
                    self.lights_engine = LightingEngine(screen_res= self.screen_res,native_res= self.screen_res,lightmap_res= (int(self.screen_res[0] / LIGHTMAP_SCALE) , int(self.screen_res[1] / LIGHTMAP_SCALE) ))
                    self.lights_engine.set_ambient(225,225,225,225)
                    self.RENDER_SCALE = 2.5
                    self.DEFAULT_LIGHT_RADIUS = 890

                    pygame.display.set_caption('editor')
                    
                    self.background_surf = pygame.Surface((int(self.screen_res[0]/self.RENDER_SCALE),int(self.screen_res[1]/self.RENDER_SCALE)),pygame.SRCALPHA)
                    self.foreground_surf = pygame.Surface((int(self.screen_res[0]/self.RENDER_SCALE),int(self.screen_res[1]/self.RENDER_SCALE)),pygame.SRCALPHA)
                    

                    #print(self.background_surf.get_width())
                    self.main_tile_panel =  tile_panel((0,0),self.foreground_surf.get_width() // 5 ,self.assets)
                    #print("check")
                    
                    
                    self.lights_engine.lights.clear()
                   
                    for light in self.Tilemap.extract([('lights','0;0'),('lights','1;0'),('lights','2;0'),('lights','3;0'),('lights','4;0')],keep=True):
                        light = PointLight(position=(self.RENDER_SCALE*(light.pos[0]*self.Tilemap.tile_size + 8), (light.pos[1]*self.Tilemap.tile_size)*self.RENDER_SCALE), power=1., radius=self.DEFAULT_LIGHT_RADIUS)
                        light.set_color(255, 255, 255, 200)
                        self.lights_engine.lights.append(light)
                    
                    

                    #self.screen = pygame.display.set_mode((event.w,event.h),pygame.RESIZABLE) 

                #We need to define when the close button is pressed on the window. 
                if event.type == pygame.QUIT: 
                    #then pygame is closed, and the system is closed. 
                    pygame.quit() 
                    sys.exit() 
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.clicking = True
                        self.main_tile_panel.check_click(mpos,self.background_surf)
                    if event.button == 3:
                        self.right_clicking = True  
                    """
                    if self.left_shift_pressed : 
                        if self.selected:
                            if event.button == 4:
                                #change category 
                                self.tile_group = (self.tile_group -1) % len(self.tile_list)
                                self.tile_rel_pos=0
                            if event.button == 5:
                                self.tile_group = (self.tile_group +1 ) % len(self.tile_list)
                                self.tile_rel_pos=0
                    else: 
                        if self.selected:
                            if self.change_variant:
                                if event.button == 4:
                                    self.tile_rel_pos = (self.tile_rel_pos -1) % len(self.assets[self.tile_list[self.tile_group]])
                                    self.tile_variant = 0
                                
                                if event.button == 5:
                                    self.tile_rel_pos = (self.tile_rel_pos +1 ) % len(self.assets[self.tile_list[self.tile_group]])
                                    self.tile_variant = 0
                            else: 
                                if isinstance(self.assets[self.tile_list[self.tile_group]][self.tile_rel_pos],list):
                                    if event.button == 4:
                                        self.tile_variant = (self.tile_variant -1) % len(self.assets[self.tile_list[self.tile_group]][self.tile_rel_pos])
                                        
                                    if event.button == 5:
                                        self.tile_variant = (self.tile_variant +1 ) % len(self.assets[self.tile_list[self.tile_group]][self.tile_rel_pos])

                    """

                if event.type == pygame.MOUSEWHEEL:
                    
                    self.main_tile_panel.check_scroll(event.y,mpos,self.background_surf,self.left_shift_pressed,self.change_variant)
                    
                if event.type == pygame.MOUSEBUTTONUP: 
                    if event.button == 1 :
                        self.clicking = False 
                    if event.button == 3:
                        self.right_clicking = False 
                

                #self.background_surf = pygame.Surface((int(self.screen_res[0]/RENDER_SCALE),int(self.screen_res[1]/RENDER_SCALE)),pygame.SRCALPHA)
                    #print(self.background_surf.get_width())
                #self.main_tile_panel =  tile_panel((0,0),self.background_surf.get_width() // 5 ,self.assets)

                #define when the right or left arrow keys are pressed, the corresponding player's movement variable varlues are changed. 
                if event.type == pygame.KEYDOWN: 
                    if pygame.key.get_mods() & pygame.KMOD_LCTRL:
                        if event.key == pygame.K_EQUALS: 
                            self.lights_engine._release_frame_buffers()
                            self.lights_engine._create_frame_buffers()
                            
                            
                            self.RENDER_SCALE = min(5.184,self.RENDER_SCALE * 1.2)
                            self.DEFAULT_LIGHT_RADIUS = min(1845.504, self.DEFAULT_LIGHT_RADIUS *1.2)


                            self.background_surf = pygame.Surface((int(self.screen_res[0]/self.RENDER_SCALE),int(self.screen_res[1]/self.RENDER_SCALE)),pygame.SRCALPHA)
                            self.foreground_surf = pygame.Surface((int(self.screen_res[0]/self.RENDER_SCALE),int(self.screen_res[1]/self.RENDER_SCALE)),pygame.SRCALPHA)

                            
                            

                            #print(self.background_surf.get_width())
                            self.main_tile_panel =  tile_panel((0,0),self.foreground_surf.get_width() // 5 ,self.assets)
                            self.lights_engine.lights.clear()
                   
                            for light in self.Tilemap.extract([('lights','0;0'),('lights','1;0'),('lights','2;0'),('lights','3;0'),('lights','4;0')],keep=True):
                                light = PointLight(position=(int((self.RENDER_SCALE)*(light.pos[0]*self.Tilemap.tile_size + 8)), int((self.RENDER_SCALE)*(light.pos[1]*self.Tilemap.tile_size))), power=1., radius=self.DEFAULT_LIGHT_RADIUS)
                                light.set_color(255, 255, 255, 200)
                                self.lights_engine.lights.append(light)

                        if event.key == pygame.K_MINUS:
                            self.lights_engine._release_frame_buffers()
                            self.lights_engine._create_frame_buffers()
                            

                            self.RENDER_SCALE = max(1.206,self.RENDER_SCALE / 1.2)
                            self.DEFAULT_LIGHT_RADIUS = max(429.2, self.DEFAULT_LIGHT_RADIUS / 1.2)

                            self.background_surf = pygame.Surface((int(self.screen_res[0]/self.RENDER_SCALE),int(self.screen_res[1]/self.RENDER_SCALE)),pygame.SRCALPHA)
                            
                            self.foreground_surf = pygame.Surface((int(self.screen_res[0]/self.RENDER_SCALE),int(self.screen_res[1]/self.RENDER_SCALE)),pygame.SRCALPHA)

                            #print(self.background_surf.get_width())
                            self.main_tile_panel =  tile_panel((0,0),self.foreground_surf.get_width() // 5 ,self.assets)


                            self.lights_engine.lights.clear()
                   
                            for light in self.Tilemap.extract([('lights','0;0'),('lights','1;0'),('lights','2;0'),('lights','3;0'),('lights','4;0')],keep=True):
                                light = PointLight(position=(self.RENDER_SCALE*(light.pos[0]*self.Tilemap.tile_size + 8), (light.pos[1]*self.Tilemap.tile_size)*self.RENDER_SCALE), power=1., radius=self.DEFAULT_LIGHT_RADIUS)
                                light.set_color(255, 255, 255, 200)
                                self.lights_engine.lights.append(light)
           
                        
                        
                    if event.key == pygame.K_a: 
                        self.movement[0] = True 
                    if event.key == pygame.K_d: 
                        self.movement[1] = True
                    if event.key == pygame.K_w:
                        self.movement[2] = True
                    if event.key == pygame.K_s:
                        self.movement[3] = True
                    if event.key == pygame.K_LSHIFT:
                        self.left_shift_pressed = True 
                    if event.key == pygame.K_RSHIFT: 
                        self.scroll_Fast = not self.scroll_Fast
                    if event.key == pygame.K_g: 
                        self.on_grid = not self.on_grid 
                    if event.key == pygame.K_h: 
                        self.stick_to_grid = not self.stick_to_grid
                    if event.key == pygame.K_f: 
                        self.flip_tile = not self.flip_tile

                    if event.key == pygame.K_o: 
                        self.Tilemap.save('map.json')
                    if event.key == pygame.K_t:
                        self.Tilemap.autotile(self.auto_random)
                    if event.key == pygame.K_y: 
                        self.auto_random = not self.auto_random

                    if event.key == pygame.K_v:
                        self.change_variant = True 
                    if event.key == pygame.K_b:
                        self.selection_box_button = not self.selection_box_button
                    if event.key == pygame.K_ESCAPE:
                        self.selection_box = None 
                    if event.key == pygame.K_DELETE:
                        self.delete_selection_box_content = True 
                    if event.key == pygame.K_m:
                        self.selection_box_del_option = min(2,self.selection_box_del_option+1)
                    
                    if event.key == pygame.K_n:
                        self.selection_box_del_option = max(0,self.selection_box_del_option-1)
                    
                    if event.key == pygame.K_LEFTBRACKET:
                        self.cur_offgrid_layer = max(0,self.cur_offgrid_layer-1)
                    if event.key == pygame.K_RIGHTBRACKET:
                        self.cur_offgrid_layer = min(self.Tilemap.offgrid_layers,self.cur_offgrid_layer+1)
                    

                if event.type == pygame.KEYUP: 
                    if event.key == pygame.K_a: 
                        self.movement[0] = False 
                    if event.key == pygame.K_d: 
                        self.movement[1] = False
                    if event.key == pygame.K_w:
                        self.movement[2] = False
                    if event.key == pygame.K_s:
                        self.movement[3] = False
                    if event.key == pygame.K_LSHIFT:
                        self.left_shift_pressed = False 
                    if event.key == pygame.K_v:
                        self.change_variant = False 
                    if event.key == pygame.K_DELETE:
                        self.delete_selection_box_content = False 
                    
                    #if event.key == pygame.K_b:
                     #   self.selection_box_button = False 
        
            #pygame.display.update() updates the screen, and the clock.tick() adds the sleep in between every frame. 
            #self.screen.blit(pygame.transform.scale(self.display,self.screen.get_size()),(0,0))
            

            tex = self.lights_engine.surface_to_texture(self.background_surf)
            self.lights_engine.render_texture(
                tex, Layer.BACKGROUND,
                pygame.Rect(0,0,tex.width *self.RENDER_SCALE,tex.height*self.RENDER_SCALE),
                pygame.Rect(0,0,tex.width,tex.height)
            )
            tex.release()

            tex = self.lights_engine.surface_to_texture(self.foreground_surf)

            self.lights_engine.render_texture(
                tex, Layer.FOREGROUND,
                pygame.Rect(0,0,tex.width *self.RENDER_SCALE,tex.height*self.RENDER_SCALE),
                pygame.Rect(0,0,tex.width,tex.height)
            )
            tex.release()

            self.lights_engine.render((int(render_scroll[0] *self.RENDER_SCALE),int(render_scroll[1] *self.RENDER_SCALE)))
            pygame.display.flip()
            #pygame.display.update()
            self.clock.tick(60)

Editor().run()

