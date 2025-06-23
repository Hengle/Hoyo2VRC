import bpy

def draw_settings(layout):
    """Draw all settings in the given layout"""
    # Settings Section
    box = layout.box()
    box.label(text="Conversion Settings", icon="SETTINGS")
    
    # Mesh Settings
    box.prop(bpy.context.scene, "merge_all_meshes", 
            text="Merge Meshes",
            icon="CHECKBOX_HLT" if bpy.context.scene.merge_all_meshes else "CHECKBOX_DEHLT")
    
    box.prop(bpy.context.scene, "generate_shape_keys",
            text="Generate Shape Keys",
            icon="CHECKBOX_HLT" if bpy.context.scene.generate_shape_keys else "CHECKBOX_DEHLT")
    
    box.prop(bpy.context.scene, "keep_star_eye_mesh",
            text="Keep Star Eye Mesh",
            icon="CHECKBOX_HLT" if bpy.context.scene.keep_star_eye_mesh else "CHECKBOX_DEHLT")
    

def register_settings():
    # UI Display Settings
    bpy.types.Scene.hoyo2vrc_show_conversion = bpy.props.BoolProperty(
        name="Show Conversion Section",
        description="Show/Hide the conversion section",
        default=True
    )
    
    bpy.types.Scene.hoyo2vrc_show_settings = bpy.props.BoolProperty(
        name="Show Settings Section",
        description="Show/Hide the settings section",
        default=True
    )
    
    # Conversion State
    bpy.types.Object.hoyo2vrc_converted = bpy.props.BoolProperty(
        name="Converted",
        description="Whether this model has been converted",
        default=False
    )

    # Mesh Settings
    bpy.types.Scene.merge_all_meshes = bpy.props.BoolProperty(
        name="Merge Meshes",
        description="Merge all meshes into a single mesh",
        default=False
    )

    bpy.types.Scene.generate_shape_keys = bpy.props.BoolProperty(
        name="Generate Shape Keys",
        description="Generate shape keys for the model",
        default=True
    )

    bpy.types.Scene.keep_star_eye_mesh = bpy.props.BoolProperty(
        name="Keep Star Eye Mesh",
        description="Keep the star eye mesh in the model",
        default=False
    )
    

def unregister_settings():
    # UI Display Settings
    del bpy.types.Scene.hoyo2vrc_show_conversion
    del bpy.types.Scene.hoyo2vrc_show_settings
    
    # Mesh Settings
    del bpy.types.Scene.merge_all_meshes
    
    # Additional Features
    del bpy.types.Scene.generate_shape_keys
    del bpy.types.Scene.keep_star_eye_mesh 