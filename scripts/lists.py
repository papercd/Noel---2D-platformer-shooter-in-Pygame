from pygame import Rect
from numpy import uint16,uint32,int64,int32,float32
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scripts.item import Weapon
    from scripts.new_cursor import Cursor
    from scripts.new_entities import Player
    from scripts.new_tilemap import Tilemap
class Node:
    def __init__(self, cell_ind:int, data)->None:
        self.cell_ind = cell_ind
        self.data = data 
        self.next = None
        self.prev = None

    def __repr__(self):
        return f"Node(cell_ind={self.cell_ind}, data={self.data})"

class DoublyLinkedList:
    def __init__(self,objs:list= None):
        self.head = None
        self.curr_node = None 
        self.tail = None
        if objs: 
            for i,obj in enumerate(objs):
                self.add_node(i,obj)
    

    def add_node(self, cell_ind:int, data)->None:
        new_node = Node(cell_ind, data)
        
        # If the list is empty, make the new node the head and the tail
        if self.head is None:
            self.head = self.tail = new_node
            return
        
        # Compare cell_ind values and find the correct spot
        current = self.head
        while current:
            if new_node.cell_ind < current.cell_ind:
                # Insert before the current node
                self._insert_before(current, new_node)
                if current == self.head:
                    self.head = new_node
                return
            elif new_node.cell_ind > current.cell_ind:
                if current.next is None:
                    # Insert at the end of the list
                    self._insert_after(current, new_node)
                    return
            current = current.next

    def _insert_before(self, node:Node, new_node:Node)->None:
        new_node.prev = node.prev
        new_node.next = node
        if node.prev:
            node.prev.next = new_node
        node.prev = new_node

    def _insert_after(self, node:Node, new_node:Node)->None:
        new_node.next = node.next
        new_node.prev = node
        if node.next:
            node.next.prev = new_node
        else:
            self.tail = new_node
        node.next = new_node

    def delete_node(self, node:Node)->None:
        if node is None:
            return
        if node == self.curr_node: 
            if node.prev:
                self.curr_node = node.prev 
            elif node.next: 
                self.curr_node = node.next  
            else: 
                self.curr_node = None 
        if node.prev:
            node.prev.next = node.next
        if node.next:
            node.next.prev = node.prev
        if node == self.head:
            self.head = node.next
        if node == self.tail:
            self.tail = node.prev


        if node == self.curr_node:
            pass 
        node.next = node.prev = None

    def change_head(self, cell_ind:int)->None:
        new_head = self.find_node(cell_ind)
        if new_head:
            self.head = new_head

    def find_node(self, cell_ind:int)->Node:
        current = self.head
        while current:
            if current.cell_ind == cell_ind:
                return current
            current = current.next
        return None


class WeaponInvenList(DoublyLinkedList):
    def __init__(self, inven_ind:uint16,objs = None)->None:
        super().__init__(objs)

        self._inventory_id = inven_ind
        self._type = 'weapon'

    
    @property 
    def inventory_id(self)->uint16:
        return self._inventory_id

    def add_weapon(self,weapon:"Weapon",on_inven_item_change_callback:"function",on_current_weapon_change_callback:"function")->None:
        current = self.head 
        while current:
           if current.weapon is None:
                current.weapon =weapon 
                
                if not (self.curr_node and self.curr_node.weapon):
                    self.curr_node = current 
                    on_current_weapon_change_callback(None,current)

                on_inven_item_change_callback(current)
                return 
           current = current.next 
        

        
    def add_node(self,cell_ind:int,data)->None:
        new_node = WeaponNode(self,cell_ind,*data)

        if self.head is None:
            self.head = self.tail = new_node
            return 
        
        current = self.head
        while current:
            if new_node._cell_ind < current._cell_ind:
                self._insert_before(current,new_node)
                if current == self.head:
                    self.head = new_node
                return 
            elif new_node._cell_ind > current._cell_ind:
                if current.next is None:
                    self._insert_after(current,new_node)
                    return 
            current = current.next

    def change_weapon(self,scroll:int,on_current_weapon_change_callback:"function")-> None:
        current = self.curr_node
        if scroll > 0:
            while current: 
                if current.next: 
                    if current.next.weapon: 
                        on_current_weapon_change_callback(self.curr_node,current.next)
                        self.curr_node = current.next
                        break
                    current = current.next 
                else: 
                    break 
        else: 
            while current: 
                if current.prev: 
                    if current.prev.weapon: 
                        on_current_weapon_change_callback(self.curr_node,current.prev)
                        self.curr_node = current.prev
                        break
                    current = current.prev
                else: 
                    break 


    def update(self,stack_limit:int,cursor:"Cursor",inven_open_state:bool,on_inven_item_change_callback:"function",
               on_current_weapon_change_callback:"function",on_cursor_item_change_callback:"function")->None:
        
        current = self.head
        interacting = False

        while current:
            current_interact = current.update(stack_limit,cursor,inven_open_state,on_inven_item_change_callback,
                                              on_current_weapon_change_callback,on_cursor_item_change_callback)
            interacting = current_interact or interacting
            current = current.next

        return interacting

