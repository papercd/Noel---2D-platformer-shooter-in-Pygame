import pygame 

class Background:
    def __init__(self,game,images,infinite = True):
        self.game = game 
        self.bg_layers = images
        self.infinite = infinite

    def render(self,surf,offset= (0,0)): 
        scroll = offset[0]
        
        speed = 1
        for image in self.bg_layers:
            image = pygame.transform.scale(image,surf.get_size())
            for panels in range(-1,2):
             
                surf.blit(image,(panels*image.get_width() - scroll *0.05 * speed ,0 - min(0,offset[1] * 0.05)))     
            speed +=1