#version 330 core

in vec2 fragmentTexCoord;// top-left is [0, 1] and bottom-right is [1, 0]
uniform sampler2D imageTexture;// texture in location 0

uniform float u_alpha =1; 
out vec4 color;

void main()
{
    color=texture(imageTexture,fragmentTexCoord);
    color.a *= u_alpha;
}
