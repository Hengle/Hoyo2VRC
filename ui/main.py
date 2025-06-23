import bpy
from bpy.types import Panel
from .. import bl_info
from . import settings
from . import updater
from ..functions.game_detection import GameDetector

class HOYO2VRC_PT_MainPanel(Panel):
    bl_label = bl_info["name"] + " " + ".".join(str(x) for x in bl_info["version"])
    bl_idname = "HOYO2VRC_PT_MainPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Hoyo2VRC"

    def draw(self, context):
        layout = self.layout

        # Import/Export Section
        box = layout.box()
        row = box.row(align=True)
        row.operator("hoyo2vrc.import", text="Import", icon='IMPORT')
        row.operator("hoyo2vrc.export", text="Export", icon='EXPORT')
        
        # Convert Section
        box = layout.box()
        
        # Get active object
        active_obj = context.active_object
        
        if active_obj and active_obj.type == 'ARMATURE' and active_obj.get("hoyo2vrc_converted"):
            # Display stored model info for converted models
            row = box.row()
            row.alignment = 'CENTER'
            row.label(text=active_obj.get("hoyo2vrc_model_name", "Unknown Model"), icon='OUTLINER_OB_ARMATURE')
            
            if active_obj.get("hoyo2vrc_game"):
                row = box.row()
                row.alignment = 'CENTER'
                row.label(text=active_obj.get("hoyo2vrc_game"), icon='RESTRICT_VIEW_OFF')
                
            if active_obj.get("hoyo2vrc_body_type"):
                row = box.row()
                row.alignment = 'CENTER'
                row.label(text=active_obj.get("hoyo2vrc_body_type"), icon='ARMATURE_DATA')
                
            row = box.row()
            row.alignment = 'CENTER'
            row.label(text="Model Converted", icon='CHECKMARK')
        else:
            # Get model info and display clean name for unconverted models
            model_info, display_name, icon = GameDetector.get_model_name(context)
            row = box.row()
            row.alignment = 'CENTER'
            row.label(text=display_name, icon=icon)

            # Game info
            if model_info and model_info.game:
                row = box.row()
                row.alignment = 'CENTER'
                row.label(text=f"{model_info.game}", icon='RESTRICT_VIEW_OFF')
                
                # Body type info (if available)
                if model_info.body_type:
                    row = box.row()
                    row.alignment = 'CENTER' 
                    row.label(text=f"{model_info.body_type}", icon='ARMATURE_DATA')
            
            # Convert button or status
            if context.active_object:
                if model_info.is_legacy:
                    row = box.row()
                    row.alignment = 'CENTER'
                    row.label(text="Old Face Not Supported", icon='ERROR')
                else:
                    box.operator("hoyo2vrc.convert", text="Convert", icon='PLAY')

        # Conversion Settings Section
        settings.draw_settings(layout)
        
        # Updater Section
        updater.draw_updater(layout)