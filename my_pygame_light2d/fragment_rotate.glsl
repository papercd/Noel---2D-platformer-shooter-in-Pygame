#version 330
in vec2 fragmentTexCoord;
uniform sampler2D source_texture;
out vec4 color;
void main() {
    color = texture(source_texture, fragmentTexCoord);
}
