from scripts.utils import load_images

DEFAULT_NUMBERS = load_images('text/numbers',background='transparent')

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
        if self.number ==0:
            self.length+=4
            number.append(DEFAULT_NUMBERS[0])
            return number
        else: 
            while self.number > 0 :
                digit = self.number % 10
                number.append(DEFAULT_NUMBERS[digit])
                self.number = self.number // 10
                self.length+=4
            return number 
    
    def render(self,x,y,surf):
        count = 0
        for digit in self.display_number:
            surf.blit(digit,(x - count*4,y))
            count += 1

        

