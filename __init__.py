bl_info = {
    "name": "Hoyo2VRC",
    "author": "Meliodas",
    "version": (5, 2, 1),
    "blender": (4, 0, 0),
    "location": "View3D > UI > Hoyo2VRC",
    "description": "Convert Hoyoverse models to VRChat",
    "warning": "",
    "doc_url": "",
    "category": "Import-Export",
}

import bpy
from .functions.converter import HOYO2VRC_OT_Convert
from .ui.main import HOYO2VRC_PT_MainPanel
from .ui.settings import register_settings, unregister_settings
from .ui.updater import register_updater, unregister_updater, Hoyo2VRCPreferences
from .io.hoyofbx import Hoyo2VRCImport, Hoyo2VRCExport
from .io.exporter import Hoyo2VRCExportFbx
from .io.importer import Hoyo2VRCImportFbx
from .updater import addon_updater_ops

classes = [
    HOYO2VRC_OT_Convert,
    HOYO2VRC_PT_MainPanel,
    Hoyo2VRCPreferences,
    Hoyo2VRCImport,
    Hoyo2VRCExport,
    Hoyo2VRCImportFbx,
    Hoyo2VRCExportFbx,
]

def register():
    """Register the addon"""
    # Register settings
    register_settings()
    
    # Register updater properties
    register_updater()
    
    # Register operators and panels
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Register addon updater
    addon_updater_ops.register(bl_info)

def unregister():
    """Unregister the addon"""
    # Unregister addon updater
    addon_updater_ops.unregister()
    
    # Unregister operators and panels
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    # Unregister updater properties
    unregister_updater()
    
    # Unregister settings
    unregister_settings()

if __name__ == "__main__":
    register() 