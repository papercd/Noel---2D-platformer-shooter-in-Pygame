
class Rectangle:
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
    
    def contains(self, entity):
        return (entity.pos[0] + entity.size[0] >= self.x and entity.pos[0] <= self.x + self.w and 
        entity.pos[1] + entity.size[1] >= self.y and entity.pos[1] <= self.y + self.h)

    
    def intersects(self, range):
        return not (range.x - range.w > self.x + self.w or 
                    range.x + range.w < self.x - self.w or 
                    range.y - range.h > self.y + self.h or 
                    range.y + range.h < self.y - self.h)