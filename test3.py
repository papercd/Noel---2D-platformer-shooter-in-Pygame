import pygame
import numpy as np
import random
from noise import snoise2  # You may need to install noise via pip

# Constants
WIDTH, HEIGHT = 800, 600
GRID_SIZE = 100  # Size of the grid for smoke simulation
SMOKE_PARTICLE_COUNT = 500  # Number of smoke particles
NOISE_SCALE = 0.1  # Scale of the noise function

# Smoke Class
class Smoke:
    def __init__(self):
        self.particles = []
        self.density_grid = np.zeros((GRID_SIZE, GRID_SIZE))

    def emit(self, pos):
        for _ in range(SMOKE_PARTICLE_COUNT):
            # Create particles with a position near the emit position
            x_offset = random.uniform(-5, 5)
            y_offset = random.uniform(-5, -1)  # Emit particles upwards
            self.particles.append(pygame.Vector2(pos[0] + x_offset, pos[1] + y_offset))

    def update(self):
        self.density_grid.fill(0)  # Reset the density grid

        for particle in self.particles[:]:
            # Calculate grid position
            grid_x = int(particle.x / (WIDTH / GRID_SIZE))
            grid_y = int(particle.y / (HEIGHT / GRID_SIZE))

            # Update the density at the grid position
            if 0 <= grid_x < GRID_SIZE and 0 <= grid_y < GRID_SIZE:
                self.density_grid[grid_x, grid_y] += 1  # Increase density

            # Move particles upwards and add random movement
            particle.y -= random.uniform(0.5, 1.0)  # Move upwards
            particle.x += random.uniform(-0.5, 0.5)  # Drift

            # Remove particles that go off screen
            if particle.y < 0:
                self.particles.remove(particle)

        # Apply noise to the density grid
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                noise_value = snoise2(i * NOISE_SCALE, j * NOISE_SCALE, octaves=1)
                self.density_grid[i, j] += noise_value * 5  # Adjust strength

    def draw(self, surface):
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                alpha = min(int(self.density_grid[i, j]), 255)
                if alpha > 0:
                    color = (200, 200, 200, alpha)
                    pygame.draw.circle(surface, color, (int(i * (WIDTH / GRID_SIZE)), int(j * (HEIGHT / GRID_SIZE))), 3)

# Pygame setup
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
smoke_system = Smoke()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    screen.fill((0, 0, 0))  # Clear screen

    # Emit smoke at a random position
    if random.random() < 0.05:  # Control emission rate
        smoke_system.emit((random.randint(200, 600), 550))

    smoke_system.update()
    smoke_system.draw(screen)

    pygame.display.flip()
    clock.tick(60)  # Limit to 60 FPS

pygame.quit()
