import random 

class Cloud:
    def __init__(self,pos,sprite,speed,depth,direction,transparency = 120):
        self.pos = list(pos)
        self.speed = speed 
        self.depth = depth 
        self.transparency = transparency
        self.sprite = sprite
        self.sprite.set_alpha(self.transparency)
        self.direction = direction 

    def update(self):
        if self.direction == 'right':
            self.pos[0] += self.speed  
        if self.direction == 'left':
            self.pos[0] -= self.speed 

    def render(self, surf, offset = (0,0)):
        render_pos  = (self.pos[0] - offset[0] * self.depth ,self.pos[1] - offset[1] *self.depth)
        surf.blit(self.sprite, (render_pos[0] % (surf.get_width() + self.sprite.get_width()) - self.sprite.get_width(), render_pos[1] %(surf.get_height() + self.sprite.get_height()) -self.sprite.get_height())) 

    


class Clouds: 
    def __init__(self, cloud_images, count = 16, direction = 'right'):
        self.clouds = [] 
        self.direction = direction

        for i in range(count):
            self.clouds.append(Cloud((random.random()*99999,random.random()*99999), random.choice(cloud_images),random.random()* 0.05 + 0.05, random.random()*0.6 +0.2,self.direction))
        
        self.clouds.sort(key = lambda x:x.depth)

    def update(self):
        for cloud in self.clouds: 
            cloud.update()

    def render(self, surf, offset = (0,0)):
        for cloud in self.clouds: 
            cloud.render(surf,offset=offset)