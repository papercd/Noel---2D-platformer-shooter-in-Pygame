#version 430 

in vec2 in_position; 

uniform vec2[6] vertices; 
uniform vec2[6] texCoords;

out vec2 fragmentTexCoord;

void main(){
    vec2 ndcVertex = vertices[gl_VertexID];
    vec2 finalPosition = ndcVertex + in_position;

    gl_Position = vec4(finalPosition,0.0,1.0);
    fragmentTexCoord = texCoords[gl_VertexID];
}