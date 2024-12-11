#version 330 core

layout(location = 0) in vec3 vertexPos;    // Vertex position
layout(location = 1) in vec2 vertexTexCoord; // Texture coordinate

uniform vec2 pivotTexCoord;  // Pivot point in texture coordinates
uniform float rotation;      // Rotation angle in radians
uniform vec2 pivotPosition;  // Pivot point in world coordinates
uniform vec2 scale;          // Scaling factor (optional)

uniform bool flip_horizontal; // Horizontal flip flag
uniform bool flip_vertical;   // Vertical flip flag

out vec2 fragmentTexCoord;   // Output texture coordinate

void main() {
    // Adjust texture coordinates based on flip flags
    vec2 adjustedTexCoord = vertexTexCoord;
    if (flip_horizontal) {
        adjustedTexCoord.x = 1.0 - adjustedTexCoord.x;
    }
    if (flip_vertical) {
        adjustedTexCoord.y = 1.0 - adjustedTexCoord.y;
    }

    // Rotate the texture coordinates around the pivot
    vec2 relativeTexCoord = adjustedTexCoord - pivotTexCoord;

    float cos_angle = cos(rotation);
    float sin_angle = sin(rotation);

    vec2 rotatedTexCoord = vec2(
        relativeTexCoord.x * cos_angle - relativeTexCoord.y * sin_angle,
        relativeTexCoord.x * sin_angle + relativeTexCoord.y * cos_angle
    );

    fragmentTexCoord = rotatedTexCoord + pivotTexCoord;

    // Rotate the vertex position around the pivot
    vec2 relativePos = vertexPos.xy - pivotPosition;

    vec2 rotatedPos = vec2(
        relativePos.x * cos_angle - relativePos.y * sin_angle,
        relativePos.x * sin_angle + relativePos.y * cos_angle
    );

    // Apply scale (optional) and output the transformed position
    gl_Position = vec4(rotatedPos + pivotPosition, vertexPos.z, 1.0);
}
