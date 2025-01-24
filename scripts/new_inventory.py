from pygame import Rect
from scripts.lists import WeaponInvenList

from typing import TYPE_CHECKING

if TYPE_CHECKING: 
    from scripts.entitiesManager import EntitiesManager
    from scripts.item import Item,Weapon 
    from scripts.new_cursor import Cursor 
    from scripts.new_entities import Player
class Inventory:
    def __init__(self,name:str,rows:int,columns:int,topleft:tuple[int,int],cell_dim:tuple[int,int]\
                    ,space_between_cells:int,stack_limit:int,expandable:bool = False):
        self._ind = 0
        self._name = name
        self._rows = rows 
        self._columns = columns
        self._topleft = topleft 
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
    def cells(self):
        return self._cells
    
    @property 
    def rows(self):
        return self._rows
    
    @property
    def columns(self):
        return self._columns

    @property
    def done_open(self)->int:
        return self._done_open

    @property 
    def topleft(self)->tuple[int,int]:
        return self._topleft

    @property
    def name(self)->str:
        return self._name

    @property   
    def expandable(self)->bool:
        return self._expandable

    @property
    def cur_opacity(self)->int:
        return self._cur_opacity
 
    @property
    def cur_capacity(self)->int:
        return self._cur_capacity

    @property 
    def max_capacity(self)->int: 
        return self._max_capacity
    
    @property
    def stack_limit(self)->int: 
        return self._stack_limit

    @property
    def size(self)->int:
        return self._size
    @property 
    def ind(self)->int:
        return self._ind
    
    def set_ind(self,ind:int)->None:
        self._ind = ind

        for i in range(self._rows):
            new_row = []
            for j in range(self._columns):
                topleft = (self._topleft[0] + (j * self._cell_dim[0]) + ((self._space_between_cells * (j)) if j >0 else 0), 
                           self._topleft[1] + (i * self._cell_dim[1]) + ((self._space_between_cells * (i)) if i >0 else 0))
                new_row.append(Cell(i*self._columns+ j,topleft,self._cell_dim,self._ind,self._name))
            self._cells.append(new_row)


    def add_item(self,item:"Item") -> None:
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

    def update(self, inventory_list, cursor:"Cursor",inven_open_state:bool,cursor_hover_state_change_callback:"function")->bool:
        inven_active = ( not self._expandable ) or (self._expandable and inven_open_state)

        interacting = False

        if inven_active:
            self._done_open = min(5,self._done_open +1)
        else:
            self._done_open = max(0,self._done_open -1)
        
        self._cur_opacity = 255 * (self._done_open/5)
        self._offset = self._cell_dim[1] * (self._done_open/5)


        for i, row in enumerate(self._cells):
            for j, cell in enumerate(row):
                cell_interact =cell.update(self._stack_limit,inventory_list,cursor,self._cur_opacity)
                interacting = cell_interact or interacting  

        if cursor.ref_hovered_cell != cursor.ref_prev_hovered_cell:
            cursor_hover_state_change_callback()
            cursor.ref_prev_hovered_cell = cursor.ref_hovered_cell
            
        return interacting
        
        

class WeaponInventory(Inventory):
    def __init__(self, rows:int, columns:int, topleft:tuple[int,int], cell_dim:tuple[int,int], \
                 space_between_cells:int, stack_limit:int, expandable:bool=False)->None:
        super().__init__('weapon', rows, columns, topleft, cell_dim, space_between_cells, stack_limit, expandable)
    
    def set_ind(self,ind:int)->None:
        self._ind = ind 
        self._weapons_list = WeaponInvenList()
        for i in range(self._rows):
            for j in range(self._columns):
                topleft = (self._topleft[0] + (j * self._cell_dim[0]) + ((self._space_between_cells * (j)) if j >0 else 0), 
                           self._topleft[1] + (i * self._cell_dim[1]) + ((self._space_between_cells * (i)) if i >0 else 0))
                self._weapons_list.add_node(i * self._columns + j, (topleft,self._cell_dim))


    @property 
    def weapons_list(self) -> "WeaponInvenList":
        return self._weapons_list

    def change_weapon(self,scroll:int)->None:
        self._weapons_list.change_weapon(scroll)


    def add_weapon(self,weapon:"Weapon") -> None:
        self._weapons_list.add_weapon(weapon)

    def remove_current_weapon(self,em:"EntitiesManager")->"Item": 
        if self._weapons_list.curr_node.weapon: 
            temp = self._weapons_list.curr_node
            weapon = self._weapons_list.curr_node.weapon

            left,right = temp.check_nearest_node_with_item()

            self._weapons_list.curr_node.weapon = None 
            if left: 
                self._weapons_list.curr_node = left
            elif right: 
                self._weapons_list.curr_node = right 

            return weapon 

    def update(self,cursor:"Cursor",inven_open_state:bool,cursor_hover_state_change_callback:"function")->bool:
        inven_active = ( not self._expandable ) or (self._expandable and inven_open_state)
        
        interacting = False

        if inven_active:
            interacting = self._rect.colliderect(cursor.box)
            self._done_open = min(5,self._done_open +1)
        
        else: 
            self._done_open = max(0,self._done_open -1) 
        self._cur_opacity= 255 * (self._done_open /5)
        self._offset = self._cell_dim[1] * (self._done_open/5)
        
        self._weapons_list.update(self._stack_limit,cursor,self._cur_opacity)
        #player.curr_weapon_node = self._weapons_list.curr_node
        return interacting


