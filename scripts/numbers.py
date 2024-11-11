from scripts.utils import load_textures,load_texture

NEW_NUMBERS = load_textures('text/new_numbers')
DEFAULT_NUMBERS = load_textures('text/numbers')
MINUS = load_texture('text/minus.png')
#only positive numbers for now. 

class numbers:
    def __init__(self,number):
        self.number = number 
        self.length = 0
        self.display_number = self.transform()

    def change_number(self,number):
        self.number = number 
        self.length = 0    
        self.display_number = self.transform()    

    def transform(self):
        number = []
        if self.number == 0:
            self.length+=4
            number.append(DEFAULT_NUMBERS[0])
            return number
        else: 
            dummy_number = self.number
            if dummy_number < 0:
                dummy_number = -dummy_number
                number.append(MINUS)
                self.length+=4
            while dummy_number > 0 :
                digit = dummy_number % 10
                number.append(DEFAULT_NUMBERS[digit])
                dummy_number = dummy_number // 10
                self.length+=4
            return number 
    
    def render(self,x,y,surf,offset = (0,0)):
        count = 0
        for digit in self.display_number:
            surf.blit(digit,(x - count*4 - offset[0],y- offset[1]))
            count += 1

        

class new_numbers: 
    def __init__(self,number):
        self.number = number 
        self.length = 0
        self.display_number = self.transform()

    def change_number(self,number):
        self.number = number 
        self.length = 0    
        self.display_number = self.transform()    

    def transform(self):
        number = []
        if self.number == 0:
            self.length+=4
            number.append(NEW_NUMBERS[0])
            return number
        else: 
            dummy_number = self.number
            if dummy_number < 0:
                dummy_number = -dummy_number
                number.append(MINUS)
                self.length+=4
            while dummy_number > 0 :
                digit = dummy_number % 10
                number.append(NEW_NUMBERS[digit])
                dummy_number = dummy_number // 10
                self.length+=5
            return number 
    
    def render(self,x,y,surf,offset = (0,0)):
        count = 0
        for digit in self.display_number:
            surf.blit(digit,(x - count*4 - offset[0],y- offset[1]))
            count += 1

        
    
