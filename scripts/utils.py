import os 
import pygame 
from PIL import Image, ImageFilter

#so in here we are going to define a function that creates pygame image objects
#and returns them, so that we can simplify our code when creating our assets 
#dictionary.The assets dictionary is going to contain lists as well, lists of sprite objects
#for our grass, stone, and clouds, etc.

BASE_PATH = 'data/images/'

def load_image(path,background = 'black'):
     
    
    if background == 'black':
        sprite = pygame.image.load(BASE_PATH + path).convert()
        sprite.set_colorkey((0,0,0))
    elif background == 'transparent': 
        sprite= pygame.image.load(BASE_PATH + path)
    return sprite 


#now the this load_images function will get all the sprites within one directory and turn them into a list.

def load_assets(path):
    for dir in sorted(os.listdir(BASE_PATH+ path)):
        print(dir)
    


def load_images(path,background = 'black'):
    sprites = []
    #the sorted() method will turn the list into an alphabetically-sorted list.
    for sprite_name in sorted(os.listdir(BASE_PATH + path)):
        sprites.append(load_image(path+ '/' + sprite_name,background))

    return sprites

def load_tile_images(path,background = 'black'):
    list_of_lists = []
    for dir in sorted(os.listdir(BASE_PATH + path)):
        dir_check = dir.split('.')
        if len(dir_check) > 1:
            
            list_of_lists.append(load_image(path +'/'+dir,background))
        else: 
            new_list = load_tile_images(path +'/' + dir, background)
            list_of_lists.append(new_list)
    return list_of_lists


def load_sounds(path):
    sound_lib  = {}
    for dir in os.listdir(path):
        key = dir.split('.',1)[0]
        sound_lib[key] = pygame.mixer.Sound(path + '/' + dir)

    return sound_lib 
    

class Animation: 
    def __init__(self, images, img_dur = 5, halt = False, loop = True):
        self.images = images 
        self.loop = loop 
        self.halt = halt
        self.img_dur = img_dur 
        self.done = False 
        self.frame = 0

    def copy(self):
        return Animation(self.images,self.img_dur,self.halt,self.loop)
    
    def update(self):
        if self.halt: 
             self.frame = min(self.frame+1,self.img_dur * len(self.images) -1)
        else: 
            if self.loop:
                self.frame = (self.frame+1) % (self.img_dur * len(self.images))
            else: 
                self.frame = min(self.frame+1,self.img_dur * len(self.images) -1)
                if self.frame >= self.img_dur *len(self.images) -1:
                    self.done = True 


    def img(self):
        return self.images[int(self.frame / self.img_dur)]





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
