from scripts.data import BYTES_PER_TEXTURE_QUAD,BYTES_PER_POSITION_VEC2, TILE_ATLAS_POSITIONS,IRREGULAR_TILE_SIZES,TileInfo,LightInfo,DoorInfo,DoorAnimation,HULL_OUTER_EDGE_OFFSET,TILE_NEIGHBOR_MAP,OPEN_SIDE_OFFSET_TO_AXIS_NUM,\
                            LIGHT_POSITION_OFFSET_FROM_TOPLEFT,DoorTileInfoWithAnimation,TrapDoorTileInfoWithOpenState,RegularTileInfo,LightTileInfo, PHYSICS_APPLIED_TILE_TYPES

from scripts.spatial_grid import hullSpatialGrid,lightSpatialGrid 
from scripts.lists import ambientNodeList,ambientNode
from my_pygame_light2d.hull import Hull 
from pygame import Rect
from my_pygame_light2d.light import PointLight
from scripts.new_resource_manager import ResourceManager
import numpy as np
from numpy import int32, uint16,uint32,array
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pygame.math import Vector2 as vec2
    from moderngl import Context
    from scripts.data import TileColorKey,RGBA_tuple,TileInfoDataClass,TileTexcoordsKey



class Tilemap:
    def __init__(self,game_context,json_file= None):
        self._game_ctx = game_context
        self._ref_rm = ResourceManager.get_instance()
        if json_file:
            self.load_map(json_file)

    @property 
    def initial_player_position(self)->tuple[int32,int32]:
        return self._initial_player_position

    @property
    def tile_size(self)->int32: 
        return self._tile_size
    
    @property 
    def tiles_in_buffer(self)->int32:
        return self._tiles_per_screen_row * self._tiles_per_screen_col

    @property
    def physical_tiles(self)->dict[tuple[int,int],"TileInfoDataClass"]:
        return self._physical_tiles
    
    @property 
    def non_physical_tiles(self)->list[dict[tuple[int,int],"TileInfo"]]:
        return self._non_physical_tiles
    
    @property 
    def physical_tiles_texcoords_vbo(self)->"Context.buffer":
        return self._physical_tiles_texcoords_vbo

    @property 
    def non_physical_tiles_texcoords_vbo(self)->"Context.buffer":
        return self._non_physical_tiles_texcoords_vbo
    
    @property 
    def physical_tiles_position_vbo(self)->"Context.buffer":
        return self._physical_tiles_position_vbo
    
    @property 
    def non_physical_tiles_position_vbo(self)->"Context.buffer":
        return self._non_physical_tiles_position_vbo
       
    def load_map(self,json_file):

        self._tile_size:int32 = int32(json_file['tile_size'])
        self._non_physical_tile_layers:int32= int32(json_file['offgrid_layers'])
        self._non_physical_tiles:list[dict[tuple[int,int],"TileInfo"]] = [{} for i in range(0,self._non_physical_tile_layers)]
        self._physical_tiles:dict[tuple[int32,int32],"TileInfoDataClass"] = {}
        self._ref_ambient_node:ambientNode = None


        self.hull_grid  = hullSpatialGrid(cell_size= self._tile_size)        
        self.lights_grid = lightSpatialGrid(cell_size= self._tile_size)
    
        self.ambientNodes = ambientNodeList()
        self.tile_colors:dict["TileColorKey","RGBA_tuple"]= {}
        self.tile_texcoords_bytes : dict["TileTexcoordsKey",bytes] = {}


        # the player position is also quried from the json file. 
        self._initial_player_position = (int32(600),int32(32))


        for tile_key in json_file['tilemap']: 
            tile_size = (self._tile_size,self._tile_size) if json_file['tilemap'][tile_key]['type'] \
                                    not in IRREGULAR_TILE_SIZES else IRREGULAR_TILE_SIZES[json_file['tilemap'][tile_key]['type']]

            atl_pos = TILE_ATLAS_POSITIONS[json_file['tilemap'][tile_key]['type']]
            tile_pos = (int32(json_file['tilemap'][tile_key]["pos"][0]),
                        int32(json_file['tilemap'][tile_key]["pos"][1]))

            relative_position_index,variant = map(uint16,json_file['tilemap'][tile_key]['variant'].split(';'))

            if json_file['tilemap'][tile_key]['type'] != "lights":
                if json_file['tilemap'][tile_key]['type'].endswith('door'):
                    if json_file['tilemap'][tile_key]['type'].split('_')[0] == 'trap':
                        # Tile info creation for trap door 

                        rect = Rect(tile_pos[0] * self._tile_size, tile_pos[1] * self._tile_size, self._tile_size,int32(5))

                        # ONCE YOU HAVE TRAP DOORS, CHECK ON THIS 
                        self._physical_tiles[tile_pos] = TrapDoorTileInfoWithOpenState(
                                                            info = DoorInfo((json_file['tilemap'][tile_key]["type"],relative_position_index,variant,\
                                                                 tile_pos,tile_size,rect,atl_pos)),
                                                            open= False
                                                         )
                    else: 
                        # ONCE YOU HAVE NORMAL DOORS, CHECK ON THIS 
                        if tile_key in self._physical_tiles: continue 
                        else: 
                            rect = Rect(tile_pos[0] * self._tile_size + 3, tile_pos[1] * self._tile_size ,6,32)

                            door = DoorTileInfoWithAnimation(
                                info = DoorInfo(json_file['tilemap'][tile_key]["type"],relative_position_index,variant,\
                                tile_pos,tile_size,rect,atl_pos),
                                animation= DoorAnimation(5,5)
                            )

                            self._physical_tiles[tile_pos] = door 

                            pos_below = (tile_pos[0],tile_pos[1] +1)
                            self._physical_tiles[pos_below]  = door 

                else:   
                    #hull = self._create_hulls(json_file['tilemap'][tile_key])
                    # TODO: THE TILE KEYS NEED TO BE CHANGED TO INTS, NOT STRINGS. 

                    self._physical_tiles[tile_pos] = RegularTileInfo(
                                                        info =TileInfo(json_file['tilemap'][tile_key]["type"],relative_position_index,variant,
                                                        tile_pos,tile_size,atl_pos) 
                                                    )

            
            else: 
                if isinstance(json_file['tilemap'][tile_key]["pos"][0],int):
                    # for lights that are on the tile grid 
                    #TODO: ADD LIGHTING LATER 
                    
                    light = PointLight(position = (json_file['tilemap'][tile_key]["pos"][0]*self._tile_size+LIGHT_POSITION_OFFSET_FROM_TOPLEFT[0],
                                                   json_file['tilemap'][tile_key]["pos"][1]*self._tile_size+LIGHT_POSITION_OFFSET_FROM_TOPLEFT[1]),\
                                         power= json_file['tilemap'][tile_key]["power"],radius = json_file['tilemap'][tile_key]["radius"] )
                    light.set_color(*json_file['tilemap'][tile_key]["colorValue"])
                    self.lights_grid.insert(light)
   
                else: 
                    # for lights that are not placed on the tile grid  
                    # TODO : ADD LIGHTING LATER
                  
                    light = PointLight(position = (json_file['tilemap'][tile_key]["pos"][0]+LIGHT_POSITION_OFFSET_FROM_TOPLEFT[0],
                                                   json_file['tilemap'][tile_key]["pos"][1]+LIGHT_POSITION_OFFSET_FROM_TOPLEFT[1]),\
                                         power= json_file['tilemap'][tile_key]["power"],radius = json_file['tilemap'][tile_key]["radius"] )
                    light.set_color(*json_file['tilemap'][tile_key]["colorValue"])
                    self.lights_grid.insert(light)
        
                    
                rect = Rect(tile_pos[0] * self._tile_size +3, tile_pos[1] * self._tile_size, 10,6)

                self._physical_tiles[tile_pos] = LightTileInfo(
                                                   info = LightInfo(json_file['tilemap'][tile_key]["type"],relative_position_index,variant,\
                                                 tile_pos,tile_size,rect,json_file['tilemap'][tile_key]["radius"], json_file['tilemap'][tile_key]["power"],
                                                 json_file['tilemap'][tile_key]["colorValue"],atl_pos) ,
                                                 refPointLight= light
                                                )
        
        for i in range(0,self._non_physical_tile_layers):
            tilemap_key = f"offgrid_{i}"
            for tile_key in json_file[tilemap_key]:
                tile_pos = (int32(json_file[tilemap_key][tile_key]["pos"][0]),
                            int32(json_file[tilemap_key][tile_key]["pos"][1]))
                atl_pos = TILE_ATLAS_POSITIONS[json_file[tilemap_key][tile_key]["type"]]
                tile_size = (self._tile_size,self._tile_size) if json_file[tilemap_key][tile_key]['type'] \
                                    not in IRREGULAR_TILE_SIZES else IRREGULAR_TILE_SIZES[json_file[tilemap_key][tile_key]['type']]
                relative_position_index,variant = map(uint16,json_file[tilemap_key][tile_key]['variant'].split(';'))
                if json_file[tilemap_key][tile_key]["type"] == "lights":
                    pass 
                    """
                    
                    if isinstance(json_file['offgrid_'+ str(i)][tile_key]["pos"][0],int):
                        light = PointLight(position = (json_file['offgrid_'+ str(i)][tile_key]["pos"][0]*self._regular_tile_size+7,json_file['offgrid_'+ str(i)][tile_key]["pos"][1]*self._regular_tile_size+3),\
                                         power= json_file['offgrid_'+ str(i)][tile_key]["power"],radius = json_file['offgrid_'+ str(i)][tile_key]["radius"] )
                        light.set_color(*json_file['offgrid_' + str(i)][tile_key]["colorValue"])
                        lights.append(light)
                        self.offgrid_tiles[i][tile_key] = Light(json_file['offgrid_'+str(i)][tile_key]["type"],json_file['offgrid_'+str(i)][tile_key]["variant"],json_file['offgrid_'+str(i)][tile_key]["pos"],\
                                                                radius = json_file['offgrid_'+str(i)][tile_key]['radius'],power = json_file['offgrid_'+str(i)][tile_key]['power'],color_value=json_file['offgrid_'+str(i)][tile_key]['colorValue'] )
                    else: 
                        light = PointLight(position = (json_file['offgrid_'+ str(i)][tile_key]["pos"][0]+7,json_file['offgrid_'+ str(i)][tile_key]["pos"][1]+3),\
                                         power= json_file['offgrid_'+ str(i)][tile_key]["power"],radius = json_file['offgrid_'+ str(i)][tile_key]["radius"] )
                        light.set_color(*json_file['offgrid_' + str(i)][tile_key]["colorValue"])
                        lights.append(light)
                        self.offgrid_tiles[i][tile_key] = Light(json_file['offgrid_'+str(i)][tile_key]["type"],json_file['offgrid_'+str(i)][tile_key]["variant"],(json_file['offgrid_'+str(i)][tile_key]["pos"][0] // self._regular_tile_size,json_file['offgrid_'+str(i)][tile_key]["pos"][1] // self._regular_tile_size),\
                                                            radius = json_file['offgrid_'+str(i)][tile_key]['radius'],power = json_file['offgrid_'+str(i)][tile_key]['power'],color_value=json_file['offgrid_'+str(i)][tile_key]['colorValue'] )
                    """
                else: 
                    self._non_physical_tiles[i][tile_pos] = TileInfo(json_file[tilemap_key][tile_key]["type"],relative_position_index,variant,
                                                            tile_pos,tile_size,atl_pos)
        
        for node_data in json_file['ambient_nodes']:
            if len(node_data.items()) == 4:
                self.ambientNodes.insert_interpolated_ambient_node(node_data["range"],node_data['hull_range'],node_data["leftColorValue"],node_data["rightColorValue"])
            else: 
                self.ambientNodes.insert_ambient_node(node_data["range"],node_data['hull_range'],node_data["colorValue"])
        

        self._create_hulls()
        for hull in self._hulls:
            self.hull_grid.insert(hull)
        

        self._tilemap_buffer_padding,self._tiles_per_screen_row,self._tiles_per_screen_col,self._physical_tiles_texcoords_vbo, self._non_physical_tiles_texcoords_vbo, self._physical_tiles_position_vbo,self._non_physical_tiles_position_vbo\
        = self._ref_rm.create_tilemap_vbos(self._tile_size,self._non_physical_tile_layers)

        self.null_texcoords_bytes = np.zeros(12,dtype = np.float32).tobytes()
        self.null_positions_bytes = np.zeros(2,dtype= np.float32).tobytes()


        self.NDC_tile_vertices_array = self._ref_rm.get_NDC_tile_vertices(self._tile_size)
        self.tile_colors = self._ref_rm.get_tile_colors(self._physical_tiles)
        self.tile_texcoords_bytes = self._ref_rm.get_tile_texcoords(self._physical_tiles,self._non_physical_tiles)

        self.load_initial_tilemap_buffers()


    def load_initial_tilemap_buffers(self)->None: 

        # x, y 
        self._physical_tiles_texcoords_write_offset_ind = array([0,0],dtype = int32)
        self._physical_tiles_positions_write_offset_ind = array([0,0],dtype = int32)

        self._current_grid_topleft = array([ (self._initial_player_position[0] + int32(self._game_ctx['true_res'][0]) // int32(2)) // int32(16) - int32(self._tilemap_buffer_padding),
                                             (self._initial_player_position[1] + int32(self._game_ctx['true_res'][1]) // int32(2)) // int32(16) - int32(self._tilemap_buffer_padding)])

        #self._current_grid_topleft = [int((self._initial_player_position[0] - self._game_ctx['true_res'][0] / 2) / 16) - self._tilemap_buffer_padding,
        #                            int((self._initial_player_position[1] - self._game_ctx['true_res'][1] / 2) / 16) - self._tilemap_buffer_padding]

        texcoords_buffer_write_offset = 0
        positions_buffer_write_offset = 0

        for grid_x_offset in range(0,self._tiles_per_screen_row):
            for grid_y_offset in range(0,self._tiles_per_screen_col):
                coor = (self._current_grid_topleft[0] + grid_x_offset, self._current_grid_topleft[1] + grid_y_offset)

                if coor in self.physical_tiles:
                    tile_data = self.physical_tiles[coor]
                    tile_general_info = tile_data.info

                    type,relative_position_index,variant = tile_general_info.type,tile_general_info.relative_pos_ind, tile_general_info.variant

                    self.physical_tiles_texcoords_vbo.write(self.tile_texcoords_bytes[(type,relative_position_index,variant)],offset = texcoords_buffer_write_offset)
                    self.physical_tiles_position_vbo.write(self.tile_pos_to_ndc_bytes(coor),offset = positions_buffer_write_offset)
                else: 
                    self.physical_tiles_texcoords_vbo.write(self.null_texcoords_bytes,offset = texcoords_buffer_write_offset)
                    self.physical_tiles_position_vbo.write(self.null_positions_bytes,offset = positions_buffer_write_offset)

                """
                for non_physical_tile_layer in self.non_physical_tiles:
                    if coor in non_physical_tile_layer:
                        tile_info = non_physical_tile_layer[coor]
                """

                texcoords_buffer_write_offset += BYTES_PER_TEXTURE_QUAD
                positions_buffer_write_offset += BYTES_PER_POSITION_VEC2
        
    # TODO: when rendering optimization is done, creation of tile vertices need to be precomputed.   
    def tile_pos_to_ndc_bytes(self,tile_grid_pos:tuple[int32,int32])->bytes: 
        return np.array([2. * (tile_grid_pos[0] *self._tile_size) / self._game_ctx['true_res'][0]-1.
                , 1. - 2. * (tile_grid_pos[1] * self.tile_size) / self._game_ctx['true_res'][1]],dtype=np.float32).tobytes()

    def _sign(self,x:int32)->int32: 
        return (x >> 30) | (x != 0)
    
    def update_tilemap_vbos(self, player_position: "vec2") -> None:

        new_grid_topleft = (
            (player_position[0] - int32(self._game_ctx['true_res'][0] >> 1)) // int32(16) - self._tilemap_buffer_padding,
            (player_position[1] - int32(self._game_ctx['true_res'][1] >> 1)) // int32(16) - self._tilemap_buffer_padding
        )


        signs = (
            self._sign(new_grid_topleft[0] - self._current_grid_topleft[0]),
            self._sign(new_grid_topleft[1] - self._current_grid_topleft[1])
        )


        if signs[0] == int32(0) and signs[1] == int32(0):
            return  # No movement, no updates needed

        # Update X direction
        while self._current_grid_topleft[0] != new_grid_topleft[0]:
            self._current_grid_topleft[0] += signs[0]
            self._update_tilemap_vbos_x(signs[0])

        # Update Y direction
        while self._current_grid_topleft[1] != new_grid_topleft[1]:
            self._current_grid_topleft[1] += signs[1]
            self._update_tilemap_vbos_y(signs[1])

    def _write_tile_to_vbo(self,coor:tuple[int32,int32],texcoords_write_offset:int, position_write_offset:int)->None:

        if coor in self.physical_tiles: 
            tile_data = self.physical_tiles[coor]
            tile_general_info = tile_data.info
            relative_pos_ind,variant = tile_general_info.relative_pos_ind,tile_general_info.variant
            texcoords_bytes = self.tile_texcoords_bytes[(tile_general_info.type,relative_pos_ind,variant)]
            position_bytes = self.tile_pos_to_ndc_bytes(coor)
        else: 
            texcoords_bytes = self.null_texcoords_bytes
            position_bytes = self.null_positions_bytes

        self.physical_tiles_texcoords_vbo.write(texcoords_bytes,offset = texcoords_write_offset )
        self.physical_tiles_position_vbo.write(position_bytes,offset = position_write_offset)


    def _update_tilemap_vbos_x(self,direction:int32)->None: 

        in_column_tile_texcoords_write_offset = 0 
        in_column_tile_position_write_offset = 0
        
        texcoords_write_offset_from_y = self._physical_tiles_texcoords_write_offset_ind[1] * BYTES_PER_TEXTURE_QUAD
        positions_write_offset_from_y = self._physical_tiles_positions_write_offset_ind[1] * BYTES_PER_POSITION_VEC2

        if direction == 1: 
            for new_column_grid_y_offset in range(0,self._tiles_per_screen_col):
                coor = (self._current_grid_topleft[0]-1 + self._tiles_per_screen_row ,self._current_grid_topleft[1] + new_column_grid_y_offset)

                # calculate the write offsets 
                col_wrap_around_texcoords_write_offset = (texcoords_write_offset_from_y + in_column_tile_texcoords_write_offset) % (self._tiles_per_screen_col * BYTES_PER_TEXTURE_QUAD)
                final_texcoords_write_offset = col_wrap_around_texcoords_write_offset + self._physical_tiles_texcoords_write_offset_ind[0] * self._tiles_per_screen_col * BYTES_PER_TEXTURE_QUAD

                col_wrap_around_positions_write_offset = (positions_write_offset_from_y + in_column_tile_position_write_offset) % (self._tiles_per_screen_col * BYTES_PER_POSITION_VEC2)
                final_positions_write_offset = col_wrap_around_positions_write_offset + self._physical_tiles_positions_write_offset_ind[0] * self._tiles_per_screen_col * BYTES_PER_POSITION_VEC2

                self._write_tile_to_vbo(coor,final_texcoords_write_offset,final_positions_write_offset)

                in_column_tile_texcoords_write_offset += BYTES_PER_TEXTURE_QUAD
                in_column_tile_position_write_offset +=  BYTES_PER_POSITION_VEC2  
            
            self._physical_tiles_texcoords_write_offset_ind[0] = (self._physical_tiles_texcoords_write_offset_ind[0]+1) % self._tiles_per_screen_row
            self._physical_tiles_positions_write_offset_ind[0] = (self._physical_tiles_positions_write_offset_ind[0]+1) % self._tiles_per_screen_row

        else: 
            self._physical_tiles_texcoords_write_offset_ind[0] = (self._physical_tiles_texcoords_write_offset_ind[0]-1) % self._tiles_per_screen_row
            self._physical_tiles_positions_write_offset_ind[0] = (self._physical_tiles_positions_write_offset_ind[0]-1) % self._tiles_per_screen_row

            for new_column_grid_y_offset in range(0,self._tiles_per_screen_col):
                coor = (self._current_grid_topleft[0],self._current_grid_topleft[1] + new_column_grid_y_offset)

                col_wrap_around_texcoords_write_offset = (texcoords_write_offset_from_y + in_column_tile_texcoords_write_offset) % (self._tiles_per_screen_col * BYTES_PER_TEXTURE_QUAD)
                final_texcoords_write_offset = col_wrap_around_texcoords_write_offset + self._physical_tiles_texcoords_write_offset_ind[0] * self._tiles_per_screen_col * BYTES_PER_TEXTURE_QUAD

                col_wrap_around_positions_write_offset = (positions_write_offset_from_y + in_column_tile_position_write_offset) % (self._tiles_per_screen_col * BYTES_PER_POSITION_VEC2)
                final_positions_write_offset = col_wrap_around_positions_write_offset + self._physical_tiles_positions_write_offset_ind[0] * self._tiles_per_screen_col * BYTES_PER_POSITION_VEC2

                self._write_tile_to_vbo(coor,final_texcoords_write_offset,final_positions_write_offset)
                
                in_column_tile_texcoords_write_offset +=  BYTES_PER_TEXTURE_QUAD 
                in_column_tile_position_write_offset +=  BYTES_PER_POSITION_VEC2 
            


    def _update_tilemap_vbos_y(self,direction:int32)->None: 
        
        in_row_tile_texcoords_write_offset = 0 
        in_row_tile_position_write_offset = 0

        texcoords_write_offset_from_x = self._physical_tiles_texcoords_write_offset_ind[0] * self._tiles_per_screen_col * BYTES_PER_TEXTURE_QUAD
        positions_write_offset_from_x = self._physical_tiles_positions_write_offset_ind[0] * self._tiles_per_screen_col * BYTES_PER_POSITION_VEC2

        if direction == 1: 
            for new_row_grid_x_offset in range(0,self._tiles_per_screen_row):
                coor = (self._current_grid_topleft[0] + new_row_grid_x_offset,self._current_grid_topleft[1] -1 + self._tiles_per_screen_col)    

                # calculate the write offset 

                row_wrap_texcoords_write_offset = (texcoords_write_offset_from_x + in_row_tile_texcoords_write_offset) % self._physical_tiles_texcoords_vbo.size
                row_wrap_positions_write_offset = (positions_write_offset_from_x + in_row_tile_position_write_offset) % self._physical_tiles_position_vbo.size 

                final_texcoords_write_offset = row_wrap_texcoords_write_offset + self._physical_tiles_texcoords_write_offset_ind[1] * BYTES_PER_TEXTURE_QUAD 
                final_positions_write_offset = row_wrap_positions_write_offset + self._physical_tiles_positions_write_offset_ind[1] * BYTES_PER_POSITION_VEC2

                self._write_tile_to_vbo(coor,final_texcoords_write_offset,final_positions_write_offset)

                in_row_tile_texcoords_write_offset +=  self._tiles_per_screen_col * BYTES_PER_TEXTURE_QUAD 
                in_row_tile_position_write_offset +=  self._tiles_per_screen_col * BYTES_PER_POSITION_VEC2

            self._physical_tiles_texcoords_write_offset_ind[1] = (self._physical_tiles_texcoords_write_offset_ind[1] + 1) % self._tiles_per_screen_col
            self._physical_tiles_positions_write_offset_ind[1] = (self._physical_tiles_positions_write_offset_ind[1] + 1) % self._tiles_per_screen_col 

        else: 
            self._physical_tiles_texcoords_write_offset_ind[1] = (self._physical_tiles_texcoords_write_offset_ind[1] - 1) % self._tiles_per_screen_col
            self._physical_tiles_positions_write_offset_ind[1] = (self._physical_tiles_positions_write_offset_ind[1] - 1) % self._tiles_per_screen_col 

            for new_row_grid_x_offset in range(0,self._tiles_per_screen_row):
                coor = (self._current_grid_topleft[0] + new_row_grid_x_offset,self._current_grid_topleft[1])    

                row_wrap_texcoords_write_offset = (texcoords_write_offset_from_x + in_row_tile_texcoords_write_offset) % self._physical_tiles_texcoords_vbo.size
                row_wrap_positions_write_offset = (positions_write_offset_from_x + in_row_tile_position_write_offset) % self._physical_tiles_position_vbo.size 

                final_texcoords_write_offset = row_wrap_texcoords_write_offset + self._physical_tiles_texcoords_write_offset_ind[1] * BYTES_PER_TEXTURE_QUAD 
                final_positions_write_offset = row_wrap_positions_write_offset + self._physical_tiles_positions_write_offset_ind[1] * BYTES_PER_POSITION_VEC2

                self._write_tile_to_vbo(coor,final_texcoords_write_offset,final_positions_write_offset)

                in_row_tile_texcoords_write_offset +=  self._tiles_per_screen_col * BYTES_PER_TEXTURE_QUAD  
                in_row_tile_position_write_offset += self._tiles_per_screen_col * BYTES_PER_POSITION_VEC2 



    def update_ambient_node_ref(self,pos:tuple[int,int],callback:"function",camera_offset:tuple[int,int],
                                screen_shake:tuple[int,int])->None:
        
        if self._ref_ambient_node is None: 
            
            self._ref_ambient_node = self.ambientNodes.get_node_at_pos(pos[0])
        else:
            if pos[0] < self._ref_ambient_node.range[0]:
                if self._ref_ambient_node.prev: 
                    self._ref_ambient_node = self._ref_ambient_node.prev
                    callback(camera_offset,screen_shake,pos)
                  
            elif pos[0] > self._ref_ambient_node.range[1]:
                if self._ref_ambient_node.next: 
                    self._ref_ambient_node = self._ref_ambient_node.next
                    callback(camera_offset,screen_shake,pos)

    


    def _create_rectangles(self,tile_general_info: TileInfo) -> tuple[int,int,int,int]:

        rel_pos,variant = tile_general_info.relative_pos_ind,tile_general_info.variant
        tile_size = self._tile_size

        x1 = tile_general_info.tile_pos[0] * tile_size
        x2 = (tile_general_info.tile_pos[0] + 1 ) * tile_size
        y1 = tile_general_info.tile_pos[1] * tile_size
        y2 = (tile_general_info.tile_pos[1] +1 ) * tile_size

        if tile_general_info.type.endswith('stairs') :
            if rel_pos == 0:
                return  [
                    (x1+2,y2-2,x2,y2),
                    (x1+6,y2-6,x2,y2-2),
                    (x2-5,y1+5,x2,y1+10)
                ]
            elif rel_pos == 1:
                return  [
                    (x1,y2-2,x2-2,y2),
                    (x1,y2-6,x2-6,y2-2),
                    (x1,y1+5,x1+5,y1+10)
                ]
            else:
                if variant == 0:
                    return [(x1,y1,x2,y2)]
                else: 
                    return [(x1,y1+HULL_OUTER_EDGE_OFFSET,x2,y2)]
        elif tile_general_info.type.endswith('door'):
            pass 
        else: 

            open_side_offsets = [(1, 0), (-1, 0), (0, 1), (0, -1)]
            neighbor_offsets = TILE_NEIGHBOR_MAP[tile_general_info.type][rel_pos]

            # Create a new list with only the offsets not in neighbor_offsets
            open_side_offsets = [offset for offset in open_side_offsets if offset not in neighbor_offsets]

            axis =[x1,x2,y1,y2]
            for offset in open_side_offsets:
                if (tile_general_info.tile_pos[0] +offset[0],tile_general_info.tile_pos[1] + offset[1]) in self._physical_tiles:
                    neightbor_tile_data = self._physical_tiles[ (tile_general_info.tile_pos[0] +offset[0],tile_general_info.tile_pos[1] + offset[1])]
                    neighbor_tile_general_info = neightbor_tile_data.info
                    if neighbor_tile_general_info.type == 'lights' or neighbor_tile_general_info.type.endswith('stairs'):
                        axis_ind = OPEN_SIDE_OFFSET_TO_AXIS_NUM[offset]
                        dir = -offset[0] if offset[1] == 0 else -offset[1]
                        axis[axis_ind] += dir * HULL_OUTER_EDGE_OFFSET

                    
                else: 
                    axis_ind = OPEN_SIDE_OFFSET_TO_AXIS_NUM[offset]
                    dir = -offset[0] if offset[1] == 0 else -offset[1]
                    axis[axis_ind] += dir * HULL_OUTER_EDGE_OFFSET

            return [(axis[0],axis[2],axis[1],axis[3])]


    def _create_hulls(self)->None:
        """
        Merges rectangles in a dictionary where only rectangles of type "regular" are merged.
        
        :param rect_dict: Dictionary with keys as top-left grid-aligned positions (x, y) and 
                        values as (width, height, type).
        :param tile_size: Dimension of a grid square (default is 16).
        :return: List of merged rectangles [(x1, y1, x2, y2)].
        """
        # Convert rect_dict into a list of rectangles with positions
        self._rectangles = []

        for pos, tile_data in sorted(self._physical_tiles.items()):
            tile_general_info = tile_data.info
            if tile_general_info.type != 'spawners' and tile_general_info.type != 'lights':
                self._rectangles.extend(self._create_rectangles(tile_general_info))

        # extend rectangle sides for tiles with neighbors
        

        merged = True
        while merged:
            merged = False
            new_rectangles = []
            skip = set()

            for i, rect1 in enumerate(self._rectangles):
                if i in skip:
                    continue
                x1, y1, x2, y2 = rect1
                merged_with_other = False

                for j, rect2 in enumerate(self._rectangles):
                    if i == j or j in skip:
                        continue

                    a1, b1, a2, b2 = rect2

                    # Check if rectangles are touching and aligned
                    if (y1 == b1 and y2 == b2 and (x1 == a2 or x2 == a1)):  # Horizontal touch
                        # Merge horizontally
                        new_rectangles.append((min(x1, a1), y1, max(x2, a2), y2))
                        skip.add(i)
                        skip.add(j)
                        merged_with_other = True
                        merged = True
                        break
                    # check if rectangles are horizontally next to each other, and extend axis if needed 
                    elif (x1 == a1 and x2 == a2 and (y1 == b2 or y2 == b1)):  # Vertical touch
                        # Merge vertically
                        new_rectangles.append((x1, min(y1, b1), x2, max(y2, b2)))
                        skip.add(i)
                        skip.add(j)
                        merged_with_other = True
                        merged = True
                        break
                    elif (): 
                        pass 

                if not merged_with_other:
                    new_rectangles.append(rect1)

            # Update rectangles with the newly merged ones
            self._rectangles = new_rectangles

        # hull vertices order: topleft, topright, bottomright, bottomleft

        self._hulls = [] 

         
        for rectangle in self._rectangles:
            x1, y1, x2, y2 = rectangle
            self._hulls.append(Hull( vertices=[(x1, y1), (x2, y1), (x2, y2), (x1, y2)]))
            

    def tiles_around(self, pos:tuple[int32,int32], size:tuple[uint32,uint32], dir: bool = False) -> list["TileInfoDataClass"]:
        tiles = []

        # Calculate the tile coordinates of the center position
        tile_center = (pos[0] // self._tile_size, pos[1] // self._tile_size)

        # Calculate the boundary coordinates of the surrounding tiles
        x_start = tile_center[0] - int32(1)
        x_end = tile_center[0] + int32(int32(size[0]) // self._tile_size) + int32(1)
        y_start = tile_center[1] - int32(1)
        y_end = tile_center[1] + int(int32(size[1]) // self._tile_size) + int32(1)

        # Determine the x iteration order based on the 'dir' flag
        x_range = range(x_start, x_end + 1) if dir else range(x_end, x_start - 1, -1)

        # Iterate through the surrounding tiles and check if they exist in the tilemap
        for x in x_range:
            for y in range(y_start, y_end + 1):
                tile_key = (x, y)

                if tile_key in self._physical_tiles:
                    tile_general_info = self._physical_tiles[tile_key].info

                    if isinstance(tile_general_info, DoorTileInfoWithAnimation):
                        pass
                    elif isinstance(tile_general_info, TrapDoorTileInfoWithOpenState):
                        pass
                    elif isinstance(tile_general_info, LightInfo):
                        pass
                    else:
                        tiles.append(self._physical_tiles[tile_key])

        return tiles


    def get_at(self,check_pos,side):
        coor =(check_pos[0] // self._tile_size , check_pos[1] //self._tile_size)       
        tile_info_list = self._physical_tiles[coor]
        tile_info = tile_info_list[0] 
        rel_pos,variant = tile_info.relative_pos_ind,tile_info.variant
        return self._tile_colors[(tile_info.type,rel_pos,variant,side)]


    
    def solid_check(self,check_pos) -> bool:
        coor =(check_pos[0]//self._tile_size,check_pos[1]//self._tile_size)
        return coor  in self._physical_tiles\
                and self._physical_tiles[coor][0].type in PHYSICS_APPLIED_TILE_TYPES

    def query_rect_tile_pair_around_ent(self,pos:tuple[int32,int32],size:tuple[uint32,uint32],dir:bool = False)->list[tuple[Rect,"TileInfoDataClass"]]:
        surrounding_rects = []
        tiles_around = self.tiles_around(pos,size,dir)
        
        for tile_data in tiles_around:
            if tile_data.info.type in PHYSICS_APPLIED_TILE_TYPES: 
                if tile_data.info.type.endswith('door'):
                    #TODO: add this when you have doors. 
                    pass 
                else: 
                    rect = (
                        tile_data.info.tile_pos[0] * self._tile_size,       # left
                        tile_data.info.tile_pos[1] * self._tile_size,       # top
                        self._tile_size,                                    # width
                        self._tile_size                                     # height
                    )
                
                    surrounding_rects.append((Rect(*rect),tile_data))

            else: 
                # TODO: add this when you have non physical tiles. 
                pass 
        return surrounding_rects

    def write_to_physical_tiles_texcoords_vbo(self,buffer_data:bytes|bytearray)->None: 
        self._physical_tiles_texcoords_vbo.write(buffer_data)


    def write_to_physical_tiles_positions_vbo(self,buffer_data:bytes|bytearray)->None: 
        self._physical_tiles_position_vbo.write(buffer_data)



    def write_to_non_physical_tiles_texcoords_vbo(self,buffer_data:bytes|bytearray)->None: 
        self._non_physical_tiles_texcoords_vbo.write(buffer_data)


    def write_to_non_physical_tiles_positions_vbo(self,buffer_data:bytes|bytearray)->None: 
        self._non_physical_tiles_position_vbo.write(buffer_data)


