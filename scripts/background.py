import pygame 
from moderngl import Texture
class Background:
    "A class for managing Background scene with parallax"

    def __init__(self,textures:list[Texture]):
        """
        Initialize the Background object.
        
        Args:
            textures (list[moderngl.Texture]) : the list of textures that are to be rendered in the way they are ordered. 
            infinite (bool = False) : a boolean to indicate whether the background should wrap around the screen 
        """
        self.bg_textures =textures 
    
