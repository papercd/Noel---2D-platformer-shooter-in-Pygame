from my_pygame_light2d.light import PointLight
from scripts.data import LIGHT_POSITION_OFFSET_FROM_TOPLEFT

from numpy import int32

class hullSpatialGrid:
    def __init__(self, cell_size:int32):
        self.cell_size = cell_size
        self.grid = {}

    def _get_cell_coords(self, x, y):
        return int(x // self.cell_size), int(y // self.cell_size)

    def insert(self, hull):
        x1, y1 = hull.vertices[0]
        x2, y2 = hull.vertices[2]
        
        # Calculate overlapping grid cells
        cell_x1, cell_y1 = self._get_cell_coords(x1, y1)
        cell_x2, cell_y2 = self._get_cell_coords(x2, y2)

        for cx in range(cell_x1, cell_x2 + 1):
            for cy in range(cell_y1, cell_y2 + 1):
                if (cx, cy) not in self.grid:
                    self.grid[(cx, cy)] = []
                self.grid[(cx, cy)].append(hull)

    def query(self, x1, y1, x2, y2):
        visible_hulls = set()

        # Get grid cell range for query area
        cell_x1, cell_y1 = self._get_cell_coords(x1, y1)
        cell_x2, cell_y2 = self._get_cell_coords(x2, y2)

        for cx in range(cell_x1, cell_x2 + 1):
            for cy in range(cell_y1, cell_y2 + 1):
                if (cx, cy) in self.grid:
                    visible_hulls.update(self.grid[(cx, cy)])

        return list(visible_hulls)

class lightSpatialGrid: 
    def __init__(self,cell_size:int32)->None: 
        self.cell_size = cell_size 
        self.grid = {}

    def _get_cell_coords(self, x, y):
        return int(x // self.cell_size), int(y // self.cell_size)

    def insert(self,light:PointLight)->None: 
        key = (light.position[0]- LIGHT_POSITION_OFFSET_FROM_TOPLEFT[0],
               light.position[1]- LIGHT_POSITION_OFFSET_FROM_TOPLEFT[1])
        
        grid_position = (key[0] // self.cell_size, key[1] // self.cell_size)
        if grid_position not in self.grid: 
            self.grid[grid_position] = []
        self.grid[grid_position].append(light)
      

    def query(self,x1,y1,x2,y2)->list[PointLight]:
        visible_lights = []
        cell_x1, cell_y1 = self._get_cell_coords(x1,y1)
        cell_x2, cell_y2 = self._get_cell_coords(x2,y2)

        for cx in range(cell_x1,cell_x2 + 1):
            for cy in range(cell_y1, cell_y2 + 1):
                if (cx,cy) in self.grid: 
                    visible_lights.extend(self.grid[(cx,cy)])
        return visible_lights