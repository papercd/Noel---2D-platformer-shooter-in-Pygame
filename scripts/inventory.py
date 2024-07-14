from pygame.locals import *
import pygame
import random 
from scripts.utils import load_images,load_image
from scripts.alphabet import alphabets,new_alphabets
import os 

WEAPON_CELL = load_image("ui/inventory/weapon_tile.png",background="transparent")  
WEAPON_CELL_SELECTED = load_image("ui/inventory/weapon_tile_selected.png",background="transparent") 

CELL = load_image("ui/inventory/tile.png",background="transparent")
CELL_SELECTED = load_image("ui/inventory/tile_selected.png",background="transparent")
BIN_CELL = load_image("ui/inventory/tile_bin.jpg",background="transparent")
BIN_CELL_SELECTED = load_image("ui/inventory/tile_bin_selected.jpg",background="transparent")
Bounding_boxes = {
    "item" : load_image("ui/inventory/expanded_inven_bounding_box.png",background="transparent"),
    "weapon" : load_image("ui/inventory/expanded_weapon_bounding_box.png",background="transparent"),

}

CURSOR_ICONS = {
    "cursor": load_image("ui/inventory/cursor.png",background='transparent'),
    "grab": load_image("ui/inventory/cursor_grab.png",background='transparent'),
    "magnet": load_image("ui/inventory/cursor_magnet.png",background='transparent'),
    "move": load_image("ui/inventory/cursor_move.png",background='transparent'),
    "text": load_image("ui/inventory/cursor_text.png",background='transparent'),           # Added cursor text icon
}


ITEM_TEXTURES = {
    "grass": load_image("items/grass.png",background = "transparent"),
    "string": load_image("items/string.png",background = "transparent"),
    "silver_arrow": load_image("items/silver_arrow.png",background = "transparent"),
    "amethyst_clump": load_image("items/amethyst_clump.png",background = "transparent"),
    "iron_bar": load_image("items/iron_bar.png",background = "transparent"),
    "silver_bar": load_image("items/silver_bar.png",background = "transparent"),
    "gold_bar": load_image("items/gold_bar.png",background = "transparent"),
    "stick": load_image("items/stick.png",background = "transparent"),
    "diamond_clump": load_image("items/diamond_clump.png",background = "transparent"),
    "bone": load_image("items/bone.png",background = "transparent"),
    "flint": load_image("items/flint.png",background = "transparent"),
    "arrow": load_image("items/arrow.png",background = "transparent"),
    "book": load_image("items/book.png",background = "transparent"),
    "gold_sword": load_image("items/gold_sword.png",background = "transparent"),
    "iron_sword": load_image("items/iron_sword.png",background = "transparent"),
    "bow": load_image("items/bow.png",background = "transparent"),
    "gold_bow": load_image("items/gold_bow.png",background = "transparent"),
    "scythe": load_image("items/scythe.png",background = "transparent"),
    "poison": load_image("items/poison.png",background = "transparent"),
    "poison_arrow": load_image("items/poison_arrow.png",background = "transparent"),
    "health_potion": load_image("items/health_potion.png",background = "transparent"),
    "bronze_bar": load_image("items/bronze_bar.png",background = "transparent"),
    "bronze_sword": load_image("items/bronze_sword.png",background = "transparent"),
    "glass": load_image("items/glass.png",background = "transparent"),
    "glass_bottle": load_image("items/glass_bottle.png",background = "transparent"),
    "paper": load_image("items/paper.png",background = "transparent"),
    "rose": load_image("items/rose.png",background = "transparent"),
    "daisy": load_image("items/daisy.png",background = "transparent"),
    "amethyst_arrow": load_image("items/amethyst_arrow.png",background = "transparent"),
    "feather": load_image("items/feather.png",background = "transparent"),
    "bone_arrow": load_image("items/bone_arrow.png",background = "transparent"),
}

