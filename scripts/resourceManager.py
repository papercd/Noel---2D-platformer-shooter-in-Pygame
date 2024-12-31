from scripts.utils import load_texture
from typing import TYPE_CHECKING
from os import listdir
from json import load as jsLoad
import numpy as np 
from scripts.data import TEXTURE_BASE_PATH,UI_ATLAS_POSITIONS_AND_SIZES,ITEM_ATLAS_POSITIONS_AND_SIZES,UI_WEAPON_ATLAS_POSITIONS_AND_SIZES,GRASS_ASSET_ATLAS_POS_AND_INFO,PARTICLE_ANIMATION_DATA,\
                                  TEXT_ATLAS_POSITIONS_AND_SPACE_AND_SIZES,IN_WORLD_WEAPON_ATLAS_POSITIONS_AND_SIZES,BULLET_ATLAS_POSITIONS_AND_SIZES,PARTICLE_ATLAS_POSITIONS_AND_SIZES

if TYPE_CHECKING: 
    from moderngl import Context,Texture
    from scripts.new_grass import GrassManager


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
        self.asset_name:str = asset_name
        self.grass_count_for_grass_var: tuple[int] = GRASS_ASSET_ATLAS_POS_AND_INFO[asset_name][0]
        self.texture_dim:tuple[int,int]=  GRASS_ASSET_ATLAS_POS_AND_INFO[asset_name][1]
        self.burn_palette:tuple[int,int,int] = GRASS_ASSET_ATLAS_POS_AND_INFO[asset_name][2]
        self.gm : "GrassManager" = None 
         
   

