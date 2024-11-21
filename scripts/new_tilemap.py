from scripts.atlass_positions import TILE_ATLAS_POSITIONS,IRREGULAR_TILE_SIZES
from scripts.custom_data_types import TileInfo,LightInfo,DoorInfo,DoorAnimation
from my_pygame_light2d.hull import Hull 
from moderngl import Texture
from pygame import Rect
from my_pygame_light2d.light import PointLight
from scripts.utils import load_texture

TEXTURE_BASE_PATH = 'data/images/'
PHYSICS_APPLIED_TILE_TYPES = {'grass','stone','box','building_0','building_1','building_2','building_3','building_4','building_5','building_stairs','building_door','trap_door',\
                              'ladder'}

HULL_EDGE_OFFSET_EVEN_REL_POS = [(1,1),(-1,1),(-1,-1),(1,-1)]
HULL_EDGE_OFFSET_ODD_REL_POS = [(0,1),(-1,0),(0,-1),(1,0)]

class Tilemap:
    def __init__(self,texture_atlas:Texture,json_data = None):
        """ 
        Initialize the Tilemap object. 

        Args:
            json_data (json) : the json data you want to load the tilemap with. leave this blank 
            for empty Tilemap object. 
        
        """

        self._texture_atlas = texture_atlas

        if json_data:
            self.load_map(json_data)
    
    def _create_hulls(self,tile_json_data) -> list[Hull]:
        """
        Create hull objects associated with a physical tile. 

        Args: 
            tile_json_data : tile's data in json format

        Returns: 
            list[Hull] : hulls (my_pygame_light2D.Hull hull) associated with a physical tile in the tilemap.
        """
        
        hulls = []

        if tile_json_data['type'] != "spawners":
            tile_type_check = len(tile_json_data['type'].split('_')) == 1
            if not tile_type_check and tile_json_data['type'].split('_')[1] == 'stairs':
                variant = tile_json_data['variant'].split(';')
                if variant[0] == '0':
                    vertices = ((tile_json_data['pos'][0] * self._regular_tile_size +4   ,tile_json_data['pos'][1]   * self._regular_tile_size+13 ) , 
                                ((tile_json_data['pos'][0]+1) *self._regular_tile_size -1 ,tile_json_data['pos'][1] *self._regular_tile_size +13  ) , 
                                ((tile_json_data['pos'][0]+1)*self._regular_tile_size-1 ,(tile_json_data['pos'][1]+1) *self._regular_tile_size  ) ,
                                ((tile_json_data['pos'][0]) *self._regular_tile_size+4,(tile_json_data['pos'][1]+1) *self._regular_tile_size  ) ,
                                ),((tile_json_data['pos'][0] * self._regular_tile_size +8   ,tile_json_data['pos'][1]   * self._regular_tile_size+9 ) , 
                                ((tile_json_data['pos'][0]+1) *self._regular_tile_size -1 ,tile_json_data['pos'][1] *self._regular_tile_size +9  ) , 
                                ((tile_json_data['pos'][0]+1)*self._regular_tile_size-1 ,(tile_json_data['pos'][1]+1) *self._regular_tile_size-2  ) ,
                                ((tile_json_data['pos'][0]) *self._regular_tile_size+8,(tile_json_data['pos'][1]+1) *self._regular_tile_size-2  ) ,
                                ),((tile_json_data['pos'][0] * self._regular_tile_size +12   ,tile_json_data['pos'][1]   * self._regular_tile_size+5 ) , 
                                ((tile_json_data['pos'][0]+1) *self._regular_tile_size -1 ,tile_json_data['pos'][1] *self._regular_tile_size +5  ) , 
                                ((tile_json_data['pos'][0]+1)*self._regular_tile_size-1 ,(tile_json_data['pos'][1]+1) *self._regular_tile_size-7  ) ,
                                ((tile_json_data['pos'][0]) *self._regular_tile_size+12,(tile_json_data['pos'][1]+1) *self._regular_tile_size-7  ) ,
                                ),((tile_json_data['pos'][0] * self._regular_tile_size +17   ,tile_json_data['pos'][1]   * self._regular_tile_size+1 ) , 
                                ((tile_json_data['pos'][0]+1) *self._regular_tile_size -1 ,tile_json_data['pos'][1] *self._regular_tile_size +1  ) , 
                                ((tile_json_data['pos'][0]+1)*self._regular_tile_size-1 ,(tile_json_data['pos'][1]+1) *self._regular_tile_size-11  ) ,
                                ((tile_json_data['pos'][0]) *self._regular_tile_size+17,(tile_json_data['pos'][1]+1) *self._regular_tile_size -11 ) ,
                                )
                    for vertice in vertices:
                        hulls.append(Hull(vertice))
                elif variant[0] == '1':
                    vertices = ((tile_json_data['pos'][0] * self._regular_tile_size    ,tile_json_data['pos'][1]   * self._regular_tile_size+13 ) , 
                                ((tile_json_data['pos'][0]+1) *self._regular_tile_size -1 ,tile_json_data['pos'][1] *self._regular_tile_size +13  ) , 
                                ((tile_json_data['pos'][0]+1)*self._regular_tile_size-1 ,(tile_json_data['pos'][1]+1) *self._regular_tile_size  ) ,
                                ((tile_json_data['pos'][0]) *self._regular_tile_size,(tile_json_data['pos'][1]+1) *self._regular_tile_size  ) ,
                                ),((tile_json_data['pos'][0] * self._regular_tile_size    ,tile_json_data['pos'][1]   * self._regular_tile_size+9 ) , 
                                ((tile_json_data['pos'][0]+1) *self._regular_tile_size -5 ,tile_json_data['pos'][1] *self._regular_tile_size +9  ) , 
                                ((tile_json_data['pos'][0]+1)*self._regular_tile_size-5 ,(tile_json_data['pos'][1]+1) *self._regular_tile_size-3  ) ,
                                ((tile_json_data['pos'][0]) *self._regular_tile_size,(tile_json_data['pos'][1]+1) *self._regular_tile_size-3  ) ,
                                ),((tile_json_data['pos'][0] * self._regular_tile_size    ,tile_json_data['pos'][1]   * self._regular_tile_size+5 ) , 
                                ((tile_json_data['pos'][0]+1) *self._regular_tile_size -9 ,tile_json_data['pos'][1] *self._regular_tile_size +5  ) , 
                                ((tile_json_data['pos'][0]+1)*self._regular_tile_size-9 ,(tile_json_data['pos'][1]+1) *self._regular_tile_size-7  ) ,
                                ((tile_json_data['pos'][0]) *self._regular_tile_size,(tile_json_data['pos'][1]+1) *self._regular_tile_size-7  ) ,
                                ),((tile_json_data['pos'][0] * self._regular_tile_size    ,tile_json_data['pos'][1]   * self._regular_tile_size+1 ) , 
                                ((tile_json_data['pos'][0]) *self._regular_tile_size +2 ,tile_json_data['pos'][1] *self._regular_tile_size +1  ) , 
                                ((tile_json_data['pos'][0])*self._regular_tile_size+2 ,(tile_json_data['pos'][1]) *self._regular_tile_size+4  ) ,
                                ((tile_json_data['pos'][0]) *self._regular_tile_size,(tile_json_data['pos'][1]) *self._regular_tile_size+4 ) ,
                                )
                    for vertice in vertices:
                        hulls.append(Hull(vertice))
                    
                else: 
                    if variant[1] == '1':
                        vertices = ((tile_json_data['pos'][0] *   self._regular_tile_size  ,tile_json_data['pos'][1]   * self._regular_tile_size + 4 ) , 
                                    ((tile_json_data['pos'][0]+1) *self._regular_tile_size  ,tile_json_data['pos'][1] *self._regular_tile_size+4  ) , 
                                    ((tile_json_data['pos'][0]+1)*self._regular_tile_size  ,(tile_json_data['pos'][1]+1) *self._regular_tile_size ) ,
                                    ((tile_json_data['pos'][0]) *self._regular_tile_size ,(tile_json_data['pos'][1]+1) *self._regular_tile_size  ) ,
                                    )
                            
                                        
                    else: 
                        vertices = ((tile_json_data['pos'][0] *   self._regular_tile_size   ,tile_json_data['pos'][1]   * self._regular_tile_size ) , 
                                    ((tile_json_data['pos'][0]+1) *self._regular_tile_size ,tile_json_data['pos'][1] *self._regular_tile_size  ) , 
                                    ((tile_json_data['pos'][0]+1)*self._regular_tile_size ,(tile_json_data['pos'][1]+1) *self._regular_tile_size  ) ,
                                    ((tile_json_data['pos'][0]) *self._regular_tile_size ,(tile_json_data['pos'][1]+1) *self._regular_tile_size  ) ,
                                    )
                    hulls.append(Hull(vertices))
                
                return hulls                      
            else:
                if tile_json_data['type'].endswith('door'):
                    if tile_json_data['type'].split('_')[0] == 'trap':
                        # trap door
                        
                        vertices = [(tile_json_data['pos'][0] * self._regular_tile_size ,tile_json_data['pos'][1] * self._regular_tile_size +4), 
                                        ((tile_json_data['pos'][0] + 1) * self._regular_tile_size ,tile_json_data['pos'][1] * self._regular_tile_size +4),
                                        ((tile_json_data['pos'][0] +1) * self._regular_tile_size ,tile_json_data['pos'][1] * self._regular_tile_size +5),
                                        (tile_json_data['pos'][0]  * self._regular_tile_size ,tile_json_data['pos'][1] * self._regular_tile_size +5 ),
                                        ]

                        hulls.append(Hull(vertices))
                        return hulls 

                    else:                         
                        variant_num = int(tile_json_data['variant'].split(';')[0])
                        if variant_num == 0:
                            # Left facing door 
                            
                            vertices = [(tile_json_data['pos'][0] * self._regular_tile_size + 4,tile_json_data['pos'][1] * self._regular_tile_size -1), 
                                        (tile_json_data['pos'][0] * self._regular_tile_size + 5,tile_json_data['pos'][1] * self._regular_tile_size -1),
                                        (tile_json_data['pos'][0] * self._regular_tile_size + 5,(tile_json_data['pos'][1]+2) * self._regular_tile_size ),
                                        (tile_json_data['pos'][0] * self._regular_tile_size + 4,(tile_json_data['pos'][1]+2) * self._regular_tile_size ),
                                        ]
                            
                            hulls.append(Hull(vertices))

                        if variant_num == 1:
                            # Right facing door 
                            # Not made yet 
                            
                            pass
                        return hulls 

                else: 
                    variant_num = int(tile_json_data['variant'].split(';')[0])
                    
                    if variant_num == 8:
                        vertices = [(tile_json_data['pos'][0] *   self._regular_tile_size + 2  ,tile_json_data['pos'][1]   * self._regular_tile_size+ 2 ) , 
                                    ((tile_json_data['pos'][0]+1) *self._regular_tile_size - 2 ,tile_json_data['pos'][1] *self._regular_tile_size+ 2  ) , 
                                    ((tile_json_data['pos'][0]+1)*self._regular_tile_size- 2 ,(tile_json_data['pos'][1]+1) *self._regular_tile_size- 2  ) ,
                                    ((tile_json_data['pos'][0]) *self._regular_tile_size+ 2 ,(tile_json_data['pos'][1]+1) *self._regular_tile_size- 2  ) ,
                                    ]
                        hulls.append(Hull(vertices))
                    else: 
                        step = HULL_EDGE_OFFSET_EVEN_REL_POS[ variant_num // 2] if variant_num %2 == 0 else HULL_EDGE_OFFSET_ODD_REL_POS[variant_num//2]
                        vertices = [(tile_json_data['pos'][0] *   self._regular_tile_size + step[0]* 4  ,tile_json_data['pos'][1]   * self._regular_tile_size+step[1]* 4 ) , 
                                    ((tile_json_data['pos'][0]+1) *self._regular_tile_size+step[0]* 4 ,tile_json_data['pos'][1] *self._regular_tile_size+step[1]* 4  ) , 
                                    ((tile_json_data['pos'][0]+1)*self._regular_tile_size+step[0]* 4 ,(tile_json_data['pos'][1]+1) *self._regular_tile_size+step[1]* 4  ) ,
                                    ((tile_json_data['pos'][0]) *self._regular_tile_size+step[0]* 4 ,(tile_json_data['pos'][1]+1) *self._regular_tile_size+step[1]* 4  ) ,
                                    ]
                        hulls.append(Hull(vertices))
                    return hulls 
        else: 
            return None
       

    
    def load_map(self,json_data):
        
        self._regular_tile_size = json_data['tile_size']

        # one step at a time.The tilemap.
        self._non_physical_tile_layers= json_data['offgrid_layers']
        self.lights = []

        self._physical_tiles= {}
        self.non_physical_tiles = [{} for i in range(0,self._non_physical_tile_layers)]


        for tile_key in json_data['tilemap']: 

            tile_size = (self._regular_tile_size,self._regular_tile_size) if json_data['tilemap'][tile_key]['type'] \
                                    not in IRREGULAR_TILE_SIZES else IRREGULAR_TILE_SIZES[json_data['tilemap'][tile_key]['type']]
            atl_pos = TILE_ATLAS_POSITIONS[json_data['tilemap'][tile_key]['type']]
            tile_pos = tuple(json_data['tilemap'][tile_key]["pos"])

            if json_data['tilemap'][tile_key]['type'] != "lights":
                if json_data['tilemap'][tile_key]['type'].endswith('door'):
                    hull = self._create_hulls(json_data['tilemap'][tile_key])
                    if json_data['tilemap'][tile_key]['type'].split('_')[0] == 'trap':
                        # Tile info creation for trap door 

                        rect = Rect(tile_pos[0] * self._regular_tile_size, self.pos[1] * self._regular_tile_size, self._regular_tile_size,5)
            
                        self._physical_tiles[tile_key] = [DoorInfo(json_data['tilemap'][tile_key]["type"],json_data['tilemap'][tile_key]["variant"],\
                                                                 tile_pos,tile_size,rect,atl_pos),False,hull]
                    else: 
                        if tile_key in self._physical_tiles: continue 
                        else: 
                            # TODO : ADD HULLS LATER 
                            rect = Rect(tile_pos[0] * self._regular_tile_size + 3, tile_pos[1] * self._regular_tile_size ,6,32)

                            door = [DoorInfo(json_data['tilemap'][tile_key]["type"],json_data['tilemap'][tile_key]["variant"],\
                                                                 tile_pos,tile_size,rect,atl_pos),DoorAnimation(5,5),hull]
                            self._physical_tiles[tile_pos] = door 
                            pos_below = (tile_pos[0],tile_pos[1] +1)
                            self._physical_tiles[pos_below]  = door 

                else:   
                    hull = self._create_hulls(json_data['tilemap'][tile_key])
                    # TODO: THE TILE KEYS NEED TO BE CHANGED TO INTS, NOT STRINGS. 

                    self._physical_tiles[tile_pos] = [TileInfo(json_data['tilemap'][tile_key]["type"],json_data['tilemap'][tile_key]["variant"],
                                                    tile_pos,tile_size,atl_pos),hull] 
            
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
       # self._get_hull_grid_mapping()


    @property
    def texture_atlas(self):
        return self._texture_atlas

    @property
    def physical_tiles(self):
        return self._physical_tiles

    @property
    def tile_size(self):
        return self._regular_tile_size
    
    @property
    def non_physical_tile_layers(self):
        return self._non_physical_tile_layers


    def get_minimal_rectangles(self):
        # Sorting the keys (grid positions) in increasing order
        sorted_positions = sorted(self._physical_tiles.keys())
        
        rectangles = []
        current_rectangle = None
        
        def add_rectangle(x1, y1, x2, y2):
            rectangles.append((x1, y1, x2, y2))
        
        for position in sorted_positions:
            x, y = position[0]*16,position[1] * 16
            tile = self._physical_tiles[position]  # Get the tile info (e.g., type, size)
            
            # We assume tile size is always 16x16 for simplicity
            tile_width, tile_height = 16, 16
            
            # If current_rectangle is None, start a new rectangle
            if current_rectangle is None:
                current_rectangle = (x, y, x + tile_width, y + tile_height)
            else:
                # Get the current rectangle boundaries
                current_x1, current_y1, current_x2, current_y2 = current_rectangle
                
                # Check if the current tile can be part of the current rectangle
                # They must be either horizontally or vertically aligned.
                if (x == current_x2 or y == current_y2): 
                    # Extend the current rectangle if possible
                    current_rectangle = (min(current_x1, x),
                                        min(current_y1, y),
                                        max(current_x2, x + tile_width),
                                        max(current_y2, y + tile_height))
                else:
                    # Otherwise, finalize the current rectangle and start a new one
                    add_rectangle(*current_rectangle)
                    current_rectangle = (x, y, x + tile_width, y + tile_height)
        
        # Add the last rectangle if any
        if current_rectangle is not None:
            add_rectangle(*current_rectangle)
        
        return rectangles

    def _get_hull_grid_mapping(self):
        """
        Groups tiles into the smallest possible rectangles and maps grid positions to their corresponding hulls.

        :param tile_dict: Dictionary where keys are grid positions (x, y) and values are tile objects.
        :return: Dictionary mapping grid positions to their corresponding hull objects.
        """
        # Sorting the grid positions
        sorted_positions = sorted(self._physical_tiles.keys())

        # List to store rectangles and dictionary for grid mapping
        hulls = []
        self._hull_grid_mapping = {}

        current_rectangle = None


        def create_rectangle(x1, y1, x2, y2):
            vertices = ((x1,y1),(x2,y1),(x2,y2),(x1,y2))
            hull = Hull(vertices,enabled= True)
            hulls.append(hull)


            # Calculate the grid cells spanned by this rectangle
            grid_start_x = x1 // self._regular_tile_size
            grid_start_y = y1 // self._regular_tile_size
            grid_end_x = (x2 - 1) // self._regular_tile_size  # Subtract 1 to avoid overshooting
            grid_end_y = (y2 - 1) // self._regular_tile_size

            # Map all grid cells covered by the rectangle to this hull
            for grid_x in range(grid_start_x, grid_end_x + 1):
                for grid_y in range(grid_start_y, grid_end_y + 1):
                    if (grid_x, grid_y) not in self._hull_grid_mapping:  # Avoid duplicates
                        self._hull_grid_mapping[(grid_x, grid_y)] = hull

        for position in sorted_positions:
            x, y =position 
            tile_width, tile_height = self._regular_tile_size,self._regular_tile_size 

            # If no current rectangle, start one
            if current_rectangle is None:
                current_rectangle = (x * self._regular_tile_size, y * self._regular_tile_size, 
                                    (x+1) * self._regular_tile_size,(y +1) * self._regular_tile_size)
            else:
                # Check if the tile can be added to the current rectangle
                current_x1, current_y1, current_x2, current_y2 = current_rectangle
                if y == current_y1 //self._regular_tile_size or x == current_x2 //self._regular_tile_size:
                    current_rectangle = (
                        current_x1,current_y1, 
                        current_x2 + tile_width, current_y2
                    )
                else:
                    # Finalize the current rectangle and start a new one
                    create_rectangle(*current_rectangle)
                    current_rectangle = (x * self._regular_tile_size, y * self._regular_tile_size, 
                                        (x+1) * self._regular_tile_size, (y+1)  * self._regular_tile_size)

        # Add the last rectangle if any
        if current_rectangle:
            create_rectangle(*current_rectangle)






    def get_lights(self) -> list[PointLight]:
        """
        Return all the lights that are in the tilemap.

        Is supposed to be used to initialize the pointlights for the render engine. 

        Returns: 
            list[PointLight] 
        """

        return self.lights
    

    def update_shadow_objs(self, native_res,camera_scroll):
        queried_hulls = []

        x_start = camera_scroll[0] // self.tile_size - 10
        x_end = (camera_scroll[0] + native_res[0]) // self.tile_size + 10
        y_start = camera_scroll[1] // self.tile_size - 10
        y_end = (camera_scroll[1] + native_res[1]) // self.tile_size + 10
        
        for x_cor in range(x_start, x_end):
            for y_cor in range(y_start, y_end):
                coor = (x_cor,y_cor)
                if coor in self._hull_grid_mapping:
                    queried_hulls.append(self._hull_grid_mapping[coor])
        return queried_hulls
                    


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

    
    def solid_check(self,check_pos) -> bool:
        return False 
        


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
