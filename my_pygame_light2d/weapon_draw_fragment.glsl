#version 330 core

in vec2 fragmentTexCoord;  // Input texture coordinate
out vec4 fragColor;        // Output fragment color

uniform sampler2D textureSampler;  // The texture to sample from

void main() {
    // Sample the texture at the given coordinates
    fragColor = texture(textureSampler, fragmentTexCoord);
}
