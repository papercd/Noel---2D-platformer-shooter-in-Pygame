import pygame
from scripts.numbers import numbers


UNSELECTED = "red"
SELECTED = "white"
BUTTONSTATES = {
    True:SELECTED,
    False:UNSELECTED
}

class UI:
    @staticmethod
    def init(surf):
        UI.font = pygame.font.Font(None, 15)
        UI.sfont = pygame.font.Font(None, 15)
        UI.lfont = pygame.font.Font(None, 15)
        UI.xlfont = pygame.font.Font(None, 15)
        UI.center = (surf.get_size()[0]//2, surf.get_size()[1]//2)
        UI.half_width = surf.get_size()[0]//2
        UI.half_height = surf.get_size()[1]//2

        UI.fonts = {
            'sm':UI.sfont,
            'm':UI.font,
            'l':UI.lfont,
            'xl':UI.xlfont
        }

class Menu:
    def __init__(self, game, pos, bg="gray") -> None:
        self.game = game
        self.bg = bg
        self.pos = pos

        self.sliders = [
            Slider(pos, (25,5), 0.5, 0, 255),
            Slider((pos[0], pos[1]+15), (25,5), 0.5, 0, 255),
            Slider((pos[0], pos[1]+30), (25,5), 0.5, 0, 255),
            Slider((pos[0] + 35, pos[1]), (25,5), 0.5, 0, 100),
            Slider((pos[0] + 35, pos[1]+15), (25,5), 0.5, 0, 356),
        ]

    def run(self):
        
        mouse = pygame.mouse.get_pressed()
        mpos = pygame.mouse.get_pos() 
        mpos = (mpos[0]/ self.game.RENDER_SCALE, mpos[1]/self.game.RENDER_SCALE) 
       
        #self.app.foreground_surf.fill("black")
        for slider in self.sliders:
            if slider.container_rect.collidepoint(mpos):
                if mouse[0]:
                    slider.grabbed = True
            if not mouse[0]:
                slider.grabbed = False
            if slider.button_rect.collidepoint(mpos):  
                slider.hover()
            if slider.grabbed:
                slider.move_slider(mpos)
                slider.hover()
            else:
                slider.hovered = False
            slider.render(self.game.foreground_surf)
            #slider.display_value(self.game.foreground_surf)
        

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                
                if event.key == pygame.K_x or event.key == pygame.K_ESCAPE:
                    self.game.lights_engine._release_frame_buffers()
                    self.game.lights_engine._create_frame_buffers()
                    self.game.foreground_surf = \
                        pygame.Surface((int(self.game.screen_res[0]/self.game.RENDER_SCALE),int(self.game.screen_res[1]/self.game.RENDER_SCALE)),pygame.SRCALPHA)
                    return False
        return True                 

                     

class Label:
    def __init__(self, font: str, content: str, pos: tuple, value = "blue", selected: bool = False) -> None:
        self.font = font
        self.selected = selected
        self.content = content

        self.value = value

        self.text = UI.fonts[self.font].render(content, True, BUTTONSTATES[self.selected], None)
        self.text_rect = self.text.get_rect(center = pos)
    def render(self, app):
        app.foreground_surf.blit(self.text, self.text_rect)

        

class Slider:
    def __init__(self, pos: tuple, size: tuple, initial_val: float, min: int, max: int) -> None:
        self.pos = pos
        self.size = size
        self.hovered = False
        self.grabbed = False



        self.slider_left_pos = int(self.pos[0]) -  (size[0]//2)
        self.slider_right_pos = int(self.pos[0]) + (size[0]//2)
        self.slider_top_pos = int(self.pos[1]) - (size[1]//2)


        #display number done with my numbers class 
        self.display_number = numbers(0)


        self.min = min
        self.max = max
        self.initial_val = (self.slider_right_pos-self.slider_left_pos)*initial_val # <- percentage

        self.container_rect = pygame.Rect(self.slider_left_pos, self.slider_top_pos, self.size[0], self.size[1])
        self.button_rect = pygame.Rect(self.slider_left_pos + self.initial_val - 5, self.slider_top_pos, 10, self.size[1])

        # label
        self.text = UI.fonts['m'].render(str(int(self.get_value())), True, "white", None)
        self.label_rect = self.text.get_rect(center = (self.pos[0], self.slider_top_pos - 15))
        
    def move_slider(self, mouse_pos):
        pos = mouse_pos[0]
        if pos < self.slider_left_pos:
            pos = self.slider_left_pos
        if pos > self.slider_right_pos:
            pos = self.slider_right_pos
        self.button_rect.centerx = pos
    def hover(self):
        self.hovered = True
    def render(self, surf):
        pygame.draw.rect(surf,(92,92,92),(self.container_rect.topleft[0]-5,self.container_rect.topleft[1]-8, self.size[0]+9,self.size[1]+8))
        self.display_number.change_number(int(self.get_value()))
        self.display_number.render(self.pos[0],self.pos[1]-8,surf)
        pygame.draw.rect(surf, "darkgray", self.container_rect)
        pygame.draw.rect(surf, BUTTONSTATES[self.hovered], self.button_rect)


    def get_value(self):
        val_range = self.size[0] - 1
        button_val = self.button_rect.centerx - self.slider_left_pos

        return (button_val/val_range)*(self.max-self.min)+self.min
    
    def display_value(self, surf):
        self.text = UI.fonts['m'].render(str(int(self.get_value())), True, "white", None)
        surf.blit(self.text, self.label_rect)









