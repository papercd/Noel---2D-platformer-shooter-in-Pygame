

class Node:
    def __init__(self, cell_ind, weapon):
        self.cell_ind = cell_ind
        self.weapon = weapon
        self.next = None
        self.prev = None

    def __repr__(self):
        return f"Node(cell_ind={self.cell_ind}, weapon={self.weapon})"

class DoublyLinkedList:
    def __init__(self):
        self.head = None
        self.tail = None

    def add_weapon(self, cell_ind, weapon):
        new_node = Node(cell_ind, weapon)
        
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

    def _insert_before(self, node, new_node):
        new_node.prev = node.prev
        new_node.next = node
        if node.prev:
            node.prev.next = new_node
        node.prev = new_node

    def _insert_after(self, node, new_node):
        new_node.next = node.next
        new_node.prev = node
        if node.next:
            node.next.prev = new_node
        else:
            self.tail = new_node
        node.next = new_node

    def delete_node(self, node):
        if node is None:
            return
        if node.prev:
            node.prev.next = node.next
        if node.next:
            node.next.prev = node.prev
        if node == self.head:
            self.head = node.next
        if node == self.tail:
            self.tail = node.prev
        node.next = node.prev = None

    def change_head(self, cell_ind):
        new_head = self.find_node(cell_ind)
        if new_head:
            self.head = new_head

    def find_node(self, cell_ind):
        current = self.head
        while current:
            if current.cell_ind == cell_ind:
                return current
            current = current.next
        return None


class ambientNode:

    def __init__(self,light_range,colorValue = (255,255,255,255) , default = True):
        self.range = list(light_range)
        self.colorValue = colorValue
        self.prev = None
        self.next = None
        self.default = default
        self.hull_y_range = (0,0)
        self.hulls = []


    def return_values(self):
        return (self.range,self.colorValue,self.default)

class ambientNodeList:
    def __init__(self,default_color = (255,255,255,255)):
        # Initialize with a single default node covering the specified range
        self.default_color = default_color
        self.head =ambientNode((float('-inf'), float('inf')), colorValue=self.default_color, default=True)
    
    def find_overlapping_node(self, new_range):
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
    
    
    def create_hull_lists(self,tilemap):
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


        



    def set_ptr(self,pos_x): 
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
                data.append({'range': current.range, 'hull_range': current.hull_y_range, 'colorValue': current.colorValue})
            current = current.next 
        
        return data 


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
                                 
                         
        
        
        

         

    
    def insert_node(self, new_range, hull_range, colorValue):
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
            print(f"Range: {current.range}, Color: {current.colorValue}, Status: {default_status}")
            current = current.next
