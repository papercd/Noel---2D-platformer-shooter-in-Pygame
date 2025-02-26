from numpy import cos, sin, float32
from pygame.math import Vector2 as vec2
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pygame.rect import Rect

def project_polygon(corners, axis): 
    dots = [corner.dot(axis) for corner in corners]
    return min(dots), max(dots)

class RotatedRect:
    def __init__(self, center: tuple[int, int], size: tuple[int, int]) -> None:
        self.set_initial_corners(center, size)
        self.vertices = self.initial_corners.copy()  # Ensure vertices exist

    def set_initial_corners(self, center, size) -> None:
        self.initial_cx, self.initial_cy = center

        half_width, half_height = size[0] // 2, size[1] // 2

        self.initial_corners = [
            vec2(-half_width, -half_height),
            vec2(half_width, -half_height),
            vec2(half_width, half_height),
            vec2(-half_width, half_height),
        ]

    def set_rotation(self, angle: float) -> None:
        """Rotates the rectangle around its center."""
        cos_a, sin_a = cos(angle), sin(angle)
        self.vertices = [
            vec2(
                self.initial_cx + corner.x * cos_a - corner.y * sin_a,
                self.initial_cy + corner.x * sin_a + corner.y * cos_a
            ) for corner in self.initial_corners
        ]

    def move(self, displacement: tuple[int, int]) -> None:
        """Moves the rectangle by adding displacement."""
        for i in range(4):
            self.vertices[i] += vec2(displacement)

    def colliderect(self, other_rect: "Rect") -> bool:
        """Checks collision using the Separating Axis Theorem (SAT)."""
        other_corners = [
            vec2(other_rect.topleft),
            vec2(other_rect.topright),
            vec2(other_rect.bottomright),
            vec2(other_rect.bottomleft),
        ]

        axes = []
        for i in range(4):
            edge = self.vertices[i] - self.vertices[(i + 1) % 4]
            axes.append(vec2(-edge.y, edge.x).normalize())

        for i in range(2):  # Only two edges matter for an axis-aligned rectangle
            edge = other_corners[i] - other_corners[(i + 1) % 4]
            axes.append(vec2(-edge.y, edge.x).normalize())

        for axis in axes:
            proj1 = project_polygon(self.vertices, axis)
            proj2 = project_polygon(other_corners, axis)
            if proj1[1] < proj2[0] or proj2[1] < proj1[0]:
                return False
        return True