class WeaponNode:
    def __init__(self,list:WeaponInvenList,cell_ind:int32,pos:tuple[int64,int64],size:tuple[uint32,uint32])->None:
        self.list = list 
        self._cell_ind = cell_ind 
        self._pos = pos 
        self._hovered = False 
        self._size = size 
        self._rect = Rect(*self._pos, *self._size)

        self.next = None 
        self.prev = None 
        self.weapon= None
    @property 
    def ind(self)->int: 
        return self._cell_ind
    
    @property 
    def hovered(self) ->bool: 
        return self._hovered


    def update_current_node(self)->None: 
        left,right = self.check_nearest_node_with_item()
        if left: 
            self.list.curr_node = left
        elif right: 
            self.list.curr_node = right 
        else: 
            self.list.curr_node = None 

    def check_nearest_node_with_item(self)->None:
        right_current = self 
        left_current = self 
        right_node = None 
        left_node = None 
        while right_current:
            if right_current.next: 
                if right_current.next.weapon: 
                    right_node = right_current.next
                    break
                right_current = right_current.next 
            else: 
                break

        while left_current.prev: 
            if left_current.prev: 
                if left_current.prev.weapon: 
                    left_node = left_current.prev 
                    break 
                left_current = left_current.prev 
            else: 
                break

        return (left_node,right_node)
    

    
    def update(self,stack_limit:int,cursor:"Cursor",inven_open_state:bool,on_inven_item_add_callback:"function",
               on_current_weapon_change_callback:"function",on_cursor_item_change_callback:"function")->None:
            
            if cursor.box.colliderect(self._rect):
                self._hovered = True 
                cursor.ref_hovered_cell = self
            else: 
                self._hovered = False

            if inven_open_state:
                if self.weapon is not None:
                    if not self._hovered:
                        return 
                    if cursor.cooldown > 0:
                        return
                    if cursor.magnet and cursor.item.name == self.weapon.name and self.weapon.stackable:
                        # this part actually never gets called as weapon inventory items are always not stackable. 
                        if not (cursor.item.type == self._type):
                            return
                        amount = stack_limit - cursor.item.count[0]
                        if self.weapon.count[0] + cursor.item.count[0] <= stack_limit:
                            cursor.item.count[0] = cursor.item.count[0] + self.weapon.count[0]
                            self.weapon= None 

                            on_inven_item_add_callback(self)
                        else: 
                            cursor.item.count[0] = cursor.item.count[0] + amount 
                            self.weapon.count[0] = self.weapon.count[0] - amount
                        cursor.set_cooldown()
                    if cursor.item is None:
                        if self._hovered:
                            cursor.text = (self.weapon.name,self.weapon.description)
                        if cursor.pressed[0] and cursor.move:
                            temp = self.weapon 
                            self.weapon = None 

                            if self.ind == self.list.curr_node.ind:
                                self.update_current_node()
                                on_current_weapon_change_callback(self,self.list.curr_node)

                            on_inven_item_add_callback(self)
                            self.list.add_weapon(temp,on_inven_item_add_callback,on_current_weapon_change_callback)
                            cursor.set_cooldown()

                        elif cursor.pressed[0]:
                            cursor.item = self.weapon 
                            self.weapon = None 
                            cursor.set_cooldown()

                            if self.ind == self.list.curr_node.ind: 
                                self.update_current_node()
                                on_current_weapon_change_callback(self,self.list.curr_node)

                            on_inven_item_add_callback(self)
                            on_cursor_item_change_callback()

                        elif cursor.pressed[1] and self.weapon.count[0] > uint16(1):
                            half = self.weapon.count[0] >> 1
                            cursor.item = self.weapon.copy()
                            cursor.item.count[0] = half 
                            self.weapon.count[0] = self.weapon.count[0] - half 
                            cursor.set_cooldown()
                        else: 
                            # this part seems off, unneeded maybe. 
                            if cursor.cooldown != 0:
                                return 
                            if cursor.pressed[0] and cursor.item.name == self.weapon.name and self.weapon.count[0] + cursor.item.count[0] <= stack_limit and self.weapon.stackable:
                                self.weapon.count[0] = self.weapon.count[0] + cursor.item.count[0]
                                cursor.item = None 
                                cursor.set_cooldown()
                                on_cursor_item_change_callback()
                            elif cursor.pressed[0] and cursor.item.name == self.weapon.name and self.weapon.stackable :
                                amount = stack_limit - self.weapon.count[0]
                                self.weapon.count[0] = self.weapon.count[0] + amount 
                                cursor.item.count[0] = cursor.item.count[0] - amount 
                                cursor.set_cooldown()
                            elif cursor.pressed[0]:
                                temp = cursor.item.copy()
                                cursor.item = self.weapon 
                                self.weapon = temp 

                                cursor.set_cooldown()

                                on_inven_item_add_callback(self)
                                on_cursor_item_change_callback()

                    elif cursor.item is not None and cursor.item.type == "weapon"\
                          and self._hovered and cursor.cooldown <= float32(0):
                        if cursor.pressed[0] :
                            temp = cursor.item.copy()
                            cursor.item = self.weapon
                            self.weapon = temp

                            cursor.set_cooldown()
                            on_inven_item_add_callback(self)
                            on_cursor_item_change_callback()

                elif cursor.item is not None and self._hovered and cursor.cooldown <= float32(0):
                    if cursor.item.type != self.list._type:
                        return
                    if cursor.pressed[0]:
                        self.weapon = cursor.item 
                        cursor.item = None 
                        
                        if not self.list.curr_node:
                            self.list.curr_node = self 
                            on_current_weapon_change_callback(None,self)

                        cursor.set_cooldown()

                        on_inven_item_add_callback(self)
                        on_cursor_item_change_callback()

                    elif cursor.pressed[1] and cursor.item.stackable:
                        if cursor.item.count[0] > uint16(1):
                            half = cursor.item.count >> 1
                            self.weapon = cursor.item.copy()
                            self.weapon.count[0] = half 
                            cursor.item.count[0] = cursor.item.count[0] - half 
                        else: 
                            self.weapon = cursor.item 
                            cursor.item = None 

                            if not self.list.curr_node:
                                self.list.curr_node = self 
                                on_current_weapon_change_callback(None,self)

                            on_inven_item_add_callback(self)
                            on_cursor_item_change_callback()
                        cursor.set_cooldown()

            return self.hovered


