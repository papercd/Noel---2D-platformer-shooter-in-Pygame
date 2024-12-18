#version 330 core
in vec2 in_vert;   // Circle geometry vertex 
in vec2 offset;    // Circle world position offset
in vec4 in_color;  // per-instance color 
in float size;     // per-instance size  

out vec4 fragColor; // Pass color to fragment shader

void main() {
    fragColor = in_color;
    vec2 scaled_vert = in_vert * size; //scale the circle geometry
    gl_Position = vec4(scaled_vert + offset,0.0,1.0);
}
