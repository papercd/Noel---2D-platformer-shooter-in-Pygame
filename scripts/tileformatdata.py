from scripts.data import TileInfo
from typing import TYPE_CHECKING

if TYPE_CHECKING: 
    from scripts.new_tilemap import Tilemap

PHYSICS_APPLIED_TILE_TYPES = {'grass','stone','box','building_0','building_1','building_2','building_3','building_4','building_5','building_stairs','building_door','trap_door',\
                              'ladder'}

HULL_OUTER_EDGE_OFFSET = 4 
HULL_AXIS_TO_OFFSET_EVEN_POS= [ ((0,2),(1,1)),((1,2),(-1,1)),((1,3),(-1,-1)),((0,3),(1,-1))]
HULL_AXIS_TO_OFFSET_ODD_POS = [(2,1),(1,-1),(3,-1),(0,1)]
OPEN_SIDE_OFFSET_TO_AXIS_NUM = {(1,0):1,(-1,0):0,(0,1):3,(0,-1):2}
TILE_SIDE_TO_SAMPLE_POS= {
    'regular' :{
     "top": (0.5,1),
    "left": (0,0.5),
    "right": (1,0.5),
    "bottom": (0.5,0),
   
    },
    'door':
    {

    },
    'stairs': (0.5,0.3125)

    
}


TILE_NEIGHBOR_MAP = {
    "building_0" : 
    {
        0 : ((1,0),(0,1)),
        1 : ((1,0),(0,1),(-1,0)),
        2 : ((-1,0),(0,1)),
        3 : ((-1,0),(0,1),(0,-1)),
        4 : ((-1,0),(0,-1)),
        5 : ((1,0),(0,-1),(-1,0)),
        6 : ((1,0),(0,-1)),
        7 : ((1,0),(0,1),(0,-1)),
        8 : ((1,0),(-1,0),(0,1),(0,-1)),
    },

    'building_1': 
    {
        0: ((1,0),(0,1)),
        1: ((1,0),(0,1),(-1,0)),
        2: ((-1,0),(0,1)) ,
        3: ((-1,0),(0,-1),(0,1)),
        4: ((-1,0),(0,-1)),
        5: ((-1,0),(0,-1),(1,0)),
        6: ((1,0),(0,-1)),
        7: ((1,0),(0,-1),(0,1)),
        8: ((1,0),(-1,0),(0,1),(0,-1))
     },
     

    'building_2': {
        0: ((0,1)),
        1:((0,-1),(0,1)),
        2:((0,-1)),
     },
    
    'building_3' : {
        0:((1,0)),
        1:((-1,0),(1,0)),
        2:((-1,0)),
    },

    'building_4': {
        0: ((1,0),(0,1)),
        1:((-1,0),(0,1)),
        2:((0,-1),(-1,0)),
        3:((0,-1),(1,0)),
    },
 
}



def get_tile_rectangle(tile_info:TileInfo,tile_size:int,physical_tiles:"Tilemap.physical_tiles") -> tuple[int,int,int,int]:
    """
    Get the rectangle (not pygame.Rect nor Hull) for a tile.

    :param tile_info (TileInfo) -the tile information.
    :param tile_size (int) - the regular tile dimensions of the tilemap. 

    :return rectangle (tuple[int,int,int,int])

    """

    rel_pos,variant = map(int,tile_info.variant.split(';'))
    x1 = tile_info.tile_pos[0] * tile_size
    x2 = (tile_info.tile_pos[0] + 1 ) * tile_size
    y1 = tile_info.tile_pos[1] * tile_size
    y2 = (tile_info.tile_pos[1] +1 ) * tile_size

    if tile_info.type.endswith('stairs') :
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
    elif tile_info.type.endswith('door'):
        pass 
    else: 

        open_side_offsets = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        neighbor_offsets = TILE_NEIGHBOR_MAP[tile_info.type][rel_pos]

        # Create a new list with only the offsets not in neighbor_offsets
        open_side_offsets = [offset for offset in open_side_offsets if offset not in neighbor_offsets]

        axis =[x1,x2,y1,y2]
        for offset in open_side_offsets:
            if (tile_info.tile_pos[0] +offset[0],tile_info.tile_pos[1] + offset[1]) in physical_tiles:
                neightbor_tile_data = physical_tiles [ (tile_info.tile_pos[0] +offset[0],tile_info.tile_pos[1] + offset[1])]
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
