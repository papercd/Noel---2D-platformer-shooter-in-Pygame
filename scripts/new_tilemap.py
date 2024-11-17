from scripts.atlass_positions import TILE_ATLAS_POSITIONS
from scripts.custom_data_types import TileInfo
from moderngl import Texture
from pygame import Rect
from scripts.utils import load_texture

TEXTURE_BASE_PATH = 'data/images/'
PHYSICS_APPLIED_TILE_TYPES = {'grass','stone','box','building_0','building_1','building_2','building_3','building_4','building_5','building_stairs','building_door','trap_door',\
                              'ladder'}



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
            self._load_map(json_data)


    def _load_map(self,json_data):
        
        self._regular_tile_size = json_data['tile_size']

        # one step at a time.The tilemap.

        self.physical_tiles:dict[tuple[int,int],TileInfo] = {}

        for tile_key in json_data['tilemap']:
            if json_data['tilemap'][tile_key]['type'] != "lights":

                # TODO: DON'T THINK ABOUT LIGHTS FOR NOW, get the tile rendering working first. 
                atlass_query_pos = TILE_ATLAS_POSITIONS[json_data['tilemap'][tile_key]["type"]]

                # TODO: THE TILE KEYS NEED TO BE CHANGED TO INTS, NOT STRINGS. 
                tile_pos = tuple(json_data['tilemap'][tile_key]["pos"])


                self.physical_tiles[tile_pos] = TileInfo(json_data['tilemap'][tile_key]["type"],json_data['tilemap'][tile_key]["variant"],
                                                 tile_pos,atlass_query_pos) 
            
            else: 
                pass


    

    def get_atlas(self) -> Texture: 
        """
        Return the tilemap's texture atlas.
        
        Returns: 
            texture atlas (moderngl.Texture)
            
        """
        
        return self._texture_atlas

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

                if tile_key in self.physical_tiles:
                    tile = self.physical_tiles[tile_key]

                    # TODO : differentiate tile info objects based on tile type
                    if tile.type.endswith('door') and not tile.open:
                        # Check whether there is a door tile above, and if there isn't, add it to the list. 
                        if (x,y) in self.physical_tiles:
                            if not self.physical_tiles[(x,y)].type.endswith('door'):
                                tiles.append(self.physical_tiles[tile_key])
                        else: 
                            tiles.append(self.physical_tiles[tile_key])
                    else: 
                        tiles.append(self.physical_tiles[tile_key])
                
                # TODO: add grass tiles later.  


        return tiles

    
    def solid_check(self,check_pos) -> bool:
        return False 
        


    def phy_rects_around(self,pos,size)->tuple[Rect,TileInfo]:
        surrounding_rects = []

        tiles_around = self.tiles_around(pos,size)
        
        for tile in tiles_around:
            if tile.type in PHYSICS_APPLIED_TILE_TYPES: 
                if tile.type.endswith('door'):
                    #TODO: add this when you have doors. 
                    pass 
                else: 
                    rect = (
                        tile.pos[0] * self.tile_size,         # left
                        tile.pos[1] * self.tile_size,         # top
                        self.tile_size,                       # width
                        self.tile_size                        # height
                    )
                
                    surrounding_rects.append((Rect(*rect),tile))

            else: 
                # TODO: add this when you have non physical tiles. 
                pass 

        return surrounding_rects
