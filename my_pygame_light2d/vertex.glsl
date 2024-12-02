#version 330 core

layout(location=0) in vec3 vertexPos;
layout(location=1) in vec2 vertexTexCoord;

uniform float rotation;          // Rotation angle in radians
uniform bool flip_horizontal;     // Horizontal flip flag
uniform bool flip_vertical;       // Vertical flip flag


out vec2 fragmentTexCoord;

void main()
{
    // Rotation around the Z-axis (2D rotation)
    float cos_angle = cos(rotation);
    float sin_angle = sin(rotation);

    // Apply rotation to vertex position (around origin)
    vec2 rotatedPos = vec2(
        vertexPos.x * cos_angle - vertexPos.y * sin_angle,
        vertexPos.x * sin_angle + vertexPos.y * cos_angle
    );

    // Move the rotated position to screen coordinates
    gl_Position = vec4(rotatedPos, vertexPos.z, 1.0);

    // Adjust texture coordinates based on flip flags
    fragmentTexCoord = vertexTexCoord;
    if (flip_horizontal) {
        fragmentTexCoord.x = 1.0 - fragmentTexCoord.x;
    }
    if (flip_vertical) {
        fragmentTexCoord.y = 1.0 - fragmentTexCoord.y;
    }
}
