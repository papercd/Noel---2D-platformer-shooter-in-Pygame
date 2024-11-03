import pygame
import math
import itertools

# Initialize Pygame
pygame.init()

# Constants for screen dimensions and colors
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
BACKGROUND_COLOR = (25, 25, 25)

# Set up the display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()
FPS = 60

# Define a function to create procedural animation
def procedural_leg_movement(tick):
    # Calculates the position of a leg using sine and cosine for given tick value
    amplitude = 30                         # Amplitude of the sine wave
    frequency = 0.1                        # Frequency of the sine wave
    phase = tick * frequency               # Compute phase for cyclic movement
    x_pos = amplitude * math.sin(phase)    # X position follows a sine wave
    y_pos = abs(amplitude * math.cos(phase))  # Y position follows the absolute value of a cosine wave
    
    return x_pos, y_pos
    
# Define a class for the creature
class Creature:
    def __init__(self):
        self.base_x = SCREEN_WIDTH // 2
        self.base_y = SCREEN_HEIGHT // 2
        self.legs = 4
        self.leg_seg_length = 50  # Length of each segment of the leg

    def draw(self, tick):
        for i, phase_offset in zip(range(self.legs), itertools.cycle([0, math.pi])):
            # Get the procedural leg position with added phase offset for variety
            leg_x_offset, leg_y_offset = procedural_leg_movement(tick + phase_offset)
            
            # Calculate start and end positions of each leg segment
            for segment in range(2):
                start_pos = (
                    self.base_x + leg_x_offset * segment,
                    self.base_y + self.leg_seg_length * segment + leg_y_offset
                )
                end_pos = (
                    self.base_x + leg_x_offset * (segment + 1),
                    self.base_y + self.leg_seg_length * (segment + 1) + leg_y_offset
                )
                
                # Draw the leg segment
                pygame.draw.line(screen, (255, 220, 150), start_pos, end_pos, 5)
    
# Instantiate a creature
creature = Creature()

# Game loop
running = True
tick = 0
while running:
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Update
    tick += 1 # Increment tick

    # Draw everything
    screen.fill(BACKGROUND_COLOR)
    creature.draw(tick)
    
    # Update the display
    pygame.display.flip()

    # Tick the clock
    clock.tick(FPS)

# Clean up
pygame.quit()