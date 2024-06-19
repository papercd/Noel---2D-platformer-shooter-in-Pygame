import sys
from array import array
from collections import deque

import pygame
import moderngl

pygame.init()

# Set up Pygame with OpenGL context
screen = pygame.display.set_mode((800, 600), pygame.OPENGL | pygame.DOUBLEBUF)
ctx = moderngl.create_context()

clock = pygame.time.Clock()

# Load image
img = pygame.image.load('data/images/background.png')

# Vertex buffer data: position (x, y), uv coords (x, y)
quad_buffer = ctx.buffer(data=array('f', [
    -1.0, 1.0, 0.0, 0.0,  # topleft
    1.0, 1.0, 1.0, 0.0,   # topright
    -1.0, -1.0, 0.0, 1.0, # bottomleft
    1.0, -1.0, 1.0, 1.0,  # bottomright
]))

# Vertex shader source code
vert_shader = '''
#version 330 core

in vec2 vert;
in vec2 texcoord;
out vec2 uvs;

void main() {
    uvs = texcoord;
    gl_Position = vec4(vert, 0.0, 1.0);
}
'''

# Fragment shader source code for circular ripple effect
frag_shader = '''
#version 330 core

uniform sampler2D tex;
uniform float time;
uniform vec2 resolution;
uniform vec2 click_pos;
uniform float click_time;

in vec2 uvs;
out vec4 f_color;

void main() {
    vec2 uv = uvs;
    vec2 click_uv = click_pos / resolution;

    float dist = distance(uv, click_uv);
    float elapsed = time - click_time;
    float ripple = sin(10.0 * dist - elapsed * 5.0) * exp(-elapsed * 2.0) * 0.1;

    uv += ripple * normalize(uv - click_uv);

    f_color = texture(tex, uv);
}
'''

# Compile shaders and create a shader program
program = ctx.program(vertex_shader=vert_shader, fragment_shader=frag_shader)
render_object = ctx.vertex_array(program, [(quad_buffer, '2f 2f', 'vert', 'texcoord')])

# Function to convert Pygame surface to OpenGL texture
def surf_to_texture(surf):
    tex = ctx.texture(surf.get_size(), 4)
    tex.filter = (moderngl.NEAREST, moderngl.NEAREST)
    tex.swizzle = 'BGRA'
    tex.write(surf.get_view('1'))
    return tex

click_positions = deque(maxlen=10)
start_time = pygame.time.get_ticks()

# Main loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            click_positions.append((event.pos, pygame.time.get_ticks() - start_time))

    # Create a Pygame surface to draw the image
    display = pygame.Surface((800, 600))
    display.fill((0, 0, 0))
    display.blit(img, (0, 0))
    
    current_time = (pygame.time.get_ticks() - start_time) / 1000.0
    
    # Convert the Pygame surface to an OpenGL texture
    frame_tex = surf_to_texture(display)
    frame_tex.use(0)
    program['tex'] = 0
    program['time'] = current_time
    program['resolution'] = (800, 600)
    
    if click_positions:
        click_pos, click_time = click_positions[-1]
        program['click_pos'] = click_pos
        program['click_time'] = click_time / 1000.0
    else:
        program['click_pos'] = (0, 0)
        program['click_time'] = -100.0  # A large negative value to ensure no ripple at start

    render_object.render(mode=moderngl.TRIANGLE_STRIP)
    
    pygame.display.flip()
    
    frame_tex.release()
    
    clock.tick(60)
