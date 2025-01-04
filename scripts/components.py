from dataclasses import dataclass as component 
from pygame.math import Vector2 as vec2
import numpy as np


@component 
class PhysicsComponent: 
    transform: np.matrix 
    velocity: vec2


@component
class RenderComponent:
    size : vec2
    pivot_point : vec2
    rotation_transform: np.matrix 
    flip_bit :bool
    vertices: np.array 
    texcoords = np.array 