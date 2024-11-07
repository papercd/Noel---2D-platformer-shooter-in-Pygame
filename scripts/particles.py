import pygame
import random 
import math 

class Particle: 
    def __init__(self,game, p_type, pos, source,velocity = [0,0], frame = 0):
        self.game = game 
        self.type = p_type
        self.pos = list(pos)
        self.velocity = velocity
        self.animation = self.game.general_sprites['particle/' + p_type].copy()
        self.animation.frame = frame
        self.source = source 

  
            

    def update(self):
        kill = False 
        if self.animation.done: 
            kill = True 
        
        self.pos[0] += self.velocity[0]
        self.pos[1] += self.velocity[1]

        self.animation.update()

        return kill 
    
    def render(self,surf, offset= (0,0)):
        img = self.animation.img()
        surf.blit(img, (self.pos[0]-offset[0]-img.get_width()//2,self.pos[1]- offset[1]-img.get_height()//2))

class glass():
    def __init__(self,pos,size,speed,angle,idle_time):
        self.size = size
        self.pos = pos
        self.angle =angle 
        self.speed =speed 
        self.velocity = self.calculate_initial_velocity() 
        self.dead = False 
        self.frames_flown = 0
        self.idle_time = idle_time
        self.size_shaping_seed = (random.random(),random.random())
        self.base_vertices = self.generate_convex_vertices()

    def generate_convex_vertices(self):
        # Create a set of vertices in a convex shape around (0, 0)
        num_points = random.randint(5, 7)  # Number of points for the polygon
        vertices = []
        angle_step = 2 * math.pi / num_points

        for i in range(num_points):
            # Slightly randomize angle and radius while keeping the points in circular order
            angle = i * angle_step + random.uniform(-0.1, 0.1)
            radius = self.size * (0.7 + random.uniform(0, 0.3) * self.size_shaping_seed[0])
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            vertices.append((x, y))

        # Sort vertices by angle to ensure convexity
        vertices.sort(key=lambda point: math.atan2(point[1], point[0]))
        return vertices
    
    def get_rotated_vertices(self):
        # Rotate each vertex around the shard's center by its current angle
        cos_theta = math.cos(self.angle)
        sin_theta = math.sin(self.angle)
        rotated_vertices = []
        for x, y in self.base_vertices:
            # Apply rotation
            rotated_x = x * cos_theta - y * sin_theta
            rotated_y = x * sin_theta + y * cos_theta
            # Translate to the shard's position
            rotated_vertices.append((rotated_x + self.pos[0], rotated_y + self.pos[1]))
        return rotated_vertices
        

    def velocity_adjust(self):
        friction = random.uniform(0.44,0.46)
        self.velocity[0] *= friction  
            
    def calculate_initial_velocity(self):
        return [math.cos(self.angle) * self.speed , math.sin(self.angle) * self.speed ]


    def update(self,tilemap,dt):

        self.frames_flown += 1
        if self.frames_flown > 50: 
            self.dead = True 
            return True 
        
        self.pos[0] += self.velocity[0] 
        tile_loc = (int(self.pos[0])//tilemap.tile_size,int(self.pos[1])//tilemap.tile_size)
        key = f"{tile_loc[0]};{tile_loc[1]}" 
        if  key in tilemap.tilemap:
            
            tile = tilemap.tilemap[key]
            if tile.type == 'lights':
                pass
            elif tile.type.split('_')[1] == 'stairs' and tile.variant.split(';')[0] in ['0', '1']:
                check_rects = [pygame.Rect(tile_loc[0], tile_loc[1] + tilemap.tile_size + 4, tilemap.tile_size, 4),
                                pygame.Rect(tile_loc[0] + 12, tile_loc[1], 4, 12),
                                pygame.Rect(tile_loc[0] + 6, tile_loc[1] + 6, 6, 6)] if tile.variant.split(';')[0] == '0' else \
                                [pygame.Rect(tile_loc[0], tile_loc[1] + tilemap.tile_size + 4, tilemap.tile_size, 4),
                                pygame.Rect(tile_loc[0], tile_loc[1], 4, 12),
                                pygame.Rect(tile_loc[0] + 4, tile_loc[1] + 6, 6, 6)]
                for check_rect in check_rects:
                    if check_rect.collidepoint(self.pos): 
                        if self.velocity[0] <0 :
                            self.pos[0] =  check_rect.right
                        else:
                            self.pos[0] =  check_rect.left
                        self.velocity[0] = - self.velocity[0] * 0.5 

                        #self.dead = True 
                        #return True
            else: 
                if self.velocity[0] <0 :
                    self.pos[0] =  tile_loc[0] * tilemap.tile_size + tilemap.tile_size
                else:
                    self.pos[0] =  tile_loc[0] * tilemap.tile_size - 1
                self.velocity[0] = - self.velocity[0] *0.5
                #self.dead = True 
                #return True
        
        self.velocity[1] = min(5,self.velocity[1] +0.26)
        self.pos[1] += self.velocity[1] 
        tile_loc = (int(self.pos[0])//tilemap.tile_size,int(self.pos[1])//tilemap.tile_size)
        key = f"{tile_loc[0]};{tile_loc[1]}" 
        
        if  key in tilemap.tilemap:
            tile = tilemap.tilemap[key]
            if tile.type == 'lights':
                pass
            elif tile.type.split('_')[1] == 'stairs' and tile.variant.split(';')[0] in ['0', '1']:
                check_rects = [pygame.Rect(tile_loc[0], tile_loc[1] + tilemap.tile_size + 4, tilemap.tile_size, 4),
                                pygame.Rect(tile_loc[0] + 12, tile_loc[1], 4, 12),
                                pygame.Rect(tile_loc[0] + 6, tile_loc[1] + 6, 6, 6)] if tile.variant.split(';')[0] == '0' else \
                                [pygame.Rect(tile_loc[0], tile_loc[1] + tilemap.tile_size + 4, tilemap.tile_size, 4),
                                pygame.Rect(tile_loc[0], tile_loc[1], 4, 12),
                                pygame.Rect(tile_loc[0] + 4, tile_loc[1] + 6, 6, 6)]
                for check_rect in check_rects:
                    if check_rect.collidepoint(self.pos): 
                        if self.velocity[0] <0 :
                            self.pos[1] =  check_rect.bottom
                        else:
                            self.pos[1] =  check_rect.top
                        self.velocity_adjust()
                        self.velocity[1] = -self.velocity[1] * 0.5
                    
            else:
                if self.velocity[1] <0 :
                    self.pos[1] =  tile_loc[1]* tilemap.tile_size + tilemap.tile_size
                else:
                    self.pos[1] =  tile_loc[1]* tilemap.tile_size - 1
                self.velocity[1] = - self.velocity[1] * 0.5
                self.velocity_adjust()
       







    def render(self, surf, offset=(0, 0)):
        # Offset the vertices based on the camera offset
        vertices = [(x - offset[0], y - offset[1]) for x, y in self.get_rotated_vertices()]
        
        # Draw the glass shard polygon
        glass_color = (173, 216, 230, 120)  # Transparent light blue
        pygame.draw.polygon(surf, glass_color, vertices)

        # Optional: Add highlights to edges for a glass-like effect
        for i in range(len(vertices)):
            if random.random() < 0.6:
                start, end = vertices[i], vertices[(i + 1) % len(vertices)]
                pygame.draw.line(surf, (255, 255, 255, 100), start, end, 2)

      


            
class non_animated_particle():
    def __init__(self,pos,color,velocity,tilemap,life = 60):
        self.time = 0
        self.pos = pos
        self.color = color
        self.tilemap = tilemap
        self.velocity = velocity
        self.life = life 
        self.create_surf()
    
    #the default non-animated particle is a circle. 
    def create_surf(self):
        self.image = pygame.Surface((1,1)).convert_alpha()
        self.image.set_colorkey("black")
        pygame.draw.rect(self.image,self.color, pygame.Rect(0,0,1,1))
        self.rect  = self.image.get_rect()
    
   
    def update(self,dt):
        self.time +=1
        for rect_tile in self.tilemap.physics_rects_around(self.pos,(1,1)):
            if self.rect.colliderect(rect_tile[0]):
                if rect_tile[1].type == 'stairs' and  rect_tile[1].variant.split(';')[0] in ['0','1']:
                    if rect_tile[1].variant.split(';')[0] == '0':
                        #left stairs
                        #this part where check rects are created is not dynamic, so if tilesize changes this part needs to be changed manually. maybe figure out a mathematical 
                        #way to create rects. 
                        check_rects = [pygame.Rect(rect_tile[0].left,rect_tile[0].bottom + 4,rect_tile[0].width,4),
                                       pygame.Rect(rect_tile[0].left + 12,rect_tile[0].top,4,12),
                                       pygame.Rect(rect_tile[0].left + 6,rect_tile[0].top + 6,6,6)
                                       ]
                        for check_rect in check_rects:
                            if self.rect.colliderect(check_rect):
                                return True
                    else: 
                        check_rects = [pygame.Rect(rect_tile[0].left,rect_tile[0].bottom + 4,rect_tile[0].width,4),
                                       pygame.Rect(rect_tile[0].left,rect_tile[0].top,4,12),
                                       pygame.Rect(rect_tile[0].left + 4,rect_tile[0].top + 6,6,6)
                                       ]
                        for check_rect in check_rects:
                            if self.rect.colliderect(check_rect):
                                return True 
                else: 

                    return True 
        if self.time > self.life:
            return True 
       
        self.pos[0] += self.velocity[0] * dt 
        self.pos[1] += self.velocity[1] * dt 
        self.rect.topleft = self.pos 
        return False 
    
    def render(self,surf,offset = (0,0)):
        surf.blit(self.image,(self.pos[0]- offset[0],self.pos[1]-offset[1]))



class bullet_collide_particle:
    def __init__(self,size, pos, angle, speed,color,tilemap,life = 60,gravity_factor = 1):
        self.pos = list(pos)
        self.angle = angle
        self.speed = speed
        self.color = color 
        self.tilemap = tilemap
        self.time = 0
        self.velocity = [0,0]
        self.life = life
        self.size = size 
        
        self.gravity_factor= gravity_factor
        self.create_surf()
    
    def create_surf(self):
        self.image = pygame.Surface(self.size).convert_alpha()
        self.image.set_colorkey("black")
        pygame.draw.rect(self.image,self.color, pygame.Rect(0,0,self.size[0],self.size[1]))
        self.rect  = self.image.get_rect()
    

    def update(self,dt):
        self.time +=1
        self.velocity[1] = min(5,self.velocity[1] +0.20 / self.gravity_factor)

        for rect_tile in self.tilemap.physics_rects_around(self.pos,(1,1)):
            if self.rect.colliderect(rect_tile[0]):
                if rect_tile[1].type == 'stairs' and  rect_tile[1].variant.split(';')[0] in ['0','1']:
                    if rect_tile[1].variant.split(';')[0] == '0':
                        #left stairs
                        #this part where check rects are created is not dynamic, so if tilesize changes this part needs to be changed manually. maybe figure out a mathematical 
                        #way to create rects. 
                        check_rects = [pygame.Rect(rect_tile[0].left,rect_tile[0].bottom + 4,rect_tile[0].width,4),
                                       pygame.Rect(rect_tile[0].left + 12,rect_tile[0].top,4,12),
                                       pygame.Rect(rect_tile[0].left + 6,rect_tile[0].top + 6,6,6)
                                       ]
                        for check_rect in check_rects:
                            if self.rect.colliderect(check_rect):
                                return True
                    else: 
                        check_rects = [pygame.Rect(rect_tile[0].left,rect_tile[0].bottom + 4,rect_tile[0].width,4),
                                       pygame.Rect(rect_tile[0].left,rect_tile[0].top,4,12),
                                       pygame.Rect(rect_tile[0].left + 4,rect_tile[0].top + 6,6,6)
                                       ]
                        for check_rect in check_rects:
                            if self.rect.colliderect(check_rect):
                                return True 
                else: 
                    return True 
        if self.time > self.life:
            return True 
        self.pos[0] += math.cos(math.radians(self.angle)) * self.speed
        self.pos[1] += math.sin(math.radians(self.angle)) * self.speed

        self.pos[1] += self.velocity[1]

        self.rect.topleft = self.pos 
        
        self.speed = max(0, self.speed - 0.1)
        return False 
    
    def render(self, surf, offset=(0, 0)):
        surf.blit(self.image,(self.pos[0]- offset[0],self.pos[1]-offset[1]))

class bullet_trail_particle_wheelbot:
    def __init__(self,radius,decay_rate,pos,color):
        self.radius  = radius
        self.decay_rate = decay_rate
        self.pos = pos #center position 
        self.color = color
        #and there won't be a velocity. 

        
    def update(self,dt):
        self.radius -=  self.decay_rate 
        return self.radius <= 0  


    def render(self,surf,offset = (0,0)):
        pygame.draw.circle(surf,self.color,(self.pos[0]-offset[0],self.pos[1]-offset[1]),self.radius) 
    