import pygame
import random
import time
import math

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()

# Particle class with glow effect
class Particle:
    def __init__(self, pos, spawn_time,index):
        self.pos = pos
        self.index = index
        self.start_time = spawn_time
        self.lifetime = 1.4  # Particle lifetime in seconds
        self.velocity = [random.uniform(-2, 2), random.uniform(-2, 2)]
        #self.seed = 0.32

    def update(self, current_time):
        elapsed_time = current_time - self.start_time
        if elapsed_time > self.lifetime:
            return False  # Particle should be removed

        timecycle = elapsed_time / self.lifetime
        #self.seed += timecycle + math.tan(self.seed)
        #tPos = (math.cos(self.seed), math.sin(self.seed))
        invparticles = 1.0 / 30.0  # Hardcoded particles count from shader
        #tPos = [tPos[0] * invparticles, tPos[1] * invparticles]

        self.pos[0] += self.velocity[0] 
        self.pos[1] += self.velocity[1] # Using gravity from shader

        return True

    def draw(self, surface, current_time):
        elapsed_time = current_time - self.start_time
        timecycle = elapsed_time / self.lifetime

        # Calculate base color based on the fragment shader logic
        clr = math.sin(1.4 * self.index)*(1.0 - timecycle)
        red = min(255, int(clr * 4 * 255))
        green = min(255, int(clr * 0.5 * 255))
        blue = min(255, int(clr * 0.1 * 255))

        # Draw glow effect
        glow_radius = 10  # Radius for the glow
        max_alpha = 128   # Maximum alpha for the glow

        for i in range(glow_radius, 0, -1):
            alpha = int(max_alpha * (i / glow_radius))
            color = (red, green, blue, alpha)
            print(color)
            s = pygame.Surface((i * 2, i * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, color, (i, i), i)
            surface.blit(s, (int(self.pos[0] - i), int(self.pos[1] - i)), special_flags=pygame.BLEND_RGBA_ADD)

        # Draw the main particle
        pygame.draw.circle(surface, (red, green, blue), (int(self.pos[0]), int(self.pos[1])), 5)

particles = []

# Main loop
running = True
start_time = time.time()

while running:
    current_time = time.time() - start_time
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                # Spawn 20 particles at the click position
                for _ in range(20):
                    particles.append(Particle(list(event.pos), current_time,_))

    # Update particles
    particles = [p for p in particles if p.update(current_time)]

    # Clear the screen
    screen.fill((0, 0, 0))

    # Draw particles
    for particle in particles:
        particle.draw(screen, current_time)

    # Swap buffers
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
