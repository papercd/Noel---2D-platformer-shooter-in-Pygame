from scripts.utils import load_image
from scripts.numbers import numbers 


slash = load_image('text/others/0.png',background='transparent')

class indicator: 
    def __init__(self,cur_resource,max_resource):
        self.cur_resource = numbers(cur_resource)
        self.max_resource = numbers(max_resource)

    def render(self,x,y,surf):
        self.cur_resource.render(x,y,surf)
        surf.blit(slash,(x+self.cur_resource.length,y))
        self.max_resource.render(x+self.cur_resource.length+20,y,surf)