from pygame import Rect



class Cell:
    def __init__(self,ind,type = None,item = None):
        self._ind = ind 
        self._item = item 
        self._type  = type 
    
    def update(self):
        pass 


class Inventory:
    def __init__(self,name,rows,columns,x,y,cell_dim,stack_limit,expandable = False):
        self._name = name
        self._rows = rows 
        self._columns = columns
        self._cells = [[Cell(i,self._name) for i in range(columns)] for j in range(rows)]
        self._topleft = [x,y]
        self._cell_dim = cell_dim
        self._stack_limit = stack_limit
        self._max_capacity = rows * columns

        #TODO: need to account for space between cells 
        self._size = (self._columns * self._cell_dim[0],self._rows * self._cell_dim[1])
        self._rect = Rect(*self._topleft,*self._size)
        self._expandable =  expandable

        if self._expandable:
            self._done_open = 0
            self._cur_capacity = 255
            self._offset = 0

    def add_item(self,item) -> None:
        pass 


    def remove_current_item(self):
        pass 

    def update(self, inventory_id, inventory_list, cursor,inven_open_state, player):
        interacting  = self._rect.colliderect(cursor.box)

        if self._expandable:
            if not inven_open_state:
                self._done_open = min(4,self._done_open +1)
            else:
                self._done_open = max(0,self._done_open -1)
            
            self._cur_opacity = 255 * (self._done_open/4)
            self._offset = self._cell_dim[1] * (self._done_open/4)


        for i, row in enumerate(self._cells):
            for j, cell in enumerate(row):
               cell.update() 

        
        return interacting





class Inventory_Engine: 
    def __init__(self,inven_list,player):
        self._inventory_list = inven_list 
        self._player = player

    def update(self,cursor,inven_open_state):

        interacting = False 

        for i, inventory in enumerate(self._inventory_list):
            check = inventory.update(i,self._inventory_list,cursor,inven_open_state,self._player)
            interacting = check or interacting 

        cursor.interacting = interacting 



