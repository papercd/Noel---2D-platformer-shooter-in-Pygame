#version 330 core

in vec2 in_vert;   // Circle geometry vertex 
in vec4 in_color;  // per-instance color 

out vec4 fragColor; // Pass color to fragment shader

void main() {
    fragColor = in_color;
    gl_Position = vec4(in_vert,0.0,1.0);
}
