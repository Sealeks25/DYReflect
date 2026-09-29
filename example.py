import DYReflect as dyr   # Import the dynamic reflection module with a concise alias
from ursina import *

app = Ursina()           

EditorCamera()   # Enable built-in editor camera controls for scene navigation

# --- Scene objects setup ---

cube = Entity(
    model = 'cube',                    
    texture = 'glare',
    texture_scale = (1.2, 12),
    scale = 3,                        
    position = (0, 6, 0)               
)

floor = Entity(
    model = 'plane',                   
    double_sided = True,               
    color = color.rgb(0.6, 1.2, 0.6),  
    texture = 'floor',               
    scale = 36                         
)

sphere = Entity(
    model = 'sphere.glb',   # Custom 3D model (GLB format)
    scale = 3,
    position = (12, 6, 0)           
)

# --- Apply dynamic reflections ---

# Apply default shader to the floor 
# dyr.apply_shader(floor) 

# Add a normal map to the floor for surface relief/detail
dyr.apply_shader(floor, normal_map = 'floor_normal')

dyr.apply_shader(sphere, 
    color_map = 'dynamic',         # Use dynamic color mapping
    colorTint = (0.6, 0.6, 1.2),   # Slightly desaturate the base color
    highlight = 0,                 # Disable additional highlights
    normals = 0,                   # Disable normal map effect
    metallic = 0.6,                # Moderate metallic property
    reflection = 0.6,              # Reflection strength
    specular = 1.2,                # Specular highlight intensity
    use_bottom_mask = 0,           # Disable bottom masking
    use_normal_uv = 1              # Use normal UV coordinates for effects
)

def update():

    # Static camera config for floor reflections (optional):  
    # This sets a fixed camera direction/position for floor reflections.
    # By default, uses optimized values; customize here if reflections 
    # in your scene look different than expected.
    # dyr.set_camera_static((0, -12, 0), (0, 36, 0))

    # Dynamic reflection camera config (optional): 
    # This prevents the sphere from reflecting objects behind it.
    # Adjust bounds here if you want reflections to cover a different area.
    if camera.world_position.x > 0:
        dyr.update_camera_dynamic((0, 36, 0), (0, -36, 0))
    else:
        dyr.update_camera_dynamic((0, -36, 0), (0, 36, 0))
        
app.run() 
