TILE_ATLAS_POSITIONS ={




}




class Tilemap:
    def __init__(self,json_data):
        self.physical_tiles = {}
        
        self._load_map(json_data)


    def _load_map(self,json_data):

        # one step at a time. create another test, and 
        pass 