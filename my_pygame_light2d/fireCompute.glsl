
#version 430

layout(local_size_x = 256) in; 

struct FireParticle {
    int damage;
    float life; 
    bool dead; 
    int i; 
    vec2 velocity;
    vec2 position;
    vec2 renderPosition; 
    vec2 center; 
    float alpha; 
};

layout(std430, binding = 0) buffer ParticleBuffer {
    FireParticle particles[];
};

uniform float dt; 

void main(){
    uint id = gl_GlobalInvocationID.x; 


    if (particles[id].life >0.0) {
        particles[id].position += particles[id].velocity * dt; 

        particles[id].life -= dt; 
    }
}