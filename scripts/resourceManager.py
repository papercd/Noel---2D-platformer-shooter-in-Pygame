from utils import load_texture
from moderngl import Context
class ResourceManager: 
    _instance = None 

    @staticmethod
    def get_instance(ctx:Context,atlas_name_to_path: dict[str,str] = None):
        if ResourceManager._instance is None: 
            ResourceManager._instance = ResourceManager(ctx,atlas_name_to_path)
        return ResourceManager._instance

    def __init__(self,ctx,atlas_name_to_path):
        self.ctx = ctx 

    def compute_texture_coords(self):
        pass