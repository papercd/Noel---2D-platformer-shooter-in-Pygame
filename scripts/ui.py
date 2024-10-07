
import pygame
from scripts.utils import load_image

START_UI_IMAGE = load_image('ui/start_ui/start_element.png','transparent')
OPTIONS_UI_IMAGE = load_image('ui/options_ui/options_ui.png','transparent')
EXIT_UI_IMAGE = load_image('ui/exit_ui/exit_ui.png','transparent')



class UIElement:
    def __init__(self, pos,image) -> None:
        #a UI needs a sprite, and a position value. We also may need 
        #a separate sprite to blit behind the original sprite to give it an interactive
        #effect on mouse hover.
        self.hover = False 
        self.pos = pos
        self.image = image
        self.image_dim = self.image.get_size()

    def rect(self):
        #we need this to do rect collision between the ui element and the cursor.
        return pygame.Rect(self.pos[0] - self.image_dim[0] //2, self.pos[1] - (0 if not self.hover else 3), *self.image_dim)
    
    def update(self,cursor):
        if cursor.box.colliderect(self.rect()):
            self.hover = True 
        else: 
            self.hover  = False 

    def render(self,surf):
        surf.blit(self.image,self.pos)

    #why would you need separate classes for different ui elements?
    #well, because different ui elements interact differently on click. How would I implement this? 

    
class startUI(UIElement):
    def __init__(self, pos) -> None:
        super().__init__( pos, START_UI_IMAGE)

class optionsUI(UIElement):
    def __init__(self, pos) -> None:
        super().__init__(pos, OPTIONS_UI_IMAGE)

class exitUI(UIElement):
    def __init__(self, pos) -> None:
        super().__init__(pos, EXIT_UI_IMAGE)


class startScreenUI:
    def __init__(self,screen_res) -> None:
        #you need a component for each option.
        #start ui, option ui, new game ui, etc. How is this gonna work? 
        self.screen_res = screen_res
        self.ui_elements = [startUI((self.screen_res[0]//4,self.screen_res[1]//4)), 
                            optionsUI((self.screen_res[0]//4,self.screen_res[1]//4 + OPTIONS_UI_IMAGE.get_height() + 2)),
                            exitUI((self.screen_res[0]//4,self.screen_res[1]//4 + OPTIONS_UI_IMAGE.get_height() + EXIT_UI_IMAGE.get_height() +4))]
        
        
    def update(self,cursor):
        for ui_element in self.ui_elements:
            ui_element.update(cursor)

    def render(self,surf,offset = (0,0)):
        for ui_element in self.ui_elements:
            ui_element.render(surf)