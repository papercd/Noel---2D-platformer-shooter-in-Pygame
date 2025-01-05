from dataclasses import dataclass 


# be careful about using this class, be wary of floating point 
# precision problems.

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
    def bottomleft(self)->tuple[float,float]:
        return (self.x,self.y+self.height)

    @property 
    def topright(self)->tuple[float,float]:
        return (self.x+self.width,self.y)
    
    @property 
    def bottomright(self)->tuple[float,float]:
        return (self.x+self.width,self.y+self.height)

    @property 
    def midtop(self)->tuple[float,float]:
        return (self.x + self.width/2 , self.y)
    
    @property 
    def midleft(self)->tuple[float,float]:
        return (self.x,self.y+self.height/2)

    @property 
    def midbottom(self)->tuple[float,float]:
        return (self.x+self.width/2,self.y+self.height)
    
    @property
    def midright(self)->tuple[float,float]:
        return (self.x+self.width,self.y + self.height/2)
    

    @property
    def center(self)->tuple[float,float]:
        return (self.x + self.width/2, self.y + self.height /2)
    
    @property 
    def centerx(self)->float: 
        return self.x + self.width /2 
    
    @property
    def centery(self)->float:
        return self.y + self.height/2 

    @property 
    def size(self)->tuple[float,float]:
        return (self.width,self.height)
    
    @top.setter
    def top(self,new_top)->None: 
        self.y = new_top 

    @left.setter 
    def left(self,new_left)->None: 
        self.x = new_left 

    @bottom.setter 
    def bottom(self,new_bottom)->None: 
        self.y = new_bottom -self.height

    @right.setter
    def right(self,new_right)->None: 
        self.x  = new_right - self.width

    @topleft.setter
    def topleft(self,new_topleft)->None: 
        self.x = new_topleft[0]
        self.y = new_topleft[1]
    
    @bottomleft.setter 
    def bottomleft(self,new_bottomleft)->None: 
        self.x = new_bottomleft[0]
        self.y = new_bottomleft[1] - self.height


    @topright.setter
    def topright(self,new_topright)->None: 
        self.x = new_topright[0] - self.width
        self.y = new_topright[1]

    @bottomright.setter
    def bottomright(self,new_bottomright)->None: 
        self.x = new_bottomright[0] - self.width
        self.y = new_bottomright[1] - self.height

    @midtop.setter
    def midtop(self,new_mid_top)->None: 
        self.x = new_mid_top[0] - self.width / 2
        self.y = new_mid_top[1]

    @midleft.setter
    def midleft(self,new_mid_left)->None: 
        self.x = new_mid_left[0]
        self.y = new_mid_left[1] - self.height /2

    @midbottom.setter
    def midbottom(self,new_mid_bottom)->None: 
        self.x = new_mid_bottom[0] - self.width /2
        self.y = new_mid_bottom[1] - self.height

    @midright.setter
    def midright(self,new_mid_right)->None: 
        self.x = new_mid_right[0] - self.width
        self.y = new_mid_right[1] - self.height /2

    @center.setter
    def center(self,new_center)->None: 
        self.x = new_center[0] - self.width/2
        self.y = new_center[1] - self.height/2

    @centerx.setter
    def centerx(self,new_centerx)->None: 
        self.x = new_centerx - self.width /2

    @centery.setter
    def centery(self,new_centery)->None: 
        self.y = new_centery - self.height/2 
    
    @size.setter
    def size(self,new_size)->None:
        self.width = new_size[0]
        self.height = new_size[1]

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



    