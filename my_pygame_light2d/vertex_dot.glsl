#version 330 core

layout (location = 0) in vec2 aPos;  // Dot position in NDC (-1 to 1)
layout (location = 1) in vec4 aColor; // Dot color

out vec4 Color;  // Pass color to the fragment shader

uniform float pointSize = 1.0;  // Uniform point size

void main() {
    gl_Position = vec4(aPos, 0.0, 1.0);
    gl_PointSize = pointSize;
    Color = aColor;
}
