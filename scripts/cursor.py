import pygame 
from my_pygame_light2d.engine import RenderEngine,Layer_
from pygame.locals import * 


"""
CURSOR_ICONS = {
    "cursor": load_image("ui/inventory/cursor.png",background='transparent'),
    "grab": load_image("ui/inventory/cursor_grab.png",background='transparent'),
    "magnet": load_image("ui/inventory/cursor_magnet.png",background='transparent'),
    "move": load_image("ui/inventory/cursor_move.png",background='transparent'),
    "text": load_image("ui/inventory/cursor_text.png",background='transparent'),           # Added cursor text icon

    "rifle_crosshair": load_image("cursor/default_cursor.png",background= 'black'),
}
"""
class Cursor:
    def __init__(self,game,pos,aim_offset,type = 'default'):
        self.game = game 
        self.type = type
        self.pos = list(pos)
        self.aim_offset = list(aim_offset)
        self.sprite = self.game.general_sprites['cursor' + '/' + self.type]


        #attributes to use with new inventory module 
        self.interacting = False 
        self.item  = None
        self.box = pygame.Rect(*self.pos,1,1)
        self.cooldown = 0
        self.pressed = None
        self.magnet = False
        self.move = False
        self.context = None
        self.image = self.game.general_sprites["cursor"]




    def set_cooldown(self) -> None:
        self.cooldown = 10

    def update_render(self,render_engine_ref:RenderEngine):
        
        self.pos = pygame.mouse.get_pos()
        self.pos = ((self.pos[0]/2),(self.pos[1]/2))
        self.box = pygame.Rect(*self.pos, 1, 1)

        self.pressed = self.game.mouse_pressed


        if self.item is not None:

            render_engine_ref.render_texture(
                self.item.tex,Layer_.FOREGROUND,
                dest=pygame.Rect(self.pos[0],self.pos[1],self.item.tex.width,self.item.tex.height),
                source= pygame.Rect(0,0,self.item.tex.width,self.item.tex.height)
            )


            #self.item.draw(*self.pos,surf, 1)
        if self.cooldown > 0:
            self.cooldown -= 1

                  # Colliding with search box changes cursor to text

        self.magnet = self.game.shift_pressed and self. item is not None 
        self.move = self.game.shift_pressed and not self.magnet 


        """
        self.magnet = keys[K_LSHIFT] and self.item is not None
        self.move = keys[K_LSHIFT] and not self.magnet
        """

        if self.context is not None:
            self.context.update(*self.pos,render_engine_ref,1)
            self.context = None

        if self.interacting: 
            if self.magnet:
                self.image = self.game.general_sprites["magnet"]
               # pygame.transform.scale(
               # CURSOR_ICONS["magnet"], (9 * 1, 10 * 1))
            elif self.move:
                self.image = self.game.general_sprites["move"]
                #self.image = pygame.transform.scale(
                #   CURSOR_ICONS["move"], (9 * 1, 10 * 1))
            elif self.item is not None:
                self.image = self.game.general_sprites["grab"]
                #self.image = pygame.transform.scale(
                #    CURSOR_ICONS["grab"], (9 * 1, 10 * 1))
            
            else:
                self.image = self.game.general_sprites["cursor"]
                #self.image = pygame.transform.scale(
                #    CURSOR_ICONS["cursor"], (9 * 1, 10 * 1))    
        else: 
            if self.game.player.cur_weapon_node:
                #self.image = CURSOR_ICONS["rifle_crosshair"]
                self.image = self.game.general_sprites["rifle_crosshair"]
            else: 
                self.image = self.game.general_sprites["cursor"]
                #self.image = pygame.transform.scale(
                #    CURSOR_ICONS["cursor"], (9 * 1, 10 * 1))   

        render_engine_ref.render_texture(
            self.image,Layer_.FOREGROUND,
            dest= pygame.Rect(self.pos[0] - self.aim_offset[0], self.pos[1] -self.aim_offset[1],self.image.width,self.image.height),
            source= pygame.Rect(0,0,self.image.width,self.image.height)
        )
        #surf.blit(self.image,(self.pos[0] - self.aim_offset[0],self.pos[1] - self.aim_offset[1]))



    