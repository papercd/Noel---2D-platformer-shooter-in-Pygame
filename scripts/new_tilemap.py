from scripts.atlass_positions import TILE_ATLAS_POSITIONS
from moderngl import Texture,Context
from scripts.utils import load_texture

TEXTURE_BASE_PATH = 'data/images/'

class Tilemap:
    def __init__(self,context:Context,json_data = None):
        """ 
        Initialize the Tilemap object. 

        Args:
            json_data (json) : the json data you want to load the tilemap with. leave this blank 
            for empty Tilemap object. 
        
        """

        self._ctx = context
        self._atlas_dict = self._create_atlasses()
        
        if json_data:
            self._load_map(json_data)


    def _load_map(self,json_data):
        
        self._regular_tile_size = json_data['tile_size']

        # one step at a time.The tilemap.

        self.physical_tiles = {}

        for tile_key in json_data['tilemap']:
            if json_data['tilemap'][tile_key]['type'] != "lights":
                # TODO: DON'T THINK ABOUT LIGHTS FOR NOW, get the tile rendering working first. 
                atlass_query_pos = TILE_ATLAS_POSITIONS[json_data['tilemap'][tile_key]["type"]]

                # TODO: THE TILE KEYS NEED TO BE CHANGED TO INTS, NOT STRINGS. 
                tile_pos = tuple(json_data['tilemap'][tile_key]["pos"])
                self.physical_tiles[tile_pos] = (json_data['tilemap'][tile_key]["type"],json_data['tilemap'][tile_key]["variant"],
                                                 tile_pos,atlass_query_pos)    
            
            else: 
                pass


    def _create_atlasses(self) -> dict[str,Texture]:
        """
        Create a dictionary for the atlasses (texture map) you want to use. 
        
        Access the atlass with the name of the atlass type (str) ex: 'tiles', 'spawners'

        """
        dict = {}
        
        # load tile atlas 
        dict['tiles'] = load_texture(TEXTURE_BASE_PATH + 'tiles/tile_atlas.png',self._ctx)
        
        return dict


    def get_atlas(self,atlas_name:str) -> Texture: 
        """
        Return a texture atlas from the atlas dictionary with its name.
        
        Args:
            atlas_name (str) 
        
        Returns: 
            texture atlas (moderngl.Texture)
            
        """
        
        return self._atlas_dict[atlas_name]