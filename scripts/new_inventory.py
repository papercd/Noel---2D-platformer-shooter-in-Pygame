from pygame import Rect



class Cell:
    def __init__(self,ind,type = None,item = None):
        self._ind = ind 
        self._item = item 
        self._type  = type 
    
    def update(self):
        pass 


class Inventory:
    def __init__(self,name,rows,columns,x,y,stack_limit,expandable = False):
        self._name = name
        self._done_open = 0 
        self._rows = rows 
        self._columns = columns
        self._cells = [[Cell(i,self.name) for i in range(columns)] for j in range(rows)]
        self._topleft = [x,y]
        self._max_capacity = rows * columns
        self._cur_capacity = 0
        self._size = (0,0)
        self._rect = Rect(*self._topleft,*self._size)
        self._expandable =  expandable



    def add_item(self,item) -> None:
        pass 


    def remove_current_item(self):
        pass 

    def update(self, inventory_id, inventory_list, cursor,text,closing, player):
        pass 








class Inventory_Engine: 
    def __init__(self,player,inven_list):
        self._inventory_list = inven_list 
        self._player = player

    def update(self,cursor,closing,text):

        interacting = False 

        for i, inventory in enumerate(self._inventory_list):
            check = inventory[1].update(i,self._inventory_list,cursor,text,closing,self._player)
            interacting = check or interacting 

        cursor.interacting = interacting 



