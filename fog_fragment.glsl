#version 330 core

out vec4 fragColor;
in vec2 TexCoord;
in vec3 fragmentColor;

uniform sampler2D iChannel0;
uniform vec2 iResolution;
uniform float iTime;

float random(vec2 _st)
{
    return fract(sin(dot(_st.xy,
                         vec2(0.630, 0.710))) *
        43759.329);
}

float noise(vec2 _st)
{
    vec2 i = floor(_st);
    vec2 f = fract(_st);

    float a = random(i);
    float b = random(i + vec2(1.0, 0.0));
    float c = random(i + vec2(0.0, 1.0));
    float d = random(i + vec2(1.0, 1.0));

    vec2 u = f * f * (3.0 - 2.0 * f);

    return mix(a, b, u.x) +
            (c - a) * u.y * (1.0 - u.x) +
            (d - b) * u.x * u.y;
}

#define NUM_OCTAVES 6

float fbm(vec2 _st)
{
    float v = 0.0;
    float a = 0.5;
    vec2 shift = vec2(100.0, 100.0);
    mat2 rot = mat2(cos(0.5), sin(0.5),
                    -sin(0.5), cos(0.50));

    for (int i = 0; i < NUM_OCTAVES; ++i)
    {
        v += a * noise(_st);
        _st = _st * rot * 2.0 + shift;
        a *= 0.5;
    }
    return v;
}

vec3 FilterColor(vec3 color1, vec3 color2)
{
    return 1.0 - (1.0 - color1) * (1.0 - color2);
}

void main()
{
    vec2 uv = TexCoord;
    vec3 backcolor = texture(iChannel0, uv).rgb;
    uv.y = 1.0 - uv.y;

    vec2 st = uv * 10.0f;
    st.x += iTime * 0.1f;
    st.y -= iTime * 0.2f;
    vec3 color;

    vec2 q;
    q.x = fbm(st + 0.00 * iTime * 5.0);
    q.y = fbm(st + vec2(1.0, 1.0));

    vec2 r;
    r.x = fbm(st + 1.0 * q + vec2(1.7, 9.2) + 0.15 * iTime * 5.0);
    r.y = fbm(st + 1.0 * q + vec2(8.3, 2.8) + 0.126 * iTime * 5.0);

    float f = fbm(st + r);

    float fogIntensity = 0.3;

    color = mix(vec3(1.0, 1.0, 1.0),
                vec3(1.0, 1.0, 1.0),
                clamp((f * f) * 4.0 * fogIntensity, 0.0, 1.0));

    color = mix(color,
                vec3(1.0, 1.0, 1.0),
                clamp(length(q), 0.0, 1.0));

    color = mix(color,
                vec3(1.0, 1.0, 1.0),
                clamp(length(r.x), 0.0, 1.0));

    vec3 cloud = vec3((f * f * f + 0.3 * f * f + 0.5 * f) * color);

    cloud = mix(vec3(0.0f, 0.0f, 0.0f), cloud, uv.y);

    float blendFactor = 0.2;
    fragColor = vec4(FilterColor(cloud*blendFactor, backcolor), 1.0);
}