#version 330
in vec2 vertexPos;
in vec2 vertexTexCoord;
uniform mat3 rotation_matrix;
uniform vec2 translation;
out vec2 fragmentTexCoord;
void main() {
    vec2 rotatedPos = (rotation_matrix * vec3(vertexPos, 1.0)).xy;
    gl_Position = vec4(rotatedPos + translation, 0.0, 1.0);
    fragmentTexCoord = vertexTexCoord;
}