import pygame 
from scripts.utils import load_image
from pygame.locals import * 

CURSOR_ICONS = {
    "cursor": load_image("ui/inventory/cursor.png",background='transparent'),
    "grab": load_image("ui/inventory/cursor_grab.png",background='transparent'),
    "magnet": load_image("ui/inventory/cursor_magnet.png",background='transparent'),
    "move": load_image("ui/inventory/cursor_move.png",background='transparent'),
    "text": load_image("ui/inventory/cursor_text.png",background='transparent'),           # Added cursor text icon

    "rifle_crosshair": load_image("cursor/default_cursor.png",background= 'black'),
}

class Cursor:
    def __init__(self,game,pos,aim_offset,type = 'default'):
        self.game = game 
        self.type = type
        self.pos = list(pos)
        self.aim_offset = list(aim_offset)
        self.sprite = self.game.assets['cursor' + '/' + self.type]


        #attributes to use with new inventory module 
        self.interacting = False 
        self.item  = None
        self.box = pygame.Rect(*self.pos,1,1)
        self.cooldown = 0
        self.pressed = None
        self.magnet = False
        self.move = False
        self.context = None 




    def set_cooldown(self) -> None:
        self.cooldown = 10

    def update(self,keys,surf):
        self.pos = pygame.mouse.get_pos()
        self.pos = ((self.pos[0]/2),(self.pos[1]/2))

        self.box = pygame.Rect(*self.pos, 1, 1)
        self.pressed = pygame.mouse.get_pressed()


        if self.item is not None:
            self.item.draw(*self.pos,surf, 1)
        if self.cooldown > 0:
            self.cooldown -= 1

                  # Colliding with search box changes cursor to text
        self.magnet = keys[K_LSHIFT] and self.item is not None
        self.move = keys[K_LSHIFT] and not self.magnet

        if self.context is not None:
            self.context.update(*self.pos,surf,1)
            self.context = None

        if self.interacting: 
            if self.magnet:
                self.image = pygame.transform.scale(
                CURSOR_ICONS["magnet"], (9 * 1, 10 * 1))
            elif self.move:
                self.image = pygame.transform.scale(
                    CURSOR_ICONS["move"], (9 * 1, 10 * 1))
            elif self.item is not None:
                self.image = pygame.transform.scale(
                    CURSOR_ICONS["grab"], (9 * 1, 10 * 1))
            
            else:
                self.image = pygame.transform.scale(
                    CURSOR_ICONS["cursor"], (9 * 1, 10 * 1))    
        else: 
            if self.game.player.equipped:
                if self.game.player.cur_weapon.type =='rifle':
                    self.image = CURSOR_ICONS["rifle_crosshair"]
        surf.blit(self.image,(self.pos[0] - self.aim_offset[0],self.pos[1] - self.aim_offset[1]))



    