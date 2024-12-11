#version 330 core

layout(location = 0) in vec3 vertexPos;        // Vertex position
layout(location = 1) in vec2 vertexTexCoord;   // Texture coordinate

uniform mat3 transformationMatrix;  // Transformation matrix (3x3 for 2D)

out vec2 fragmentTexCoord;           // Output texture coordinate

void main() {
    // Apply the transformation matrix to the vertex position
    vec3 transformedPos = transformationMatrix * vec3(vertexPos.x, vertexPos.y, 1.0);

    // Pass the transformed position to the fragment shader
    gl_Position = vec4(transformedPos.x, transformedPos.y, 0.0, 1.0);

    // Pass the texture coordinates to the fragment shader
    fragmentTexCoord = vertexTexCoord;
}
