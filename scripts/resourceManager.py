from scripts.utils import load_texture
from typing import TYPE_CHECKING
from os import listdir
from json import load as jsLoad
import numpy as np 
from scripts.data import UI_ATLAS_POSITIONS_AND_SIZES,ITEM_ATLAS_POSITIONS_AND_SIZES,UI_WEAPON_ATLAS_POSITIONS_AND_SIZES,GRASS_ASSET_ATLAS_POS_AND_INFO,\
                                  TEXT_ATLAS_POSITIONS_AND_SPACE_AND_SIZES,IN_WORLD_WEAPON_ATLAS_POSITIONS_AND_SIZES,BULLET_ATLAS_POSITIONS_AND_SIZES

if TYPE_CHECKING: 
    from moderngl import Context,Texture


TEXTURE_BASE_PATH = 'data/images/'
RESOURCE_NAME_TO_PATH = {
    'tiles' : TEXTURE_BASE_PATH + "tiles/tile_atlas.png",
    'entities' : TEXTURE_BASE_PATH + 'entities/entities_atlas.png',
    'cursor' : TEXTURE_BASE_PATH +'cursor/cursor_atlas.png',
    'particles' : TEXTURE_BASE_PATH + 'particles/animation_atlas.png',
    'UI_and_items' : TEXTURE_BASE_PATH + 'ui/ui_atlas.png',
    'items' : TEXTURE_BASE_PATH +'items/item_atlas.png',
    'backgrounds' : TEXTURE_BASE_PATH + 'backgrounds',
    'tilemap_jsons' : 'map_jsons',
    'holding_weapons' : TEXTURE_BASE_PATH + 'weapons/holding',
    'weapons' : TEXTURE_BASE_PATH+'weapons/weapon_atlas.png',
    'bullets' : TEXTURE_BASE_PATH+'bullets/bullet_atlas.png',
    'grass_assets' : [
        TEXTURE_BASE_PATH + 'tiles/grass_atlasses/test_grass.png',
    ]
}

# maintain the grass assets class, so you can have different grass tilesets 
class GrassAssets:
    def __init__(self,asset_name:str)->None: 
        self.asset_name = asset_name
        self.grass_count_for_grass_var = GRASS_ASSET_ATLAS_POS_AND_INFO[asset_name][0]
        self.texture_dim =  GRASS_ASSET_ATLAS_POS_AND_INFO[asset_name][1]
        self.burn_palette = GRASS_ASSET_ATLAS_POS_AND_INFO[asset_name][2]
        self.gm = None 
         
   

