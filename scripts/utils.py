import os 
import pygame 
import math
import numpy as np
from moderngl import Context,Texture,NEAREST
#from PIL import Image, ImageFilter

#so in here we are going to define a function that creates pygame image objects
#and returns them, so that we can simplify our code when creating our assets 
#dictionary.The assets dictionary is going to contain lists as well, lists of sprite objects
#for our grass, stone, and clouds, etc.

BASE_PATH = 'data/images/'

def load_texture(path: str,ctx:Context) -> Texture:
    """
    Load a texture from a file.

    Args:
        path (str): Path to the texture file.
        ctx (moderngl.Context) : a moderngl context. 

    Returns:
        moderngl.Texture: Loaded texture.
    """

    img = pygame.image.load(path).convert_alpha()
    
    return surface_to_texture(img,ctx)



def surface_to_texture(img:pygame.Surface,ctx :Context) -> Texture:
    """
    Convert a pygame.Surface to a moderngl.Texture.

    Args:
        sfc (pygame.Surface): Surface to convert.

    Returns:
        moderngl.Texture: Converted texture.

    """
    img_flip = pygame.transform.flip(img, False, True)
    img_data = pygame.image.tostring(img_flip, "RGBA")

    tex = ctx.texture(img.get_size(), components=4, data=img_data)
    tex.filter = (NEAREST, NEAREST)
    return tex


def load_pygame_srf(path):
    
    """
    if background == 'black':
        sprite = pygame.image.load(BASE_PATH + path)
        sprite.set_colorkey((0,0,0))
       
    elif background == 'transparent': 
    """
    sprite= pygame.image.load(BASE_PATH + path).convert_alpha()
    return sprite 


def smoothclamp(x, mi, mx):
    t = (x - mi) / (mx - mi)
    smooth_t = np.where(t < 0, 0, np.where(t <= 1, 3 * t**2 - 2 * t**3, 1))
    return mi + (mx - mi) * smooth_t

def smoothclamp_decreasing(x, mi, mx):
    t = (x - mi) / (mx - mi)
    smooth_t = np.where(t < 0, 1, np.where(t <= 1, 1 - (3 * t**2 - 2 * t**3), 0))
    return mi + (mx - mi) * smooth_t

def rect_corners(rect, angle):
    """Returns the four corners of a rotated rectangle."""
    cx, cy = rect.center
    w, h = rect.size
    angle_rad = math.radians(angle)

    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)

    # Define the rectangle's corners (relative to the center)
    corners = [
        pygame.math.Vector2(-w / 2, -h / 2),
        pygame.math.Vector2(w / 2, -h / 2),
        pygame.math.Vector2(w / 2, h / 2),
        pygame.math.Vector2(-w / 2, h / 2)
    ]

    # Rotate the corners around the center
    rotated_corners = [pygame.math.Vector2(
        cx + corner.x * cos_a - corner.y * sin_a,
        cy + corner.x * sin_a + corner.y * cos_a
    ) for corner in corners]

    return rotated_corners

def project_polygon(corners, axis):
    """Projects the corners of a polygon onto an axis."""
    dots = [corner.dot(axis) for corner in corners]
    return min(dots), max(dots)

def obb_collision(rect1_corners, rect2):
    """Detects collision between a rotated rectangle and an axis-aligned rectangle."""
    rect2_corners = [
        pygame.math.Vector2(rect2.topleft),
        pygame.math.Vector2(rect2.topright),
        pygame.math.Vector2(rect2.bottomright),
        pygame.math.Vector2(rect2.bottomleft)
    ]

    axes = []
    for i in range(4):
        edge = rect1_corners[i] - rect1_corners[(i + 1) % 4]
        normal = pygame.math.Vector2(-edge.y, edge.x)
        axes.append(normal.normalize())

    for i in range(2):  # We only need 2 axes for the AABB rectangle (rect2)
        edge = rect2_corners[i] - rect2_corners[(i + 1) % 4]
        normal = pygame.math.Vector2(-edge.y, edge.x)
        axes.append(normal.normalize())

    for axis in axes:
        proj1 = project_polygon(rect1_corners, axis)
        proj2 = project_polygon(rect2_corners, axis)
        if proj1[1] < proj2[0] or proj2[1] < proj1[0]:
            return False  # No overlap on this axis, so no collision
    return True








