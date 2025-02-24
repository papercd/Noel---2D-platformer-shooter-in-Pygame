from scripts.background import Background
from scripts.utils import load_texture
from os import listdir
from json import load as jsLoad
from scripts.data import IN_WORLD_WEAPON_ATLAS_POSITIONS_AND_SIZES,UI_WEAPON_ATLAS_POSITIONS_AND_SIZES,ITEM_ATLAS_POSITIONS,ITEM_SIZES,TEXTURE_BASE_PATH,TILE_COLOR_SAMPLE_POS_TO_DIM_RATIO,TILE_ATLAS_POSITIONS,ENTITIES_ATLAS_POSITIONS ,ENTITY_ANIMATION_DATA,ENTITY_SIZES,\
                    DoorTileInfoWithAnimation,TrapDoorTileInfoWithOpenState,TileInfo,TileInfoDataClass,AnimationDataCollection,UI_ATLAS_POSITIONS_AND_SIZES

from numpy import uint32,uint8,uint16,int32,float32,array,zeros,frombuffer
from moderngl import Context

from typing import TYPE_CHECKING

if TYPE_CHECKING: 
    from moderngl import Texture
    from scripts.new_tilemap import Tilemap
    from scripts.data import TileColorKey,RGBA_tuple,TileTexcoordsKey

TEXTURE_ATLAS_NAMES_TO_PATH = {
    'tiles' : TEXTURE_BASE_PATH + 'tiles/tile_atlas.png',
    'entities' :   TEXTURE_BASE_PATH + 'entities/entities_atlas.png',
    'ui' : TEXTURE_BASE_PATH + 'ui/ui_atlas.png',
    'items' : TEXTURE_BASE_PATH + 'items/item_atlas.png',
    'holding_weapons' : TEXTURE_BASE_PATH + 'weapons/weapon_atlas.png',
    'bullet': TEXTURE_BASE_PATH + 'bullets/bullet_atlas.png'
}