ITEMS = {
    "grass": {"name": "Grass", "description": "It's some grass."},
    "string": {"name": "String", "description": ""},
    "silver_arrow": {"name": "Silver Arrow", "description": "A stronger arrow made from silver. Suitable for hunting the supernatural."},
    "amethyst_clump": {"name": "Amethyst Clump", "description": ""},
    "iron_bar": {"name": "Iron Bar", "description": ""},
    "silver_bar": {"name": "Silver Bar", "description": ""},
    "gold_bar": {"name": "Gold Bar", "description": ""},
    "stick": {"name": "Stick", "description": ""},
    "diamond_clump": {"name": "Diamond Clump", "description": ""},
    "bone": {"name": "Bone", "description": ""},
    "flint": {"name": "Flint", "description": ""},
    "arrow": {"name": "Arrow", "description": ""},
    "book": {"name": "Book", "description": ""},
    "poison": {"name": "Poison", "description": ""},
    "poison_arrow": {"name": "Poison Arrow", "description": ""},
    "health_potion": {"name": "Health Potion", "description": ""},
    "bronze_bar": {"name": "Bronze Bar", "description": ""},
    "glass": {"name": "Glass", "description": ""},
    "glass_bottle": {"name": "Glass Bottle", "description": ""},
    "paper": {"name": "Paper", "description": ""},
    "rose": {"name": "Rose", "description": ""},
    "daisy": {"name": "Daisy", "description": ""},
    "amethyst_arrow": {"name": "Amethyst Arrow", "description": ""},
    "feather": {"name": "Feather", "description": ""},
    "bone_arrow": {"name": "Bone Arrow", "description": ""},
}

WEAPONS = {
    "gold_sword": {"name": "Gold Sword", "description": ""},
    "iron_sword": {"name": "Iron Sword", "description": ""},
    "bow": {"name": "Bone Arrow", "description": ""},
    "gold_bow": {"name": "Gold Bow", "description": ""},
    "scythe": {"name": "Scythe", "description": "Used for farming and combat!"},
    "bronze_sword": {"name": "Bronze Sword", "description": ""},

}

FONT = {
    "16": pygame.font.Font("data/fonts/DTM-Sans.otf", 16),
    "24": pygame.font.Font("data/fonts/DTM-Sans.otf", 10)
}



INVENTORY_SORTING_BUTTONS = {
    "name": load_image("ui/inventory/sort_name.jpg",background="transparent"),
    "amount": load_image("ui/inventory/sort_amount.jpg",background="transparent"),
    "type": load_image("ui/inventory/sort_type.jpg",background="transparent"),
    "select": load_image("ui/inventory/sort_select.png",background="transparent"),

}

# Search Bar assets (Made temporarily for visual purposes)

SEARCH_BAR = {
    "left": load_image("ui/inventory/search_left.png",background="transparent"),
    "middle": load_image("ui/inventory/search_middle.png",background="transparent"),
    "right": load_image("ui/inventory/search_right.png",background="transparent"),
}

SEARCH_BAR_SELECTED = {
    "left": load_image("ui/inventory/search_sel_left.png",background="transparent"),
    "middle": load_image("ui/inventory/search_sel_middle.png",background="transparent"),
    "right": load_image("ui/inventory/search_sel_right.png",background="transparent"),
}



DUST = load_images("ui/inventory/dust",background="transparent")


