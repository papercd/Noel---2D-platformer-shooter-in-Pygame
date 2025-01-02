from scripts.data import TILE_ATLAS_POSITIONS,IRREGULAR_TILE_SIZES,TileInfo,LightInfo,DoorInfo,DoorAnimation,\
                            DoorTileInfoWithAnimation,TrapDoorTileInfoWithOpenState,RegularTileInfo,LightTileInfo,get_tile_rectangle, PHYSICS_APPLIED_TILE_TYPES

from scripts.spatial_grid import SpatialGrid
from scripts.lists import ambientNodeList,ambientNode
from my_pygame_light2d.hull import Hull 
from pygame import Rect
from my_pygame_light2d.light import PointLight
from scripts.resourceManager import ResourceManager

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np
    from moderngl import Context
    from scripts.data import TileColorKey,RGBA_tuple,TileInfoDataClass,TileTexcoordsKey



class Tilemap:
    def __init__(self,json_file= None):
        if json_file:
            self.load_map(json_file)

    @property
    def regular_tile_size(self)->int: 
        return self._regular_tile_size

    @property
    def physical_tiles(self)->dict[tuple[int,int],"TileInfoDataClass"]:
        return self._physical_tiles
    
    @property 
    def non_physical_tiles(self)->list[dict[tuple[int,int],"TileInfo"]]:
        return self._non_physical_tiles
    
    @property 
    def physical_tiles_vbo(self)->"Context.buffer":
        return self._physical_tiles_vbo

    @property 
    def non_physical_tiles_vbo(self)->"Context.buffer":
        return self._non_physical_tiles_vbo
       
    def load_map(self,json_file):

        rm = ResourceManager.get_instance()


        self._regular_tile_size:int = json_file['tile_size']
        self._non_physical_tile_layers:int= json_file['offgrid_layers']
        self._non_physical_tiles:list[dict[tuple[int,int],"TileInfo"]] = [{} for i in range(0,self._non_physical_tile_layers)]
        self._physical_tiles:dict[tuple[int,int],"TileInfoDataClass"] = {}
        self._ambient_node_ptr:ambientNode = None


        self.ref_texture_atlas = rm.texture_atlasses['tiles']
        self.hull_grid  = SpatialGrid(cell_size= self._regular_tile_size)
        self.lights : list["PointLight"]= []
        self.ambientNodes = ambientNodeList()
        self.tile_colors:dict["TileColorKey","RGBA_tuple"]= {}
        self.tile_texcoords: dict["TileTexcoordsKey","np.array"] = {}


        for tile_key in json_file['tilemap']: 
            tile_size = (self._regular_tile_size,self._regular_tile_size) if json_file['tilemap'][tile_key]['type'] \
                                    not in IRREGULAR_TILE_SIZES else IRREGULAR_TILE_SIZES[json_file['tilemap'][tile_key]['type']]

            atl_pos = TILE_ATLAS_POSITIONS[json_file['tilemap'][tile_key]['type']]
            tile_pos = tuple(json_file['tilemap'][tile_key]["pos"])

            relative_position_index,variant = map(int,json_file['tilemap'][tile_key]['variant'].split(';'))

            if json_file['tilemap'][tile_key]['type'] != "lights":
                if json_file['tilemap'][tile_key]['type'].endswith('door'):
                    if json_file['tilemap'][tile_key]['type'].split('_')[0] == 'trap':
                        # Tile info creation for trap door 

                        rect = Rect(tile_pos[0] * self._regular_tile_size, self.pos[1] * self._regular_tile_size, self._regular_tile_size,5)

                        self._physical_tiles[tile_pos] = TrapDoorTileInfoWithOpenState(
                                                            info = DoorInfo((json_file['tilemap'][tile_key]["type"],relative_position_index,variant,\
                                                                 tile_pos,tile_size,rect,atl_pos)),
                                                            open= False
                                                         )
                    else: 
                        if tile_key in self._physical_tiles: continue 
                        else: 
                            rect = Rect(tile_pos[0] * self._regular_tile_size + 3, tile_pos[1] * self._regular_tile_size ,6,32)

                            door = DoorTileInfoWithAnimation(
                                info = DoorInfo(json_file['tilemap'][tile_key]["type"],relative_position_index,variant,\
                                tile_pos,tile_size,rect,atl_pos),
                                animation= DoorAnimation(5,5)
                            )

                            self._physical_tiles[tile_pos] = door 

                            pos_below = (tile_pos[0],tile_pos[1] +1)
                            self._physical_tiles[pos_below]  = door 

                else:   
                    #hull = self._create_hulls(json_file['tilemap'][tile_key])
                    # TODO: THE TILE KEYS NEED TO BE CHANGED TO INTS, NOT STRINGS. 

                    self._physical_tiles[tile_pos] = RegularTileInfo(
                                                        info =TileInfo(json_file['tilemap'][tile_key]["type"],relative_position_index,variant,
                                                        tile_pos,tile_size,atl_pos) 
                                                    )

            
            else: 
                if isinstance(json_file['tilemap'][tile_key]["pos"][0],int):
                    # for lights that are on the tile grid 
                    #TODO: ADD LIGHTING LATER 
                    
                    light = PointLight(position = (json_file['tilemap'][tile_key]["pos"][0]*self._regular_tile_size+7,json_file['tilemap'][tile_key]["pos"][1]*self._regular_tile_size+3),\
                                         power= json_file['tilemap'][tile_key]["power"],radius = json_file['tilemap'][tile_key]["radius"] )
                    light.set_color(*json_file['tilemap'][tile_key]["colorValue"])
                    self.lights.append(light)
                    
                    pass 
                else: 
                    # for lights that are not placed on the tile grid  
                    # TODO : ADD LIGHTING LATER
                  
                    light = PointLight(position = (json_file['tilemap'][tile_key]["pos"][0]+7,json_file['tilemap'][tile_key]["pos"][1]+3),\
                                         power= json_file['tilemap'][tile_key]["power"],radius = json_file['tilemap'][tile_key]["radius"] )
                    light.set_color(*json_file['tilemap'][tile_key]["colorValue"])
                    self.lights.append(light)
                    
                rect = Rect(tile_pos[0] * self._regular_tile_size +3, tile_pos[1] * self._regular_tile_size, 10,6)

                self._physical_tiles[tile_pos] = LightTileInfo(
                                                   info = LightInfo(json_file['tilemap'][tile_key]["type"],relative_position_index,variant,\
                                                 tile_pos,tile_size,rect,json_file['tilemap'][tile_key]["radius"], json_file['tilemap'][tile_key]["power"],
                                                 json_file['tilemap'][tile_key]["colorValue"],atl_pos) ,
                                                 refPointLight= light
                                                )
        
        for i in range(0,self._non_physical_tile_layers):
            tilemap_key = f"offgrid_{i}"
            for tile_key in json_file[tilemap_key]:
                tile_pos = tuple(json_file[tilemap_key][tile_key]["pos"])
                atl_pos = TILE_ATLAS_POSITIONS[json_file[tilemap_key][tile_key]["type"]]
                tile_size = (self._regular_tile_size,self._regular_tile_size) if json_file[tilemap_key][tile_key]['type'] \
                                    not in IRREGULAR_TILE_SIZES else IRREGULAR_TILE_SIZES[json_file[tilemap_key][tile_key]['type']]

                if json_file[tilemap_key][tile_key]["type"] == "lights":
                    pass 
                    """
                    
                    if isinstance(json_file['offgrid_'+ str(i)][tile_key]["pos"][0],int):
                        light = PointLight(position = (json_file['offgrid_'+ str(i)][tile_key]["pos"][0]*self._regular_tile_size+7,json_file['offgrid_'+ str(i)][tile_key]["pos"][1]*self._regular_tile_size+3),\
                                         power= json_file['offgrid_'+ str(i)][tile_key]["power"],radius = json_file['offgrid_'+ str(i)][tile_key]["radius"] )
                        light.set_color(*json_file['offgrid_' + str(i)][tile_key]["colorValue"])
                        lights.append(light)
                        self.offgrid_tiles[i][tile_key] = Light(json_file['offgrid_'+str(i)][tile_key]["type"],json_file['offgrid_'+str(i)][tile_key]["variant"],json_file['offgrid_'+str(i)][tile_key]["pos"],\
                                                                radius = json_file['offgrid_'+str(i)][tile_key]['radius'],power = json_file['offgrid_'+str(i)][tile_key]['power'],color_value=json_file['offgrid_'+str(i)][tile_key]['colorValue'] )
                    else: 
                        light = PointLight(position = (json_file['offgrid_'+ str(i)][tile_key]["pos"][0]+7,json_file['offgrid_'+ str(i)][tile_key]["pos"][1]+3),\
                                         power= json_file['offgrid_'+ str(i)][tile_key]["power"],radius = json_file['offgrid_'+ str(i)][tile_key]["radius"] )
                        light.set_color(*json_file['offgrid_' + str(i)][tile_key]["colorValue"])
                        lights.append(light)
                        self.offgrid_tiles[i][tile_key] = Light(json_file['offgrid_'+str(i)][tile_key]["type"],json_file['offgrid_'+str(i)][tile_key]["variant"],(json_file['offgrid_'+str(i)][tile_key]["pos"][0] // self._regular_tile_size,json_file['offgrid_'+str(i)][tile_key]["pos"][1] // self._regular_tile_size),\
                                                            radius = json_file['offgrid_'+str(i)][tile_key]['radius'],power = json_file['offgrid_'+str(i)][tile_key]['power'],color_value=json_file['offgrid_'+str(i)][tile_key]['colorValue'] )
                    """
                else: 
                    self._non_physical_tiles[i][tile_pos] = TileInfo(json_file[tilemap_key][tile_key]["type"],relative_position_index,variant,
                                                            tile_pos,tile_size,atl_pos)
        
        for node_data in json_file['ambient_nodes']:
            if len(node_data.items()) ==4:
                self.ambientNodes.insert_interpolated_ambient_node(node_data["range"],node_data['hull_range'],node_data["leftColorValue"],node_data["rightColorValue"])
            else: 
                self.ambientNodes.insert_ambient_node(node_data["range"],node_data['hull_range'],node_data["colorValue"])
        

        self._create_hulls()
        for hull in self._hulls:
            self.hull_grid.insert(hull)

        

        self._physical_tiles_vbo, self._non_physical_tiles_vbo = rm.create_tilemap_vbos(self._regular_tile_size,self._non_physical_tile_layers)

        self.tile_colors = rm.get_tile_colors(self._physical_tiles)
        self.tile_texcoords = rm.get_tile_texcoords(self._physical_tiles,self._non_physical_tiles)




    def update_ambient_node_ptr(self,pos)->None:
        if self._ambient_node_ptr is None: 
            self._ambient_node_ptr = self.ambientNodes.set_ptr(pos[0])
        else: 
            if pos[0] < self._ambient_node_ptr.range[0]:
                if self._ambient_node_ptr.prev: 
                    self._ambient_node_ptr = self._ambient_node_ptr.prev
            elif pos[0] > self._ambient_node_ptr.range[1]:
                if self._ambient_node_ptr.next: 
                    self._ambient_node_ptr = self._ambient_node_ptr.next

    





    def _create_rectangles(self,tile_general_info: TileInfo) -> tuple[int,int,int,int]:
        return get_tile_rectangle(tile_general_info,self._regular_tile_size,self._physical_tiles)
        
          
    def _create_hulls(self)->None:
        """
        Merges rectangles in a dictionary where only rectangles of type "regular" are merged.
        
        :param rect_dict: Dictionary with keys as top-left grid-aligned positions (x, y) and 
                        values as (width, height, type).
        :param tile_size: Dimension of a grid square (default is 16).
        :return: List of merged rectangles [(x1, y1, x2, y2)].
        """
        # Convert rect_dict into a list of rectangles with positions
        self._rectangles = []

        for pos, tile_data in sorted(self._physical_tiles.items()):
            tile_general_info = tile_data.info
            if tile_general_info.type != 'spawners' and tile_general_info.type != 'lights':
                self._rectangles.extend(self._create_rectangles(tile_general_info))

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
        coor =(check_pos[0] // self._regular_tile_size , check_pos[1] //self._regular_tile_size)       
        tile_info_list = self._physical_tiles[coor]
        tile_info = tile_info_list[0] 
        rel_pos,variant = tile_info.relative_pos_ind,tile_info.variant
        return self._tile_colors[(tile_info.type,rel_pos,variant,side)]


    
    def solid_check(self,check_pos) -> bool:
        coor =(check_pos[0]//self._regular_tile_size,check_pos[1]//self._regular_tile_size)
        return coor  in self._physical_tiles\
                and self._physical_tiles[coor][0].type in PHYSICS_APPLIED_TILE_TYPES

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

    def write_to_physical_tiles(self,buffer_data:"np.array")->None: 
        self._physical_tiles_vbo.write(buffer_data.tobytes())