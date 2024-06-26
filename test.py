import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import numpy as np

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((800, 600), DOUBLEBUF | OPENGL)
pygame.display.set_caption("GLSL Shader with Pygame")

# Vertex Shader Source Code
vertex_shader_code = """
#version 330
in vec2 position;
out vec2 texCoord;
void main()
{
    gl_Position = vec4(position, 0.0, 1.0);
    texCoord = (position + 1.0) / 2.0;
}
"""

# Fragment Shader Source Code
fragment_shader_code = """
#version 330
out vec4 fragColor;
in vec2 texCoord;
uniform sampler2D iChannel0;
uniform vec2 iResolution;
uniform float iTime;

void mainImage(out vec4 fragColor, in vec2 fragCoord)
{
    // Normalized coordinates
    vec2 uv = (fragCoord - 0.5 * iResolution.xy) / iResolution.x + 0.5;
    
    // Calculate radius and angle
    float radius = length(uv - 0.5) + 0.1 - iTime / 0.5;
    float angle = atan(uv.y - 0.5, uv.x - 0.5);
    
    // Calculate the distortion effect
    float distortion = smoothstep(0.1, 0.2, radius) * smoothstep(0.3, 0.2, radius) * smoothstep(0.0, 1.0, radius);
    
    // Calculate the light intensity and make it dissipate over time
    float lightIntensity = max(1.75 - iTime / 0.2, 0.0); // Adjust the denominator to control the dissipation rate
    vec4 light = vec4(1.0, 0.8, 0.7, 1.0) * smoothstep(0.5, 0.0, radius) * lightIntensity;

    // Apply distortion
    uv += distortion * vec2(cos(angle), sin(angle)) * max(1.0 - iTime / 5.0, 0.0); // Adjust the denominator to control the dissipation rate

    // Sample the texture
    vec4 col = texture(iChannel0, uv);
    col += light;

    // Output the final color
    fragColor = vec4(col);
}

void main()
{
    mainImage(fragColor, texCoord * iResolution);
}

"""

# Compile Shaders and Create Shader Program
vertex_shader = compileShader(vertex_shader_code, GL_VERTEX_SHADER)
fragment_shader = compileShader(fragment_shader_code, GL_FRAGMENT_SHADER)
shader = compileProgram(vertex_shader, fragment_shader)

# Define a Full-Screen Quad
quad_vertices = np.array([
    [-1.0, -1.0],
    [ 1.0, -1.0],
    [ 1.0,  1.0],
    [-1.0,  1.0]
], dtype=np.float32)

quad_indices = np.array([0, 1, 2, 2, 3, 0], dtype=np.uint32)

vao = glGenVertexArrays(1)
vbo = glGenBuffers(1)
ebo = glGenBuffers(1)

glBindVertexArray(vao)

glBindBuffer(GL_ARRAY_BUFFER, vbo)
glBufferData(GL_ARRAY_BUFFER, quad_vertices.nbytes, quad_vertices, GL_STATIC_DRAW)

glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
glBufferData(GL_ELEMENT_ARRAY_BUFFER, quad_indices.nbytes, quad_indices, GL_STATIC_DRAW)

position = glGetAttribLocation(shader, 'position')
glVertexAttribPointer(position, 2, GL_FLOAT, GL_FALSE, 2 * quad_vertices.itemsize, ctypes.c_void_p(0))
glEnableVertexAttribArray(position)

glBindBuffer(GL_ARRAY_BUFFER, 0)
glBindVertexArray(0)
glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

# Load Texture using Pygame
texture_surface = pygame.image.load("data/images/background.png")
texture_data = pygame.image.tostring(texture_surface, "RGBA", 1)
width, height = texture_surface.get_rect().size

texture = glGenTextures(1)
glBindTexture(GL_TEXTURE_2D, texture)
glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, texture_data)
glGenerateMipmap(GL_TEXTURE_2D)

glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

# Main Loop
running = True
start_time = pygame.time.get_ticks()
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    glClear(GL_COLOR_BUFFER_BIT)

    glUseProgram(shader)
    
    iResolution_location = glGetUniformLocation(shader, "iResolution")
    glUniform2f(iResolution_location, 800, 600)
    
    iTime_location = glGetUniformLocation(shader, "iTime")
    current_time = (pygame.time.get_ticks() - start_time) / 1000.0
    glUniform1f(iTime_location, current_time)

    glActiveTexture(GL_TEXTURE0)
    glBindTexture(GL_TEXTURE_2D, texture)
    iChannel0_location = glGetUniformLocation(shader, "iChannel0")
    glUniform1i(iChannel0_location, 0)

    glBindVertexArray(vao)
    glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)
    glBindVertexArray(0)

    pygame.display.flip()
    pygame.time.wait(10)

# Clean up
glDeleteProgram(shader)
glDeleteBuffers(1, [vbo])
glDeleteBuffers(1, [ebo])
glDeleteVertexArrays(1, [vao])
pygame.quit()
