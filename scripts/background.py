import numpy as np
from moderngl import Texture, Context


class Background:
    def __init__(self,textures:list[Texture],texcoords:bytes)->None: 
        self.textures = textures
        self.identity_texcoords = texcoords
