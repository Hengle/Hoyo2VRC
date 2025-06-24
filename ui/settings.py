import bpy
from ..functions.game_detection import GameDetector

def get_game_icon(game_name):
    """Get appropriate icon for each game"""
    game_icons = {
        'Genshin Impact': 'WORLD',
        'Genshin Impact Weapon': 'TOOL_SETTINGS',
        'Honkai Star Rail': 'LIGHTPROBE_PLANAR',
        'Honkai Impact 3rd': 'OUTLINER_DATA_LIGHTPROBE',
        'Zenless Zone Zero': 'GHOST_ENABLED',
        'Wuthering Waves': 'FORCE_WIND'
    }
    return game_icons.get(game_name, 'RESTRICT_VIEW_OFF')

def draw_settings(layout):
    """Draw all settings in the given layout"""
    # Get current model info to determine game context
    model_info, display_name, icon = GameDetector.get_model_name(bpy.context)
    current_game = model_info.game if model_info else None
    
    # Only show settings if there's a supported game
    if not current_game or not GameDetector.is_game_supported(current_game):
        # Settings Section (but empty)
        box = layout.box()
        box.label(text="Conversion Settings", icon="SETTINGS")
        
        # Show message about no supported game
        help_row = box.row()
        help_row.alignment = 'CENTER'
        if not current_game:
            help_row.label(text="Select a supported model to view settings", icon='INFO')
        else:
            help_row.label(text="No settings available for " + current_game, icon='INFO')
        return
    
    # Settings Section
    box = layout.box()
    box.label(text="Conversion Settings", icon="SETTINGS")
    
    # Show game context
    row = box.row()
    row.alignment = 'CENTER'
    game_icon = get_game_icon(current_game)
    row.label(text=f"Settings for {current_game}", icon=game_icon)
    box.separator()
    
    # Define setting configurations with game compatibility
    setting_configs = {
        'merge_all_meshes': {
            'text': 'Merge Meshes',
            'games': {'Genshin Impact', 'Genshin Impact Weapon', 'Honkai Star Rail', 
                     'Honkai Impact 3rd', 'Zenless Zone Zero', 'Wuthering Waves'},
            'description': 'Combine all mesh objects into a single mesh',
            'category': 'mesh'
        },
        'generate_shape_keys': {
            'text': 'Generate VRChat Shape Keys',
            'games': {'Genshin Impact', 'Honkai Star Rail', 'Honkai Impact 3rd', 
                     'Zenless Zone Zero', 'Wuthering Waves'},
            'description': 'Create VRChat viseme and expression shape keys',
            'category': 'shapekey'
        },
        'generate_shape_keys_mmd': {
            'text': 'Generate MMD Shape Keys',
            'games': {'Genshin Impact', 'Honkai Star Rail', 'Honkai Impact 3rd', 'Zenless Zone Zero', 'Wuthering Waves'},
            'description': 'Create MMD-compatible facial expression shape keys',
            'category': 'shapekey'
        },
        'keep_star_eye_mesh': {
            'text': 'Keep Star Eye Mesh',
            'games': {'Genshin Impact'},
            'description': 'Preserve special star-shaped eye effects mesh',
            'category': 'mesh'
        }
    }
    
    # Group settings by category for better organization
    categories = {
        'mesh': {'name': 'Mesh Options', 'icon': 'MESH_DATA'},
        'shapekey': {'name': 'Shapekey Options', 'icon': 'ANIM_DATA'}
    }
    
    # Draw settings for the current supported game
    for category_key, category_info in categories.items():
        category_settings = [k for k, v in setting_configs.items() 
                           if v['category'] == category_key and current_game in v['games']]
        
        if not category_settings:
            continue
            
        # Draw category header if there are multiple categories with settings
        total_settings = sum(1 for k, v in setting_configs.items() 
                           if current_game in v['games'])
        if total_settings > 2:
            sub_box = box.box()
            header_row = sub_box.row()
            header_row.label(text=category_info['name'], icon=category_info['icon'])
        else:
            sub_box = box
        
        # Draw each setting in this category
        for setting_key in category_settings:
            config = setting_configs[setting_key]
            
            # Create the property row
            row = sub_box.row()
            
            # Draw the setting
            setting_value = getattr(bpy.context.scene, setting_key, False)
            row.prop(bpy.context.scene, setting_key, 
                    text=config['text'],
                    icon="CHECKBOX_HLT" if setting_value else "CHECKBOX_DEHLT")

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

    bpy.types.Scene.generate_shape_keys_mmd = bpy.props.BoolProperty(
        name="Generate MMD Shape Keys",
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
    del bpy.types.Scene.generate_shape_keys_mmd
    del bpy.types.Scene.keep_star_eye_mesh 