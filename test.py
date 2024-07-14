import pygame
import numpy as np

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 1000, 1000
GRID_SIZE = 100
CELL_SIZE = WIDTH // GRID_SIZE

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2D Eulerian Fluid Simulator")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Clock to control the frame rate
clock = pygame.time.Clock()

# Fluid simulation parameters
diffusion = 0.0001
viscosity = 0.0001
dt = 0.1

# Grid initialization
u = np.zeros((GRID_SIZE, GRID_SIZE))  # velocity x
v = np.zeros((GRID_SIZE, GRID_SIZE))  # velocity y
p = np.zeros((GRID_SIZE, GRID_SIZE))  # pressure
s = np.zeros((GRID_SIZE, GRID_SIZE))  # source (density)
density = np.zeros((GRID_SIZE, GRID_SIZE))  # density field

def add_source(x, s, dt):
    x += dt * s

def diffuse(b, x, x0, diff, dt):
    a = dt * diff * (GRID_SIZE - 2) * (GRID_SIZE - 2)
    for k in range(20):
        x[1:-1, 1:-1] = (x0[1:-1, 1:-1] + a * (x[2:, 1:-1] + x[:-2, 1:-1] +
                                               x[1:-1, 2:] + x[1:-1, :-2])) / (1 + 4 * a)
        set_bnd(b, x)

def advect(b, d, d0, u, v, dt):
    N = GRID_SIZE
    dt0 = dt * N
    for i in range(1, N-1):
        for j in range(1, N-1):
            x = i - dt0 * u[i, j]
            y = j - dt0 * v[i, j]
            if x < 0.5: x = 0.5
            if x > N + 0.5: x = N + 0.5
            i0 = int(x)
            i1 = i0 + 1
            if y < 0.5: y = 0.5
            if y > N + 0.5: y = N + 0.5
            j0 = int(y)
            j1 = j0 + 1
            s1 = x - i0
            s0 = 1 - s1
            t1 = y - j0
            t0 = 1 - t1
            d[i, j] = s0 * (t0 * d0[i0, j0] + t1 * d0[i0, j1]) + s1 * (t0 * d0[i1, j0] + t1 * d0[i1, j1])
    set_bnd(b, d)

def set_bnd(b, x):
    N = GRID_SIZE
    for i in range(1, N-1):
        x[0, i] = -x[1, i] if b == 1 else x[1, i]
        x[N-1, i] = -x[N-2, i] if b == 1 else x[N-2, i]
        x[i, 0] = -x[i, 1] if b == 2 else x[i, 1]
        x[i, N-1] = -x[i, N-2] if b == 2 else x[i, N-2]
    x[0, 0] = 0.5 * (x[1, 0] + x[0, 1])
    x[0, N-1] = 0.5 * (x[1, N-1] + x[0, N-2])
    x[N-1, 0] = 0.5 * (x[N-2, 0] + x[N-1, 1])
    x[N-1, N-1] = 0.5 * (x[N-2, N-1] + x[N-1, N-2])

def project(u, v, p, div):
    N = GRID_SIZE
    div[1:-1, 1:-1] = -0.5 * (u[2:, 1:-1] - u[:-2, 1:-1] +
                              v[1:-1, 2:] - v[1:-1, :-2]) / N
    p.fill(0)
    set_bnd(0, div)
    set_bnd(0, p)
    for k in range(20):
        p[1:-1, 1:-1] = (div[1:-1, 1:-1] + p[2:, 1:-1] + p[:-2, 1:-1] +
                         p[1:-1, 2:] + p[1:-1, :-2]) / 4
        set_bnd(0, p)
    u[1:-1, 1:-1] -= 0.5 * N * (p[2:, 1:-1] - p[:-2, 1:-1])
    v[1:-1, 1:-1] -= 0.5 * N * (p[1:-1, 2:] - p[1:-1, :-2])
    set_bnd(1, u)
    set_bnd(2, v)

def vel_step(u, v, u0, v0, visc, dt):
    add_source(u, u0, dt)
    add_source(v, v0, dt)
    u0, u = u, u0
    v0, v = v, v0
    diffuse(1, u, u0, visc, dt)
    diffuse(2, v, v0, visc, dt)
    project(u, v, u0, v0)
    u0, u = u, u0
    v0, v = v, v0
    advect(1, u, u0, u0, v0, dt)
    advect(2, v, v0, u0, v0, dt)
    project(u, v, u0, v0)

def density_step(x, x0, u, v, diff, dt):
    add_source(x, x0, dt)
    x0, x = x, x0
    diffuse(0, x, x0, diff, dt)
    x0, x = x, x0
    advect(0, x, x0, u, v, dt)

def draw_density(screen, density):
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            d = density[i, j]
            color = (min(255, int(d * 255)), 0, 0)
            pygame.draw.rect(screen, color, (i * CELL_SIZE, j * CELL_SIZE, CELL_SIZE, CELL_SIZE))

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Add mouse interaction for creating fluid sources
        if pygame.mouse.get_pressed()[0]:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            grid_x = mouse_x // CELL_SIZE
            grid_y = mouse_y // CELL_SIZE
            if 1 <= grid_x < GRID_SIZE-1 and 1 <= grid_y < GRID_SIZE-1:
                s[grid_x, grid_y] = 100.0
                density[grid_x, grid_y] = 1.0
                u[grid_x, grid_y] = 10.0 * (mouse_x - WIDTH / 2) / WIDTH
                v[grid_x, grid_y] = 10.0 * (mouse_y - HEIGHT / 2) / HEIGHT

    vel_step(u, v, np.zeros_like(u), np.zeros_like(v), viscosity, dt)
    density_step(density, s, u, v, diffusion, dt)
    s.fill(0)  # Reset source field after each step

    screen.fill(BLACK)
    draw_density(screen, density)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
