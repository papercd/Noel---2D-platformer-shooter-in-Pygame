
class Rectangle:
    def __init__(self, position, scale):
        self.position = position
        self.scale = scale
        self.color = (255, 255, 255)
        self.lineThickness = 1

    def containsEntity(self, entity):
        x, y = entity.pos[0],entity.pos[1]
        bx, by = self.position
        w, h = self.scale
        if x >= bx and x <= bx+w and y >= by and y <= by+h:
            return True
        else:
            return False

    def intersects(self,_range):
        x, y = self.position
        w, h = self.scale
        xr, yr = _range.position
        wr, hr = _range.scale
        if xr > x + w or xr+wr < x-w or yr > y + h or yr+hr < y-h:
            return True
        else:
            return False

class Circle:
    def __init__(self, position, radius):
        self.position = position
        self.radius = radius
        self.sqradius = self.radius * self.radius
        self.scale = None
        self.color = (255, 255, 255)
        self.lineThickness = 1

    def containsEntity(self, entity):
        x1, y1 = self.position
        x2, y2 = entity.pos[0],entity.pos[1]
        dist = pow(x2-x1, 2) + pow(y2-y1, 2)
        if dist <= self.sqradius:
            return True
        else:
            return False

    def intersects(self, _range):
        x1, y1 = self.position
        x2, y2 = _range.position
        w, h = _range.scale
        r = self.radius
        dist_x, dist_y = abs(x2-x1), abs(y2-y1)

        edges = pow(dist_x-w, 2) + pow(dist_y-h, 2)

        if dist_x > (r+w) or dist_y > (r+h):
            return False

        if dist_x <= w or dist_y <= h:
            return True

        return (edges <= self.sqradius)
