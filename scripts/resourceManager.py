from scripts.utils import load_texture
from moderngl import Context
from os import listdir
from json import load as jsLoad
class ResourceManager: 
    _instance = None 

    @staticmethod
    def get_instance(ctx:Context = None,resource_name_to_path: dict[str,str] = None):
        if ResourceManager._instance is None: 
            ResourceManager._instance = ResourceManager(ctx,resource_name_to_path)
        return ResourceManager._instance

    def __init__(self,ctx,resource_name_to_path):
        self.ctx = ctx 
        self._texture_atlasses = {}
        for resource_name,path in resource_name_to_path.items():
            if resource_name == 'backgrounds':
                self._load_backgrounds(path)
            elif resource_name == 'tilemap_jsons':
                self._load_tilemap_jsons(path)
            else: 
                self._texture_atlasses[resource_name] = load_texture(path,self.ctx)

    def _load_backgrounds(self,path:str):
        self._backgrounds= {}
        
        for folder in listdir(path = path):
            textures = []
            for tex_path in listdir(path= path+'/'+folder):
                tex = load_texture(path+ '/' +folder + '/' + tex_path,self.ctx)
                textures.append(tex)

            self._backgrounds[folder] = textures
        

    def _load_tilemap_jsons(self,path:str):
        self._tilemap_data = {}

        for file_name in listdir(path = path):
            f = open(path+'/'+file_name,'r')
            tilemap_data = jsLoad(f)
            self._tilemap_data[file_name] = tilemap_data

    def get_tilemap_json(self,name:str):
        return self._tilemap_data[name]

    def get_background_of_name(self,name:str):
        return self._backgrounds[name]
    
    def get_atlas_of_name(self,name:str):
        return self._texture_atlasses[name]

    def compute_texture_coords(self):
        pass