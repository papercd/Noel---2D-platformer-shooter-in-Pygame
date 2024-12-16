#version 330

in vec3 frag_color;
out vec4 frag_output;

void main() {
    frag_output= vec4(frag_color,1.0);  
}
