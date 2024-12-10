


class Bar:
    def __init__(self,topleft,size,max_resource):
        self.topleft = topleft
        self.size = size
        self.max_resource = max_resource
        self.cur_resource = max_resource


class HealthBar(Bar):
    def __init__(self,topleft,size,max_hp):
        super().__init__(topleft,size,max_hp)
        self.mid_cur = self.cur_resource
        self.last_cur = self.cur_resource
        self.shake = 0 
        self.last_shake = False

    def update(self,health):
        self.shake = max(0,self.shake -1)
        health_dec = min(7,self.cur_resource - health)
        self.shake = max(health_dec,self.shake)

        self.cur_resource = health
        if int(self.mid_cur) > self.cur_resource:
            self.mid_cur -= 2*(self.mid_cur-self.cur_resource )/4
        
        if int(self.last_cur) > self.cur_resource:
            self.last_cur -= (self.last_cur-self.cur_resource )/4


class StaminaBar(Bar):
    def __init__(self,topleft,size,max_stamina):
        super().__init__(topleft,size,max_stamina)

    def update(self,stamina):
        self.cur_resource = stamina