class ResourceManager: 
    _instance = None 

    @staticmethod
    def get_instance(ctx:"Context" = None):
        if ResourceManager._instance is None: 
            ResourceManager._instance = ResourceManager(ctx)
        return ResourceManager._instance

    def __init__(self,ctx:"Context")-> None:
        self.ctx = ctx 
        self._texture_atlasses:dict[str,"Texture"]= {}
        for resource_name,path in RESOURCE_NAME_TO_PATH.items():
            if resource_name == 'backgrounds':
                self._load_backgrounds(path)
            elif resource_name == 'tilemap_jsons':
                self._load_tilemap_jsons(path)
            elif resource_name == 'holding_weapons':
                self._load_held_wpn_textures(path)
            elif resource_name =='grass_assets':
                self._load_grass_assets(path)
            else: 
                self._texture_atlasses[resource_name] = load_texture(path,self.ctx)

        self._compute_texture_coords()
        self._compute_particle_resources()

    @property 
    def bullet_atlas(self) -> "Texture":
        return self._texture_atlasses["bullets"]

    @property
    def ui_item_atlas(self) -> "Texture":
        return self._texture_atlasses["UI_and_items"]
    
    @property 
    def tile_atlas(self) -> "Texture": 
        return self._texture_atlasses['tiles']

    @property
    def entities_atlas(self) -> "Texture": 
        return self._texture_atlasses['entities']
    
    @property
    def particles_atlas(self) ->"Texture": 
        return self._texture_atlasses['particles']
    
    @property
    def held_wpn_atlas(self) -> "Texture": 
        return self._texture_atlasses['weapons']

    @property
    def held_wpn_textures(self) ->dict[str,"Texture"]:
        return self._held_wpn_textures
    
    @property 
    def circle_template(self) -> tuple["Context.buffer","Context.buffer"]:
        return (self._circle_vbo,self._circle_ibo)

    def _load_grass_assets(self,paths:str)->None: 
        self._grass_assets = {}
        self._grass_asset_texture_coords = {}

        for path in paths:
            split_path = path.split('/')
            asset_name = split_path[-1].split('.')[0] 
            self._texture_atlasses[asset_name] = load_texture(path,self.ctx)
            self._grass_assets[asset_name] = GrassAssets(asset_name)

            self._grass_asset_texture_coords[asset_name] = {}
            grass_variation_info,size = GRASS_ASSET_ATLAS_POS_AND_INFO[asset_name][0], GRASS_ASSET_ATLAS_POS_AND_INFO[asset_name][1] 
            for i,variations in enumerate(grass_variation_info):
                if i not in self._grass_asset_texture_coords[asset_name]:
                    self._grass_asset_texture_coords[asset_name][i] = []
                for j in range(variations):
                    bottomleft = (size[0]*j,size[1]*i) 
                    self._grass_asset_texture_coords[asset_name][i].append(self._create_texture_coords(bottomleft,size,self._texture_atlasses[asset_name]))


    def _load_backgrounds(self,path:str)->None:
        self._backgrounds= {}
        
        for folder in listdir(path = path):
            textures = []
            for tex_path in listdir(path= path+'/'+folder):
                tex = load_texture(path+ '/' +folder + '/' + tex_path,self.ctx)
                textures.append(tex)

            self._backgrounds[folder] = textures
        
    def _load_held_wpn_textures(self,path:str)-> None:
        self._held_wpn_textures = {}
        for texture_name in listdir(path = path):
            texture_name = texture_name.split('.')[0]
            self._held_wpn_textures[texture_name] = load_texture(f"{path}/{texture_name}.png",self.ctx)


    def _load_tilemap_jsons(self,path:str) -> None:
        self._tilemap_data = {}

        for file_name in listdir(path = path):
            f = open(path+'/'+file_name,'r')
            tilemap_data = jsLoad(f)
            self._tilemap_data[file_name] = tilemap_data

    def get_tilemap_json(self,name:str):
        return self._tilemap_data[name]

    def get_background_of_name(self,name:str):
        return self._backgrounds[name]
    
    def get_ga_of_name(self,name:str)->GrassAssets: 
        return self._grass_assets[name]
    

    def _compute_particle_resources(self) -> None: 
        # circle template for the fire particles 
        circle_vertices = self._generate_circle_vertices((0.0,0.0),1.0,segments = 100)
        self._circle_vbo = self.ctx.buffer(np.array(circle_vertices,dtype=np.float32).tobytes())
        
        circle_indices = self._generate_circle_indices(segments =100)
        self._circle_ibo = self.ctx.buffer(np.array(circle_indices,dtype ='i4').tobytes())
 

    def _generate_circle_vertices(self,center,radius,segments)-> list: 
        vertices = [center]
        for i in range(segments + 1):
            angle = 2 * np.pi * i / segments 
            x =  center[0] + radius * np.cos(angle)
            y = center[1] + radius * np.sin(angle)
            vertices.append((x,y))
        return vertices

    def _generate_circle_indices(self,segments)-> list:
        indices = []
        for i in range(1,segments):
            indices.extend([0,i,i+1])
        indices.extend([0,segments,1])

        return indices

    def _compute_texture_coords(self)-> None:
        self._ui_texcoords = {}
        self._item_texcoords = {}
        self._text_texcoords = {}
        self._bullet_texcoords = {}
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

        for key in IN_WORLD_WEAPON_ATLAS_POSITIONS_AND_SIZES:
            weapon = IN_WORLD_WEAPON_ATLAS_POSITIONS_AND_SIZES[key]
            self._in_world_item_texcoords[key] = {}
            for state in weapon: 
                pos,size = weapon[state] 
                self._in_world_item_texcoords[key][state] = self._create_texture_coords(pos,size,self.held_wpn_atlas)

        for key in BULLET_ATLAS_POSITIONS_AND_SIZES: 
            pos,size = BULLET_ATLAS_POSITIONS_AND_SIZES[key]
            self._bullet_texcoords[key] = self._create_texture_coords(pos,size,self.bullet_atlas)
 
    

    def _create_texture_coords(self,bottomleft:tuple[int,int],size:tuple[int,int],atlas :"Texture")->np.array:
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
