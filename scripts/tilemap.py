
import json 
import random 
import pygame
import heapq

PHYSICS_APPLIED_TILE_TYPES = {'grass','stone','box','building_0','building_1','building_2','building_3','building_4','building_5','stairs'}
AUTOTILE_TYPES = {'grass','stone','building_0','building_1','building_2','building_3','building_4'}
SMOOTH_TRANS_TILES = {'building_0'}
BULLET_TILE_OFFSET = [(1,0),(1,-1),(0,-1),(-1,-1),(-1,0),(-1,1),(0,1),(1,1)]
SURROUNDING_TILE_OFFSET = [(1,0),(1,-1),(0,-1),(0,0),(-1,-1),(-1,0),(-1,1),(0,1),(1,1)]


#variant rules that we expect to see depending on what side of the tile is empty. 

AUTOTILE_MAP ={
    tuple(sorted([(1,0),(0,1)])) : 0,
    tuple(sorted([(1,0),(0,1),(-1,0)])) : 1,
    tuple(sorted([(-1,0),(0,1)])) : 2,
    tuple(sorted([(-1,0),(0,-1),(0,1)])) :3,
    tuple(sorted([(-1,0),(0,-1)])) : 4,
    tuple(sorted([(-1,0),(0,-1),(1,0)])) :5,
    tuple(sorted([(1,0),(0,-1)])) :6,
    tuple(sorted([(1,0),(0,-1),(0,1)])) :7,
    tuple(sorted([(1,0),(-1,0),(0,1),(0,-1)])) :8
}

BUILDING_AUTOTILE ={

    '0': { tuple(sorted([(1,0),(0,1)])) : 0,
    tuple(sorted([(1,0),(0,1),(-1,0)])) : 1,
    tuple(sorted([(-1,0),(0,1)])) : 2,
    tuple(sorted([(-1,0),(0,-1),(0,1)])) :3,
    tuple(sorted([(-1,0),(0,-1)])) : 4,
    tuple(sorted([(-1,0),(0,-1),(1,0)])) :5,
    tuple(sorted([(1,0),(0,-1)])) :6,
    tuple(sorted([(1,0),(0,-1),(0,1)])) :7,
    tuple(sorted([(1,0),(-1,0),(0,1),(0,-1)])) :8
     },

    '1': {
         tuple(sorted([(1,0),(0,1)])) : 0,
    tuple(sorted([(1,0),(0,1),(-1,0)])) : 1,
    tuple(sorted([(-1,0),(0,1)])) : 2,
    tuple(sorted([(-1,0),(0,-1),(0,1)])) :3,
    tuple(sorted([(-1,0),(0,-1)])) : 4,
    tuple(sorted([(-1,0),(0,-1),(1,0)])) :5,
    tuple(sorted([(1,0),(0,-1)])) :6,
    tuple(sorted([(1,0),(0,-1),(0,1)])) :7,
    tuple(sorted([(1,0),(-1,0),(0,1),(0,-1)])) :8
     },
     

    '2': {
         
    tuple([(0,1)]) : 0,
    tuple(sorted([(0,-1),(0,1)])) : 1,
    tuple([(0,-1)]) : 2,
     },
    
    '3' : {
    tuple([(1,0)]) : 0,
    tuple(sorted([(-1,0),(1,0)])) : 1,
    tuple([(-1,0)]) : 2,
    },

    '4': {
         tuple(sorted([(1,0),(0,1)])) : 0,
    tuple(sorted([(-1,0),(0,1)])) : 1,
    tuple(sorted([(0,-1),(-1,0)])) : 2,
    tuple(sorted([(0,-1),(1,0)])) :3,
    }
    
}


