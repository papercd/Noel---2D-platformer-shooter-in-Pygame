import moderngl
from scripts.utils import load_texture
import numpy as np

def build_model_matrix(pivot, position, rotation_angle):
    pivot_translate = np.eye(3)
    pivot_translate[:2, 2] = -np.array(pivot)

    rotation = np.eye(3)
    cos_a, sin_a = np.cos(rotation_angle), np.sin(rotation_angle)
    rotation[:2, :2] = [[cos_a, -sin_a], [sin_a, cos_a]]

    reverse_pivot = np.eye(3)
    reverse_pivot[:2, 2] = np.array(pivot)

    final_translate = np.eye(3)
    final_translate[:2, 2] = np.array(position)

    return final_translate @ reverse_pivot @ rotation @ pivot_translate

# Context setup
ctx = moderngl.create_context()

# Define vertices for a quad (positions and texcoords)
vertices = np.array([
# x, y, u, v
-0.5, -0.5, 0.0, 0.0,  # Bottom-left
    0.5, -0.5, 1.0, 0.0,  # Bottom-right
-0.5,  0.5, 0.0, 1.0,  # Top-left
    0.5,  0.5, 1.0, 1.0,  # Top-right
], dtype='f4')

# Create VBO and VAO
vbo = ctx.buffer(vertices.tobytes())
vao = ctx.simple_vertex_array(
ctx.program(
    vertex_shader=open('vertex_shader.glsl').read(),
    fragment_shader=open('fragment_shader.glsl').read(),
),
vbo,
'in_pos', 'in_texcoord'
)

# Load texture
texture = load_texture('data/images/entities/player.png',ctx)
texture.use()

# Create transformation matrix
pivot = (16, 16)   # Pivot point in texture space
position = (100, 100)  # Final position
rotation_angle = np.radians(45)

model_matrix = build_model_matrix(pivot, position, rotation_angle)  # Function from earlier

# Render loop
while True:
    ctx.clear(0.0, 0.0, 0.0)  # Clear screen
    vao.program['model'].write(model_matrix.astype('f4').tobytes())  # Pass model matrix
    vao.render(moderngl.TRIANGLE_STRIP)  # Draw quad



