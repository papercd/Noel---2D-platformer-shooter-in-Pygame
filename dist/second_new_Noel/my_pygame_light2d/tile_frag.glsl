#version 430 

in vec2 frag_texcoord;
uniform sampler2D imageTexture;

out vec4 color; 

void main(){
    color = texture(imageTexture,frag_texcoord);
}