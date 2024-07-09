import pygame
from pygame.locals import *
import OpenGL.GL as gl
import numpy as np
import ctypes
import time

# Shader source code
vertex_shader_source = """
#version 330 core

layout(location=0) in vec3 vertexPos;
layout(location=1) in vec2 vertexTexCoord;

out vec2 fragmentTexCoord;

void main()
{
    gl_Position = vec4(vertexPos, 1.0);
    fragmentTexCoord = vertexTexCoord;
}
"""

fragment_shader_source = """
#version 330 core

uniform vec3 iResolution;
uniform float iTime;
out vec4 fragColor;
in vec2 fragmentTexCoord;

vec3 permute(vec3 x) { return mod(((x*34.0)+1.0)*x, 289.0); }

float snoice(vec2 v) {
  const vec4 C = vec4(0.211324865405187, 0.366025403784439,
                      -0.577350269189626, 0.024390243902439);
  vec2 i  = floor(v + dot(v, C.yy));
  vec2 x0 = v - i + dot(i, C.xx);
  vec2 i1;
  i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
  vec4 x12 = x0.xyxy + C.xxzz;
  x12.xy -= i1;
  i = mod(i, 289.0);
  vec3 p = permute(permute(i.y + vec3(0.0, i1.y, 1.0)) + i.x + vec3(0.0, i1.x, 1.0));
  vec3 m = max(0.5 - vec3(dot(x0, x0), dot(x12.xy, x12.xy), dot(x12.zw, x12.zw)), 0.0);
  m = m * m;
  m = m * m;
  vec3 x = 2.0 * fract(p * C.www) - 1.0;
  vec3 h = abs(x) - 0.5;
  vec3 ox = floor(x + 0.5);
  vec3 a0 = x - ox;
  m *= 1.79284291400159 - 0.85373472095314 * (a0 * a0 + h * h);
  vec3 g;
  g.x  = a0.x  * x0.x  + h.x  * x0.y;
  g.yz = a0.yz * x12.xz + h.yz * x12.yw;
  return 130.0 * dot(m, g);
}

void mainImage(out vec4 fragColor, in vec2 fragCoord)
{
    vec2 uv = fragCoord / iResolution.xy;
    
    float noice = snoice(vec2(uv.x * 3.4 - 2.0, uv.y - iTime) * 2.3);
        
    vec2 circleParams = vec2(cos(noice) + 4.0, abs(sin(noice) + 2.5));
    
    float circleRatio = circleParams.y / circleParams.x;
    
    float circle = pow(circleParams.y, -abs(length((fragCoord + fragCoord - iResolution.xy) / iResolution.y) - circleRatio) * 20.0) * atan(iTime) * 1.3;
   
    circle += 2.0 * pow(circleParams.y, -abs(length((fragCoord + fragCoord - iResolution.xy) / iResolution.y - circleRatio * vec2(cos(iTime), sin(iTime)))) * circleParams.x); 
   
    fragColor.rgb = circle * vec3(circleParams * 0.1, 0.5);
}

void main()
{
    mainImage(fragColor, fragmentTexCoord * iResolution.xy);
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
    # Positions       # Texture Coords
    -1.0, -1.0, 0.0,   0.0, 0.0,
     1.0, -1.0, 0.0,   1.0, 0.0,
     1.0,  1.0, 0.0,   1.0, 1.0,
    -1.0,  1.0, 0.0,   0.0, 1.0
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
gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, 5 * quad_vertices.itemsize, ctypes.c_void_p(0))

gl.glEnableVertexAttribArray(1)
gl.glVertexAttribPointer(1, 2, gl.GL_FLOAT, gl.GL_FALSE, 5 * quad_vertices.itemsize, ctypes.c_void_p(3 * quad_vertices.itemsize))

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
