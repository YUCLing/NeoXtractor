#version 440

layout(location = 0) in vec2 in_position;
layout(location = 1) in vec2 in_texcoord;

layout(location = 0) out vec2 v_texcoord;

layout(binding = 0) uniform UniformBufferObject {
    mat4 projection;
    vec4 textColor;
};

void main() {
    gl_Position = projection * vec4(in_position, 0.0, 1.0);
    v_texcoord = in_texcoord;
}
