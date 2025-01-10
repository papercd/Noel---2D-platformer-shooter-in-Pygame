#version 430 

in vec2 in_position[6]; 
in vec2 texcoord[6];

in vec3 col1; 
in vec3 col2; 
in vec3 col3; 


out vec2 frag_texcoord; 

void main() {
    mat3 transform = mat3(col1,col2,col3);
    vec3 localVertex = vec3(in_position[gl_VertexID],1.0);

    vec3 ndcVertex = transform * localVertex; 

    gl_Position = vec4(ndcVertex.xy,0.0,1.0);
    frag_texcoord = texcoord[gl_VertexID]; 
}
