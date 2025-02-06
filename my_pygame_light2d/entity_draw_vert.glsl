#version 430

layout (location = 0) in vec2 in_position;  // Per-vertex position
layout (location = 1) in vec2 texcoord;     // Per-vertex texture coordinate

layout (location = 2) in vec3 col1;  // Per-instance transformation matrix row 1
layout (location = 3) in vec3 col2;  // Per-instance transformation matrix row 2
layout (location = 4) in vec3 col3;  // Per-instance transformation matrix row 3

out vec2 frag_texcoord;

void main() {
    // Construct the transformation matrix
    mat3 transform = mat3(col1, col2, col3);

    // Transform local vertex position
    vec3 localVertex = vec3(in_position, 1.0);
    vec3 ndcVertex = transform * localVertex;

    gl_Position = vec4(ndcVertex.xy, 0.0, 1.0);  // Assuming 2D rendering
    frag_texcoord = texcoord;
}
