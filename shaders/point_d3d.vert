#version 440

layout(location = 0) in vec3 in_vert;
layout(location = 1) in float point_size;
layout(location = 2) in vec2 in_offset;

layout(std140, binding = 0) uniform UniformBufferObject {
    mat4 mvp;
};

layout(location = 0) out vec2 tex_coord;

void main() {
    vec4 clip_pos = mvp * vec4(in_vert, 1.0);
    
    // Get the viewport aspect ratio from the projection matrix
    float aspect_ratio = mvp[1][1] / mvp[0][0];
    
    // Apply aspect ratio correction to keep circles circular
    vec2 offs = in_offset * point_size;
    offs.x /= aspect_ratio;
    
    gl_Position = clip_pos + vec4(offs * clip_pos.w, 0.0, 0.0);
    
    // Pass the offset directly as texture coordinate
    tex_coord = in_offset;
}