class ResourceManager: 
    _instance = None 
    _ctx = None



    @staticmethod
    def get_instance(ctx:"Context" = None)->"ResourceManager":
        if ResourceManager._instance is None: 
            ResourceManager._ctx = ctx
            ResourceManager._instance = ResourceManager()
        return ResourceManager._instance
    

    def __init__(self)-> None:
        if not hasattr(self,"initialized") :
            self.initialized: bool = True
            self.texture_atlasses:dict[str,"Texture"]= {}

            self.backgrounds:dict[str,list["Texture"]] = {}
            self.tilemap_data = {}
            self.held_wpn_textures:dict[str,"Texture"] = {}
            
            self.grass_assets:dict[str,GrassAssets] = {}
            self.grass_asset_texcoords:dict[str,dict[int,np.array]] = {}


            self.ui_texcoords = {}
            self.item_texcoords = {}
            self.text_texcoords:dict[str,list[np.array]] = {}
            self.bullet_texcoords:dict[str,np.array] = {}
            self.in_world_item_texcoords:dict[str,dict[str,np.array]] = {}
            self.animated_particle_texcoords:dict[tuple[str,int],np.array] = {}

            for resource_name,path in RESOURCE_NAME_TO_PATH.items():
                if resource_name == 'backgrounds':
                    self._load_backgrounds(path)
                elif resource_name == 'tilemap_jsons':
                    self._load_tilemap_jsons(path)
                elif resource_name == 'holding_weapons':
                    self._load_held_wpn_textures(path)
                elif resource_name =='grass_assets':
                    self._load_grass_assets_and_texcoords(path)
                else: 
                    self.texture_atlasses[resource_name] = load_texture(path,ResourceManager._ctx)

            self._compute_texture_coords()
            self._compute_fire_particle_vertices_and_indices()


    def _load_grass_assets_and_texcoords(self,paths:list[str])->None: 

        for path in paths:
            split_path = path.split('/')
            asset_name = split_path[-1].split('.')[0] 
            self.texture_atlasses[asset_name] = load_texture(path,ResourceManager._ctx)
            self.grass_assets[asset_name] = GrassAssets(asset_name)

            self.grass_asset_texcoords[asset_name] = {}
            grass_variation_info,size = GRASS_ASSET_ATLAS_POS_AND_INFO[asset_name][0], GRASS_ASSET_ATLAS_POS_AND_INFO[asset_name][1] 
            for i,variations in enumerate(grass_variation_info):
                if i not in self.grass_asset_texcoords[asset_name]:
                    self.grass_asset_texcoords[asset_name][i] = []
                for j in range(variations):
                    bottomleft = (size[0]*j,size[1]*i) 
                    self.grass_asset_texcoords[asset_name][i].append(self._create_texture_coords(bottomleft,size,self.texture_atlasses[asset_name]))


    def _load_backgrounds(self,path:str)->None:
        
        for folder in listdir(path = path):
            textures = []
            for tex_path in listdir(path= path+'/'+folder):
                tex = load_texture(path+ '/' +folder + '/' + tex_path,ResourceManager._ctx)
                textures.append(tex)

            self.backgrounds[folder] = textures
        
    def _load_held_wpn_textures(self,path:str)-> None:
        for texture_name in listdir(path = path):
            texture_name = texture_name.split('.')[0]
            self.held_wpn_textures[texture_name] = load_texture(f"{path}/{texture_name}.png",ResourceManager._ctx)


    def _load_tilemap_jsons(self,path:str) -> None:

        for file_name in listdir(path = path):
            f = open(path+'/'+file_name,'r')
            tilemap_data = jsLoad(f)
            self.tilemap_data[file_name] = tilemap_data



    

    def _compute_fire_particle_vertices_and_indices(self) -> None: 
        # circle template for the fire particles 
        circle_vertices = self._generate_circle_vertices((0.0,0.0),1.0,segments = 100)
        self.circle_vbo = ResourceManager._ctx.buffer(np.array(circle_vertices,dtype=np.float32).tobytes())
        
        circle_indices = self._generate_circle_indices(segments =100)
        self.circle_ibo = ResourceManager._ctx.buffer(np.array(circle_indices,dtype ='i4').tobytes())


    def _generate_circle_vertices(self,center:tuple[float,float],radius:float,segments:int)->list[tuple[float,float]]: 
        vertices = [center]
        for i in range(segments + 1):
            angle = 2 * np.pi * i / segments 
            x =  center[0] + radius * np.cos(angle)
            y = center[1] + radius * np.sin(angle)
            vertices.append((x,y))
        return vertices

    def _generate_circle_indices(self,segments:int)->list[int]:
        indices = []
        for i in range(1,segments):
            indices.extend([0,i,i+1])
        indices.extend([0,segments,1])

        return indices

    def _compute_texture_coords(self)-> None:

        for key in UI_ATLAS_POSITIONS_AND_SIZES:
            if key.endswith('slot'):
                self.ui_texcoords[key] = {}
                for state in UI_ATLAS_POSITIONS_AND_SIZES[key]:
                    pos,size = UI_ATLAS_POSITIONS_AND_SIZES[key][state]
                    self.ui_texcoords[key][state] = self._create_texture_coords(pos,size,self.texture_atlasses["UI_and_items"])

            elif key == "cursor":
                self.ui_texcoords[key] = {}
                for state in UI_ATLAS_POSITIONS_AND_SIZES[key]:
                    pos,size = UI_ATLAS_POSITIONS_AND_SIZES[key][state]
                    self.ui_texcoords[key][state] = self._create_texture_coords(pos,size,self.texture_atlasses["UI_and_items"])
            else: 
                pos,size = UI_ATLAS_POSITIONS_AND_SIZES[key]
                self.ui_texcoords[key] = self._create_texture_coords(pos,size,self.texture_atlasses["UI_and_items"])

        for key in ITEM_ATLAS_POSITIONS_AND_SIZES:
            pos,size= ITEM_ATLAS_POSITIONS_AND_SIZES[key]
            self.item_texcoords[key] = self._create_texture_coords(pos,size,self.texture_atlasses["UI_and_items"])

        for key in UI_WEAPON_ATLAS_POSITIONS_AND_SIZES:
            pos,size = UI_WEAPON_ATLAS_POSITIONS_AND_SIZES[key]
            self.item_texcoords[key] = self._create_texture_coords(pos,size,self.texture_atlasses["UI_and_items"])

        for key in TEXT_ATLAS_POSITIONS_AND_SPACE_AND_SIZES:
            pos,space,size = TEXT_ATLAS_POSITIONS_AND_SPACE_AND_SIZES[key]
            self.text_texcoords[key] = []
            if key == 'CAPITAL' or key == 'LOWER':
                count = 26
            else:
                count = 10
            for i in range(count):
                bottomleft = (pos[0] + space[0] *i,pos[1])
                self.text_texcoords[key].append(self._create_texture_coords(bottomleft,size,self.texture_atlasses["UI_and_items"]))

        for key in IN_WORLD_WEAPON_ATLAS_POSITIONS_AND_SIZES:
            weapon = IN_WORLD_WEAPON_ATLAS_POSITIONS_AND_SIZES[key]
            self.in_world_item_texcoords[key] = {}
            for state in weapon: 
                pos,size = weapon[state] 
                self.in_world_item_texcoords[key][state] = self._create_texture_coords(pos,size,self.texture_atlasses['weapons'])

        for key in BULLET_ATLAS_POSITIONS_AND_SIZES: 
            pos,size = BULLET_ATLAS_POSITIONS_AND_SIZES[key]
            self.bullet_texcoords[key] = self._create_texture_coords(pos,size,self.texture_atlasses['bullets'])
 
    
        # precompute animated particle texture coords 
        for key in PARTICLE_ATLAS_POSITIONS_AND_SIZES: 
            atl_pos,tex_size = PARTICLE_ATLAS_POSITIONS_AND_SIZES[key]
            animationData =PARTICLE_ANIMATION_DATA[key]
            for frame in range(animationData.n_textures):
                bottomleft = (atl_pos[0] + tex_size[0] * frame, atl_pos[1])
                self.animated_particle_texcoords[(key,frame)] = self._create_texture_coords(bottomleft,tex_size,self.texture_atlasses["particles"])


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


    def get_tilemap_json(self,name:str):
        return self.tilemap_data[name]

    def get_background_of_name(self,name:str):
        return self.backgrounds[name]
    
    def get_ga_of_name(self,name:str)->GrassAssets: 
        return self.grass_assets[name]
    

