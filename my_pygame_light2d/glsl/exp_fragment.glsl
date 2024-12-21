#version 330 core

out vec4 fragColor;
in vec2 fragmentTexCoord;

uniform vec2 iResolution;
uniform float iTime;
uniform vec2 iSpawnPos; // New uniform for spawn position
uniform float iSpeed; 
uniform float iInitialAngle; // New uniform for initial angle


float seed = 0.32; // Starting seed
const float particles = 32.0; // Change particle count
float res = 96.0; // Pixel resolution
float gravity = 2.59; // Set gravity

void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
    vec2 uv = (-iResolution.xy + 2.0 * fragCoord.xy) / iResolution.y;
    float clr = 0.0;
    float timecycle = (iTime * iSpeed) - floor(iTime * iSpeed);
    seed = (seed + floor(iTime * iSpeed));

    // Testing
    float invres = 1.0 / res;
    float invparticles = 1.0 / particles;

    for (float i = 0.0; i < particles; i += 1.0)
    {
        seed += i + tan(seed+iInitialAngle);
        vec2 tPos = (vec2(cos(seed), sin(seed))) * i * invparticles;

        vec2 pPos = iSpawnPos; // Start with the spawn position
        pPos.x += ((tPos.x) * timecycle);
        pPos.y += -gravity * (timecycle * timecycle) + tPos.y * timecycle + pPos.y;

        pPos = floor(pPos * res) * invres; // Comment this out for smooth version 

        vec2 p1 = pPos;
        vec4 r1 = vec4(vec2(step(p1, uv)), 1.0 - vec2(step(p1 + invres, uv)));
        float px1 = r1.x * r1.y * r1.z * r1.w;
        float px2 = smoothstep(0.0, 200.0, (1.0 / distance(uv, pPos + .005))); // Added glow
        px1 = max(px1, px2);

        clr += px1 * (sin(iTime * 20.0 * iSpeed + i) + 1.0);
    }

    fragColor = vec4(clr * (1.0 - timecycle)) * vec4(4, 0.5, 0.1, 1.0);
}

void main()
{
    mainImage(fragColor, fragmentTexCoord * iResolution);
}
