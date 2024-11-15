

class Tilemap:
    def __init__(self,json_data):
        self.physical_tiles = {}
        
        self._load_map(json_data)


    def _load_map(self,json_data):
        for tile_key in json_data['tilemap']:
            pass 