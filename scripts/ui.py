import pygame
from scripts.utils import load_image

START_UI_IMAGE = load_image(('ui/start_ui/start_element.png'),'transparent')
OPTIONS_UI_IMAGE = load_image(('ui/options_ui/options_ui.png'),'transparent')
EXIT_UI_IMAGE = load_image(('ui/exit_ui/exit_ui.png'),'transparent')

class UIElement:
    def __init__(self, pos, image):
        self.pos = pos 
        self.hover = False 
        self.image = image 
        self.image_dim = self.image.get_size() 

    def rect(self):
        return pygame.Rect(self.pos[0] , self.pos[1], *self.image_dim)

    
    def render(self,surf):
        surf.blit(self.image, (self.pos[0],self.pos[1] - (1 if self.hover else 0)))


class startUI(UIElement):
    def __init__(self,pos):
        super().__init__(pos,START_UI_IMAGE)


class optionsUI(UIElement):
    def __init__(self, pos):
        super().__init__(pos, OPTIONS_UI_IMAGE)


class exitUI(UIElement):
    def __init__(self, pos):
        super().__init__(pos, EXIT_UI_IMAGE)



class startScreenUI:
    def __init__(self,screen_res):
        self.screen_res =  screen_res
        self.ui_elements = [startUI((self.screen_res[0]//4,self.screen_res[1]//4)),
                            optionsUI(((self.screen_res[0]//4,self.screen_res[1]//4 + OPTIONS_UI_IMAGE.get_height() + 2))),
                            exitUI(((self.screen_res[0]//4,self.screen_res[1]//4 + OPTIONS_UI_IMAGE.get_height() + EXIT_UI_IMAGE.get_height() + 4)))]

    def update(self,cursor):
        for ui_element in self.ui_elements:
            #check for collision for each of the ui elements in the list. 
            if ui_element.rect().colliderect(cursor.box):
                #then you change the hover value. 
                ui_element.hover = True 
            else: 
                ui_element.hover = False 
             


    def render(self, surf, offset = (0,0)):
        for ui_element in self.ui_elements: 
            ui_element.render(surf)