class Tilemap: 
    def __init__(self,game,tile_size = 16, offgrid_layers = 1):
        self.tile_size = tile_size
        self.game = game
        
        #self.enemies = []
        #self.bullets = []

        self.tilemap = {}
        self.grass = {}
       
        self.offgrid_layers = offgrid_layers
        self.offgrid_tiles = [{} for i in range(0,offgrid_layers)]
        
       
        
        self.decorations = []
        self.path_graph = {}


    def json_seriable(self):
        seriable_tilemap = {}
        for key in self.tilemap: 
            tile = self.tilemap[key]
            seriable_tilemap[str(tile.pos[0]) +';' + str(tile.pos[1])] = {'type': tile.type,'variant' : tile.variant, 'pos' : tile.pos}
        
   
        seriable_decor = []
        for tile in self.decorations:
            seriable_decor.append({'type': tile.type,'variant' : tile.variant, 'pos' : tile.pos})

        seriable_grass = {}
        for key in self.grass: 
            grass = self.grass[key]
            seriable_grass[str(grass.pos[0]) +';' + str(grass.pos[1])] = {'type': grass.type,'variant' : grass.variant, 'pos' : grass.pos}

        
        seriable_offgrid = [{} for i in range(0,self.offgrid_layers)] 
        
        for i,dict in  enumerate(self.offgrid_tiles):
            for key in dict: 
                tile = dict[key] 
                seriable_offgrid[i][str(tile.pos[0]) + ';' + str(tile.pos[1])] = {'type': tile.type , 'variant': tile.variant, 'pos' : tile.pos}

        return seriable_tilemap,seriable_offgrid,seriable_decor,seriable_grass


    def save(self,path):
        f = open(path,'w')
        tilemap,offgrid, decor, grass = self.json_seriable()
        data = {
            'tilemap': tilemap,
            'tile_size': self.tile_size,
            **{'offgrid_' + str(i): v for i, v in enumerate(offgrid)},
            'decor': decor,
            'grass': grass
            
        }

        json.dump(data,f)
        f.close

    def load(self,path):
        f = open(path,'r')
        tilemap_data = json.load(f)

        for tile_key in tilemap_data['tilemap']:
            self.tilemap[tile_key] = Tile(tilemap_data['tilemap'][tile_key]["type"],tilemap_data['tilemap'][tile_key]["variant"],tilemap_data['tilemap'][tile_key]["pos"] )
       
        for i in range(0,self.offgrid_layers):
            for tile_key in tilemap_data['offgrid_'+ str(i)]:
                self.offgrid_tiles[i][tile_key] = Tile(tilemap_data['offgrid_'+str(i)][tile_key]["type"],tilemap_data['offgrid_'+str(i)][tile_key]["variant"],tilemap_data['offgrid_'+str(i)][tile_key]["pos"] )
        

        for tile_value in tilemap_data['decor']:
            self.decorations.append(Tile(tile_value["type"],tile_value["variant"],tile_value["pos"]))

        
        for grass_key in tilemap_data['grass']:
            self.grass[grass_key] = Tile(tilemap_data['grass'][grass_key]["type"],tilemap_data['grass'][grass_key]["variant"],tilemap_data['grass'][grass_key]["pos"] )
       
        """        for tile_value in tilemap_data['offgrid']:
            self.offgrid_tiles.append(Tile(tile_value["type"],tile_value["variant"],tile_value["pos"]))
       
            
            if (tile_value["pos"][0],tile_value["pos"][1]) not in self.offgrid_tiles_pos:
                print(tile_value["pos"][0],tile_value["pos"][1])
                self.offgrid_tiles_pos[(tile_value["pos"][0],tile_value["pos"][1])] = True 
        """


        f.close

    def graph_between_ent_player(self,ent_pos,player_pos):

        grid = {}
        
        ent_tile_pos = (ent_pos[0]//self.tile_size, ent_pos[1]//self.tile_size)
        player_tile_pos = (player_pos[0]//self.tile_size, player_pos[1]//self.tile_size)

        offset = (player_tile_pos[0] - ent_tile_pos[0],player_tile_pos[1] - ent_tile_pos[1])
        
        
           
        for y_cor in range(int(offset[1]) - 15 if int(offset[1]) <=0 else -15, 15 if int(offset[1]) <= 0 else int(offset[1]) + 15,1):
            for x_cor in range(-15 if offset[0] >= 0 else 15,int(offset[0]) + (15 if offset[0] >= 0 else -15),1 if offset[0] >= 0 else -1):
            

                tile_loc =  (int(ent_tile_pos[0] + x_cor),int(ent_tile_pos[1] + y_cor))
                tile_loc_check = str(tile_loc[0]) + ';' +str(tile_loc[1])  
                

                
                if tile_loc_check not in self.tilemap:
                    
                    below_tile_loc = (int(tile_loc[0]),int(tile_loc[1]+1))
                    below_tile_loc_check = str(below_tile_loc[0]) + ';' + str(below_tile_loc[1])

                    if below_tile_loc_check in self.tilemap: 
                        
                        new_node = Node(tile_loc)
                        new_node.down = self.tilemap[below_tile_loc_check]

                        grid[tile_loc] = new_node
                        
                        #check for connections. 
                        
                        if offset[0] >=0:
                            
                            left_loc = (tile_loc[0]-1,tile_loc[1])
                            left_loc_check = str(left_loc[0]) + ';' + str(left_loc[1])

                           

                            if left_loc in grid: 
                                grid[left_loc].right = grid[tile_loc]
                                grid[tile_loc].left = grid[left_loc]
                            elif left_loc_check in self.tilemap: 
                                grid[tile_loc].left = self.tilemap[left_loc_check]

                            
                        else: 
                            
                            right_loc = (tile_loc[0]+1,tile_loc[1])
                            right_loc_check = str(right_loc[0]) + ';' + str(right_loc[1])

                           

                            if right_loc in grid: 
                                grid[right_loc].left = grid[tile_loc]
                                grid[tile_loc].right = grid[right_loc]

                            elif right_loc_check in self.tilemap:
                    
                                
                                grid[tile_loc].right = self.tilemap[right_loc_check]
                            
                            
        
        #now, for the jump nodes. 
        
        airborne_grid = {}

        

        for key in grid: 
            node = grid[key]
            if not node.left : 
                #if there is no left neighbor: 
                #add a node there. 

                new_node_loc = (node.pos[0] -1 , node.pos[1])
                new_node = Node(new_node_loc)

                node.left = new_node 
                new_node.right = node 
                
                #check for downward connections. and continue on doing it until you reach another node or a tile. 
                self.recursion_depth = 0
                new_node.down = self.downward_connection(new_node,grid,airborne_grid)

                #once you've added all the connections, add the node to the grid. 
                airborne_grid[new_node_loc] = new_node
                
                
            if not node.right : 
                #if there is no up neighbor: 
                new_node_loc = (node.pos[0] +1 , node.pos[1])
                new_node = Node(new_node_loc)

                node.right = new_node 
                new_node.left = node 
                
                #check for downward connections. and continue on doing it until you reach another node or a tile. 
                self.recursion_depth = 0
                new_node.down = self.downward_connection(new_node,grid,airborne_grid)

                #once you've added all the connections, add the node to the grid. 
                airborne_grid[new_node_loc] = new_node
        
        if ent_tile_pos not in grid and ent_tile_pos not in airborne_grid:
            #this means that the tile location of the enemy is empty, as well as the tile location beneath it. 
            new_node = Node(ent_tile_pos)
            self.recursion_depth = 0
            new_node.down = self.downward_connection(new_node,grid,airborne_grid)
            airborne_grid[ent_tile_pos] = new_node 

        if player_tile_pos not in grid and player_tile_pos not in airborne_grid:
            #this means that the tile location of the player is empty, as well as the tile location beneath it. 
            new_node = Node(player_tile_pos)
            self.recursion_depth = 0
            new_node.down = self.downward_connection(new_node,grid,airborne_grid)
            airborne_grid[player_tile_pos] = new_node 
            
            
        for key in airborne_grid: 
            node = airborne_grid[key]
            grid[key] = node 
        
        return grid
           
        
                 
    def downward_connection(self,node,grid,airborne_grid):
        if self.recursion_depth >= 15:
            return None
        else: 
            #check for the position below the given node. 
            below_loc = (int(node.pos[0]),int(node.pos[1]+1))
            below_loc_check = str(below_loc[0]) + ';' + str(below_loc[1])

            if below_loc_check not in self.tilemap and below_loc not in grid and below_loc not in airborne_grid:
                #if the space below is empty, then create a node and continue the downard connection. 
                new_node = Node(below_loc)
                new_node.up = node 

                self.recursion_depth +=1
                airborne_grid[below_loc] = new_node 
                new_node.down = self.downward_connection(new_node,grid,airborne_grid)
                
                return new_node 
            elif below_loc_check in self.tilemap: 
                #if the space below has a tile, 
                return self.tilemap[below_loc_check]
            elif below_loc in grid: 
                #if the space below is another node, 
                grid[below_loc].up = node 
                return grid[below_loc]
            else: 
                #if the space below is another airborne node 
                airborne_grid[below_loc].up  = node 
                return airborne_grid[below_loc]
            
    def Astar_pathfinding(self,start_pos,end_pos):
       
        graph = self.graph_between_ent_player(start_pos,end_pos)
        
        start_node = graph[(start_pos[0]//self.tile_size,start_pos[1]//self.tile_size)]
        end_node = graph[(end_pos[0]//self.tile_size,end_pos[1]//self.tile_size)]

        # Initialize the open and closed sets
        open_set = []
        closed_set = set()

        # Initialize the start node's g score to 0 and its f score to the heuristic estimate
        start_node.g = 0
        start_node.f = self.heuristic(start_node.pos, end_node.pos)

        # Add the start node to the open set
        heapq.heappush(open_set,(start_node.f, start_node))
        while open_set:
            # Pop the node with the lowest f score from the open set
            current_f, current_node = heapq.heappop(open_set)

            # If the current node is the goal, reconstruct the path and return it
            if current_node == end_node:
                path = []
                while current_node is not None:
                    path.append(current_node)
                    current_node = current_node.parent
                
                return path[::-1]

            # Add the current node to the closed set
            closed_set.add(current_node)

            # Explore neighbors of the current node
            for neighbor_node in [current_node.left, current_node.right, current_node.up, current_node.down]:
                if neighbor_node is None or neighbor_node in closed_set:
                    continue
                if isinstance(neighbor_node,Tile):
                    continue
                # Calculate tentative g score
                tentative_g = current_node.g + 1

                # If the neighbor has not been evaluated yet or the new g score is lower
                if neighbor_node not in open_set or tentative_g < neighbor_node.g:
                    # Update neighbor's parent and g score
                    neighbor_node.parent = current_node
                    neighbor_node.g = tentative_g
                    neighbor_node.f = tentative_g + self.heuristic(neighbor_node.pos, end_pos)

                    # Add neighbor to the open set
                    heapq.heappush(open_set, (neighbor_node.f, neighbor_node))

        # If open set is empty and goal not reached, return empty path
        return []
    

        





    def heuristic(self, a, b):
        """
        Calculate the Manhattan distance heuristic between two points.
        """
        return abs(a[0] - b[0]) + abs(a[1] - b[1])


    def extract(self,id_pairs,keep = False):
        matches = []
        
        for i,dict in enumerate(self.offgrid_tiles.copy()):
            for loc in dict:
                tile = dict[loc]
                
                if (tile.type,tile.variant) in id_pairs: 
                    
                    matches.append(tile)
                    
                    matches[-1].pos = matches[-1].pos.copy()
                    """
                    matches[-1].pos[0] *= self.tile_size
                    matches[-1].pos[1] *= self.tile_size
                    """
                    
                    if not keep: 
                        del self.offgrid_tiles[i][loc]
                    

        
        for tile in self.decorations.copy():
            if (tile.type,tile.variant) in id_pairs: 
                matches.append(tile)
                if not keep: 
                    self.decorations.remove(tile)


        grass_copy = self.grass.copy()
        print(grass_copy)
        for loc in grass_copy: 
            grass = grass_copy[loc]
            print(grass)
            if (grass.type,grass.variant) in id_pairs:
                matches.append(grass)
                matches[-1].pos = matches[-1].pos.copy()
                """
                matches[-1].pos[0] *= self.tile_size
                matches[-1].pos[1] *= self.tile_size
                """
                if not keep: 
                    del self.grass[loc]

        copy_tilemap = self.tilemap.copy()
        for loc in self.tilemap.copy(): 
            tile = copy_tilemap[loc]
            if (tile.type,tile.variant) in id_pairs:
                matches.append(tile)
                matches[-1].pos = matches[-1].pos.copy()
                """
                matches[-1].pos[0] *= self.tile_size
                matches[-1].pos[1] *= self.tile_size
                """
                if not keep: 
                    del self.tilemap[loc]

        return matches
  

    def tiles_around(self,pos,size):
        """
        tiles = []

        tile_loc = (int(pos[0] // self.tile_size),int(pos[1] // self.tile_size))
        #surrounding tile offset needs to be changed according to sprite size 
        x_bound = size[0]-1 // 16
        y_bound = size[1]-1 //16
        loc_x = tile_loc[0]
        loc_y = tile_loc[1]

        for x_cor in range(-1,x_bound +2):
            for y_cor in range(-1,y_bound +2):
                check_loc = f"{loc_x +x_cor};{loc_y +y_cor}"
                #check_loc = str(tile_loc[0]+ x_cor) + ';' + str(tile_loc[1]+ y_cor)
                if check_loc in self.tilemap: 
                    tiles.append(self.tilemap[check_loc])
        return tiles 
        
        """
        tiles = []
    
        # Calculate the tile coordinates of the center position
        tile_center = (int(pos[0] // self.tile_size), int(pos[1] // self.tile_size))
        
        # Calculate the boundary coordinates of the surrounding tiles
        x_start = tile_center[0] - 1
        x_end = tile_center[0] + int(size[0] // self.tile_size) + 1
        y_start = tile_center[1] - 1
        y_end = tile_center[1] + int(size[1] // self.tile_size) + 1
        
        # Iterate through the surrounding tiles and check if they exist in the tilemap
        for x in range(x_start, x_end + 1):
            for y in range(y_start, y_end + 1):
                tile_key = f"{x};{y}"
                if tile_key in self.tilemap:
                    tiles.append(self.tilemap[tile_key])
        
        return tiles
        
                
    

    def physics_rects_around(self, pos,size):
        """        rects = []
        for tile in self.tiles_around(pos,size):
            if tile.type in PHYSICS_APPLIED_TILE_TYPES:
                rect = pygame.Rect(tile.pos[0]*self.tile_size,tile.pos[1]*self.tile_size,self.tile_size,self.tile_size) 
                rects.append(rect)
        return rects 
        """
        """
        rects = []
        tiles = []
        """
        surrounding_rects_tiles = []

        # Get the tiles around the given position
        tiles_around = self.tiles_around(pos, size)
        
        for tile in tiles_around:
            if tile.type in PHYSICS_APPLIED_TILE_TYPES:
                rect = (
                    tile.pos[0] * self.tile_size,         # left
                    tile.pos[1] * self.tile_size,         # top
                    self.tile_size,                       # width
                    self.tile_size                        # height
                )
               
                surrounding_rects_tiles.append((pygame.Rect(*rect),tile))
        # Convert the tuples to pygame Rect objects if needed
        #surrounding_rects_tiles = [ for rect in rects, tile for tile in tiles]
        
        

        return surrounding_rects_tiles
    


    def solid_check(self,pos):
        tile_loc = str(int(pos[0]//self.tile_size)) + ';' + str(int(pos[1]//self.tile_size))
        if tile_loc in self.tilemap:
            if self.tilemap[tile_loc].type in PHYSICS_APPLIED_TILE_TYPES:
                return self.tilemap[tile_loc]

    def return_tile(self,rect,pos = None):
        if pos == None: 
            tile_key = str(rect.left//self.tile_size) + ';' + str(rect.top//self.tile_size)
            return self.tilemap[tile_key]
        else: 
            tile_key = str(pos[0]//self.tile_size) + ';' + str(pos[1]//self.tile_size)
            if tile_key in self.tilemap:
                return self.tilemap[tile_key]
            else: 
                return None 

    
    def return_color(self,rect):
        tile = self.return_tile(rect)
        variant_sub = tile.variant.split(';')
        if  isinstance(self.game.assets[tile.type][int(variant_sub[0])],list):
        #if isinstance(self.game.assets[tile.type][int(variant_sub[0])],list):
            tile_img = self.game.assets[tile.type][int(variant_sub[0])][int(variant_sub[1])]
        else: 
             tile_img = self.game.assets[tile.type][int(variant_sub[0])]

        return tile_img.get_at((8,8))
    

    def autotile(self,random_ = False):
        dicts = [self.tilemap]
        for dict in self.offgrid_tiles:
            dicts.append(dict)
        
        for autotile_dicts in dicts:
            for loc in autotile_dicts:
                tile = autotile_dicts[loc]
                
                neighbors= set()
                for side in [(1,0),(-1,0),(0,-1),(0,1)]:
                    check_loc = str(tile.pos[0]+side[0]) +';' + str(tile.pos[1]+side[1])
                    if check_loc in autotile_dicts: 
                        if autotile_dicts[check_loc].type == tile.type: 
                            neighbors.add(side)
                        elif tile.type in SMOOTH_TRANS_TILES:
                            neighbors.add(side)
                        

                neighbors = tuple(sorted(neighbors))
                #print(f"Tile type: {tile.type}, AUTOTILE_TYPES: {AUTOTILE_TYPES}")
                if tile.type in AUTOTILE_TYPES: 
                
                    if tile.type[0:8] == 'building':
                        
                        auto_map = BUILDING_AUTOTILE[tile.type.split('_')[1]]
                        if neighbors in auto_map:
                            variant_sub_0 = BUILDING_AUTOTILE[tile.type.split('_')[1]][neighbors]
                            if isinstance(self.game.assets[tile.type][int(variant_sub_0)],list):
                                if random_:
                                    variant_sub_1 = random.randint(0,len(self.game.assets[tile.type][int(variant_sub_0)]) -1)
                                else: 
                                    variant_sub_1 = 0
                                tile.variant = str(variant_sub_0) +';' +str(variant_sub_1) 
                            else: 
                                tile.variant = str(variant_sub_0) +';0' 
                    else: 
                        if neighbors in AUTOTILE_MAP:
                            variant_sub_0 = AUTOTILE_MAP[neighbors]
                            if isinstance(self.game.assets[tile.type][int(variant_sub_0)],list):
                                if random_:
                                    variant_sub_1 = random.randint(0,len(self.game.assets[tile.type][int(variant_sub_0)]) -1)
                                else: 
                                    variant_sub_1 = 0
                                tile.variant = str(variant_sub_0) +';' +str(variant_sub_1) 
                            else: 
                                tile.variant = str(variant_sub_0) +';0'  
   
    #the only thing that needs updating for tiles are the decals for now, So there is no separate update function for now. 
    #if the tiles can be destroyed, I guess that is when I will add an update function.

    def render(self, surf, offset = (0,0)):
        
        for x_cor in range(offset[0] // self.tile_size, (offset[0] + surf.get_width()) // self.tile_size +1):
            for y_cor in range(offset[1] // self.tile_size, (offset[1] + surf.get_height()) // self.tile_size +1): 
                coor = str(x_cor) + ';' + str(y_cor)
                for dict in self.offgrid_tiles:
                    
                    if coor in dict: 
                        tile = dict[coor]
                        variant_sub = tile.variant.split(';')

                        
                        if isinstance(self.game.assets[tile.type][int(variant_sub[0])],list):
                        #if isinstance(self.game.assets[tile.type][int(variant_sub[0])],list):

                            surf.blit(self.game.assets[tile.type][int(variant_sub[0])][int(variant_sub[1])],(tile.pos[0] * self.tile_size-offset[0], tile.pos[1] *self.tile_size-offset[1]))
                        else: 
                            surf.blit(self.game.assets[tile.type][int(variant_sub[0])],(tile.pos[0] * self.tile_size-offset[0], tile.pos[1] *self.tile_size-offset[1]))
                        
                        #you also gotta blit an alpha surface depending on their exposure ( how many neighbors they have. )
                        #render the mask 
                        #surf.blit(self.game.assets['masks'][int(variant_sub[0])], (tile.pos[0] * self.tile_size-offset[0], tile.pos[1] *self.tile_size-offset[1]))
            
        #tiles rendering, render the decals here as well. 

        for x_cor in range(offset[0] // self.tile_size, (offset[0] + surf.get_width()) // self.tile_size +1):
            for y_cor in range(offset[1] // self.tile_size, (offset[1] + surf.get_height()) // self.tile_size +1): 
                coor = str(x_cor) + ';' + str(y_cor)
                if coor in self.tilemap: 
                    tile = self.tilemap[coor]
                    variant_sub = tile.variant.split(';')

                    
                    if isinstance(self.game.assets[tile.type][int(variant_sub[0])],list):
                    #if isinstance(self.game.assets[tile.type][int(variant_sub[0])],list):

                        surf.blit(self.game.assets[tile.type][int(variant_sub[0])][int(variant_sub[1])],(tile.pos[0] * self.tile_size-offset[0], tile.pos[1] *self.tile_size-offset[1]))
                    else: 
                        surf.blit(self.game.assets[tile.type][int(variant_sub[0])],(tile.pos[0] * self.tile_size-offset[0], tile.pos[1] *self.tile_size-offset[1]))
                   
                    #you also gotta blit an alpha surface depending on their exposure ( how many neighbors they have. )
                    #render the mask 
                    #surf.blit(self.game.assets['masks'][int(variant_sub[0])], (tile.pos[0] * self.tile_size-offset[0], tile.pos[1] *self.tile_size-offset[1]))
                    for decal in tile.decals.copy():
                        #so decals need to be surface objects. 
                        
                        surf.blit(decal[0],(tile.pos[0] * self.tile_size-offset[0], tile.pos[1] *self.tile_size-offset[1]))
                        decal[1] += 1
                        if decal[1] >= 40:
                            tile.decals.remove(decal)

                        
                         

        #decorations rendering 
        
        for tile in self.decorations: 
            
                variant_sub = tile.variant.split(';')
                if isinstance(self.game.assets[tile.type][int(variant_sub[0])],list):
                #if isinstance(self.game.assets[tile.type][int(variant_sub[0])],list):
                    
                    surf.blit(self.game.assets[tile.type][int(variant_sub[0])][int(variant_sub[1])], (tile.pos[0] - offset[0],tile.pos[1]-offset[1]))
                else: 
                    
                    surf.blit(self.game.assets[tile.type][int(variant_sub[0])], (tile.pos[0] - offset[0],tile.pos[1]-offset[1]))
        

        
        
class Tile: 
    def __init__(self,type,variant,pos):
        
        self.type = type 
        self.variant = variant
        #self.tile_rel_pos = tile_rel_pos
        self.pos = pos 
        self.decals = []
   
    def drop_item(self):
        if self.type == 'box':
            print('item_dropped')

class Slab(Tile):
    def __init__(self,type,variant,pos):
        super().__init__(type,variant,pos)
        self.y_factor = 0.5

class stair(Tile):
    def __init__(self,type,variant,pos,dir):
        super().__init__(type,variant,pos)
        self.dir = dir

class Node: 
    def __init__(self,pos):
        
        self.pos = pos
        self.left = None
        self.right = None 
        self.up = None
        self.down = None 
        self.parent = None 
        self.g = float('inf')
        self.f = float('inf')
        
    def __hash__(self):
        """
        Define a hash value based on the position attribute.
        """
        return hash(self.pos)
    def __lt__(self, other):
        """
        Define comparison for the less than operator.
        """
        return self.f < other.f

   
     


