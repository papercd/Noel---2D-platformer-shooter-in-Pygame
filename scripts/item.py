from scripts.data import ITEM_DESCRIPTIONS

class Item:
    def __init__(self,name,count = 1,stackable = True):
        self._name = name 
        self._type = "item"
        self._rarity = "common"
        self._stackable = stackable
        if not stackable: 
            self.count = 1
        else: 
            self.count = count

    def copy(self):
        return Item(self.name,self.count,self._stackable)

    @property
    def stackable(self):
        return self._stackable

    @property 
    def type(self):
        return self._type 

    @property 
    def description(self):
        return ITEM_DESCRIPTIONS[self._name]

    @property 
    def name(self):
        return self._name


