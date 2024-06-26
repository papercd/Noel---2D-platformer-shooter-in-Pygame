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