class ResourceManager:

    _instance = None 
    _gl_ctx : Context = None
    _game_ctx = None

    @staticmethod
    def get_instance(gl_ctx: Context = None, game_context = None)->"ResourceManager":
        if ResourceManager._instance is None: 
            
            assert isinstance(gl_ctx, Context), "Error: Resource Manager must be initialized with an openGL context."
            assert game_context is not None , "Error: Resource Manager must be initialized with the game context."

            ResourceManager._gl_ctx = gl_ctx
            ResourceManager._game_ctx = game_context
            ResourceManager._instance = ResourceManager()

        return ResourceManager._instance
   

    def __init__(self)->None: 
   
        # create animation data collections for entities' animations 
        self._create_animation_data_collections()

        # load the background textures and create background objects 
        self._load_backgrounds(TEXTURE_BASE_PATH + 'backgrounds')

        # load tilemap json files 
        self._load_tilemap_json_files('map_jsons')

        # load texture atlasses 
        self._load_texture_atlasses()

        # load entity texcoords 
        self._load_entity_texcoords_and_local_vertices()

        # load ui texcoords 
        self._create_ui_element_texcoords()

        # load item texcoords 
        self._create_item_texcoords_and_local_vertices()

        # load holding weapon texcoords
        self._create_holding_weapon_vertices_texcoords()

        # load main bullet texcoords and vertices 
        self._create_main_weapon_bullet_vertices_texcoords()

    def _create_animation_data_collections(self)->None: 
        self.animation_data_collections = {}
        self.animation_data_collections['player'] = AnimationDataCollection(ENTITY_ANIMATION_DATA['player'])  
        
        # create animation data collections for items 

    def _load_backgrounds(self,path:str)->None:

        # identity texcoords that represent texcoords for textures without an atlas 
        self.identity_texcoords_bytes = array([(0.,1.),(1.,1.),(0.,0.),
                                            (0.,0.),(1.,1.),(1.,0.)],dtype=float32).tobytes()
        
        self.backgrounds : dict[str,Background] = {}

        for folder in listdir(path):
            textures = []
            for tex_path in listdir(path = path + '/' + folder):
                textures.append(load_texture(path +'/'+folder+'/'+tex_path,self._gl_ctx))
                
            self.backgrounds[folder] = Background(textures,self.identity_texcoords_bytes)


    def _load_tilemap_json_files(self,path:str)->None: 
        self.tilemap_jsons = {}

        for file_name in listdir(path = path):
            f = open(path+'/'+file_name,'r')
            tilemap_data = jsLoad(f)
            self.tilemap_jsons[file_name] = tilemap_data


    def _load_texture_atlasses(self)->None: 
        self.texture_atlasses: dict[str,"Texture"] = {}
        for atlas_name in TEXTURE_ATLAS_NAMES_TO_PATH:
            self.texture_atlasses[atlas_name] = load_texture(TEXTURE_ATLAS_NAMES_TO_PATH[atlas_name],self._gl_ctx)


    def get_cursor_ndc_vertices_and_buffer(self)->list[array,"Context.buffer"]: 
        x = 0. 
        y = 0. 
        w = 2. * 9 / self._game_ctx['true_res'][0]
        h = 2. * 10 / self._game_ctx['true_res'][1] 

        cursor_ndc_vertices = array([(x, y-h), (x + w, y-h), (x, y),
                            (x, y), (x + w, y - h), (x + w, y)], dtype=float32)

        return [array([(x, y-h), (x + w, y-h), (x, y), (x, y), (x + w, y - h), (x + w, y)], dtype=float32), 
                    self._gl_ctx.buffer(data= cursor_ndc_vertices,dynamic=True)]
                           

    def _create_ui_element_texcoords(self)->None: 

        self.ui_element_texcoords_bytes = {}
        self.ui_element_texcoords_array = {}

        for ui_element in UI_ATLAS_POSITIONS_AND_SIZES: 
            if ui_element.endswith('slot'):
                self.ui_element_texcoords_bytes[ui_element] = {}
                for hovered_state in UI_ATLAS_POSITIONS_AND_SIZES[ui_element]:
                    atlas_position,texture_size = UI_ATLAS_POSITIONS_AND_SIZES[ui_element][hovered_state]
                    self.ui_element_texcoords_bytes[ui_element][hovered_state] = self._create_texcoords(atlas_position,texture_size,self.texture_atlasses['ui'])
            elif ui_element == 'cursor':
                self.ui_element_texcoords_array['cursor'] = {}
                for cursor_state in UI_ATLAS_POSITIONS_AND_SIZES['cursor']:
                    atlas_position,texture_size = UI_ATLAS_POSITIONS_AND_SIZES['cursor'][cursor_state]
                    self.ui_element_texcoords_array['cursor'][cursor_state] = self._create_texcoords(atlas_position,texture_size,self.texture_atlasses['ui'],asbytes=False)
            else: 
                atlas_position,texture_size = UI_ATLAS_POSITIONS_AND_SIZES[ui_element]
                self.ui_element_texcoords_bytes[ui_element] = self._create_texcoords(atlas_position,texture_size,self.texture_atlasses['ui'])

    
    def _create_main_weapon_bullet_vertices_texcoords(self)->None: 
        size = (uint32(16),uint32(5))
        self.bullet_local_vertices_bytes = self._create_entity_local_vertices(size)
        self.bullet_texcoords_bytes = self._create_texcoords((uint32(0),uint32(0)),size,self.texture_atlasses['bullet'])

    def _create_item_texcoords_and_local_vertices(self)->None: 
        self.item_texcoords_bytes = {}
        self.item_local_vertices_bytes = {}

        for item_name in ITEM_ATLAS_POSITIONS: 
            atlas_pos,size = ITEM_ATLAS_POSITIONS[item_name], ITEM_SIZES[item_name]
            self.item_local_vertices_bytes[item_name] = self._create_entity_local_vertices(size)
            self.item_texcoords_bytes[item_name] = self._create_texcoords(atlas_pos,size,self.texture_atlasses['items'])

        for weapon_name in UI_WEAPON_ATLAS_POSITIONS_AND_SIZES: 
            atlas_pos,size = UI_WEAPON_ATLAS_POSITIONS_AND_SIZES[weapon_name]
            self.item_local_vertices_bytes[weapon_name] = self._create_entity_local_vertices(size)
            self.item_texcoords_bytes[weapon_name] = self._create_texcoords(atlas_pos,size,self.texture_atlasses['ui'])


    def _create_holding_weapon_vertices_texcoords(self)->None:

        self.holding_weapon_texcoords_bytes = {}
        self.holding_weapon_vertices_bytes = {}

        for weapon_name in IN_WORLD_WEAPON_ATLAS_POSITIONS_AND_SIZES:
            atlas_pos,size = IN_WORLD_WEAPON_ATLAS_POSITIONS_AND_SIZES[weapon_name]['holding']

            self.holding_weapon_texcoords_bytes[weapon_name] = self._create_texcoords(atlas_pos,size,self.texture_atlasses['holding_weapons'])
            self.holding_weapon_vertices_bytes[weapon_name] = self._create_entity_local_vertices(size)


    def _load_entity_texcoords_and_local_vertices(self)->None:

        self.entity_texcoords_bytes = {}
        self.entity_local_vertices_bytes = {}


        for entity_type in ENTITIES_ATLAS_POSITIONS: 
            if entity_type == 'player':
                player_texture_atlas_positions = ENTITIES_ATLAS_POSITIONS[entity_type]
                for gun_holding_state in player_texture_atlas_positions:
                    for animation_state in player_texture_atlas_positions[gun_holding_state]:
                        animation = self.animation_data_collections['player'].animations[animation_state]
                        for frame in range(animation.n_textures): 
                            self.entity_texcoords_bytes[(entity_type,gun_holding_state,animation_state,frame)] = self._create_entity_texcoords(player_texture_atlas_positions[gun_holding_state][animation_state],ENTITY_SIZES[entity_type],frame)
            else: 
                pass
            
            self.entity_local_vertices_bytes[entity_type] = self._create_entity_local_vertices(ENTITY_SIZES[entity_type])


    def _create_texcoords(self,atlas_position:tuple[uint32,uint32],texture_size:tuple[uint32,uint32],texture_atlas:"Context.Texture",asbytes = True) ->bytes:

        x =  (atlas_position[0]) / texture_atlas.size[0]
        y = (atlas_position[1]) / texture_atlas.size[1]
        w = texture_size[0] / texture_atlas.size[0]
        h = texture_size[1] / texture_atlas.size[1]

        p1 = (x, y + h)
        p2 = (x + w, y + h)
        p3 = (x, y)
        p4 = (x + w, y)

        if asbytes:
            return array([p3, p4, p1,
                            p1, p4, p2], dtype=float32).tobytes()
        else: 
            return array([p3, p4, p1,
                            p1, p4, p2], dtype=float32)

    def _create_entity_texcoords(self,texture_atlas_position:tuple[uint32,uint32],texture_size:tuple[uint32,uint32],animation_frame:uint16)->bytes:


        uint32_texture_size = (uint32(self.texture_atlasses['entities'].width),uint32(self.texture_atlasses['entities'].height))

        x =  (texture_atlas_position[0] + uint32(animation_frame) * texture_size[0]) / uint32_texture_size[0]
        y = (texture_atlas_position[1]) / uint32_texture_size[1]
        w = texture_size[0] / uint32_texture_size[0]
        h = texture_size[1] / uint32_texture_size[1]

        p1 = (x, y + h)
        p2 = (x + w, y + h)
        p3 = (x, y)
        p4 = (x + w, y)

        return array([p3, p4, p1,
                        p1, p4, p2], dtype=float32).tobytes()

    def _create_entity_local_vertices(self,entity_size:tuple[uint32,uint32])->bytes:

        x = int32(entity_size[0]) // -2
        y = int32(entity_size[1]) //  2
        w = int32(entity_size[0])
        h = int32(entity_size[1])

        return array([(x, y), (x + w, y), (x, y - h),
                (x, y - h), (x + w, y), (x + w, y - h)],dtype=float32).tobytes()

        # return the local vertices for the entity type

    



    def _get_texcoords_for_tile(self,tile_info_source:TileInfoDataClass|TileInfo)->bytes:
        if isinstance(tile_info_source,DoorTileInfoWithAnimation):
            pass
        elif isinstance(tile_info_source,TrapDoorTileInfoWithOpenState):
            pass 
        else:
            if isinstance(tile_info_source,TileInfo):
                tile_info =tile_info_source 
            else: 
                tile_info = tile_info_source.info
            relative_position_index ,variant = tile_info.relative_pos_ind, tile_info.variant
            tile_type = tile_info.type

            atlas_width,atlas_height = self.texture_atlasses['tiles'].size

            x = (TILE_ATLAS_POSITIONS[tile_type][0] + variant * tile_info.tile_size[0]) / atlas_width
            y = (TILE_ATLAS_POSITIONS[tile_type][1] + relative_position_index * tile_info.tile_size[1]) / atlas_height 

            w = tile_info.tile_size[0] /atlas_width
            h = tile_info.tile_size[1] / atlas_height            

            p1 = (x, y + h) 
            p2 = (x + w, y + h) 
            p3 = (x, y) 
            p4 = (x + w, y)

            texcoords = array([p1, p2, p3,
                                p3, p2, p4], dtype=float32).tobytes()

        return texcoords


    def create_tilemap_vbos(self,tile_size:int32,non_physical_tile_layers:int32)->tuple[uint16,uint16,uint16,"Context.buffer","Context.buffer","Context.buffer","Context.buffer"]:
        padding = uint16(11)
        tiles_per_buffer_column = padding * uint16(2) + self._game_ctx['true_res'][1] // uint16(tile_size) 
        tiles_per_buffer_row = padding * uint16(2) + self._game_ctx['true_res'][0] // uint16(tile_size)

        max_visible_tiles_plus_extra = tiles_per_buffer_column * tiles_per_buffer_row

        physical_tiles_texcoords_array = zeros(max_visible_tiles_plus_extra *12 ,dtype= float32)
        physical_tiles_positions_array = zeros(max_visible_tiles_plus_extra * 2, dtype= float32)

        physical_tiles_vbo = self._gl_ctx.buffer(data=physical_tiles_texcoords_array.tobytes(),dynamic=True)
        physical_tiles_position_vbo = self._gl_ctx.buffer(data = physical_tiles_positions_array.tobytes(),dynamic= True)

        non_physical_tiles_texcoords_array = zeros(max_visible_tiles_plus_extra * non_physical_tile_layers * 12,dtype=float32)
        non_physical_tiles_positions_array = zeros(max_visible_tiles_plus_extra * non_physical_tile_layers * 2, dtype= float32)

        non_physical_tiles_vbo = self._gl_ctx.buffer(data=non_physical_tiles_texcoords_array.tobytes(),dynamic=True)
        non_physical_tiles_position_vbo = self._gl_ctx.buffer(data = non_physical_tiles_positions_array.tobytes(),dynamic= True)

        return (padding,tiles_per_buffer_row,tiles_per_buffer_column,physical_tiles_vbo,non_physical_tiles_vbo,
                physical_tiles_position_vbo,non_physical_tiles_position_vbo)



    def get_tile_colors(self,physical_tiles:"Tilemap.physical_tiles")->dict["TileColorKey","RGBA_tuple"]:

        tile_atlas_byte_data = self.texture_atlasses["tiles"].read(alignment=4)
        width,height = self.texture_atlasses["tiles"].size
        image_data = frombuffer(tile_atlas_byte_data,dtype = uint8).reshape((height,width,4))

        tile_colors = {}

        for tile_key in physical_tiles: 
            tile_data = physical_tiles[tile_key]
            tile_general_info = tile_data.info 
            relative_position_index,variant = tile_general_info.relative_pos_ind,tile_general_info.variant

            if tile_general_info.type.endswith('stairs'):
                for side in ('top','bottom','left','right'):
                    tile_color_key = (tile_general_info.type,relative_position_index,variant,side)
                    if tile_color_key not in tile_colors:
                        sample_pos_to_dim_ratio = TILE_COLOR_SAMPLE_POS_TO_DIM_RATIO['stairs']

                        texture_coords = (TILE_ATLAS_POSITIONS[tile_general_info.type][0] + variant * tile_general_info.tile_size[0] + int((tile_general_info.tile_size[0]-1) *sample_pos_to_dim_ratio[0]),\
                                                TILE_ATLAS_POSITIONS[tile_general_info.type][1] + relative_position_index* tile_general_info.tile_size[1] + int((tile_general_info.tile_size[1]-1) * sample_pos_to_dim_ratio[1]))
                        color = tuple(image_data[texture_coords[1],texture_coords[0]])
                        tile_colors[tile_color_key] = color
                  
            elif tile_general_info.type.endswith('door'):
                pass 
            else: 
                for side in ('top','bottom','left','right'):
                    sample_side_ratio = TILE_COLOR_SAMPLE_POS_TO_DIM_RATIO['regular'][side]
                    tile_color_key = (tile_general_info.type,relative_position_index,variant,side)
                    if tile_color_key not in tile_colors:
                        texture_coords = (TILE_ATLAS_POSITIONS[tile_general_info.type][0] + variant * tile_general_info.tile_size[0] + int((tile_general_info.tile_size[0]-1) *sample_side_ratio[0]),\
                                        TILE_ATLAS_POSITIONS[tile_general_info.type][1] + relative_position_index* tile_general_info.tile_size[1] + int((tile_general_info.tile_size[1]-1) * sample_side_ratio[1]))
                        color = tuple(image_data[texture_coords[1],texture_coords[0]])
                        tile_colors[tile_color_key] = color
        
        return tile_colors

    def get_tile_texcoords(self,physical_tiles:"Tilemap.physical_tiles",non_physical_tiles:"Tilemap.non_physical_tiles")->dict["TileTexcoordsKey",bytes]: 

        tile_texcoords = {}

        for key in physical_tiles:
            tile_data = physical_tiles[key]
            relative_position_index,variant = tile_data.info.relative_pos_ind, tile_data.info.variant
            tile_texcoord_key = (tile_data.info.type,relative_position_index,variant)

            if tile_texcoord_key not in tile_texcoords:
                texcoords = self._get_texcoords_for_tile(tile_data)
                """
                if isinstance(tile_data,TrapDoorTileInfoWithOpenState):
                    texcoords = self._get_texcoords_for_tile(self.texture_atlasses['tiles'],tile_general_info,tile)
                elif tile_info.type == 'building_door':
                    door_data = tile_info_list[1]


                """
                #texture_coords = self._get_texture_coords_for_tile(tile_texture_atlas,tile_info,door_data)
                tile_texcoords[tile_texcoord_key] = texcoords 

        for i,dict in enumerate(non_physical_tiles):
            for key in dict:
                tile_info = dict[key]
                relative_position_index,variant = tile_info.relative_pos_ind,tile_info.variant
                tile_texcoord_key = (tile_info.type,relative_position_index,variant)
                if  tile_texcoord_key not in tile_texcoords:
                    texcoords = self._get_texcoords_for_tile(tile_info)
                    tile_texcoords[tile_texcoord_key] = texcoords 

        return tile_texcoords 


    def get_NDC_tile_vertices(self,tile_size:int)->array:
        x = 0.
        y = 0.
        w = 2. * tile_size / self._game_ctx['true_res'][0]
        h = 2. * tile_size / self._game_ctx['true_res'][1]

        return array([(x, y), (x + w, y), (x, y - h),
                (x, y - h), (x + w, y), (x + w, y - h)],dtype=float32)
    

    def get_hud_diplay_vertices_and_texcoords(self,quads:int) -> tuple['Context.buffer','Context.buffer']:
         
        quad_vertex_size = 2 * 4 
        quad_texcoord_size = 2 * 4
        color_data_size = 4 * 4

        vertex_buffer_size  = quad_vertex_size * 6 * quads
        texcoords_buffer_size = quad_texcoord_size * 6 * quads

        bars_vertices_and_color_buffer = self._gl_ctx.buffer(reserve= 2* (quad_vertex_size * 6 + color_data_size *6), dynamic= True)
        vertex_buffer = self._gl_ctx.buffer(reserve=vertex_buffer_size,dynamic=True)
        texcoords_buffer_size = self._gl_ctx.buffer(reserve=texcoords_buffer_size,dynamic=True)

        return (bars_vertices_and_color_buffer,vertex_buffer,texcoords_buffer_size)


    def create_hud_inven_vbos(self,opaque_ui_element_quads:int,hidden_ui_element_quads:int)->tuple["Context.buffer","Context.buffer","Context.buffer","Context.buffer"]: 

        ui_element_vertex_size = 2 * 4

        opaque_ui_elements_buffer_size = ui_element_vertex_size* 6 * opaque_ui_element_quads
        hidden_ui_elements_buffer_size = ui_element_vertex_size* 6 * hidden_ui_element_quads

        opaque_vertex_buffer = self._gl_ctx.buffer(reserve=opaque_ui_elements_buffer_size,dynamic=True)
        opaque_texcoords_buffer = self._gl_ctx.buffer(reserve=opaque_ui_elements_buffer_size,dynamic=True)

        hidden_vertex_buffer = self._gl_ctx.buffer(reserve=hidden_ui_elements_buffer_size,dynamic=True)
        hidden_texcoords_buffer = self._gl_ctx.buffer(reserve=hidden_ui_elements_buffer_size,dynamic=True)

        return (opaque_vertex_buffer,opaque_texcoords_buffer,hidden_vertex_buffer,hidden_texcoords_buffer)
    

    def create_hud_item_vbos(self,opaque_item_quads:int,hidden_item_quads:int)->tuple["Context.buffer","Context.buffer","Context.buffer","Context.buffer"]:
        item_vertex_size = 2 * 4 
        
        # account for the cursor item 
        opaque_item_buffer_size = item_vertex_size * 6 * opaque_item_quads 
        hidden_item_buffer_size = item_vertex_size * 6 * hidden_item_quads

        opaque_item_vertex_buffer = self._gl_ctx.buffer(reserve=opaque_item_buffer_size,dynamic= True)
        opaque_item_texcoords_buffer =  self._gl_ctx.buffer(reserve=opaque_item_buffer_size,dynamic=True)

        hidden_item_vertex_buffer = self._gl_ctx.buffer(reserve= hidden_item_buffer_size,dynamic=True)
        hidden_item_texcoords_buffer = self._gl_ctx.buffer(reserve= hidden_item_buffer_size,dynamic=True)

        return (opaque_item_vertex_buffer,opaque_item_texcoords_buffer,hidden_item_vertex_buffer,hidden_item_texcoords_buffer)

    def get_tilemap_json(self,name:str)->any: 
        if name in self.tilemap_jsons: 
            return self.tilemap_jsons[name]
        return None 