class Category(Node):
    def __init__(self, cell_ind:int, category:str)->None:
        self._selected = False 
        self._hovered = False 
        self._characters = len(category)
        self._calculate_length_height(category)
        super().__init__(cell_ind, category)
    
    def _calculate_length_height(self,category:str)->None:
        self._length = 0 
        max_height = 0 
        for char in category: 
            ord_val = ord(char)
            if 48 <= ord_val <= 57:
                pass
                #dim =  TEXT_DIMENSIONS['NUMBERS']
            elif 65 <= ord_val <= 90: 
                #dim = TEXT_DIMENSIONS['CAPITAL']
                pass
            elif 97 <= ord_val <= 122:
                pass
                #dim = TEXT_DIMENSIONS['LOWER']
            else: 
                pass
                #dim=  TEXT_DIMENSIONS["UNDERSCORE"]
            dim = (1,1)
            self._length += dim[0] 
            if dim[1] > max_height: max_height = dim[1]
        self._height = max_height

    @property
    def height(self):
        return self._height

    @property
    def hovered(self):
        return self._hovered

    @property
    def characters(self):
        return self._characters

    @property 
    def length(self):
        return self._length
class TileCategories(DoublyLinkedList):
    def __init__(self,topleft:tuple[int,int],size:tuple[int,int],objs:list[str]= None)->None:
        self._topleft = topleft
        self._size = size 
        super().__init__(objs)


    @property
    def size(self):
        return self._size 

    @property 
    def topleft(self):
        return self._topleft

    
    def add_node(self, cell_ind:int, category:str)->None:
        new_node = Category(cell_ind, category)
        
        # If the list is empty, make the new node the head and the tail
        if self.head is None:
            self.head = self.tail = new_node
            self.curr_node = new_node
            return
        
        # Compare cell_ind values and find the correct spot
        current = self.head
        while current:
            if new_node.cell_ind < current.cell_ind:
                # Insert before the current node
                self._insert_before(current, new_node)
                if current == self.head:
                    self.head = new_node
                self.curr_node = new_node
                return
            elif new_node.cell_ind > current.cell_ind:
                if current.next is None:
                    # Insert at the end of the list
                    self._insert_after(current, new_node)
                    self.curr_node = new_node
                    return
            current = current.next
    
    def check_hover(self,cursor:"Cursor",category_panel_scroll:int = 0,tile_panel_scroll:int = 0)->None:
        curr:Category = self.head
        category_stack_offset = 0 
        while curr: 
                
            if cursor.box.colliderect(Rect(self._topleft[0],self._topleft[1]-category_panel_scroll+ category_stack_offset,
                                           curr.length, curr.height)):
                curr._hovered = True 
            else: 
                curr._hovered = False 
            
            category_stack_offset += curr.height +1 
            curr = curr.next
    
    def check_click(self,cursor:"Cursor",category_panel_scroll:int = 0,tile_panel_scroll:int = 0)->None:
        curr: Category = self.head 
        category_stack_offset = 0
        while curr: 
            if cursor.box.colliderect(Rect(self._topleft[0],self._topleft[1]-category_panel_scroll+ category_stack_offset, 
                                           curr.length, curr.height)):
                self.curr_node._selected = False 
                curr._selected = True 
                self.curr_node = curr 
                break 

            category_stack_offset += curr.height + 1 
            curr = curr.next 

