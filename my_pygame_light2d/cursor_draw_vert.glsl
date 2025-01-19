#version 430 

in vec2 in_position; 

uniform vec2[6] texCoords;

out vec2 fragmentTexCoord;

void main(){

    gl_Position = vec4(in_position,0.0,1.0);
    fragmentTexCoord = texCoords[gl_VertexID];
}