#version 330 core

in vec2 TexCoord;
out vec4 fragColor;

uniform sampler2D iChannel0;  // Texture sampler
uniform vec2 iResolution;     // Resolution of the screen

// Bayer matrix for dithering
const mat4 bayerIndex = mat4(
    vec4(00.0/16.0, 12.0/16.0, 03.0/16.0, 15.0/16.0),
    vec4(08.0/16.0, 04.0/16.0, 11.0/16.0, 07.0/16.0),
    vec4(02.0/16.0, 14.0/16.0, 01.0/16.0, 13.0/16.0),
    vec4(10.0/16.0, 06.0/16.0, 09.0/16.0, 05.0/16.0)
);

void main()
{
    // Sample the texture
    vec2 uv = TexCoord;
    vec4 col = texture(iChannel0, uv);

    // Apply gamma correction (optional)
    col.rgb = pow(col.rgb, vec3(2.2)) - 0.004;

    // Calculate the position within the Bayer matrix
    ivec2 bayerCoord = ivec2(mod(gl_FragCoord.xy, 4.0));

    // Determine the threshold value from the Bayer matrix
    float threshold = bayerIndex[bayerCoord.x][bayerCoord.y];

 


    // Perform dithering
    fragColor = vec4(
        step(threshold, col.r),
        step(threshold, col.g),
        step(threshold, col.b),
        col.a
    );
}