class ambientNode:

    def __init__(self,light_range,colorValue :tuple[int,int,int,int]= (255,255,255,255) , \
                 default:bool = True):
        self.range = list(light_range)
        self.colorValue = colorValue
        self.prev = None
        self.next = None
        self.default = default
        self.hull_y_range = (0,0)
        self.hulls = []

    def return_values(self):
        return (self.range,self.colorValue,self.default)



class interpolatedLightNode:
    def __init__(self,light_range, left_bound_colorValue:tuple[int,int,int,int]= (255,255,255,255)\
                 , right_bound_colorValue:tuple[int,int,int,int] = (255,255,255,255)):
        self.range = list(light_range)
        self.leftBoundColor = left_bound_colorValue
        self.rightBoundColor = right_bound_colorValue
        self.prev = None
        self.next = None
        self.default = False 
        self.hull_y_range = (0,0)
        self.hulls = []

    def get_interpolated_RGBA(self, pos:tuple[int,int])->tuple[int,int,int,int]:
        # Ensure position is within the range
        if not (self.range[0] <= pos <= self.range[1]):
            raise ValueError("Position out of bounds.")

        # Calculate the interpolation factor (0 at the left bound, 1 at the right bound)
        t = (pos - self.range[0]) / (self.range[1] - self.range[0])

        # Interpolate each color component
        r = int(self.leftBoundColor[0] + t * (self.rightBoundColor[0] - self.leftBoundColor[0]))
        g = int(self.leftBoundColor[1] + t * (self.rightBoundColor[1] - self.leftBoundColor[1]))
        b = int(self.leftBoundColor[2] + t * (self.rightBoundColor[2] - self.leftBoundColor[2]))
        a = int(self.leftBoundColor[3] + t * (self.rightBoundColor[3] - self.leftBoundColor[3]))

        return (r, g, b, a) 
    
    def return_values(self):
        return (self.range,self.leftBoundColor,self.rightBoundColor,self.default)

