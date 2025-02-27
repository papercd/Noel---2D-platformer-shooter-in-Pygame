#version 330 core

layout(location=0) in vec3 vertexPos;
layout(location=1) in vec2 vertexTexCoord;



uniform vec2 camera_scroll;
uniform vec2 screen_res;
out vec2 fragmentTexCoord;

void main()
{
    vec2 worldPos = vertexPos.xy - camera_scroll;
    // Move the rotated position to screen coordinates
    gl_Position = vec4( worldPos.xy/screen_res * 2.0-1.0,vertexPos.z,1.0);

    fragmentTexCoord = vertexTexCoord;
   
}
