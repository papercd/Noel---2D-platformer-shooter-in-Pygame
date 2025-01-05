from dataclasses import dataclass 

@dataclass
class FRect:
    x:float
    y:float 
    width: float 
    height: float
    
    @property 
    def left(self)->float: 
        return self.x 
    
    @property
    def right(self)->float:
        return self.x + self.width 
    
    @property
    def top(self)->float:
        return self.y 
    
    @property
    def bottom(self)->float:
        return self.y + self.height

    @property 
    def topleft(self)->tuple[float,float]:
        return (self.x,self.y)


    @property 
    def size(self)->tuple[float,float]:
        return (self.width,self.height)

    def move(self,dx:float,dy:float)->None: 
        self.x += dx 
        self.y += dy 


    def colliderect(self,other:"FRect")->bool: 
        return (
            self.left < other.right and 
            self.right >other.left and 
            self.top < other.bottom and 
            self.bottom > other.top 
        )



    