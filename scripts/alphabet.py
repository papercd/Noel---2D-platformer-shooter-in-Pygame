from scripts.utils import load_images,load_image

DEFAULT_ALPHABETS = load_images('text/alpha',background='transparent')
DEFAULT_NUMBERS = load_images('text/numbers',background='transparent')
UNDERSCORE = load_image('text/underscore.png',background='transparent') 


class alphabets: 
    def __init__(self,text):
        self.text= text
        self.length = 0
        
        self.display_text = self.transform()


    def transform(self):
        text = []
        for char in self.text:
            if char == '_':
                text.append(UNDERSCORE)
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