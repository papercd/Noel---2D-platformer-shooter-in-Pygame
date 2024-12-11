from scripts.atlass_positions import TILE_ATLAS_POSITIONS,IRREGULAR_TILE_SIZES
from scripts.custom_data_types import TileInfo,LightInfo,DoorInfo,DoorAnimation
from scripts.tileformatdata import get_tile_rectangle, PHYSICS_APPLIED_TILE_TYPES,TILE_SIDE_TO_SAMPLE_POS
from scripts.spatial_grid import SpatialGrid
from scripts.lists import ambientNodeList,interpolatedLightNode
from my_pygame_light2d.hull import Hull 
from moderngl import Texture
from pygame import Rect
from my_pygame_light2d.light import PointLight
from scripts.utils import load_texture
from scripts.resourceManager import ResourceManager
import numpy as np 


TEXTURE_BASE_PATH = 'data/images/'



class Tilemap:
    def __init__(self):
        """ 
        Initialize the Tilemap object. 

        Args:
            json_data (json) : the json data you want to load the tilemap with. leave this blank 
            for empty Tilemap object. 
        
        """
       

    def load_map(self,name:str):
        resource_manager = ResourceManager.get_instance()
        json_data = resource_manager.get_tilemap_json(name)
        
        self._regular_tile_size = json_data['tile_size']
        self._hull_grid = SpatialGrid(cell_size= self._regular_tile_size)

        # one step at a time.The tilemap.
        self._non_physical_tile_layers= json_data['offgrid_layers']
        self.lights = []

        self.ambientNodes = ambientNodeList()

        self._physical_tiles= {}
        self.non_physical_tiles = [{} for i in range(0,self._non_physical_tile_layers)]


        for tile_key in json_data['tilemap']: 

            tile_size = (self._regular_tile_size,self._regular_tile_size) if json_data['tilemap'][tile_key]['type'] \
                                    not in IRREGULAR_TILE_SIZES else IRREGULAR_TILE_SIZES[json_data['tilemap'][tile_key]['type']]
            atl_pos = TILE_ATLAS_POSITIONS[json_data['tilemap'][tile_key]['type']]
            tile_pos = tuple(json_data['tilemap'][tile_key]["pos"])

            if json_data['tilemap'][tile_key]['type'] != "lights":
                if json_data['tilemap'][tile_key]['type'].endswith('door'):
                    if json_data['tilemap'][tile_key]['type'].split('_')[0] == 'trap':
                        # Tile info creation for trap door 

                        rect = Rect(tile_pos[0] * self._regular_tile_size, self.pos[1] * self._regular_tile_size, self._regular_tile_size,5)
            
                        self._physical_tiles[tile_key] = [DoorInfo(json_data['tilemap'][tile_key]["type"],json_data['tilemap'][tile_key]["variant"],\
                                                                 tile_pos,tile_size,rect,atl_pos),False]
                    else: 
                        if tile_key in self._physical_tiles: continue 
                        else: 
                            rect = Rect(tile_pos[0] * self._regular_tile_size + 3, tile_pos[1] * self._regular_tile_size ,6,32)

                            door = [DoorInfo(json_data['tilemap'][tile_key]["type"],json_data['tilemap'][tile_key]["variant"],\
                                                                 tile_pos,tile_size,rect,atl_pos),DoorAnimation(5,5)]
                            self._physical_tiles[tile_pos] = door 
                            pos_below = (tile_pos[0],tile_pos[1] +1)
                            self._physical_tiles[pos_below]  = door 

                else:   
                    #hull = self._create_hulls(json_data['tilemap'][tile_key])
                    # TODO: THE TILE KEYS NEED TO BE CHANGED TO INTS, NOT STRINGS. 

                    self._physical_tiles[tile_pos] = [TileInfo(json_data['tilemap'][tile_key]["type"],json_data['tilemap'][tile_key]["variant"],
                                                    tile_pos,tile_size,atl_pos),None] 
            
            else: 
                if isinstance(json_data['tilemap'][tile_key]["pos"][0],int):
                    # for lights that are on the tile grid 
                    #TODO: ADD LIGHTING LATER 
                    
                    light = PointLight(position = (json_data['tilemap'][tile_key]["pos"][0]*self._regular_tile_size+7,json_data['tilemap'][tile_key]["pos"][1]*self._regular_tile_size+3),\
                                         power= json_data['tilemap'][tile_key]["power"],radius = json_data['tilemap'][tile_key]["radius"] )
                    light.set_color(*json_data['tilemap'][tile_key]["colorValue"])
                    self.lights.append(light)
                    
                    pass 
                else: 
                    # for lights that are not placed on the tile grid  
                    # TODO : ADD LIGHTING LATER
                  
                    light = PointLight(position = (json_data['tilemap'][tile_key]["pos"][0]+7,json_data['tilemap'][tile_key]["pos"][1]+3),\
                                         power= json_data['tilemap'][tile_key]["power"],radius = json_data['tilemap'][tile_key]["radius"] )
                    light.set_color(*json_data['tilemap'][tile_key]["colorValue"])
                    self.lights.append(light)
                    
                rect = Rect(tile_pos[0] * self._regular_tile_size +3, tile_pos[1] * self._regular_tile_size, 10,6)
                self._physical_tiles[tile_pos] = [LightInfo(json_data['tilemap'][tile_key]["type"],json_data['tilemap'][tile_key]["variant"],\
                                                 tile_pos,tile_size,rect,json_data['tilemap'][tile_key]["radius"], json_data['tilemap'][tile_key]["power"],
                                                 json_data['tilemap'][tile_key]["colorValue"],atl_pos),light]
                #self._physical_tiles[tile_key].light_ptr = light 
        
        for i in range(0,self._non_physical_tile_layers):
            tilemap_key = f"offgrid_{i}"
            for tile_key in json_data[tilemap_key]:
                tile_pos = tuple(json_data[tilemap_key][tile_key]["pos"])
                atl_pos = TILE_ATLAS_POSITIONS[json_data[tilemap_key][tile_key]["type"]]
                tile_size = (self._regular_tile_size,self._regular_tile_size) if json_data[tilemap_key][tile_key]['type'] \
                                    not in IRREGULAR_TILE_SIZES else IRREGULAR_TILE_SIZES[json_data[tilemap_key][tile_key]['type']]

                if json_data[tilemap_key][tile_key]["type"] == "lights":
                    pass 
                    """
                    
                    if isinstance(json_data['offgrid_'+ str(i)][tile_key]["pos"][0],int):
                        light = PointLight(position = (json_data['offgrid_'+ str(i)][tile_key]["pos"][0]*self.tile_size+7,json_data['offgrid_'+ str(i)][tile_key]["pos"][1]*self.tile_size+3),\
                                         power= json_data['offgrid_'+ str(i)][tile_key]["power"],radius = json_data['offgrid_'+ str(i)][tile_key]["radius"] )
                        light.set_color(*json_data['offgrid_' + str(i)][tile_key]["colorValue"])
                        lights.append(light)
                        self.offgrid_tiles[i][tile_key] = Light(json_data['offgrid_'+str(i)][tile_key]["type"],json_data['offgrid_'+str(i)][tile_key]["variant"],json_data['offgrid_'+str(i)][tile_key]["pos"],\
                                                                radius = json_data['offgrid_'+str(i)][tile_key]['radius'],power = json_data['offgrid_'+str(i)][tile_key]['power'],color_value=json_data['offgrid_'+str(i)][tile_key]['colorValue'] )
                    else: 
                        light = PointLight(position = (json_data['offgrid_'+ str(i)][tile_key]["pos"][0]+7,json_data['offgrid_'+ str(i)][tile_key]["pos"][1]+3),\
                                         power= json_data['offgrid_'+ str(i)][tile_key]["power"],radius = json_data['offgrid_'+ str(i)][tile_key]["radius"] )
                        light.set_color(*json_data['offgrid_' + str(i)][tile_key]["colorValue"])
                        lights.append(light)
                        self.offgrid_tiles[i][tile_key] = Light(json_data['offgrid_'+str(i)][tile_key]["type"],json_data['offgrid_'+str(i)][tile_key]["variant"],(json_data['offgrid_'+str(i)][tile_key]["pos"][0] // self.tile_size,json_data['offgrid_'+str(i)][tile_key]["pos"][1] // self.tile_size),\
                                                            radius = json_data['offgrid_'+str(i)][tile_key]['radius'],power = json_data['offgrid_'+str(i)][tile_key]['power'],color_value=json_data['offgrid_'+str(i)][tile_key]['colorValue'] )
                    """
                else: 
                    self.non_physical_tiles[i][tile_pos] = TileInfo(json_data[tilemap_key][tile_key]["type"],json_data[tilemap_key][tile_key]["variant"],
                                                            tile_pos,tile_size,atl_pos)
        
        for node_data in json_data['ambient_nodes']:
            if len(node_data.items()) ==4:
                self.ambientNodes.insert_interpolated_ambient_node(node_data["range"],node_data['hull_range'],node_data["leftColorValue"],node_data["rightColorValue"])
            else: 
                self.ambientNodes.insert_ambient_node(node_data["range"],node_data['hull_range'],node_data["colorValue"])
        
        self._ambient_node_ptr = None

        self._create_hulls()
        for hull in self._hulls:
            self._hull_grid.insert(hull)

        self._precompute_texture_coordinates()
        self._precompute_tile_colors()



    @property
    def physical_tiles(self):
        return self._physical_tiles

    @property
    def tile_size(self):
        return self._regular_tile_size
    
    @property
    def non_physical_tile_layers(self):
        return self._non_physical_tile_layers


    def _precompute_tile_colors(self):
        rm = ResourceManager.get_instance()
        tile_texture_atlas = rm.tile_atlas 

        raw_data = tile_texture_atlas.read(alignment=4)
        width,height = tile_texture_atlas.size
        image_data = np.frombuffer(raw_data,dtype= np.uint8).reshape((height,width,4))
 
        self._tile_colors = {}

        for key in self._physical_tiles:
            tile_info_list = self._physical_tiles[key]
            tile_info = tile_info_list[0]
            rel_pos,variant = map(int,tile_info.variant.split(';'))

            if tile_info.type.endswith('stairs'):
                for side in ['top','bottom','left','right']:
                    if (tile_info.type,(rel_pos,variant),side) not in self._tile_colors:
                        sample_side_ratio = TILE_SIDE_TO_SAMPLE_POS['stairs']
                        texture_coords = (TILE_ATLAS_POSITIONS[tile_info.type][0] + variant * tile_info.tile_size[0] + int((tile_info.tile_size[0]-1) *sample_side_ratio[0]),\
                                                TILE_ATLAS_POSITIONS[tile_info.type][1] + rel_pos* tile_info.tile_size[1] + int((tile_info.tile_size[1]-1) * sample_side_ratio[1]))
                        color = tuple(image_data[texture_coords[1],texture_coords[0]])
                        self._tile_colors[(tile_info.type,(rel_pos,variant),side)] = color

                   
            elif tile_info.type.endswith('door'):
                pass 
            else: 
                for side in ['top','bottom','left','right']:
                    sample_side_ratio = TILE_SIDE_TO_SAMPLE_POS['regular'][side]
                    if (tile_info.type,(rel_pos,variant),side) not in self._tile_colors:
                        texture_coords = (TILE_ATLAS_POSITIONS[tile_info.type][0] + variant * tile_info.tile_size[0] + int((tile_info.tile_size[0]-1) *sample_side_ratio[0]),\
                                        TILE_ATLAS_POSITIONS[tile_info.type][1] + rel_pos* tile_info.tile_size[1] + int((tile_info.tile_size[1]-1) * sample_side_ratio[1]))
                        color = tuple(image_data[texture_coords[1],texture_coords[0]])
                        self._tile_colors[(tile_info.type,(rel_pos,variant),side)] = color



    def update_ambient_node_ptr(self,pos):
        if self._ambient_node_ptr is None: 
            self._ambient_node_ptr = self.ambientNodes.set_ptr(pos[0])
        else: 
            if pos[0] < self._ambient_node_ptr.range[0]:
                if self._ambient_node_ptr.prev: 
                    self._ambient_node_ptr = self._ambient_node_ptr.prev
            elif pos[0] > self._ambient_node_ptr.range[1]:
                if self._ambient_node_ptr.next: 
                    self._ambient_node_ptr = self._ambient_node_ptr.next

    
    def _precompute_texture_coordinates(self):
        rm = ResourceManager.get_instance()
        tile_texture_atlas = rm.tile_atlas

        self._texcoord_dict = {}
        for key in self.physical_tiles:
            tile_info_list = self.physical_tiles[key]
            tile_info = tile_info_list[0]
            door_data = None 
            if (tile_info.type,tile_info.variant) not in self._texcoord_dict:
                if tile_info.type == 'trap_door':
                    door_data = tile_info_list[1]
                elif tile_info.type == 'building_door':
                    door_data = tile_info_list[1]
                texture_coords = self._get_texture_coords_for_tile(tile_texture_atlas,tile_info,door_data)
                self._texcoord_dict[(tile_info.type,tile_info.variant)] = texture_coords

        for i,dict in enumerate(self.non_physical_tiles):
            for key in dict:
                tile_info = dict[key]
                if (tile_info.type,tile_info.variant) not in self._texcoord_dict:
                    texture_coords = self._get_texture_coords_for_tile(tile_texture_atlas,tile_info)
                    self._texcoord_dict[(tile_info.type,tile_info.variant)] = texture_coords
 
    def _get_texture_coords_for_tile(self,texture_atlas,tile_info:TileInfo,door_data:DoorAnimation|bool= None):
        # Fetch the texture from the atlas based on tile type and variant
        if not door_data:
            rel_pos,variant = map(int,tile_info.variant.split(';'))
            tile_type = tile_info.type

            x = (TILE_ATLAS_POSITIONS[tile_type][0] + variant * tile_info.tile_size[0]) / texture_atlas.width
            y = (TILE_ATLAS_POSITIONS[tile_type][1] + rel_pos * tile_info.tile_size[1]) / texture_atlas.height

            w = tile_info.tile_size[0] /texture_atlas.width
            h = tile_info.tile_size[1] / texture_atlas.height
            
            p1 = (x, y + h) 
            p2 = (x + w, y + h) 
            p3 = (x, y) 
            p4 = (x + w, y) 
            tex_coords = np.array([p1, p2, p3,
                                p3, p2, p4], dtype=np.float32)
        
        else: 
            if isinstance(door_data,DoorAnimation):
                pass 
            else: 
                pass 

        return tex_coords




    def _create_rectangles(self,tile_info: TileInfo) -> tuple[int,int,int,int]:
        return get_tile_rectangle(tile_info,self.tile_size,self.physical_tiles)
        
          
    def _create_hulls(self):
        """
        Merges rectangles in a dictionary where only rectangles of type "regular" are merged.
        
        :param rect_dict: Dictionary with keys as top-left grid-aligned positions (x, y) and 
                        values as (width, height, type).
        :param tile_size: Dimension of a grid square (default is 16).
        :return: List of merged rectangles [(x1, y1, x2, y2)].
        """
        # Convert rect_dict into a list of rectangles with positions
        self._rectangles = []
        for pos,tile_info_list  in sorted(self._physical_tiles.items()):
            tile_info = tile_info_list[0]
            if tile_info.type != 'spawners' and tile_info.type != 'lights':
                self._rectangles.extend(self._create_rectangles(tile_info))

        # extend rectangle sides for tiles with neighbors
        

        merged = True
        while merged:
            merged = False
            new_rectangles = []
            skip = set()

            for i, rect1 in enumerate(self._rectangles):
                if i in skip:
                    continue
                x1, y1, x2, y2 = rect1
                merged_with_other = False

                for j, rect2 in enumerate(self._rectangles):
                    if i == j or j in skip:
                        continue

                    a1, b1, a2, b2 = rect2

                    # Check if rectangles are touching and aligned
                    if (y1 == b1 and y2 == b2 and (x1 == a2 or x2 == a1)):  # Horizontal touch
                        # Merge horizontally
                        new_rectangles.append((min(x1, a1), y1, max(x2, a2), y2))
                        skip.add(i)
                        skip.add(j)
                        merged_with_other = True
                        merged = True
                        break
                    # check if rectangles are horizontally next to each other, and extend axis if needed 
                    elif (x1 == a1 and x2 == a2 and (y1 == b2 or y2 == b1)):  # Vertical touch
                        # Merge vertically
                        new_rectangles.append((x1, min(y1, b1), x2, max(y2, b2)))
                        skip.add(i)
                        skip.add(j)
                        merged_with_other = True
                        merged = True
                        break
                    elif (): 
                        pass 

                if not merged_with_other:
                    new_rectangles.append(rect1)

            # Update rectangles with the newly merged ones
            self._rectangles = new_rectangles

        # hull vertices order: topleft, topright, bottomright, bottomleft

        self._hulls = [] 

         
        for rectangle in self._rectangles:

            x1, y1, x2, y2 = rectangle
            self._hulls.append(Hull( vertices=[(x1, y1), (x2, y1), (x2, y2), (x1, y2)]))
    

    def get_lights(self) -> list[PointLight]:
        """
        Return all the lights that are in the tilemap.

        Is supposed to be used to initialize the pointlights for the render engine. 

        Returns: 
            list[PointLight] 
        """

        return self.lights
    


    def tiles_around(self,pos,size) -> list[TileInfo]:
        
        tiles = []
    
        # Calculate the tile coordinates of the center position
        tile_center = (int(pos[0] // self._regular_tile_size), int(pos[1] // self._regular_tile_size))
        
        # Calculate the boundary coordinates of the surrounding tiles
        x_start = tile_center[0] - 1
        x_end = tile_center[0] + int(size[0] // self._regular_tile_size) + 1
        y_start = tile_center[1] - 1
        y_end = tile_center[1] + int(size[1] // self._regular_tile_size) + 1
        
        # Iterate through the surrounding tiles and check if they exist in the tilemap
        for x in range(x_start, x_end + 1):
            for y in range(y_start, y_end + 1):
                tile_key = (x,y) 

                if tile_key in self._physical_tiles:
                    tile ,hull = self._physical_tiles[tile_key]

                    # TODO : differentiate tile info objects based on tile type
                    if tile.type.endswith('door') and not tile.open:
                        # Check whether there is a door tile above, and if there isn't, add it to the list. 
                        if (x,y) in self._physical_tiles:
                            if not self._physical_tiles[(x,y)].type.endswith('door'):
                                tiles.append(self._physical_tiles[tile_key])
                        else: 
                            tiles.append(self._physical_tiles[tile_key])
                    else: 
                        tiles.append(self._physical_tiles[tile_key])
                
                # TODO: add grass tiles later.  


        return tiles


    def get_at(self,check_pos,side):
        coor =(check_pos[0] // self.tile_size , check_pos[1] //self.tile_size)       
        tile_info_list = self._physical_tiles[coor]
        tile_info = tile_info_list[0] 
        rel_pos,variant = map(int,tile_info.variant.split(';'))
        return self._tile_colors[(tile_info.type,(rel_pos,variant),side)]


    
    def solid_check(self,check_pos) -> bool:
        coor =(check_pos[0]//self.tile_size,check_pos[1]//self.tile_size)
        return coor  in self.physical_tiles\
                and self.physical_tiles[coor][0].type in PHYSICS_APPLIED_TILE_TYPES

    def phy_rects_around(self,pos,size)->tuple[Rect,TileInfo]:
        surrounding_rects = []

        tiles_around = self.tiles_around(pos,size)
        
        for tile in tiles_around:
            if tile[0].type in PHYSICS_APPLIED_TILE_TYPES: 
                if tile[0].type.endswith('door'):
                    #TODO: add this when you have doors. 
                    pass 
                else: 
                    rect = (
                        tile[0].tile_pos[0] * self._regular_tile_size,         # left
                        tile[0].tile_pos[1] * self._regular_tile_size,         # top
                        self._regular_tile_size,                       # width
                        self._regular_tile_size# height
                    )
                
                    surrounding_rects.append((Rect(*rect),tile[0]))

            else: 
                # TODO: add this when you have non physical tiles. 
                pass 

        return surrounding_rects
