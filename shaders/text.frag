#version 440

layout(location = 0) in vec2 v_texcoord;

layout(location = 0) out vec4 fragColor;

layout(binding = 0) uniform UniformBufferObject {
    mat4 projection;
    vec4 textColor;
};

layout(binding = 1) uniform sampler2D atlas_texture;

void main() {
    float alpha = texture(atlas_texture, v_texcoord).r;
    fragColor = vec4(textColor.rgb, alpha);
}
