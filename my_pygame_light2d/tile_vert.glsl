#version 430 


in vec2 in_position; 
in vec2 in_texcoord; 

out vec2 frag_texcoord; 

uniform vec2 iResolution;

void main(){
    gl_Position = vec4(in_position,0.0,1.0);
    frag_texcoord = in_texcoord;
}
