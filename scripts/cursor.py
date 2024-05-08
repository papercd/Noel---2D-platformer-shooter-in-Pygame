import pygame 


class Cursor:
    def __init__(self,game,pos,aim_offset,type = 'default'):
        self.game = game 
        self.type = type
        self.pos = list(pos)
        self.aim_offset = list(aim_offset)
        self.sprite = self.game.assets['cursor' + '/' + self.type]


    def update(self):
        self.pos = pygame.mouse.get_pos()
        self.pos = ((self.pos[0]/2),(self.pos[1]/2))
    
    def render(self,surf):
        surf.blit(self.sprite,(self.pos[0] - self.aim_offset[0],self.pos[1] - self.aim_offset[1]))