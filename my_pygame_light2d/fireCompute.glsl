
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

uniform float dt; 
uniform vec2 iResolution; 

void main(){
    uint id = gl_GlobalInvocationID.x; 

    float scaled_dt = dt * 60;

    if (particles[id].life >0.0) {
        particles[id].damage = max(2.,particles[id].damage * (particles[id].life/particles[id].maxlife));

        particles[id].life -= scaled_dt;
        particles[id].i = round((particles[id].life / particles[id].maxlife) * 6);

        particles[id].velocity.x = ((particles[id].sin * sin(particles[id].life/(particles[id].sinr)))/2)*particles[id].spread * particles[id].rise_normal.x    + particles[id].rise * cos(radians(particles[id].rise_angle));
        particles[id].velocity.y = (particles[id].rise * sin(radians(particles[id].rise_angle)) + particles[id].rise_normal.y * particles[id].spread * ((particles[id].sin * sin(particles[id].life/(particles[id].sinr)))/2));



        particles[id].position += particles[id].velocity * dt; 

        particles[id].life -= dt;

        particles[id].dead = 0;
    }else{
        particles[id].dead = 1;
    }
}