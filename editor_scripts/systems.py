import pygame
from editor_scripts.interface import EditorInterface

class InputHandler:

    def __init__(self,editor_context)->None:

        self._ref_interface = EditorInterface.get_instance()
        self._ref_editor_context = editor_context


    def handle_inputs(self)->None:
        self._ref_interface.cursor.topleft = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN: 
                pass
            elif event.type == pygame.KEYUP:
                pass
            elif event.type ==pygame.MOUSEWHEEL:
                pass
            