class InventoryEngine: 
    def __init__(self,inven_list:list[Inventory]):
        self._inventory_list = inven_list 
        for i, inventory in enumerate(self._inventory_list):
            inventory.set_ind(i)

    def update(self,cursor:"Cursor",inven_open_state:bool,cursor_hover_state_change_callback:"function")->None:

        interacting = False 

        for inventory in self._inventory_list:
            if inventory._name == 'item':
                interact_check = inventory.update(self._inventory_list,cursor,inven_open_state,cursor_hover_state_change_callback)
            else: 
                interact_check =inventory.update(cursor,inven_open_state,cursor_hover_state_change_callback)
            interacting = interact_check or interacting 

        if not interacting: cursor.ref_hovered_cell = None
        cursor.interacting = interacting 



class Cell:
    def __init__(self,ind:int,pos:tuple[int,int],size:tuple[int,int],\
                 inventory_id:int,type:str = None,item:"Item"= None):
        self._ind = ind 
        self._pos = pos 
        self._hovered = False 
        self._offset = (0,0)
        self._size = size
        self._item = item 
        self._type  = type 
        self._inventory_id = inventory_id

        self._rect = Rect(*self._pos,*self._size)
    
    @property
    def ind(self)->int:
        return self._ind

    @property 
    def inventory_id(self)->int: 
        return self._inventory_id

    @property
    def item(self)->"Item": 
        return self._item
    
    @property 
    def hovered(self)->bool: 
        return self._hovered

    def update(self,stack_limit:int,inventory_list:list[Inventory],cursor:"Cursor",opacity:int)->None:
        if cursor.box.colliderect(self._rect):
            self._offset = (-1,-1)
            self._hovered = True 
            cursor.ref_hovered_cell = self
        else: 
            self._offset = (0,0)
            self._hovered = False 
        
        if opacity == 255:
            if self._item is not None: 
                if not self._hovered: 
                    return 
                if cursor.cooldown > 0:
                    return 
                
                if cursor.magnet and cursor.item.name == self._item.name and self._item.stackable: 
                    if not (cursor.item.type == self._type):
                        return 
                    
                    amount = stack_limit - cursor.item.count
                    if self._item.count + cursor.item.count <= stack_limit:
                        cursor.item.count = cursor.item.count + self._item.count
                        self._item = None 
                    else: 
                        cursor.item.count = cursor.item.count + amount 
                        self._item.count = self._item.count - amount
                    
                    cursor.set_cooldown()
                
                if cursor.item is None: 
                    if self._hovered:
                        cursor.text = (self._item.name,self._item.description)
                    if cursor.pressed[0] and cursor.move:
                        index = self._inventory_id
                        len_inventory = len(inventory_list)
                        for i in range(len_inventory):
                            index = index + 1 if index < len_inventory - 1 else 0  

                            while self._item.type != inventory_list[index].name: 
                                index = index + 1 if index < len_inventory -1 else 0 
                            if index == self._inventory_id:
                                break 
                            if inventory_list[index].max_capacity != inventory_list[index].cur_capacity:
                                break
                            else: 
                                for row in inventory_list[index].cells:
                                    for cell in row:
                                        if cell.item.name == self.item.name and cell.item.stackable: 
                                            if cell.item.count + self._item.count <= inventory_list[index].stack_limit:
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
                        if cursor.cooldown > 0:
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
                elif cursor.item is not None and cursor.item.type == self._type \
                     and self._hovered and cursor.cooldown <= 0: 
                    if cursor.pressed[0] :
                        if cursor.item.name == self._item.name: 
                            if self._item.count + cursor.item.count <= stack_limit and self._item.stackable: 
                                self._item.count = self._item.count + cursor.item.count 
                                cursor.item = None 
                            elif self._item.count + cursor.item.count > stack_limit and self._item.stackable: 
                                amount = stack_limit - self._item.count 
                                self._item.count += amount 
                                cursor.item.count -= amount 
                        else: 
                            temp = cursor.item.copy()
                            cursor.item = self._item
                            self._item = temp
                        cursor.set_cooldown()
            
            elif cursor.item is not None and self._hovered and cursor.cooldown <= 0:
                if cursor.item.type != self._type:
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
        
        return self.hovered
                        
                        
                
 