#now the this load_images function will get all the sprites within one directory and turn them into a list.

def load_tile_textures(paths):
    return {path: retrieve_textures(f'tiles/{path}') for path in paths}

def load_textures_from_path_dict(paths):
    return {key: load_texture(path) for key, (path) in paths.items()}

def load_textures_from_dict_multiple(paths):
    return {key: load_textures(path, background=bg) for key, (path, bg) in paths.items()}



def load_animation_textures(animations_paths):
    return {
        key: Animation(load_textures(path ), img_dur=dur, loop=loop, halt=halt)
        for key, (path, dur, loop, halt) in animations_paths.items()
    }

def load_textures(path):
    sprites = []
    #the sorted() method will turn the list into an alphabetically-sorted list.
    for sprite_name in sorted(os.listdir(BASE_PATH + path)):
        sprites.append(load_texture(path+ '/' + sprite_name))

    return sprites

def retrieve_textures(path):
    list_of_lists = []
    for dir in sorted(os.listdir(BASE_PATH + path)):
        dir_check = dir.split('.')
        if len(dir_check) > 1:
            
            list_of_lists.append(load_texture(path +'/'+dir))
        else: 
            new_list = retrieve_textures(path +'/' + dir)
            list_of_lists.append(new_list)
    return list_of_lists


def load_sounds(path):
    sound_lib  = {}
    for dir in os.listdir(path):
        key = dir.split('.',1)[0]
        sound_lib[key] = pygame.mixer.Sound(path + '/' + dir)

    return sound_lib 
    

class Animation: 
    def __init__(self, textures, img_dur = 5, halt = False, loop = True):
        self.textures=textures 
        self.count = len(self.textures) 
        self.loop = loop 
        self.halt = halt
        self.img_dur = img_dur 
        self.done = False 
        self.frame = 0

    def copy(self):
        return Animation(self.textures,self.img_dur,self.halt,self.loop)
    
    def update(self):
        if self.halt: 
             self.frame = min(self.frame+1,self.img_dur * len(self.textures) -1)
        else: 
            if self.loop:
                self.frame = (self.frame+1) % (self.img_dur * len(self.textures))
            else: 
                self.frame = min(self.frame+1,self.img_dur * len(self.textures) -1)
                if self.frame >= self.img_dur *len(self.textures) -1:
                    self.done = True 


    def reverse(self):
        pass 

    def curr_tex(self):
        return self.textures[int(self.frame / self.img_dur)]



"""

#                 Pygame VFX                #
#             MIT - Kadir Aksoy             #
#   https://github.com/kadir014/pygame-vfx  #


    # Optimized blurring algorithm by The New St. Paul aka MintFan
def blur(canvas, pos, size, radius=10, alpha=255, resolution=40):
    resolution = resolution #percentage of pixels to use for blur
    s = pygame.Surface(size)
    s.blit(canvas, (0, 0), (pos[0], pos[1], size[0], size[1]))
    s = pygame.transform.rotozoom(s, 0, (resolution / 100.0) * 1)
    size2 = s.get_size()
    rad = radius
    b = pygame.image.tostring(s, "RGBA", False)
    b = Image.frombytes("RGBA", size2, b)
    b = b.filter(ImageFilter.GaussianBlur(radius=int(rad)))
    b = pygame.image.frombuffer(b.tobytes(), b.size, b.mode).convert()
    b.set_alpha(alpha)
    b = pygame.transform.rotozoom(b, 0, (100.0 / resolution) * 1)
    canvas.blit(b, pos)
"""