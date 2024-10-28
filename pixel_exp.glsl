#version 330 core

in vec2 fragmentTexCoord;
out vec4 fragColor;

uniform sampler2D texture;
uniform float time;
uniform vec2 resolution;

void main()
{
    // Get the texture color
    vec4 texColor = texture(texture, fragmentTexCoord);

    // Calculate the scanline intensity based on the Y-coordinate
    float scanlineFactor = sin(fragmentTexCoord.y * resolution.y * 50.0) * 0.1;

    // Apply the scanline effect by modulating the brightness of the texture
    vec4 scanlineColor = texColor * (1.0 - scanlineFactor);

    // Output the final color
    fragColor = scanlineColor;
}
