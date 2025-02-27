#version 330 core

in vec4 Color;  // Interpolated color from vertex shader

out vec4 FragColor;

void main() {
    FragColor = Color;
}
