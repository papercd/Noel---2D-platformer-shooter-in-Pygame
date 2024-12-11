from scripts.utils import load_texture
from moderngl import Context,Texture
from os import listdir
from json import load as jsLoad
import numpy as np 
from scripts.atlass_positions import UI_ATLAS_POSITIONS_AND_SIZES,ITEM_ATLAS_POSITIONS_AND_SIZES,UI_WEAPON_ATLAS_POSITIONS_AND_SIZES,\
                                    TEXT_ATLAS_POSITIONS_AND_SPACE_AND_SIZES,IN_WORLD_WEAPON_ATLAS_POSITIONS_AND_SIZES


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

        self._compute_texture_coords()

    @property
    def ui_item_atlas(self) -> Texture:
        return self._texture_atlasses["UI_and_items"]
    
    @property 
    def tile_atlas(self) -> Texture: 
        return self._texture_atlasses['tiles']

    @property
    def entities_atlas(self) -> Texture: 
        return self._texture_atlasses['entities']
    
    @property
    def particles_atlas(self) ->Texture: 
        return self._texture_atlasses['particles']

    @property 
    def weapons_atlas(self) -> Texture: 
        return self._texture_atlasses['weapons']

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
    

    def _compute_texture_coords(self):
        self._ui_texcoords = {}
        self._item_texcoords = {}
        self._text_texcoords = {}
        self._in_world_item_texcoords = {}

        for key in UI_ATLAS_POSITIONS_AND_SIZES:
            if key.endswith('slot'):
                self._ui_texcoords[key] = {}
                for state in UI_ATLAS_POSITIONS_AND_SIZES[key]:
                    pos,size = UI_ATLAS_POSITIONS_AND_SIZES[key][state]
                    self._ui_texcoords[key][state] = self._create_texture_coords(pos,size,self.ui_item_atlas)

            elif key == "cursor":
                self._ui_texcoords[key] = {}
                for state in UI_ATLAS_POSITIONS_AND_SIZES[key]:
                    pos,size = UI_ATLAS_POSITIONS_AND_SIZES[key][state]
                    self._ui_texcoords[key][state] = self._create_texture_coords(pos,size,self.ui_item_atlas)
            else: 
                pos,size = UI_ATLAS_POSITIONS_AND_SIZES[key]
                self._ui_texcoords[key] = self._create_texture_coords(pos,size,self.ui_item_atlas)

        for key in ITEM_ATLAS_POSITIONS_AND_SIZES:
            pos,size= ITEM_ATLAS_POSITIONS_AND_SIZES[key]
            self._item_texcoords[key] = self._create_texture_coords(pos,size,self.ui_item_atlas)

        for key in UI_WEAPON_ATLAS_POSITIONS_AND_SIZES:
            pos,size = UI_WEAPON_ATLAS_POSITIONS_AND_SIZES[key]
            self._item_texcoords[key] = self._create_texture_coords(pos,size,self.ui_item_atlas)

        for key in TEXT_ATLAS_POSITIONS_AND_SPACE_AND_SIZES:
            pos,space,size = TEXT_ATLAS_POSITIONS_AND_SPACE_AND_SIZES[key]
            self._text_texcoords[key] = []
            if key == 'CAPITAL' or key == 'LOWER':
                count = 26
            else:
                count = 10
            for i in range(count):
                bottomleft = (pos[0] + space[0] *i,pos[1])
                self._text_texcoords[key].append(self._create_texture_coords(bottomleft,size,self.ui_item_atlas))
 
        for weapon_name in IN_WORLD_WEAPON_ATLAS_POSITIONS_AND_SIZES: 
            self._in_world_item_texcoords[weapon_name] = {}
            for state in IN_WORLD_WEAPON_ATLAS_POSITIONS_AND_SIZES[weapon_name]:
                pos,size = IN_WORLD_WEAPON_ATLAS_POSITIONS_AND_SIZES[weapon_name][state]
                self._in_world_item_texcoords[weapon_name][state] = self._create_texture_coords(pos,size,self.weapons_atlas)
    

    def _create_texture_coords(self,bottomleft:tuple[int,int],size:tuple[int,int],atlas :Texture):
        x = (bottomleft[0] ) / atlas.width
        y = (bottomleft[1] ) / atlas.height

        w = size[0] / atlas.width
        h = size[1] / atlas.height

        p1 = (x,y+h) 
        p2 = (x+w,y+h)
        p3 = (x,y) 
        p4 = (x+w,y)

        return np.array([p1,p2,p3,
                        p3,p2,p4],dtype = np.float32 )
