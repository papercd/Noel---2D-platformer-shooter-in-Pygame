 
from scripts.layer import Layer_
import os
import random
import math
import time 
from scripts.data import SparkData
from copy import deepcopy
from my_pygame_light2d.light import PointLight

import pygame

BURN_CHECK_OFFSETS = [(-1,0),(1,0)]
BURN_SPREAD_RANGE = 3




def normalize(val, amt, target):
    if val > target + amt:
        val -= amt
    elif val < target - amt:
        val += amt
    else:
        val = target
    return val

# the main object that manages the grass system
class GrassManager:
    
    _instance = None 

    @staticmethod
    def get_instance(grass_asset = None,tile_size:int = 16,shade_amount:int = 100, stiffness:int = 360, max_unique:int = 10, 
                     place_range:list[int,int] = [1,1] , padding:int = 13, burn_spread_speed:int = 1, burn_rate:int = 1):
        if GrassManager._instance is None: 
            GrassManager._instance = GrassManager(grass_asset,tile_size,shade_amount,stiffness,max_unique,\
                                                  place_range,padding,burn_spread_speed,burn_rate)
        return GrassManager._instance


    def __init__(self, grass_asset,tile_size=15, shade_amount=100, stiffness=360, max_unique=10, place_range=[1, 1], padding=13,burn_spread_speed = 1,burn_rate = 1):

        self.ga = grass_asset
        self.ga.gm = self 
        
        # caching variables
        self.grass_id = 0
        self.grass_cache = {}
        self.shadow_cache = {}
        self.formats = {}

        # tile data
        self.render_list = set()
        self.grass_tiles = {}
        self.burning_grass_tiles = {}

        self.visible_tile_range = (0,0)
        self.base_pos = (0,0)

        # config
        self.tile_size = tile_size
        self.shade_amount = shade_amount
        self.stiffness = stiffness
        self.max_unique = max_unique
        self.vertical_place_range = place_range
        self.ground_shadow = [0, (0, 0, 0), 100, (0, 0)]
        self.padding = padding
        self.burn_spread_speed = burn_spread_speed
        self.burn_rate = burn_rate
        
    # enables circular shadows that appear below each blade of grass
    def enable_ground_shadows(self, shadow_strength=40, shadow_radius=2, shadow_color=(0, 0, 1), shadow_shift=(0, 0)):
        # don't interfere with colorkey
        if shadow_color == (0, 0, 0):
            shadow_color = (0, 0, 1)

        self.ground_shadow = [shadow_radius, shadow_color, shadow_strength, shadow_shift]

    # either creates a new grass tile layout or returns an existing one if the cap has been hit
    def get_format(self, format_id, data, tile_id):
        if format_id not in self.formats:
            self.formats[format_id] = {'count': 1, 'data': [(tile_id, data)]}
        elif self.formats[format_id]['count'] >= self.max_unique:
            return deepcopy(random.choice(self.formats[format_id]['data']))
        else:
            self.formats[format_id]['count'] += 1
            self.formats[format_id]['data'].append((tile_id, data))
    
    def burn_tile(self,location):
        loc = tuple(location)
        if loc in self.grass_tiles: 
            #if the location does indeed have grass, burn the grass.
            self.burning_grass_tiles[loc] = self.grass_tiles.pop(loc)
            self.burning_grass_tiles[loc].swapped_dict = True
            self.burning_grass_tiles[loc].burning = 0
            self.burning_grass_tiles[loc].left_burn_progression_time = 20
            self.burning_grass_tiles[loc].right_burn_progression_time =20
        


    # attempt to place a new grass tile
    def place_tile(self, location, density, grass_options):
        # ignore if a tile was already placed in this location
        loc = tuple(location)
        if loc not in self.grass_tiles and loc not in self.burning_grass_tiles:
            self.grass_tiles[loc] = GrassTile(self.tile_size, (location[0] * self.tile_size, location[1] * self.tile_size), density, grass_options, self.ga, self)
            return True 
        return False 

    # apply a force to the grass that causes the grass to bend away
    def apply_force(self, location, radius, dropoff):
        location = (int(location[0]), int(location[1]))
        grid_pos = (int(location[0] // self.tile_size), int(location[1] // self.tile_size))
        tile_range = math.ceil((radius + dropoff) / self.tile_size)
        for y in range(tile_range * 2 + 1):
            y = y - tile_range
            for x in range(tile_range * 2 + 1):
                x = x - tile_range
                pos = (grid_pos[0] + x, grid_pos[1] + y)
                if pos in self.grass_tiles:
                    self.grass_tiles[pos].apply_force(location, radius, dropoff)
                if pos in self.burning_grass_tiles:
                    self.burning_grass_tiles[pos].apply_force(location, radius, dropoff)




    def update(self,quadtree,surf,dt, offset = (0,0),rot_function = None):
        pass 

    def render(self,qquadtree,surf,dt, offset = (0,0),rot_function = None):
        pass        

    # an update and render combination function

    def update(self,native_res,dt, offset=(0, 0), rot_function=None):
        self.visible_tile_range = (int(native_res[0] // self.tile_size) + 1, int(native_res[1] // self.tile_size) + 1)
        self.base_pos = (int(offset[0] // self.tile_size), int(offset[1] // self.tile_size))

        # Precompute the visible grass tiles 
        self.render_list = {(self.base_pos[0] + x, self.base_pos[1] + y) 
                    for y in range(self.visible_tile_range[1]) 
                    for x in range(self.visible_tile_range[0]) 
                    if (self.base_pos[0] + x, self.base_pos[1] + y) in self.grass_tiles}

        # Render shadows if ground_shadow is set
        """
        if self.ground_shadow[0]:
            shadow_offset = (offset[0] - self.ground_shadow[3][0], offset[1] - self.ground_shadow[3][1])
            for pos in render_list:
                self.grass_tiles[pos].render_shadow(offset=shadow_offset)
        """

        # Track tiles to add to burning_grass and to remove from it  
        keys_to_remove = []
        keys_to_add = []


        for key, tile in self.burning_grass_tiles.items():
            if not tile.appended: 
                self.game.lights_engine.lights.append(tile.light)
                tile.appended = True 
            if tile.burn_life >45:    
                # Update neighboring grass tiles based on burn status
                for offset_ in BURN_CHECK_OFFSETS:
                    check_pos = (key[0] + offset_[0], key[1] + offset_[1])
                    neighbor_tile = self.grass_tiles.get(check_pos)
                    if neighbor_tile:
                        if offset_[0] == 1:
                            neighbor_tile.left_is_burning = True 
                        else: 
                            neighbor_tile.right_is_burning = True 
                        neighbor_tile.burning = max(0, neighbor_tile.burning - 1)
                        if neighbor_tile.burning == 0:
                            keys_to_add.append(check_pos)

            # Only render if within the visible range
            """
            if base_pos[0] <= key[0] <= base_pos[0] + visible_tile_range[0] and \
            base_pos[1] <= key[1] <= base_pos[1] + visible_tile_range[1]:
                tile.render(dt, offset=offset)
            """
            # Mark tile for removal if fully burned out
            if tile.update_burn_state(dt):
                keys_to_remove.append(key)

        # Update dictionaries outside the main loop
        for key in keys_to_add:
            if key in self.render_list:
                self.render_list.remove(key)
            burning_tile = self.grass_tiles.pop(key, None)
            if burning_tile:
                self.burning_grass_tiles[key] = burning_tile
                burning_tile.swapped_dict = True

        for key in keys_to_remove:
            del self.burning_grass_tiles[key]

        # Render the grass tiles
        
        
        for pos in self.render_list:
            tile = self.grass_tiles[pos]
            #if quadtree:
            #    quadtree.insert(tile)
            tile.update_burn_state(dt)
            #tile.render(dt, offset=offset)
            if rot_function:
                tile.set_rotation(rot_function(tile.pos[0], tile.pos[1]), dt * tile.rot_random_factor_seed)
        
        



    """
    # an update and render combination function
    def update_render(self, surf, dt, offset=(0, 0), rot_function=None):
        visible_tile_range = (int(surf.get_width() // self.tile_size) + 1, int(surf.get_height() // self.tile_size) + 1)
        base_pos = (int(offset[0] // self.tile_size), int(offset[1] // self.tile_size))

        # get list of grass tiles to render based on visible area

        render_list = set()
        for y in range(visible_tile_range[1]):
            for x in range(visible_tile_range[0]):
                pos = (base_pos[0] + x, base_pos[1] + y)
                if pos in self.grass_tiles:
                    render_list.add(pos)
               
        # render shadow if applicable
        if self.ground_shadow[0]:
            for pos in render_list:
                self.grass_tiles[pos[0]].render_shadow(surf, offset=(offset[0] - self.ground_shadow[3][0],\
                                                                          offset[1] - self.ground_shadow[3][1]))
        
        keys_to_remove = []  # Track keys that need to be removed
        keys_to_add = []

        for key, tile in self.burning_grass_tiles.items():
            if not tile.appended: 
                self.game.lights_engine.lights.append(tile.light)
                tile.appended = True 
            
            for offset_ in BURN_CHECK_OFFSETS:
                check_pos = (key[0] + offset_[0], key[1] + offset_[1])
 
                if check_pos in self.grass_tiles:
                    self.grass_tiles[check_pos].burning = max(0, self.grass_tiles[check_pos].burning - 1)
                    if self.grass_tiles[check_pos].burning == 0:
                        keys_to_add.append(check_pos)

                    #print(self.grass_tiles[check_pos].burning)
            if base_pos[0] <= key[0] <= base_pos[0] + visible_tile_range[0] and \
            base_pos[1] <= key[1] <= base_pos[1] + visible_tile_range[1]:
                tile.render(surf, dt, offset=offset)
            
            kill = tile.update_burn_state(dt)
            if kill:
                keys_to_remove.append(key)  # Add key to the list for removal

        for key in keys_to_add:
            self.burning_grass_tiles[key] = self.grass_tiles.pop(key)
            self.burning_grass_tiles[key].swapped_dict = True 
            if key in render_list:
                render_list.remove(key)
    # Remove items after the main loop
        for key in keys_to_remove:
            del self.burning_grass_tiles[key]

       

        # render the grass tiles
        for pos in render_list:
        
            tile = self.grass_tiles[pos]
            tile.update_burn_state(dt)
            tile.render(surf, dt, offset=offset)
            if rot_function:
                tile.set_rotation(rot_function(tile.loc[0], tile.loc[1]),dt)
        """
# an asset manager that contains functionality for rendering blades of grass
"""
class GrassAssets:
    def __init__(self, path, gm):
        self.gm = gm
        self.burn_palette = (153,46,17)
        self.blades = []
        self.folder_size_info = []
        

        # load in blade images
        for folder in sorted(os.listdir(path)):
            folder_content = []
            folder_size = 0
            for blade in sorted(os.listdir(path +'/'+folder)):
                folder_size +=1
                img = pygame.image.load(path + '/' + folder +'/'+ blade).convert()
                img.set_colorkey((0, 0, 0))
                folder_content.append(img)
            self.folder_size_info.append(folder_size)
            self.blades.append(folder_content)
  



    def render_blade(self, surf, blade_id, blade_variation, location, rotation, scale, burning_sides, burning_initiation_time, palette):
        # Scale and rotate the blade image
        rot_img = pygame.transform.rotate(self.blades[blade_id][blade_variation], rotation)
        rot_img_dim = rot_img.get_size()
        rot_img = pygame.transform.scale(rot_img, (int(rot_img_dim[0] * scale), int(rot_img_dim[1] * scale)))

        # Shade the blade based on rotation
        shade = pygame.Surface(rot_img_dim)
        shade_amt = self.gm.shade_amount * (abs(rotation) / 90)
        shade.set_alpha(shade_amt)

        if 0 < scale < 1:
            if burning_initiation_time > 0:
                burn_surface = pygame.Surface(rot_img_dim, pygame.SRCALPHA)
                burn_surface.fill((255,255,255,255))
                burn_spread_ratio = burning_initiation_time / 20
                burn_alpha = int(255 * (1 - burn_spread_ratio))
                
                # Determine burn spread direction and boundary based on burn initiation time
                for x in range(rot_img_dim[0]):
                    offset = int((random.random() - 0.5) * 1)  # Jagged edge
                    if (burning_sides[0] and x < rot_img_dim[0] * (1 - burn_spread_ratio)) or \
                    (burning_sides[1] and x > rot_img_dim[0] - rot_img_dim[0] * (1 - burn_spread_ratio)):
                        for y in range(max(0, offset), rot_img_dim[1]):
                            # Flickering effect
                            flicker_intensity = 0.4
                            flicker = 1 + flicker_intensity * math.sin(time.time() * 5)
                            alpha_value = min(burn_alpha, int(burn_alpha * flicker))
                            
                            # Burn color with alpha
                            burn_color = (
                                min(255, palette[0] * flicker * (scale * 5)),
                                min(255, palette[1] * flicker * ( scale)),
                                min(255, palette[2] * flicker * (scale)),
                                alpha_value
                            )
                            burn_surface.set_at((x, y), burn_color)

                # Blit the burn surface onto the rotated image with blend mode
                rot_img.blit(burn_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            else: 
                # Flickering effect
                flicker_intensity = 0.4
                flicker = 1 + flicker_intensity * math.sin(time.time() * 5)
                red_mask = pygame.mask.from_surface(rot_img)
                red_mask.to_surface(
                    rot_img,
                    setcolor=(
                        min(255, palette[0] * flicker * (scale * 5)),
                        min(255, palette[1] * flicker * ( scale)),
                        min(255, palette[2] * flicker * ( scale))
                    )
                )

        rot_img.blit(shade, (0, 0))

        # Render the blade
        surf.blit(rot_img, (location[0] - rot_img.get_width() // 2, location[1] - rot_img.get_height() // 2))

"""

# the grass tile object that contains data for the blades
class GrassTile:
    def __init__(self, tile_size, location, amt, config, ga, gm):
        
        self.type = self.e_type = 'live_grass'
        self.ga = ga
        self.gm = gm
        self.pos = location
        self.org_img_dim = None
        self.size = tile_size
        self.blades = []
        self.rot_random_factor_seed = random.random()
        self.master_rotation = 0
        self.precision = 30
        self.padding = self.gm.padding
        self.inc = 90 / self.precision
        
        self.burn_initiated = False
        self.burn_initiation_time = 20
        self.left_is_burning  = False 
        self.right_is_burning = False

        self.burn_life = int(200/self.gm.burn_rate)
        self.max_burn_life = int(200/self.gm.burn_rate)

        self.initial_burning_val =int(60 / self.gm.burn_spread_speed)
        self.burning = int(60 / self.gm.burn_spread_speed)
        self.swapped_dict = False

        self.dead = False
        self.center = (location[0] + 8,location[1] + 16)
        self.light = PointLight(self.center,power=1,radius=22,illuminator=self,life =2* self.max_burn_life)
        self.light.cast_shadows = False
        self.light.set_color(149,46,17)
        self.appended = False 


        self.spark_colors = ((253,128,70),(244,160,86) ,(189,84,55))

        # generate blade data
        y_range = self.gm.vertical_place_range[1] - self.gm.vertical_place_range[0]
        for i in range(amt):
            new_blade = random.choice(config)
            variation_choice = random.randint(0,self.ga.grass_count_for_grass_var[new_blade]-1) 
            """
            img = self.ga.blades[new_blade][variation_choice]
            self.org_img_dim = (img.get_width(),img.get_height())
            avg_rgb = [0,0,0]
            count = 0
            for x in range(0,self.org_img_dim[0]):
                for y in range(0,self.org_img_dim[1]):
                                        
                    rgb = img.get_at((x,y))
                    if rgb != (0,0,0,255):
                        count += 1
                        avg_rgb[0] += rgb[0]
                        avg_rgb[1] += rgb[1]
                        avg_rgb[2] += rgb[2]

            avg_rgb[0] /= count
            avg_rgb[1] /= count
            avg_rgb[2] /= count
            """
            y_pos = self.gm.vertical_place_range[0]
            if y_range:
                y_pos = random.random() * y_range + self.gm.vertical_place_range[0]

            self.blades.append([(random.random() * self.size, y_pos * self.size), new_blade, variation_choice,random.random() * 30 - 15])

        # layer back to front
        self.blades.sort(key=lambda x: x[1])

        # get next ID
        self.base_id = self.gm.grass_id
        self.gm.grass_id += 1

        # check if the blade data needs to be overwritten with a previous layout to save RAM usage
        format_id = (amt, tuple(config))
        overwrite = self.gm.get_format(format_id, self.blades, self.base_id)
        if overwrite:
            self.blades = overwrite[1]
            self.base_id = overwrite[0]

        # custom_blade_data is used when the blade's current state should not be cached. all grass tiles will try to return to a cached state
        self.custom_blade_data = None

        self.update_render_data(0)

    def rect(self):
        return pygame.Rect(self.pos[0],self.pos[1]+ (self.org_img_dim[1]-self.padding)*(1- (self.burn_life/self.max_burn_life)),self.size, \
                           self.pos[1]+ (self.org_img_dim[1]-self.padding)*((self.burn_life/self.max_burn_life)))       

    # apply a force that affects each blade individually based on distance instead of the rotation of the entire tile
    def apply_force(self, force_point, force_radius, force_dropoff):
        if not self.custom_blade_data:
            self.custom_blade_data = [None] * len(self.blades)

        for i, blade in enumerate(self.blades):
            orig_data = self.custom_blade_data[i]
            dis = math.sqrt((self.pos[0] + blade[0][0] - force_point[0]) ** 2 + (self.pos[1] + blade[0][1] - force_point[1]) ** 2)
            max_force = False
            if dis < force_radius:
                force = 2
            else:
                dis = max(0, dis - force_radius)
                force = 1 - min(dis / force_dropoff, 1)
            dir = 1 if force_point[0] > (self.pos[0] + blade[0][0]) else -1
            # don't update unless force is greater
            if not self.custom_blade_data[i] or abs(self.custom_blade_data[i][3] - self.blades[i][3]) <= abs(force) * 90:
                self.custom_blade_data[i] = [blade[0], blade[1],blade[2], blade[3] + dir * force * 90]


    #burn spread here 

    # update the identifier used to find a valid cached image
    def update_render_data(self,dt):
        #print(dt)
        
       

        #basically updates rotation 
        
        self.render_data = (self.base_id, self.master_rotation)
        self.true_rotation = self.inc * self.master_rotation
        if self.custom_blade_data:
            matching = True
            for i, blade in enumerate(self.custom_blade_data):
                blade[3] = normalize(blade[3], self.gm.stiffness * dt, self.blades[i][3])
                if blade[3] != self.blades[i][3]:
                    matching = False
            # mark the data as non-custom once in base position so the cache can be used
            if matching:
                self.custom_blade_data = None

    
    def update_burn_state(self,dt):
        if self.burning <= 0:
            
            if not self.swapped_dict:
                loc = (self.pos[0]//self.gm.tile_size,self.pos[1]//self.gm.tile_size)
                self.gm.burning_grass_tiles[loc] = self.gm.grass_tiles.pop(loc)
                self.swapped_dict = True 
            

            if not self.burn_initiated:
                self.burn_initiated = True 
            self.burn_initiation_time = max(0,self.burn_initiation_time - (25 * dt)*self.burn_initiated )
             
            self.burn_life = max(0,self.burn_life - 25 * dt)
            #if the grass has burnt out completely, then gt rid of the grass data, where? from the grasstiles list, and from the cache. 
            if self.burn_life  == 0:
                self.blades = [None] * len(self.blades)
                check_loc = (self.pos[0]//self.size,self.pos[1]//self.size)
                self.dead = True
                return True 
                del self.gm.burning_grass_tiles[check_loc]
                del self
       
        

 

    # set new master tile rotation
    def set_rotation(self, rotation,dt):
        self.master_rotation = rotation
        self.update_render_data(dt)

    # render the tile's image based on its current state and return the data
    """
    def render_tile(self, render_shadow=False):
        # make a new padded surface (to fit blades spilling out of the tile)
        surf = pygame.Surface((self.size + self.padding * 2, self.size + self.padding * 2))
        surf.set_colorkey((0, 0, 0))
        
        # use custom_blade_data if it's active (uncached). otherwise use the base data (cached).
        if self.custom_blade_data:
            blades = self.custom_blade_data
        else:
            blades = self.blades

                
        # render the shadows of each blade if applicable
        if render_shadow:
            shadow_surf = pygame.Surface(surf.get_size())
            shadow_surf.set_colorkey((0, 0, 0))
            for blade in self.blades:
                pygame.draw.circle(shadow_surf, self.gm.ground_shadow[1], (blade[0][0] + self.padding, blade[0][1] + self.padding), self.gm.ground_shadow[0])
            shadow_surf.set_alpha(self.gm.ground_shadow[2])

        # render each blade using the asset manager
        for blade in blades:
            self.ga.render_blade(surf, blade[1], blade[2],(blade[0][0] + self.padding, blade[0][1] + self.padding), \
                                 max(-90, min(90, blade[3] + self.true_rotation)),self.burn_life/self.max_burn_life,(self.left_is_burning,self.right_is_burning),\
                                    self.burn_initiation_time,blade[4])

        #transform the pygame surfaces to moderngl textures 
        surf_tex = self.gm.render_engine.surface_to_texture(surf)
        shadow_tex = self.gm.render_engine.surface_to_texture(surf)

        # return surf and shadow_surf if applicable
        if render_shadow:
            return surf_tex,shadow_tex 
        else:
            return surf_tex
    """
    # draw the shadow image for the tile
    """
    def render_shadow(self, offset=(0, 0)):
        # shadow cache is just list of textures 
        if self.gm.ground_shadow[0] and (self.base_id in self.gm.shadow_cache):
            tex =self.gm.shadow_cache[self.base_id] 
            self.gm.render_engine.render_texture(
                tex,Layer_.BACKGROUND,
                dest = pygame.Rect(self.pos[0] - offset[0] - self.padding, self.pos[1] - offset[1] - self.padding,tex.width,tex.height),
                source = pygame.Rect(0,0,tex.width,tex.height)
            )
            #surf.blit(self.gm.shadow_cache[self.base_id], (self.pos[0] - offset[0] - self.padding, self.pos[1] - offset[1] - self.padding))

    # draw the grass itself
    """
    """
    def render(self, dt, offset=(0, 0)):
        # render a new grass tile image if using custom uncached data otherwise use cached data if possible Also, if the tile is burning, don't use 
        # cached data. As burning is another state.

        if self.burning <= 0:
            #if it is burning, no caaache. Performance? well, the grass will be deleted after the burn duration, so performace shouldn't be a big issue. 
            tex = self.render_tile()  
            tex_dim = tex.size 

            decay_rate = int(self.max_burn_life /self.burn_life) * 7
            
            if self.burn_life > 45 and  int(self.burn_life) %decay_rate  == 0:
                x_offset_dir = random.randint(0,1)
                x_offset_dir = -1 if x_offset_dir == 0 else 1
                #position = [self.pos[0] +img.get_width()//2 -self.padding +x_offset_dir * random.randint(0,img.get_width()//3),self.pos[1] +img.get_height()//2 -self.padding- random.randint(1,img.get_height()//2)]
                position = [self.pos[0] +tex_dim[0]//2 -self.padding +x_offset_dir * random.randint(0,tex_dim[0]//3),self.pos[1]+self.gm.tile_size-1-random.randint(1,tex_dim[1]//5,) ]
                spark = Spark(position.copy(),math.radians(random.randint(180,360)),\
                                random.randint(1,3),random.choice(self.spark_colors),scale=0.2,speed_factor=2 *(self.burn_life/self.max_burn_life))
                light = PointLight(position.copy(),power = 1,radius= 5,illuminator= spark,life = 90)
                light.cast_shadows = False
                light.set_color(149,46,17)
                self.gm.game.lights_engine.lights.append(light)
                self.gm.game.add_spark(spark)    

            self.gm.render_engine.render_texture(
                tex, Layer_.BACKGROUND,
                dest=pygame.Rect(self.pos[0] - offset[0] - self.padding, self.pos[1] - offset[1] - self.padding,tex.width,tex.height),
                source = pygame.Rect(0,0,tex.width,tex.height)
            )
            tex.release()
        else: 
            
            if self.custom_blade_data:
                    #if not cached, 

                    
                    tex = self.render_tile() 
                    
                    ######
                    
                    if self.burning == 0:
                        #if it is burning, it will have two things: the grass height is gonna decrease over time as it burns, and the outline of the grass will  shrink, and it will flicker. 
                        img_mask  = pygame.mask.from_surface(img)
                        mask_img = img_mask.to_surface()

                        centroid = img_mask.centroid()
                        #center = (centroid[0] +self.pos[0]- offset[0] - self.padding,  centroid[1]+self.pos[1]- offset[1] - self.padding )
                        #outline = [(p[0] + self.pos[0] - offset[0] - self.padding, p[1] + self.pos[1]- offset[1] - self.padding) for p in img_mask.outline(every=6)]
                        #outline = [(p[0],p[1]) for p in img_mask.outline(every =6)]

                        outline = []

                        
                        min_loc = 0
                        #move the outline points closer to the center of the grass img based on how much the grass has burnt. 
                        
                        for p in img_mask.outline(every=2):
                            dist_from_base_ratio = (mask_img.get_height() - p[1]) / (2*mask_img.get_height())
                            burn_ratio = max(dist_from_base_ratio,self.burn_life/self.max_burn_life)
                            move_vec = ((centroid[0] - p[0])*(1-burn_ratio), (centroid[1]- p[1])*(1-burn_ratio))
                            outline.append((p[0] + move_vec[0],p[1] + move_vec[1]))

                            if min_loc < p[1] + move_vec[1]:
                                min_loc  =p[1] + move_vec[1]

                        height_offset = mask_img.get_height() - min_loc - self.padding
                

                        #create a polygon out of those shrunk points and put it on a surf. 
                        poly_surf = pygame.Surface((img.get_width(),img.get_height()))
                        poly_surf.set_colorkey((0,0,0))
                        pygame.draw.polygon(poly_surf,(255,255,255),outline)

                        #test polygon for how it looks 

                        surf.blit(poly_surf,(self.pos[0] - offset[0] - self.padding, self.pos[1] - offset[1] - self.padding+height_offset))
                    
                        short_surf = pygame.Surface((img.get_width(),int(mask_img.get_height() * (self.burn_life/self.max_burn_life))))
                        short_surf.set_colorkey((0,0,0))
                        cut_offset = (0,short_surf.get_height()-img.get_height())
                        short_surf.blit(img,cut_offset)
                        surf.blit(short_surf, (self.pos[0] - offset[0] - self.padding - cut_offset[0], self.pos[1] - offset[1] - self.padding- cut_offset[1]))
                        
                        pass
                    
                    else: 

                    ######
                    ######
                    if self.burning/self.initial_burning_val<1:
                        img =img.copy()
                        burn_surface = pygame.Surface((img.get_width(),img.get_height()),pygame.SRCALPHA)
                        burn_surface.fill(
                            color=
                            (
                            self.ga.burn_palette[0],
                            self.ga.burn_palette[1],
                            self.ga.burn_palette[2],
                            max(1,255*(1-self.burning/self.initial_burning_val)))
                        )
                        img.blit(burn_surface,(0,0),special_flags=pygame.BLEND_RGBA_MULT)

                    ######
                    self.gm.render_engine.render_texture(
                        tex, Layer_.BACKGROUND,
                        dest=pygame.Rect(self.pos[0] - offset[0] - self.padding, self.pos[1] - offset[1] - self.padding,tex.width,tex.height),
                        source = pygame.Rect(0,0,tex.width,tex.height)
                    )
                    tex.release()
                    #surf.blit(img, (self.pos[0] - offset[0] - self.padding, self.pos[1] - offset[1] - self.padding))
                                        
                
                    ######
                    #surf.blit(mask_img, (self.pos[0] - offset[0] - self.padding, self.pos[1] - offset[1] - self.padding))
                    for point in outline:
                        surf.set_at((point[0],point[1]),(255,0,255))
                    surf.set_at(center,(0,0,0))
                    #pygame.draw.lines(surf,(255,0,255),False, outline,1)
                    ######
                

            else:
                #if it is cached, 
                
                # check if a new cached image needs to be generated and use the cached data if not (also cache shadow if necessary)
                if (self.render_data not in self.gm.grass_cache) and (self.gm.ground_shadow[0] and (self.base_id not in self.gm.shadow_cache)):
                    grass_tex, shadow_tex = self.render_tile(render_shadow=True)
                    self.gm.grass_cache[self.render_data] = grass_tex
                    self.gm.shadow_cache[self.base_id] = shadow_tex
                elif self.render_data not in self.gm.grass_cache:
                    self.gm.grass_cache[self.render_data] = self.render_tile()
                ######
                # render image from the cache
                if self.burning == 0:
                    
                    #if it is burning, it will have two things: the grass height is gonna decrease over time as it burns, and the outline of the grass will  shrink, and it will flicker. 
                    img = self.gm.grass_cache[self.render_data]
                    img_mask  = pygame.mask.from_surface(img)
                    mask_img = img_mask.to_surface()

                    centroid = img_mask.centroid()
                    #center = (centroid[0] +self.pos[0]- offset[0] - self.padding,  centroid[1]+self.pos[1]- offset[1] - self.padding )
                    #outline = [(p[0] + self.pos[0] - offset[0] - self.padding, p[1] + self.pos[1]- offset[1] - self.padding) for p in img_mask.outline(every=6)]
                    #outline = [(p[0],p[1]) for p in img_mask.outline(every =6)]

                    outline = []

                    #move the outline points closer to the center of the grass img based on how much the grass has burnt. 
                    min_loc = 0
                    #move the outline points closer to the center of the grass img based on how much the grass has burnt. 
                    (tile.pos[0] * tilemap.tile_size-offset[0], tile.pos[1] *tilemap.tile_size-offset[1])
                    for p in img_mask.outline(every=2):
                        dist_from_base_ratio = (mask_img.get_height() - p[1]) / (2*mask_img.get_height())
                        burn_ratio = max(dist_from_base_ratio,self.burn_life/self.max_burn_life)
                        move_vec = ((centroid[0] - p[0])*(1-burn_ratio), (centroid[1]- p[1])*(1-burn_ratio))
                        outline.append((p[0] + move_vec[0],p[1] + move_vec[1]))

                        if min_loc < p[1] + move_vec[1]:
                            min_loc  =p[1] + move_vec[1]
                    height_offset = mask_img.get_height() - min_loc - self.padding

                    #create a polygon out of those shrunk points and put it on a surf. 
                    poly_surf = pygame.Surface((img.get_width(),img.get_height()))
                    poly_surf.set_colorkey((0,0,0))
                    pygame.draw.polygon(poly_surf,(255,255,255),outline)

                    #test polygon for how it looks 

                    surf.blit(poly_surf,(self.pos[0] - offset[0] - self.padding, self.pos[1] - offset[1] - self.padding + height_offset))
                else: 

                ######
                
                tex = self.gm.grass_cache[self.render_data]
                ######
                if self.burning/self.initial_burning_val<1:
                    img = img.copy()
                    burn_surface = pygame.Surface((img.get_width(),img.get_height()),pygame.SRCALPHA)
                    burn_surface.fill(
                        color=
                        (
                        self.ga.burn_palette[0],
                        self.ga.burn_palette[1],
                        self.ga.burn_palette[2],
                        max(1,255*(1-self.burning/self.initial_burning_val)))
                    )
                    img.blit(burn_surface,(0,0),special_flags=pygame.BLEND_RGBA_MULT)
                    
                ######
                
                self.gm.render_engine.render_texture(
                    tex, Layer_.BACKGROUND,
                    dest = pygame.Rect(self.pos[0] - offset[0] - self.padding, self.pos[1] - offset[1] - self.padding,tex.width,tex.height),
                    source = pygame.Rect(0,0,tex.width,tex.height)
                )
                #surf.blit(img,(self.pos[0] - offset[0] - self.padding, self.pos[1] - offset[1] - self.padding))

        # attempt to move blades back to their base position
        if self.custom_blade_data:
            matching = True
            for i, blade in enumerate(self.custom_blade_data):
                blade[3] = normalize(blade[3], self.gm.stiffness * dt, self.blades[i][3])
                if blade[3] != self.blades[i][3]:
                    matching = False
            # mark the data as non-custom once in base position so the cache can be used
            if matching:
                self.custom_blade_data = None

       
"""