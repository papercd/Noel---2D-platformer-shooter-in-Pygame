#version 330 core

in vec2 fragmentTexCoord;// top-left is [0, 1] and bottom-right is [1, 0]
uniform sampler2D imageTexture;// texture in location 0

uniform float u_alpha =1; 
uniform float time;  // For animation

out vec4 color;


void main() {
    vec4 texColor = texture(imageTexture, fragmentTexCoord);

    
    // Shimmer Effect - Faster shimmer for flame-like or mist-like behavior
    float shimmer = 0.2 + 0.2 * sin(time * 3.0 + fragmentTexCoord.y * 15.0);  // Faster shimmer on Y
    shimmer += 0.2 * sin(time * 2.5 + fragmentTexCoord.x * 5.0);  // Faster shimmer on X

    // Flame-like color: Changing colors dynamically based on time
    vec3 flameColor = vec3(
        0.5 + 0.5 * sin(time * 0.8 + 0.0),  // Red-like component, faster
        0.5 + 0.5 * sin(time * 0.8 + 2.0),  // Greenish/yellowish component, faster
        0.5 + 0.5 * sin(time * 0.8 + 4.0)   // Blueish component, faster
    );

    // Apply shimmer to the glow effect and increase intensity
    texColor.rgb += shimmer * flameColor * 1.5;  // Boost glow intensity

    // Faster pulse effect for the item itself
    float pulse = 0.5 + 0.5 * sin(time * 4.0);  // Faster pulse speed
    texColor.rgb += pulse * 0.1 * flameColor;  // Optional additional pulse effect


    // Extended Procedural Mist Effect (flame-like mist emanating from the item)
    // Distance from the item center, we use the fragmentTexCoord to simulate mist spread
    float distToCenter = length(fragmentTexCoord - vec2(0.5, 0.5)); // Assuming the item is at the center (0.5, 0.5)
    
    // Scale the distance calculation for small textures, allowing the mist to spread further
    distToCenter *= 2.0; // Increase distance factor for small textures (adjust as needed)
    
    // Control the spread of the mist: bigger values = faster spread
    float mistIntensity = exp(-distToCenter * distToCenter * 10 ); // Increased spreading for more visible mist
    mistIntensity *= 0.5 + 0.5 * sin(time * 2.0); // Optional oscillation for dynamic mist look

    // Procedural noise to simulate the movement of the mist (flame-like behavior)
    float noise = sin(fragmentTexCoord.x * 10.0 + time * 3.0) * cos(fragmentTexCoord.y * 10.0 + time * 3.0);
    
    // Combine mist and noise
    float finalMistEffect = mistIntensity * (0.2 + 0.2 * noise); // Adjust this to control mist behavior
    
    // Apply the final mist effect to both the item and empty space (alpha = 0)
    texColor.rgb += finalMistEffect * vec3(1.0, 0.5, 0.0);  // Flame-like color for the mist (orange)

    // Final alpha check: If the texture is transparent, keep mist visible
    if (texColor.a == 0.0) {
        texColor.rgb = finalMistEffect * vec3(1.0, 0.5, 0.0);  // Apply mist color to transparent areas
    }

    color = texColor * u_alpha;  // Apply transparency (if needed)
}
