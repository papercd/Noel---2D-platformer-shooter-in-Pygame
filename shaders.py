import pygame
from pygame.locals import *
import OpenGL.GL as gl
import ctypes
import numpy as np
import time

# Shader source code
vertex_shader_source = """
#version 330 core
layout(location = 0) in vec2 position;
out vec2 fragCoord;
void main()
{
    fragCoord = position * 0.5 + 0.5;
    gl_Position = vec4(position, 0.0, 1.0);
}
"""

fragment_shader_source = """
#version 330 core
uniform vec3 iResolution;
uniform float iTime;
out vec4 fragColor;
in vec2 fragCoord;

float seed = 0.32;
const float particles = 32.0;
float res = 32.0;
float gravity = 0.72;

void mainImage(out vec4 fragColor, in vec2 fragCoord)
{
    vec2 uv = (-iResolution.xy + 2.0 * fragCoord.xy) / iResolution.y;
    float clr = 0.0;
    float timecycle = iTime - floor(iTime);
    seed = (seed + floor(iTime));
    
    float invres = 1.0 / res;
    float invparticles = 1.0 / particles;

    for(float i = 0.0; i < particles; i += 1.0)
    {
        seed += i + tan(seed);
        vec2 tPos = (vec2(cos(seed), sin(seed))) * i * invparticles;
        
        vec2 pPos = vec2(0.0, 0.0);
        pPos.x = ((tPos.x) * timecycle);
        pPos.y = -gravity * (timecycle * timecycle) + tPos.y * timecycle + pPos.y;
        
        pPos = floor(pPos * res) * invres;

        vec2 p1 = pPos;
        vec4 r1 = vec4(vec2(step(p1, uv)), 1.0 - vec2(step(p1 + invres, uv)));
        float px1 = r1.x * r1.y * r1.z * r1.w;
        float px2 = smoothstep(0.0, 200.0, (1.0 / distance(uv, pPos + 0.015)));
        px1 = max(px1, px2);

        clr += px1 * (sin(iTime * 20.0 + i) + 1.0);
    }

    fragColor = vec4(clr * (1.0 - timecycle)) * vec4(4, 0.5, 0.1, 1.0);
}

void main()
{
    mainImage(fragColor, fragCoord * iResolution.xy);
}
"""

# Compile the shaders and link the program
def compile_shader(source, shader_type):
    shader = gl.glCreateShader(shader_type)
    gl.glShaderSource(shader, source)
    gl.glCompileShader(shader)
    if not gl.glGetShaderiv(shader, gl.GL_COMPILE_STATUS):
        error = gl.glGetShaderInfoLog(shader).decode()
        raise Exception(f"Shader compilation failed:\n{error}")
    return shader

def create_shader_program(vertex_source, fragment_source):
    vertex_shader = compile_shader(vertex_source, gl.GL_VERTEX_SHADER)
    fragment_shader = compile_shader(fragment_source, gl.GL_FRAGMENT_SHADER)
    program = gl.glCreateProgram()
    gl.glAttachShader(program, vertex_shader)
    gl.glAttachShader(program, fragment_shader)
    gl.glLinkProgram(program)
    if not gl.glGetProgramiv(program, gl.GL_LINK_STATUS):
        error = gl.glGetProgramInfoLog(program).decode()
        raise Exception(f"Program linking failed:\n{error}")
    gl.glDeleteShader(vertex_shader)
    gl.glDeleteShader(fragment_shader)
    return program

# Initialize Pygame and OpenGL
pygame.init()
screen = pygame.display.set_mode((800, 600), DOUBLEBUF | OPENGL)
pygame.display.set_caption("Pixel Explosion Shader")
gl.glViewport(0, 0, 800, 600)

shader_program = create_shader_program(vertex_shader_source, fragment_shader_source)
gl.glUseProgram(shader_program)

# Define a fullscreen quad
quad_vertices = np.array([
    -1.0, -1.0,
     1.0, -1.0,
     1.0,  1.0,
    -1.0,  1.0
], dtype=np.float32)

quad_indices = np.array([0, 1, 2, 2, 3, 0], dtype=np.uint32)

# Create VAO and VBO
vao = gl.glGenVertexArrays(1)
vbo = gl.glGenBuffers(1)
ebo = gl.glGenBuffers(1)

gl.glBindVertexArray(vao)

gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo)
gl.glBufferData(gl.GL_ARRAY_BUFFER, quad_vertices.nbytes, quad_vertices, gl.GL_STATIC_DRAW)

gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, ebo)
gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER, quad_indices.nbytes, quad_indices, gl.GL_STATIC_DRAW)

gl.glEnableVertexAttribArray(0)
gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, gl.GL_FALSE, 2 * quad_vertices.itemsize, ctypes.c_void_p(0))

gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
gl.glBindVertexArray(0)

# Uniform locations
iResolution_loc = gl.glGetUniformLocation(shader_program, "iResolution")
iTime_loc = gl.glGetUniformLocation(shader_program, "iTime")

# Main loop
running = True
start_time = time.time()

while running:
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False

    # Update uniforms
    current_time = time.time() - start_time
    gl.glUniform3f(iResolution_loc, 800.0, 600.0, 1.0)
    gl.glUniform1f(iTime_loc, current_time)

    # Clear screen
    gl.glClear(gl.GL_COLOR_BUFFER_BIT)

    # Render quad
    gl.glBindVertexArray(vao)
    gl.glDrawElements(gl.GL_TRIANGLES, len(quad_indices), gl.GL_UNSIGNED_INT, None)
    gl.glBindVertexArray(0)

    pygame.display.flip()
    pygame.time.wait(10)

pygame.quit()
