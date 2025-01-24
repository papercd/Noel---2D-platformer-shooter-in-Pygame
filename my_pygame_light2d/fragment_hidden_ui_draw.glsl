#version 430 

in vec2 fragmentTexCoord;
uniform sampler2D imageTexture; 

uniform float alpha; 

out vec4 color; 

void main()
{   
    vec4 sampledColor = texture(imageTexture,fragmentTexCoord);
    color = vec4(sampledColor.rgb,sampledColor.a * alpha);
}