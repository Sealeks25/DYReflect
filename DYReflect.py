from ursina import *
from panda3d.core import BitMask32

reflection_init = True

def apply_shader(entity, color_map = 'static', normal_map = 'white', **shader_inputs):
    
    global reflection_init

    if reflection_init:
        reflection_init = False

        base.reflection_shader = Shader(
            vertex='''
            #version 330 core

            in vec2 p3d_MultiTexCoord0;
            in vec3 p3d_Normal;
            in vec4 p3d_Vertex;
            in vec4 p3d_Tangent;

            out float fragTangentW;
            out vec2 texcoord;
            out vec3 normal;
            out vec3 viewPos;
            out vec3 viewDir;
            out vec3 fragTangent;

            uniform mat4 p3d_ModelViewMatrix;
            uniform mat4 p3d_ModelViewProjectionMatrix;

            void main() {
                gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
                texcoord = p3d_MultiTexCoord0;
                viewPos = (p3d_ModelViewMatrix * p3d_Vertex).xyz;
                viewDir = normalize(-viewPos);
                mat3 mv3 = mat3(p3d_ModelViewMatrix);
                vec3 viewNormal = normalize(mv3 * p3d_Normal);
                normal = faceforward(-viewNormal, viewNormal, viewDir);
                fragTangent = normalize(mv3 * p3d_Tangent.xyz);
                fragTangentW = p3d_Tangent.w;
            }
            ''',
            fragment='''
            #version 330 core

            in float fragTangentW;
            in vec2 texcoord;
            in vec3 normal;
            in vec3 viewDir;
            in vec3 fragTangent;

            out vec4 fragColor;

            uniform float contrast;
            uniform float highlight;
            uniform float metallic;
            uniform float normals;
            uniform float reflection;
            uniform float specular;
            uniform sampler2D color_map;
            uniform sampler2D normal_map;
            uniform sampler2D p3d_Texture0;
            uniform vec3 colorTint;
            uniform vec4 p3d_ColorScale;
            uniform int use_bottom_mask;
            uniform int use_normal_uv;

            void main() {
                vec4 baseColor = texture(p3d_Texture0, texcoord);
                vec3 metallicBase = baseColor.rgb;
                metallicBase = (metallicBase - 0.5) * contrast + 0.5;
                metallicBase = clamp(metallicBase, 0.0, 1.0);
                metallicBase *= colorTint;
                vec3 Normals = normalize(normal);
                vec3 finalNormal;
                
                if (normals > 0.0) {
                    vec3 tang = normalize(fragTangent);
                    vec3 bitang = normalize(cross(Normals, tang)) * fragTangentW;
                    mat3 TBN = mat3(tang, bitang, Normals);
                    vec3 normalMap = texture(normal_map, texcoord).rgb * 2.0 - 1.0;
                    normalMap = mix(vec3(0.0, 0.0, 1.0), normalMap, normals);
                    normalMap = normalize(normalMap);
                    finalNormal = normalize(TBN * normalMap);
                } else {
                    finalNormal = Normals;
                }
                
                vec3 bentNormal = normalize(finalNormal + vec3(0.0, 1.0, 1.0));
                vec3 reflectionVector = reflect(-viewDir, bentNormal);
                reflectionVector = normalize(reflectionVector);
                vec4 reflectionColor;
                
                if (use_normal_uv == 1) {
                    float theta = atan(reflectionVector.x, reflectionVector.z);
                    float phi = acos(clamp(reflectionVector.y, -1.0, 1.0));
                    vec2 nUV = vec2(theta / 5.0 + 0.5, phi / 2.0);
                    reflectionColor = texture(color_map, nUV);
                } else {
                    vec2 reflectionUv = vec2(texcoord.x, texcoord.y);
                    reflectionUv += (1.0 - max(dot(finalNormal, viewDir), 0.0)) * 0.05;
                    reflectionColor = texture(color_map, reflectionUv);
                }
                
                float fresnel = smoothstep(0.0, 0.5, 1.0 - max(dot(finalNormal, viewDir), 0.0));
                float baseReflection = metallic * reflection;
                float fresnelHighlight = fresnel * highlight;
                vec3 reflectionPart = (baseReflection + fresnelHighlight) * reflectionColor.rgb;
                reflectionPart *= colorTint;
                
                if (use_bottom_mask == 1) {
                    if (!gl_FrontFacing) {
                        reflectionPart = vec3(0.0);
                    }
                }

                vec3 halfwayVector = normalize(normalize(vec3(0.0, 1.0, 0.5)) + viewDir);
                float specularFactor = pow(max(dot(finalNormal, halfwayVector), 0.0), 60.0) * specular;
                vec3 specularPart = specularFactor * fresnel * colorTint;
                vec3 finalColor = metallicBase + reflectionPart + specularPart;
                finalColor = clamp(finalColor, 0.0, 1.0);
                fragColor = vec4(finalColor, 1.0);
                fragColor *= p3d_ColorScale;
            }
            '''
        )

        base.buffer_static = base.win.make_texture_buffer(
            "buffer_static",
            int(base.win.getXSize() / 1.2),
            int(base.win.getYSize() * 1.2)
        )
        
        base.camera_static = base.make_camera(base.buffer_static)
        base.camera_static.reparentTo(render)
        base.camera_static.lookAt(0, -12, 0)
        base.camera_static.setPos(0, 36, 0)
        base.camera_static.node().getLens().setFov(69)
        base.camera_static.node().setCameraMask(BitMask32.bit(2))
        
        base.texture_static = base.buffer_static.get_texture()

        base.buffer_dynamic = base.win.make_texture_buffer(
            "buffer_dynamic",
            base.win.getXSize(),
            base.win.getYSize()
        )
        
        base.camera_dynamic = base.make_camera(base.buffer_dynamic)
        base.camera_dynamic.reparentTo(render)
        base.camera_dynamic.node().getLens().setFov(96)
        base.camera_dynamic.node().setCameraMask(BitMask32.bit(3))
        
        base.texture_dynamic = base.buffer_dynamic.get_texture()

    entity.shader = base.reflection_shader

    if color_map == 'static':
        texture = base.texture_static
        entity.hide(BitMask32.bit(2))
    elif color_map == 'dynamic':
        texture = base.texture_dynamic
        entity.hide(BitMask32.bit(3))

    entity.set_shader_input('color_map', texture)
    entity.set_shader_input('normal_map', normal_map)
    entity.set_shader_input('colorTint', (0.6, 0.6, 1.2))
    entity.set_shader_input('contrast', 1.2)
    entity.set_shader_input('highlight', 0.2)
    entity.set_shader_input('normals', 0.2)
    entity.set_shader_input('metallic', 0.6)
    entity.set_shader_input('reflection', 0.2)
    entity.set_shader_input('specular', 0.2)
    entity.set_shader_input('use_bottom_mask', 1)
    entity.set_shader_input('use_normal_uv', 0)   

    for key, value in shader_inputs.items():
        entity.set_shader_input(key, value)

    return entity

def set_camera_static(look_at, position):
    
    base.camera_static.setPos(*position)
    base.camera_static.lookAt(*look_at)

def update_camera_dynamic(look_at, position):

    base.camera_dynamic.setPos(*position)
    base.camera_dynamic.lookAt(*look_at)

