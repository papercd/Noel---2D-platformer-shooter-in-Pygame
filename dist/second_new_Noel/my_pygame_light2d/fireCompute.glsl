
#version 430

layout(local_size_x = 256) in; 

struct FireParticle {
    float damage;
    float life; 
    float maxlife; 
    float dead; 
    float i; 
    vec2 position;
    vec2 velocity;
    float sin; 
    float sinr; 
    float spread; 
    vec2 rise_normal; 
    float rise; 
    float rise_angle; 
    float r; 
    vec2 Os;
    float alpha; 
};

layout(std430, binding = 0) buffer ParticleBuffer {
    FireParticle particles[];
};

layout(std430, binding = 1) buffer ActiveIndicesBuffer{
    uint activeIndices[];
};

uniform float dt; 
uniform vec2 iResolution; 

void main(){
    uint id = gl_GlobalInvocationID.x; 

    if (ActiveIndicesBuffer[id] == 0) return;  

 

    uint particleIndex = activeIndices[id];

    FireParticle particle = particles[particleIndex];

    float scaled_dt = dt * 60;

    if (particle.life >0.0) {
        particle.damage = max(2.,particle.damage * (particle.life/particle.maxlife));

        particle.life -= scaled_dt;
        particle.i = round((particle.life / particle.maxlife) * 6);

        particle.velocity.x = ((particle.sin * sin(particle.life/(particle.sinr)))/2)*particle.spread * particle.rise_normal.x    + particle.rise * cos(radians(particle.rise_angle));
        particle.velocity.y = (particle.rise * sin(radians(particle.rise_angle)) + particle.rise_normal.y * particle.spread * ((particle.sin * sin(particle.life/(particle.sinr)))/2));



        particle.position += particle.velocity * scaled_dt; 
        
   

        particle.dead = 0;
    }else{
        particle.dead = 1;
    }

    particles[particleIndex] = particle; 
}