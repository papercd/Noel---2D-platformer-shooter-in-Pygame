from scripts.atlass_positions import TILE_ATLAS_POSITIONS
class Tilemap:
    def __init__(self,json_data):
        
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