#version 430 

layout(location = 0) in vec3 vertexPos;    // Vertex position
layout(location = 1) in vec2 vertexTexCoord; // Texture coordinate

out vec2 fragmentTexCoord;   // Output texture coordinate

uniform vec3 renderScroll; 


void main() {
    fragmentTexCoord = vertexTexCoord;
    gl_Position = vec4(vertexPos-renderScroll, 1.0);
}