class ambientNodeList:
    def __init__(self,default_color:tuple[int,int,int,int] = (255,255,255,255))->None:
        # Initialize with a single default node covering the specified range
        self.default_color = default_color
        self.head =ambientNode((float('-inf'), float('inf')), colorValue=self.default_color, default=True)
    
    def find_overlapping_node(self, new_range)->ambientNode:
        current = self.head
        
        # Traverse to the leftmost node
        while current.prev:
            current = current.prev
        
        # Check for overlap while moving right
        while current:
            if not current.default and current.range[0] <= new_range[0] and current.range[1] >= new_range[1]:
                return current
            current = current.next
        
        return None
    
    
    def create_hull_lists(self,tilemap:"Tilemap"):
        # Iterate over the nodes, and create the hull lists. 
        current = self.head 

        # Traverse to the leftmost node
        while current.prev:
            current = current.prev

        while current: 
            if not current.default: 
                for x in range(int(current.range[0] // tilemap.tile_size),int(current.range[1] // tilemap.tile_size) ):
                    for y in range(int(current.hull_y_range[0] // tilemap.tile_size),int(current.hull_y_range[1] // tilemap.tile_size)):
                        key = f"{x};{y}"
                        if key in tilemap.tilemap and not tilemap.tilemap[key].enclosed and tilemap.tilemap[key].hull: 
                            tile = tilemap.tilemap[key]
                            for hull in tile.hull: 
                                current.hulls.append(hull)
            current = current.next 


        



    def get_node_at_pos(self,pos_x:int)->ambientNode: 
        temp = self.head
        while pos_x < temp.range[0] or pos_x > temp.range[1]:
            if pos_x <temp.range[0] :
                temp = temp.prev
            else: 
                temp = temp.next 

        return temp

    def json_seriable(self):
        data = []
        current = self.head 
        while current.prev: 
            current = current.prev 
        
        while current: 
            if not current.default: 
                if isinstance(current,interpolatedLightNode):
                    data.append({'range': current.range, 'hull_range': current.hull_y_range, 'leftColorValue': current.leftBoundColor,'rightColorValue': current.rightBoundColor})
                else: 
                    data.append({'range': current.range, 'hull_range': current.hull_y_range, 'colorValue': current.colorValue})
            current = current.next 
        
        return data 
    

    def find_node(self,x:int)->ambientNode:
        current = self.head
        
        while current.prev:
            current=  current.prev 

        while current: 
            if current.range[0] <= x <= current.range[1]:
                return current 
            current = current.next 

        
        
        return None  


    def change_node_color(self,x):
        pass 


    def delete_node(self, x,cur_node_ptr):
        current = self.head 
        while current.prev: 
            current = current.prev 

        while current: 
            if x < current.range[0]:
                print("No non-default node found.")
                return 
            if x < current.range[1]:
                if not current.default: 
                    # then we delete it here.
                    AMBIENT_NODE_NEIGHBOR = {(False, False) : 0, (False, True):1 , (True, False):2,  (True, True) :3}

                    case_  = AMBIENT_NODE_NEIGHBOR[(current.prev.default,current.next.default)]
                    
                    match case_:
                        case 0: 
                            # when the prev and next nodes are both non-default nodes, simply change the color and state to default ones. 
                            current.colorValue = self.default_color
                            current.default = True
                            cur_node_ptr = self.set_ptr((cur_node_ptr.range[1] + cur_node_ptr.range[0]) //2)
                            return True
                        case 1:
                            # when one of them is a default-node, we expand the range of the default-node. 
                            temp = current.next
                            temp.range = (current.range[0],temp.range[1])
                            #temp.range[0] = current.range[0]
                            temp.prev = current.prev 
                            current.prev.next = temp 
                            self.head = temp 
                            del current  

                            cur_node_ptr = self.set_ptr((cur_node_ptr.range[1] + cur_node_ptr.range[0]) //2)
                            return True
                        case 2: 
                            temp = current.prev 
                            temp.range  = (temp.range[0],current.range[1])
                            #temp.range[1] = current.range[1]
                            temp.next = current.next 
                            current.next.prev = temp 
                            self.head = temp 
                            del current 

                            cur_node_ptr = self.set_ptr((cur_node_ptr.range[1] + cur_node_ptr.range[0]) //2)
                            return True
                        case 3: 
                            # when both are default nodes, we merge them into one default node. 
                            if current.next.next: 
                                temp = current.prev 
                                temp.range = (temp.range[0],current.next.range[1])
                                #temp.range[1] = current.next.range[1] 
                                temp.next = current.next.next
                                current.next.next.prev = temp  
                                
                                self.head = temp
                                del current 
                                del current.next

                                cur_node_ptr = self.set_ptr((cur_node_ptr.range[1] + cur_node_ptr.range[0]) //2) 
                                return True
                            else: 
                                temp = current.prev
                                temp.range = (temp.range[0],current.next.range[1])
                                #temp.range[1] = current.next.range[1] 
                                temp.next = None  
                                self.head = temp
                                del current 
                                del current.next 

                                cur_node_ptr = self.set_ptr((cur_node_ptr.range[1] + cur_node_ptr.range[0]) //2)
                                return True
            else: 
                current = current.next

        return False
                                 
                         
        
    def insert_interpolated_ambient_node(self, new_range, hull_range, left_colorValue, right_colorValue):
        overlapping_node = self.find_overlapping_node(new_range)
        if overlapping_node:
            print("Range overlaps with an existing non-default node. Please enter a different range.")
            return False

        current = self.head

        # Traverse to the correct insertion point
        while current.prev and current.range[0] > new_range[0]:
            current = current.prev

        while current.next and current.range[0] < new_range[0]:
            current = current.next

        new_node = interpolatedLightNode(new_range, left_bound_colorValue=left_colorValue, right_bound_colorValue=right_colorValue)
        new_node.hull_y_range = hull_range

        # Adjust default node ranges and insert the new node
        if current.default:
            if new_range[0] <= current.range[0]:
                new_node.next = current
                new_node.prev = current.prev
                if current.prev:
                    current.prev.next = new_node
                else:
                    self.head = new_node
                current.prev = new_node
            else:
                new_node.next = current.next
                new_node.prev = current
                if current.next:
                    current.next.prev = new_node
                current.next = new_node

            self.update_default_nodes()
            return True

        new_node.next = current.next
        new_node.prev = current
        if current.next:
            current.next.prev = new_node
        current.next = new_node

        self.update_default_nodes()
        return True

        


    
    def insert_ambient_node(self, new_range, hull_range, colorValue):
        overlapping_node = self.find_overlapping_node(new_range)
        if overlapping_node:
            print("Range overlaps with an existing non-default node. Please enter a different range.")
            return False
        
        current = self.head
        
        # Traverse to the correct insertion point
        while current.prev and current.range[0] > new_range[0]:
            current = current.prev
        
        while current.next and current.range[0] < new_range[0]:
            current = current.next
        
        new_node = ambientNode(new_range, colorValue, default=False)
        new_node.hull_y_range = hull_range


        # Adjust default node ranges and insert the new node
        if current.default:
            if new_range[0] <= current.range[0]:
                new_node.next = current
                new_node.prev = current.prev
                if current.prev:
                    current.prev.next = new_node
                else:
                    self.head = new_node
                current.prev = new_node
            else:
                new_node.next = current.next
                new_node.prev = current
                if current.next:
                    current.next.prev = new_node
                current.next = new_node
            
            self.update_default_nodes()
            return True
        
        new_node.next = current.next
        new_node.prev = current
        if current.next:
            current.next.prev = new_node
        current.next = new_node
        
        self.update_default_nodes()
        return True
    
    def update_default_colors(self,color_value):
        self.default_color = color_value
        current = self.head
        while current.prev: 
            current = current.prev 

        while current:
            if current.default: 
                current.colorValue = self.default_color
            if current.next:
                current = current.next
            else: break
                
    
    def update_default_nodes(self):
        current = self.head
        
        # Traverse to the leftmost node
        while current.prev:
            current = current.prev
        
        prev_end = float('-inf')
        
        while current:
            if current.default:
                if current.next:
                    next_start = current.next.range[0]
                    current.range = (prev_end, next_start)
                else:
                    current.range = (prev_end, float('inf'))
            prev_end = current.range[1]
            current = current.next
        
        # Insert default nodes in gaps
        current = self.head
        while current and current.next:
            if not current.default and current.range[1] < current.next.range[0]:
                new_default_node = ambientNode((current.range[1], current.next.range[0]), colorValue=self.default_color, default=True)
                new_default_node.prev = current
                new_default_node.next = current.next
                current.next.prev = new_default_node
                current.next = new_default_node
            current = current.next
        
        # Handle the case where the last node is non-default and we need a default node after it
        if not current.default:
            new_default_node = ambientNode((current.range[1], float('inf')), colorValue=self.default_color, default=True)
            new_default_node.prev = current
            current.next = new_default_node
        
        # Handle the case where the first node is non-default and we need a default node before it
        current = self.head
        while current.prev:
            current = current.prev
        if not current.default and current.range[0] > float('-inf'):
            new_default_node = ambientNode((float('-inf'), current.range[0]), colorValue=self.default_color, default=True)
            new_default_node.next = current
            current.prev = new_default_node
            self.head = new_default_node
    
    def print_list(self):
        # Move to the leftmost node
        current = self.head
        while current.prev:
            current = current.prev
        
        while current:
            default_status = "Default" if current.default else "Non-Default"
            if isinstance(current,interpolatedLightNode):
                print(f"Range: {current.range}, leftBoundColor: {current.leftBoundColor},\
                       rightBoundColor: {current.rightBoundColor},Status: {default_status}")
            else:
                print(f"Range: {current.range}, colorValue: {current.colorValue},\
                       ,Status: {default_status}")

            current = current.next
