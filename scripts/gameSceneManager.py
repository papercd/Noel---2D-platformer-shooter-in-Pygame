import json 
from os import listdir
from scripts.utils import load_texture 
from moderngl import Context
from scripts.background import Background

class GameSceneManager:

    """ A scene manager to handle your game scenes """

    def __init__(self,ctx: Context,backgrounds_path:str,tilemaps_path:str):
        """
        initialize the scene manager. 

        Args:
            ctx (moderngl.Context) : the moderngl context
            backgrounds_path (str): the path to your directory containing folders with the background textures. 
            tilemaps_path (str): the path to your directory containing json files for different maps. 
        
        """


        # private
        self._ctx = ctx
        self._tilemap_json_files = self._load_tilemap_jsons(tilemaps_path) 
                 
        
        # public 
        self.backgrounds = self._load_backgrounds(backgrounds_path) 
 
    
    def _load_tilemap_jsons(self,tilemaps_path:str):
        """
        load tilemap json files to create list of tilemap data

        Args: 
            tilemaps_path (str) : the path to your directory containing json files for different maps 

        Returns: 
            A dictionary with (filename, tilemap data) key-value pair 
        """
        tilemap_data_dict = {}

        for file_name in listdir(path = tilemaps_path):
            f = open(tilemaps_path+'/'+file_name,'r')
            tilemap_data = json.load(f)
            tilemap_data_dict[file_name] = tilemap_data

        return tilemap_data_dict


    def _load_backgrounds(self,backgrounds_path: str):
        """
        load background textures and create a dictionary with (path,Bacgkround) key-value pair 

        Args: 
            backgrounds_path (str) : the path to your directory containing folders with the background textures. 
        
        Returns: 
            A dictionary with (path, Background) key-value pair 
        """
        backgrounds_dict = {}
        
        for folder in listdir(path = backgrounds_path):
            textures = []
            for tex_path in listdir(path= backgrounds_path +'/'+folder):
                tex = load_texture(backgrounds_path + '/' +folder + '/' + tex_path,self._ctx)
                textures.append(tex)

            backgrounds_dict[folder] = Background(textures)
        
        return backgrounds_dict

    

    def get_json_data(self,map_json_name:str):
        """
        get the json data with the map file name. 

        Args: 
            map_json_name (str) : the name of the json file
        
        Returns: 
            the json data 
        
        """
        return self._tilemap_json_files[map_json_name]

    