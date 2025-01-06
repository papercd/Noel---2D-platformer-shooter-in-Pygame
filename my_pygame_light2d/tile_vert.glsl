#version 430 


uniform vec2 NDCVertices[6];

layout(location = 0 ) in vec2 in_position; 
layout(location = 1 ) in vec2 in_texcoord[6]; 

out vec2 frag_texcoord; 


void main(){
    vec2 ndcVertex = NDCVertices[gl_VertexID];

    vec2 finalPosition = ndcVertex + in_position;

    vec2 texCoord = in_texcoord[gl_VertexID];

    gl_Position = vec4(finalPosition,0.0,1.0);
    frag_texcoord = texCoord;
}