class Dust():
    def __init__(self) -> None:
        self.life = 20
        self.image = None
        self.scale = None

    def update(self, x, y, scale) -> None:
        self.life -= 1
        self.scale = scale
        if self.life > 0:
            self.image = pygame.transform.scale(
                DUST[5 - (self.life // 4)], (16 * scale, 16 * scale))
            

    def render(self,x,y,surf,offset=(0,0)):
        surf.blit(self.image,(x + 2 * self.scale - offset[0], y + 2 * self.scale- offset[1]))

class Cursor_Context_Box():
    def __init__(self, name, description, flip) -> None:
        self.name = name
        self.description = description
        self.flip = flip

    def update(self, x, y, surf,scale) -> None:
        #update and render together in one function 

        footer = False
        height = 0.55 * 20 * scale
        width = 4 * 20 * scale
        offset = {"x": 0, "y": 0}

        if x > surf.get_width() - width:
            offset["x"] = -width

        if y > surf.get_height() - height:
            offset["y"] = -height

        desc = [""]
        line = 0

        words = self.description.split(' ')
        if len(words) > 1:
            height += 0.26 * 20 * scale
            footer = True

        for i, word in enumerate(words):
            if not len(word) + len(desc[line]) > 30:
                desc[line] += (" " if i != 0 else "") + word
            else:
                desc.append("")
                line += 1
                desc[line] += word
                height += 0.26 * 20 * scale

        if footer:
            height += 0.2 * 20 * scale

        pygame.draw.rect(
            surf, (255, 255, 255), (x+12 + offset["x"], y+12 + offset["y"], width, height))
        pygame.draw.rect(
            surf, (31, 31, 31), (x+15 + offset["x"], y+15 + offset["y"], width - 6, height - 6))

        inventory_title = FONT["24"].render(
            self.name, 1, (255, 255, 255))
        surf.blit(inventory_title,
                 (x + 7 * 3 + offset["x"], y + 4 * 3 + offset["y"]))

        line = 0
        for d in desc:
            description = FONT["16"].render(d, 1, (180, 180, 180))
            surf.blit(description, (x + 7 * 3 + offset["x"],
                     y + 1.5 * 20 + 4 * 3 + line * 5 + offset["y"]))
            line += 3



class Cursor():
    def __init__(self) -> None:
        self.item = None
        self.position = pygame.mouse.get_pos()
        self.box = pygame.Rect(*self.position, 1, 1)
        self.cooldown = 0
        self.pressed = None
        self.magnet = False
        self.move = False
        self.text = False
        self.context = None

    def update(self, surf, keys, search_bar_pos, search_bar_scale) -> None:
        self.position = pygame.mouse.get_pos()
        self.box = pygame.Rect(*self.position, 1, 1)
        self.pressed = pygame.mouse.get_pressed()

        if self.item is not None:
            self.item.draw(*self.position, 3)
        if self.cooldown > 0:
            self.cooldown -= 1

        search_box = pygame.Rect(search_bar_pos[0], search_bar_pos[1] + 16 * search_bar_scale, 21 * 20 * search_bar_scale, 20 * search_bar_scale)
        self.text = self.box.colliderect(search_box)                # Colliding with search box changes cursor to text
        self.magnet = keys[K_LSHIFT] and self.item is not None
        self.move = keys[K_LSHIFT] and not self.magnet

        if self.context is not None:
            self.context.update(*self.position, 3)
            self.context = None

        if self.magnet:
            image = pygame.transform.scale(
                CURSOR_ICONS["magnet"], (9 * 3, 10 * 3))
        elif self.move:
            image = pygame.transform.scale(
                CURSOR_ICONS["move"], (9 * 3, 10 * 3))
        elif self.item is not None:
            image = pygame.transform.scale(
                CURSOR_ICONS["grab"], (9 * 3, 10 * 3))
        elif self.text:
            image = pygame.transform.scale(
                CURSOR_ICONS["text"], (9 * 3, 10 * 3))          # Added cursor text icon
        else:
            image = pygame.transform.scale(
                CURSOR_ICONS["cursor"], (9 * 3, 10 * 3))

        surf.blit(image, (self.position[0], self.position[1]))

    def set_cooldown(self) -> None:
        self.cooldown = 10


class Item():
    def __init__(self, name, amount) -> None:
        self.name = name
        self.amount = amount
        self.stackable = True
        self.type = "item"

    def draw(self, x, y, surf, scale) -> None:
        image = pygame.transform.scale(
            ITEM_TEXTURES[self.name], (16 * scale, 16 * scale))
        if self.amount > 1:
            image2 = pygame.transform.rotate(image, 10)
            surf.blit(image2, (x + 3 *
                              scale, y))
        if self.amount > 24:
            image2 = pygame.transform.rotate(image, -20)
            surf.blit(image2, (x + 1 *
                              scale, y))
        if self.amount > 50:
            image2 = pygame.transform.rotate(image, 30)
            surf.blit(image2, (x - 2 *
                              scale, y - 1 * scale))

        surf.blit(image, (x + 2 * scale, y + 2 * scale))

        if self.amount > 1:
            item_count = FONT["24"].render(
                str(self.amount), 1, (255, 255, 255))
            surf.blit(item_count, (x + 12 * scale, y + 10 * scale))

    def copy(self):
        return Item(self.name, self.amount)

    def get_name(self):
        return ITEMS[self.name]["name"]

    def get_description(self):
        return ITEMS[self.name]["description"]


class Weapon(Item):
    def __init__(self, name, amount) -> None:
        super().__init__(name, amount)
        self.stackable = False
        self.type = "weapon"

    def copy(self):
        return Weapon(self.name, self.amount)

    def get_name(self):
        return WEAPONS[self.name]["name"]

    def get_description(self):
        return WEAPONS[self.name]["description"]


class Cell():

    def __init__(self,ind,type = None, item=None) -> None:
        self.ind = ind
        self.item = item
        self.type = type
        self.particles = []

    def draw(self, scale, selected):
        match selected:
            case 3: 
                image = WEAPON_CELL_SELECTED
            case 2: 
                image = WEAPON_CELL
            case 1:
                image = CELL_SELECTED
                """
                image = pygame.transform.scale(
                    CELL_SELECTED, (20 * scale +2, 20 * scale+2))
                """
            case 0:
                image = pygame.transform.scale(CELL, (20 * scale, 20 * scale))
        
        return image

    def update(self, x, y,surf, scale, stack_limit, inventory_id, inventory_list, cursor,expanded,opacity,player) -> None:
        position =[x, y]


        cell_box = pygame.Rect(
            *position, 20 * scale, 20 * scale) if self.type == "item" else pygame.Rect(*position, 38 * scale, 18 * scale)

        if cursor.box.colliderect(cell_box): 
            position[0] -= 1
            position[1] -= 1
            if self.type== "weapon": image = self.draw(scale,3)
            else: image = self.draw(scale, 1)
        else:
            if self.type == "weapon" : image = self.draw(scale,2)

            else: image = self.draw(scale, 0)

        image.set_alpha(opacity)
        surf.blit(image, position)

        if len(self.particles) > 0:
            for p in self.particles:
                p.update(x, y, scale)
                if p.life < 1:
                    self.particles.remove(p)

        
        if self.type == 'weapon':
            bool = player.changing_done == 0
        else: 
            bool = True 

        if not expanded or (expanded and opacity == 255):  
            
            if self.item is not None:
                
                self.item.draw(*position,surf, scale)
           
                if bool: 
                    if not cursor.box.colliderect(cell_box):
                        return
                    
                    if cursor.cooldown != 0:
                        return
                    
                    

                    if cursor.magnet and cursor.item.name == self.item.name and self.item.stackable:
                        if not (cursor.item.type == self.type ):
                            return
                        amount = stack_limit - cursor.item.amount
                        if self.item.amount + cursor.item.amount <= stack_limit:
                            cursor.item.amount += self.item.amount
                            self.item = None
                        else:
                            cursor.item.amount += amount
                            self.item.amount -= amount

                        self.particles.append(Dust())
                        cursor.set_cooldown()

                    if cursor.item is None:
                        cursor.context = Cursor_Context_Box(
                            self.item.get_name(), self.item.get_description(), 0 if True else 1)
                        if cursor.pressed[0] and cursor.move:
                            index = inventory_id
                            for i in range(len(inventory_list)):
                                
                                index = index + \
                                    1 if index < len(inventory_list) - 1 else 0
                                while self.item.type != inventory_list[index][1].name: index = index +1 if index < len(inventory_list) -1 else 0
                                if index == inventory_id:
                                    break
                                if inventory_list[index][1].capacity != inventory_list[index][1].item_count:
                                    break
                                else:
                                    for row in inventory_list[index][1].cells:
                                        for cell in row: 
                                            if cell.item.name == self.item.name and cell.item.stackable:
                                                if cell.item.amount + self.item.amount <= inventory_list[index][1].stack_limit:
                                                    break
                            
                                                                
                                    
                            temp = self.item
                            self.item = None

                            if self.type == 'weapon':
                                
                                player.weapon_inven.delete_node(player.weapon_inven.find_node(self.ind))
                                player.equip()
                            
                        
                            inventory_list[index][1].add_item(temp)
                        


                            self.particles.append(Dust())
                            cursor.set_cooldown()

                        elif cursor.pressed[0]:
                            cursor.item = self.item
                            self.item = None
                            if self.type == 'weapon':
                                
                                player.weapon_inven.delete_node(player.weapon_inven.find_node(self.ind))
                                player.equip()
                            self.particles.append(Dust())
                            cursor.set_cooldown()
                        elif cursor.pressed[2] and self.item.amount > 1:
                            half = self.item.amount // 2
                            cursor.item = self.item.copy()
                            cursor.item.amount = half
                            self.item.amount -= half
                            self.particles.append(Dust())
                            cursor.set_cooldown()
                    else:
                        if cursor.cooldown != 0:
                            return
                        if cursor.pressed[0] and cursor.item.name == self.item.name and self.item.amount + cursor.item.amount <= stack_limit and self.item.stackable:
                            if not (cursor.item.type == self.type ):
                                return
                            self.item.amount += cursor.item.amount
                            cursor.item = None
                            self.particles.append(Dust())
                            cursor.set_cooldown()
                        elif cursor.pressed[0] and cursor.item.name == self.item.name and self.item.stackable:
                            if not (cursor.item.type == self.type ):
                                return
                            amount = stack_limit - self.item.amount
                            self.item.amount += amount
                            cursor.item.amount -= amount
                            self.particles.append(Dust())
                            cursor.set_cooldown()

                        elif cursor.pressed[0]:
                            if not (cursor.item.type == self.type ):
                                return
                            temp = cursor.item.copy()

                            
                            cursor.item = self.item
                            
                        
                            self.item = temp

                            if self.type == 'weapon':
                                
                                
                                #temp.sprite = pygame.transform.flip(temp.sprite,True,False)
                                corres_node = player.weapon_inven.find_node(self.ind)
                                corres_node.weapon = temp
                                player.equip()

                            self.particles.append(Dust())
                            cursor.set_cooldown()

            elif cursor.item is not None and cursor.box.colliderect(cell_box) and cursor.cooldown == 0:
                if bool: 
                    if cursor.pressed[0]:
                        if not (cursor.item.type == self.type ):
                                return
                        self.item = cursor.item

                        if self.type == 'weapon':
                        
                            player.weapon_inven.add_weapon(self.ind,cursor.item)
                            player.equip()

                        cursor.item = None
                        self.particles.append(Dust())
                        cursor.set_cooldown()
                    elif cursor.pressed[2] and cursor.item.stackable:
                        if not (cursor.item.type == self.type ):
                                return
                        if cursor.item.amount > 1:
                            half = cursor.item.amount // 2
                            self.item = cursor.item.copy()
                            self.item.amount = half
                            cursor.item.amount -= half
                        else:
                            self.item = cursor.item
                            cursor.item = None

                        self.particles.append(Dust())
                        cursor.set_cooldown()



class Bin(Cell):
    def __init__(self, item=None) -> None:
        super().__init__(item)

    def draw(self, scale, selected):
        match selected:
            case 1:
                image = pygame.transform.scale(
                    BIN_CELL_SELECTED, (20 * scale, 20 * scale))
            case 0:
                image = pygame.transform.scale(
                    BIN_CELL, (20 * scale, 20 * scale))
        return image


class Inventory():
    class Inventory_Sorting_Button():
        def __init__(self, name, inv) -> None:
            self.name = name
            self.image = INVENTORY_SORTING_BUTTONS[name]
            self.parent = inv
            

        def update(self, x, y, surf,scale, cursor) -> None:
            image = pygame.transform.scale(
                self.image, (10 * scale, 10 * scale))
            surf.blit(image, (x, y))

            button_box = pygame.Rect(
                x, y, 10 * scale, 10 * scale)
            if cursor.box.colliderect(button_box):
                image = pygame.transform.scale(
                    INVENTORY_SORTING_BUTTONS["select"], (10 * scale, 10 * scale))
                surf.blit(image, (x, y))
                if cursor.pressed[0]:
                    self.parent.sort_item_name()
                    match self.name:
                        case "name":
                            self.parent.sort_item_name()
                        case "amount":
                            self.parent.sort_item_amount()
                        case "type":
                            self.parent.sort_item_type()

    def __init__(self, name, rows, columns, x, y, scale=3, stack_limit=99, sorting_active=True, bin_active=False ,player = None) -> None:

        

        self.name = name
        self.inven_name_display = new_alphabets(self.name +'s')

        self.player = player 
        self.done_open = 0
        self.rows = rows
        self.columns = columns
        self.cells = [[Cell(i,self.name) for i in range(columns)] for j in range(rows)]
        self.position = [x, y]
        self.scale = scale
        self.stack_limit = stack_limit
        self.capacity = rows * columns 
        self.item_count = 0
        self.bin = bin_active
        self.box_size = (self.columns * 28 * self.scale + 2 * self.scale, self.rows * 22 * self.scale + 2 * self.scale ) if self.name == 'item' else \
                        (self.columns * 41* self.scale + 2 * self.scale, self.rows * 14 * self.scale + 2 * self.scale)

        self.rect = pygame.Rect(self.position[0] ,self.position[1] + 16* self.scale,*self.box_size) 



        if self.capacity >= 6 and self.columns >= 3 and sorting_active:
            self.buttons = [
                self.Inventory_Sorting_Button(x, self) for x in list(INVENTORY_SORTING_BUTTONS.keys()) if x != "select"
            ]
        else:
            self.buttons = []


    def update_player_weapons(self):
        filtered = [cell[0].item for cell in self.cells if cell[0].item is not None]
        self.player.weapon_inven = filtered 


    def add_item(self, item) -> None:

        for row in self.cells:
            for cell in row:
                if cell.item is None:
                    cell.item = item
                    if cell.type == 'weapon':
                        
                        self.player.weapon_inven.add_weapon(cell.ind,cell.item)
                        self.player.equip()

                    return
                elif item.stackable and cell.item.name == item.name:
                    if cell.item.amount + item.amount <= self.stack_limit:
                        cell.item.amount += item.amount
                        return
                    elif self.stack_limit - cell.item.amount > 0:
                        amount = self.stack_limit - cell.item.amount
                        cell.item.amount += amount
                        item.amount -= amount
                        if item.amount > 0:
                            self.add_item(item.copy())
                        return

    def get_item_list(self) -> list:
        item_list = []
        for row in self.cells:
            for cell in row:
                if cell.item is not None:
                    item_list.append(cell.item.copy())
        return item_list

    def get_item_count(self) -> int:
        item_count = 0
        for row in self.cells:
            for cell in row:
                if cell.item is not None:
                    item_count += 1
        return item_count

    def clear_inventory(self) -> None:
        for row in self.cells:
            for cell in row:
                cell.item = None

    def sort_item_name(self) -> None:
        item_list = self.get_item_list()
        item_list.sort(key=lambda x: x.name)
        self.clear_inventory()
        for item in item_list:
            self.add_item(item)

    def sort_item_amount(self) -> None:
        item_list = self.get_item_list()
        item_list.sort(key=lambda x: x.amount)
        self.clear_inventory()
        for item in item_list:
            self.add_item(item)

    def sort_item_type(self) -> None:
        item_list = self.get_item_list()
        item_list.sort(key=lambda x: self.get_type_sort_key(x.type))
        self.clear_inventory()
        for item in item_list:
            self.add_item(item)

    def get_type_sort_key(self, type) -> int:
        match type:
            case "weapon":
                return 1
            case "item":
                return 2

    def update(self, surf,inventory_id, inventory_list, cursor, text, expanded = False, closing = False) -> None:
        
        
        
         
        interacting = self.rect.colliderect(cursor.box) 
        
        self.item_count = self.get_item_count()
        cur_opacity = 255

        if expanded: 
            if closing:
                interacting = False
                self.done_open = max(0,self.done_open-1) 
            else:
                self.done_open = min(4,self.done_open +1)
        
            cur_opacity =  255* (self.done_open/4 )# a function of the current state, which is self.done_open
                                                   # the bounding box of the inventory is going to be blitted with an opacity that is a function of the self.done_open value. 

            offset = 10  * (self.done_open/4)




            image = Bounding_boxes[self.name]
            image.set_alpha(cur_opacity)

        
            surf.blit(image,(self.position[0]-1,self.position[1] -10+ offset+13*self.scale))

            #render name display 
            self.inven_name_display.render(surf,self.position[0]-1,self.position[1] +3,opacity=cur_opacity)

            """+ offset+13*self.scale """
            """
            pygame.draw.rect(
                surf, (31, 31, 31,cur_opacity), (*self.position,self.box_size[0],self.box_size[1]),border_radius= 2)
            """
        """
        inventory_title = FONT["24"].render(
            self.name, 1, (255, 255, 255))
        surf.blit(inventory_title,
                 (self.position[0] + 4 * self.scale, self.position[1] + 4 * self.scale))
        """
        """
        for i, b in enumerate(self.buttons):
            b.update(self.position[0] + 20 * self.columns *
                     self.scale - 9 * self.scale - i * 12 * self.scale, self.position[1] + 4 * self.scale,surf, self.scale, cursor)
        
        """


        for i, row in enumerate(self.cells):
            for j, cell in enumerate(row):
                cell.update(self.position[0] + (j * (28 if self.name == "item" else 42) * self.scale) + 2 * self.scale,
                            self.position[1] + (i * (22 if self.name == "item" else 18) * self.scale) + 16 * self.scale,surf, self.scale, self.stack_limit, inventory_id, inventory_list, cursor,expanded,cur_opacity,self.player)

            
             
                            
        """
        bin_cell = Bin()
        if self.bin:
            bin_cell.update(self.position[0] + ((len(self.cells[0]) - 1) * 20 * self.scale) + 2 * self.scale,
                            self.position[1] + (len(self.cells) * 20 * self.scale) + 16 * self.scale, surf,self.scale, self.stack_limit, inventory_id, inventory_list, cursor)
                        """

        # search shading and highlighting red (graphics not fully implemented but just the POC here)
        if text != "":
            for i, row in enumerate(self.cells):
                for j, cell in enumerate(row):
                    if cell.item is not None and text in cell.item.name:
                        pygame.draw.rect(
                            surf, (255, 0, 0), (self.position[0] + (j * 20 * self.scale) + 2 * self.scale,
                                               self.position[1] + (i * 20 * self.scale) + 16 * self.scale, 4 * self.scale, 4 * self.scale))
                    else:
                        shade = pygame.Surface((16 * self.scale, 16 * self.scale))
                        shade.set_alpha(128)
                        shade.fill((0, 0, 0))
                        surf.blit(shade,
                                 (self.position[0] + (j * 20 * self.scale) + 2 * self.scale + 2 * self.scale, self.position[1] + (i * 20 * self.scale) + 16 * self.scale + 2 * self.scale))
                        
        #if the inventory is a weapon inventory, 
        
        return interacting



class Inventory_Engine():
    def __init__(self, inventory_list) -> None:
        self.inventory_list = inventory_list

    def update(self,surf, cursor, closing, text) -> None:
       
        interacting = False
        for i, inventory in enumerate(self.inventory_list):
            
            check = inventory[1].update(surf,i, self.inventory_list, cursor, text,inventory[0],closing)
            interacting = check or interacting 

        cursor.interacting =  interacting



       

# Search bar class *Xini

class Search_Bar():
    def __init__(self, width, x, y, scale=3) -> None:
        self.width = width
        self.position = (x, y)
        self.scale = scale
        self.clicked = 0
        self.blink = 0
        self.text_pos = 0
        self.text = ""
    
    def draw(self, selected):
        images = [pygame.Surface] * self.width
        match selected:
            case 1:
                for i in range(self.width):
                    if i == 0:
                        images[i] = pygame.transform.scale(SEARCH_BAR_SELECTED["left"], (20 * self.scale, 20 * self.scale))
                    elif i == self.width - 1:
                        images[i] = pygame.transform.scale(SEARCH_BAR_SELECTED["right"], (20 * self.scale, 20 * self.scale))
                    else:
                        images[i] = pygame.transform.scale(SEARCH_BAR_SELECTED["middle"], (20 * self.scale, 20 * self.scale))
            case 0:
                for i in range(self.width):
                    if i == 0:
                        images[i] = pygame.transform.scale(SEARCH_BAR["left"], (20 * self.scale, 20 * self.scale))
                    elif i == self.width - 1:
                        images[i] = pygame.transform.scale(SEARCH_BAR["right"], (20 * self.scale, 20 * self.scale))
                    else:
                        images[i] = pygame.transform.scale(SEARCH_BAR["middle"], (20 * self.scale, 20 * self.scale))
        return images
    
    def update(self,surf, cursor) -> None:
        pygame.draw.rect(
            surf, (31, 31, 31), (*self.position, self.width * 20 * self.scale + 4 * self.scale, 20 * self.scale + 18 * self.scale))

        search_bar_title = FONT["24"].render(
            "Search:", 1, (255, 255, 255))
        surf.blit(search_bar_title, (self.position[0] + 4 * self.scale, self.position[1] + 4 * self.scale))

        search_box = pygame.Rect(
            self.position[0], self.position[1] + 16 * self.scale, self.width * 20 * self.scale, 20 * self.scale)

        if cursor.box.colliderect(search_box):
            images = self.draw(1)
        else:
            images = self.draw(0)

        for i in range(len(images)):
            surf.blit(images[i], (self.position[0] + (i * 20 * self.scale) + 2 * self.scale, self.position[1] + 16 * self.scale))
        
        text = FONT["24"].render(
            self.text, 1, (255, 255, 255))
        surf.blit(text, (self.position[0] + 4 * self.scale + 3 * self.scale, self.position[1] + 16 * self.scale + 4 * self.scale, 4 * self.scale, self.scale))

        if self.blink == 60:
            self.blink = 0
        elif self.blink > 30:
            self.blink += 1
        elif self.clicked == 1:
            pygame.draw.rect(
                surf, (255, 255, 255), (self.position[0] + 4 * self.scale + 3 * self.scale + self.text_pos * 4 * self.scale, self.position[1] + 16 * self.scale + 13 * self.scale, 4 * self.scale, self.scale))
            self.blink += 1

        if cursor.pressed is None:
            self.clicked = 0
        elif cursor.box.colliderect(search_box) and cursor.pressed[0]:
            self.clicked = 1
        elif cursor.pressed[0]:
            self.clicked = 0
    
    def handle_event(self, event) -> None:
        if self.clicked == 1:
            if event.key == pygame.K_BACKSPACE:
                if self.text_pos > 0:
                    self.text_pos -= 1
                    self.text = self.text[:-1]
            else:
                self.text_pos += 1
                self.text += event.unicode