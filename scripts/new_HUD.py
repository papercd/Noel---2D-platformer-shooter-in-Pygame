from scripts.new_entities import Player
from scripts.new_inventory import Inventory_Engine
from scripts.health import HealthBar,StaminaBar


class HUD: 
    def __init__(self,ui_atlas,player:Player,true_res:tuple[int,int]):
        self._player = player
        self._true_res = true_res
        self._ui_atlas = ui_atlas

        self._create_display_elements()



    def _create_display_elements(self):
        self._health_bar_topleft = (self._true_res[0]//12,self._true_res[1] - 64)
        self._stamina_bar_topleft = (self._true_res[0]//12,self._true_res[1] - 48)

        self._health_bar_width = self._true_res[0]//6
        self._stamina_bar_width = self._true_res[0]//6

        self._health_bar = HealthBar(*self._health_bar_topleft,self._health_bar_width,32,self._player.health)
        self._stamina_bar = StaminaBar(*self._stamina_bar_topleft,self._stamina_bar_width,32,self._player.stamina)

        self._items_engine = Inventory_Engine(self._player)


    def update(self):
        pass 