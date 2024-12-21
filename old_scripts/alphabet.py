from scripts.utils import load_images,load_image

DEFAULT_ALPHABETS = load_images('text/alpha',background='transparent')
NEW_ALPHABETS = load_images("text/new_alpha",background="transparent")
NEW_NUMBERS = load_images("text/new_numbers",background="transparent")
DEFAULT_NUMBERS = load_images('text/numbers',background='transparent')
UNDERSCORE = load_image('text/underscore.png',background='transparent') 
SPACE = load_image('text/space.png',background="transparent")

class alphabets: 
    def __init__(self,text,scale =1):
        self.text= text
        self.length = 0
        self.scale = scale 
        
        self.display_text = self.transform()


    def transform(self):
        text = []
        for char in self.text:
            if char == '_':
                text.append(UNDERSCORE)
            elif char == ' ':
                text.append(SPACE)
            elif char.isnumeric():
                text.append(DEFAULT_NUMBERS[int(char)]) 
            else: 
                text.append(DEFAULT_ALPHABETS[ord(char)-97])
            self.length += 4
        return text 

         

    def render(self,surf,x,y):
        count = 0

        for char in self.display_text:
            surf.blit(char,(x+count*4,y))
            count +=1





class new_alphabets:
    def __init__(self,text):
        self.text= text 
        self.length = 0
        self.display_text = self.transform()

    def transform(self):
        display_text = []
        for char in self.text: 
            if char == " ":
                display_text.append(SPACE)
            elif char == '_':
                display_text.append(UNDERSCORE)
            elif char.isnumeric():
                display_text.append(NEW_NUMBERS[int(char)])
            else: 
                display_text.append(NEW_ALPHABETS[ord(char) -97])
            self.length += 6
        return display_text
    


    def render(self,surf,x,y,offset = (0,0),opacity = 255):
        for i, char in enumerate(self.display_text):
            char.set_alpha(opacity)
            surf.blit(char,(x+i*6 - offset[0],y -offset[1]))
            
        