import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import numpy as np
import time

# Shader source code
vertex_shader = """
#version 330 core
layout(location = 0) in vec2 position;
void main()
{
    gl_Position = vec4(position, 0.0, 1.0);
}
"""

fragment_shader = """
#version 330 core
uniform vec2 iResolution;
uniform float iTime;

out vec4 fragColor;

float seed = 0.32; //----------------------------------------------------------starting seed
const float particles = 32.0; //----------------------------------------------change particle count
float res = 32.0; //-----------------------------------------------------------pixel resolution
float gravity = 0.72; //-------------------------------------------------------set gravity

void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
    vec2 uv = (-iResolution.xy + 2.0*fragCoord.xy) / iResolution.y;
    float clr = 0.0;  
    float timecycle = iTime-floor(iTime);  
    seed = (seed+floor(iTime));
    
    //testing
    float invres=1.0/res;
    float invparticles = 1.0/particles;

    
    for( float i=0.0; i<particles; i+=1.0 )
    {
        seed+=i+tan(seed);
        vec2 tPos = (vec2(cos(seed),sin(seed)))*i*invparticles;
        
        vec2 pPos = vec2(0.0,0.0);
        pPos.x=((tPos.x) * timecycle);
        pPos.y = -gravity*(timecycle*timecycle)+tPos.y*timecycle+pPos.y;
        
        pPos = floor(pPos*res)*invres; //-----------------------------------------comment this out for smooth version 

        vec2 p1 = pPos;
        vec4 r1 = vec4(vec2(step(p1,uv)),1.0-vec2(step(p1+invres,uv)));
        float px1 = r1.x*r1.y*r1.z*r1.w;
        float px2 = smoothstep(0.0,200.0,(1.0/distance(uv, pPos+.015)));//added glow
        px1=max(px1,px2);
        
        clr += px1*(sin(iTime*20.0+i)+1.0);
    }
    
    fragColor = vec4(clr*(1.0-timecycle))*vec4(4, 0.5, 0.1,1.0);
}

void main()
{
    mainImage(fragColor, gl_FragCoord.xy);
}
"""

# Initialize Pygame and OpenGL
pygame.init()
screen = pygame.display.set_mode((800, 600), DOUBLEBUF | OPENGL)
glViewport(0, 0, 800, 600)
glClearColor(0.0, 0.0, 0.0, 1.0)

# Compile shaders and create shader program
shader = compileProgram(
    compileShader(vertex_shader, GL_VERTEX_SHADER),
    compileShader(fragment_shader, GL_FRAGMENT_SHADER)
)

# Create a fullscreen quad
quad = np.array([
    -1.0, -1.0,
    1.0, -1.0,
    -1.0, 1.0,
    1.0, 1.0
], dtype=np.float32)

vao = glGenVertexArrays(1)
vbo = glGenBuffers(1)
glBindVertexArray(vao)
glBindBuffer(GL_ARRAY_BUFFER, vbo)
glBufferData(GL_ARRAY_BUFFER, quad.nbytes, quad, GL_STATIC_DRAW)
glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, None)
glEnableVertexAttribArray(0)

# Use the shader program
glUseProgram(shader)

# Set the iResolution uniform for the smaller surface
iResolution = glGetUniformLocation(shader, "iResolution")
surface_size = (256, 256)
glUniform2f(iResolution, surface_size[0], surface_size[1])

# Create framebuffer object (FBO) for rendering to texture
fbo = glGenFramebuffers(1)
glBindFramebuffer(GL_FRAMEBUFFER, fbo)

# Create texture to render to
texture = glGenTextures(1)
glBindTexture(GL_TEXTURE_2D, texture)
glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, surface_size[0], surface_size[1], 0, GL_RGBA, GL_UNSIGNED_BYTE, None)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

# Attach the texture to the FBO
glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, texture, 0)

# Check if FBO is complete
if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
    raise Exception("Framebuffer not complete")

# Unbind the FBO
glBindFramebuffer(GL_FRAMEBUFFER, 0)

# Main loop
running = True
start_time = time.time()
positions = []  # List to store click positions

while running:
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
        elif event.type == MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                positions.append(event.pos)

    # Render to FBO
    glBindFramebuffer(GL_FRAMEBUFFER, fbo)
    glViewport(0, 0, surface_size[0], surface_size[1])
    glClear(GL_COLOR_BUFFER_BIT)

    # Update the iTime uniform
    iTime = glGetUniformLocation(shader, "iTime")
    current_time = time.time() - start_time
    glUniform1f(iTime, current_time)

    # Draw the quad
    glBindVertexArray(vao)
    glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)

    glBindFramebuffer(GL_FRAMEBUFFER, 0)
    glViewport(0, 0, 800, 600)

    # Get the texture data
    glBindTexture(GL_TEXTURE_2D, texture)
    data = glGetTexImage(GL_TEXTURE_2D, 0, GL_RGBA, GL_UNSIGNED_BYTE)
    surface = pygame.image.fromstring(data, surface_size, "RGBA")

    # Clear the main screen
    screen.fill((0, 0, 0))

    # Blit the surface onto the main screen at the clicked positions
    for pos in positions:
        screen.blit(surface, pos)

    # Swap buffers
    pygame.display.flip()
    pygame.time.wait(10)

pygame.quit()
