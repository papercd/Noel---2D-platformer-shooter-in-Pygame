#version 330 core
in vec2 vertexPos;
out vec2 texCoord;

void main() {
    texCoord = (vertexPos + 1.0) * 0.5;  // Convert NDC to texture space
    gl_Position = vec4(vertexPos, 0.0, 1.0);
}
