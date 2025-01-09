#version 430 

layout (location = 0) in vec2 in_position; 
layout (location = 1) in vec2 texcoord;

layout (location = 2) in vec3 col1; 
layout (location = 3) in vec3 col2; 
layout (location = 4) in vec3 col3; 


out vec2 frag_texcoord; 

void main() {
    mat3 transform = mat3(col1,col2,col3);
    vec3 worldVertex = vec3(in_position,1.0);

    vec3 ndcVertex = transform * worldVertex; 

    gl_Position = vec4(ndcVertex.xy,0.0,1.0);
    frag_texcoord = texcoord; 
}
