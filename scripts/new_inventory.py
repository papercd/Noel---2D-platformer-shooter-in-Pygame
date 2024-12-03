from pygame import Rect
from scripts.lists import WeaponInvenList


class Cell:
    def __init__(self,ind,pos,size,inventory_id,type = None,item = None):
        self._ind = ind 
        self._pos = pos 
        self._hovered = False 
        self._offset = (0,0)
        self._size = size
        self._item = item 
        self._type  = type 
        self._inventory_id = inventory_id

        self._rect = Rect(*self._pos,*self._size)
    
    def update(self,stack_limit,inventory_list,cursor,opacity):
        if cursor.box.colliderect(self._rect):
            self._offset = (-1,-1)
            self._hovered = True 
        
        else: 
            self._offset = (0,0)
            self._hovered = False 
        

        if opacity == 255:
            if self._item is not None: 
                if not self._hovered: 
                    return 
                if cursor.cooldown != 0:
                    return 
                
                if cursor.magnet and cursor.item.name == self._item.name and self._item.stackable: 
                    if not (cursor.item.type == self._type):
                        return 
                    
                    amount = stack_limit - cursor.item.count
                    if self._item.count + cursor.item.count <= stack_limit:
                        cursor.item.count = cursor.item.count + self._item.count
                        self._item = None 
                    else: 
                        cursor.item.count = cursor._item.count + amount 
                        self._item.count = self._item.count - amount
                    
                    cursor.set_cooldown()
                
                if cursor.item is None: 
                    cursor.text = (self._item.get_name(),self._item.get_description())
                    
                    if cursor.pressed[0] and cursor.move:
                        index = self._inventory_id
                        len_inventory = len(inventory_list)
                        for i in range(len_inventory):
                            index = index + 1 if index < len_inventory - 1 else 0  

                            while self._item.type != inventory_list[index].name: 
                                index = index + 1 if index < len_inventory -1 else 0 
                            if index == self._inventory_id:
                                break 
                            if inventory_list[index]._max_capacity != inventory_list[index]._cur_capacity:
                                break
                            else: 
                                for row in inventory_list[index]._cells:
                                    for cell in row:
                                        if cell._item.name == self._item.name and cell._item.stackable: 
                                            if cell._item.count + self._item.count <= inventory_list[index]._stack_limit:
                                                break
                        
                        temp = self._item 
                        self._item = None 

                        inventory_list[index].add_item(temp)
                        cursor.set_cooldown()

                    elif cursor.pressed[0]:
                        cursor.item = self._item
                        self._item = None 
                        cursor.set_cooldown()
                    elif cursor.pressed[1] and self._item.count > 1:
                        half = self._item.count //2 
                        cursor.item = self._item.copy() 
                        cursor.item.count = half 
                        self._item.count = self._item.count - half

                        cursor.set_cooldown()
                    else: 
                        if cursor.cooldown != 0:
                            return 
                        if cursor.item.type != self._type: 
                            return 
                        if cursor.pressed[0] and cursor.item.name == self._item.name and \
                            self._item.count + cursor.item.count <= stack_limit and self._item.stackable: 
                            self._item.count = self._item.count + cursor.item.count 
                            cursor.item = None 
                            cursor.set_cooldown()
                        elif cursor.pressed[0] and cursor.item.name == self._item.name and self._item.stackable: 
                            amount = stack_limit - self._item.count
                            self._item.count = self._item.count + amount 
                            cursor.item.count = cursor.item.count - amount 

                            cursor.set_cooldown()
                        elif cursor.pressed[0]:
                            temp = cursor.item.copy()
                            cursor.item = self._item 
                            self._item = temp 

                            cursor.set_cooldown()
            
            elif cursor.item is not None and cursor.box.colliderect(self._rect) and cursor.cooldown ==0:
                if self._item.type != cursor.item.type: 
                    return 
                if cursor.pressed[0]:
                    self._item = cursor.item 
                    cursor.item = None 
                    cursor.set_cooldown()

                elif cursor.pressed[1] and cursor.item.stackable: 
                    if cursor.item.count > 1:
                        half = cursor.item.count //2
                        self._item = cursor.item.copy() 

                        self._item.count = half 
                        cursor.item.count = cursor.item.count - half 
                    else: 
                        self._item = cursor.item 
                        cursor.item = None 
                    cursor.set_cooldown 
                        
                        

class WeaponCellData:
    def __init__(self,pos,size,item = None):
        self._pos = pos
        self._hovered  = False 
        self._offset = (0,0)
        self._size = size 
        self._item = item 

        self._rect = Rect(*self._pos,*self._size)

    def update(self,stack_limit,inventory_list,cursor,opacity,player):
        if cursor.box.colliderect(self._rect):
            self._offset = (-1,-1)
            self._hovered = True 
        else: 
            self._offset = (0,0)
            self._hovered = True 

        if opacity == 255:
            if self._item is not None: 
                if not self._hovered:
                    return
                if cursor.cooldown != 0:
                    return 
                if cursor.magnet and cursor.item.name == self._item.name and self._item.stackable: 
                    if not (cursor.item.type == self._type):
                        return 
                    
                    amount = stack_limit - cursor.item.count
                    if self._item.count + cursor.item.count <= stack_limit:
                        cursor.item.count = cursor.item.count + self._item.count
                        self._item = None 
                    else: 
                        cursor.item.count = cursor._item.count + amount 
                        self._item.count = self._item.count - amount
                    
                    cursor.set_cooldown()
                
                if cursor.item is None: 
                    cursor.text = (self._item.get_name(),self._item.get_description())
                    if cursor.pressed[0] and cursor.move:
                        temp = self._item 
                        self._item = None 

                        

                
        

