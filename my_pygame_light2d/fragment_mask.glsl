#version 330 core

in vec2 fragmentTexCoord;
uniform sampler2D imageTexture;

uniform sampler2D lightmap;

uniform vec4 ambient;

uniform vec2 lightmapRes; 
uniform vec2 nativeRes; 

uniform float maxLuminosity=2.5f;

out vec4 color;

void main()
{
    float slack = (lightmapRes.x - nativeRes.x) / 2;

    vec2 lightmapFragmentTexCoord = vec2((fragmentTexCoord.x * nativeRes.x + slack) / lightmapRes.x, 1 - ((nativeRes.y*(-fragmentTexCoord.y + 1.0))+slack) / lightmapRes.y );
    vec4 texcolor=texture(imageTexture,fragmentTexCoord);
    vec4 lightVal=texture(lightmap,lightmapFragmentTexCoord);
    
    lightVal=clamp(lightVal,0,maxLuminosity);
    
    color=texcolor*(ambient+lightVal);
}