class Inventory:
    def __init__(self,name,rows,columns,x,y,cell_dim,space_between_cells,stack_limit,expandable = False):
        self._ind = 0
        self._name = name
        self._rows = rows 
        self._columns = columns
        self._topleft = [x,y]
        self._cell_dim = cell_dim
        self._cells =  []
        self._space_between_cells = space_between_cells

        self._stack_limit = stack_limit
        self._max_capacity = rows * columns
        self._cur_capacity = 0
        self._cur_opacity= 255
        #TODO: need to account for space between cells 
        self._size = (self._columns * self._cell_dim[0] + ((self._space_between_cells * (self._columns-1)) if self._columns > 1 else 0),
                      self._rows * self._cell_dim[1] + ((self._space_between_cells * (self._rows-1)) if self._rows > 1 else 0))
        self._rect = Rect(*self._topleft,*self._size)
        self._expandable =  expandable

        self._done_open = 0
        self._offset = 0

        #TODO: if the inventory is a weapons inventory, also create a weapon linked list. 



    @property
    def done_open(self):
        return self._done_open

    @property 
    def topleft(self):
        return self._topleft

    @property
    def name(self):
        return self._name

    @property   
    def expandable(self):
        return self._expandable

    @property
    def cur_opacity(self):
        return self._cur_opacity
    
    @property
    def size(self):
        return self._size

    @property 
    def ind(self):

        return self._ind
    
    def set_ind(self,ind:int):
        self._ind = ind

        for i in range(self._rows):
            new_row = []
            for j in range(self._columns):
                topleft = (self._topleft[0] + (j * self._cell_dim[0]) + ((self._space_between_cells * (j)) if j >0 else 0), 
                           self._topleft[1] + (i * self._cell_dim[1]) + ((self._space_between_cells * (i)) if i >0 else 0))
                new_row.append(Cell(i*self._columns+ j,topleft,self._cell_dim,self._ind,self._name))
            self._cells.append(new_row)


    def add_item(self,item) -> None:
        if self._cur_capacity == self._max_capacity: 
            return True  
        for row in self._cells:
            for cell in row:
                if cell._item is None:
                    cell._item = item
                    return False
                elif item.stackable and cell._item.name == item.name:
                    if cell._item.count+ item.count <= self._stack_limit:
                        cell._item.count = cell._item.count+ item.count
                        return False
                    elif self._stack_limit - cell._item.count> 0:
                        amount = self._stack_limit - cell._item.count
                        cell._item.count = cell._item.count + amount
                        item.count = item.count- amount
                        
                        if item.count> 0:
                            self.add_item(item.copy())
                        return False


    def remove_current_item(self):
        pass 


    def update(self, inventory_list, cursor,inven_open_state):
        inven_active = ( not self._expandable ) or (self._expandable and inven_open_state)

        interacting = False

        if inven_active:

            interacting  = self._rect.colliderect(cursor.box)

            self._done_open = min(5,self._done_open +1)
        else:
            self._done_open = max(0,self._done_open -1)
        
        self._cur_opacity = 255 * (self._done_open/5)
        self._offset = self._cell_dim[1] * (self._done_open/5)


        for i, row in enumerate(self._cells):
            for j, cell in enumerate(row):
                cell.update(self._stack_limit,inventory_list,cursor,self._cur_capacity)
                                 

            
        return interacting
        
        

class WeaponInventory(Inventory):
    def __init__(self, rows, columns, x, y, cell_dim, space_between_cells, stack_limit, expandable=False):
        super().__init__('weapon', rows, columns, x, y, cell_dim, space_between_cells, stack_limit, expandable)

    
    def set_ind(self,ind:int):
        self._ind = ind 
        self._weapons_list = WeaponInvenList()
        for i in range(self._rows):
            for j in range(self._columns):
                topleft = (self._topleft[0] + (j * self._cell_dim[0]) + ((self._space_between_cells * (j)) if j >0 else 0), 
                           self._topleft[1] + (i * self._cell_dim[1]) + ((self._space_between_cells * (i)) if i >0 else 0))
                self._weapons_list.add_node(i * self._columns + j, (topleft,self._cell_dim))


    def update(self,cursor,inven_open_state,player):
        inven_active = ( not self._expandable ) or (self._expandable and inven_open_state)
        
        interacting = False

        if inven_active:
            interacting = self._rect.colliderect(cursor.box)
            self._done_open = min(5,self._done_open +1)
        
        else: 
            self._done_open = max(0,self._done_open -1) 
        self._cur_opacity= 255 * (self._done_open /5)
        self._offset = self._cell_dim[1] * (self._done_open/5)
        
        self._weapons_list.update(self._stack_limit,cursor,self._cur_opacity,player)
        
        return interacting


class Inventory_Engine: 
    def __init__(self,inven_list,player):
        self._inventory_list = inven_list 
        for i, inventory in enumerate(self._inventory_list):
            inventory.set_ind(i)
        self._player = player

    def update(self,cursor,inven_open_state):

        interacting = False 

        for inventory in self._inventory_list:
            if inventory._name == 'item':
                interact_check = inventory.update(self._inventory_list,cursor,inven_open_state)
            else: 
                interact_check =inventory.update(cursor,inven_open_state,self._player)
            interacting = interact_check or interacting 

        cursor.interacting = interacting 



