import bpy
from bpy.types import AddonPreferences
from bpy.props import BoolProperty, IntProperty
from ..updater import addon_updater_ops

class MockSelf:
    """Mock object to provide layout attribute for updater functions"""
    def __init__(self, layout):
        self.layout = layout

class Hoyo2VRCPreferences(AddonPreferences):
    """Addon preferences for Hoyo2VRC with updater settings"""
    bl_idname = __package__.split('.')[0]  # This should be "Hoyo2VRC"
    
    # Auto-check settings
    auto_check_update: BoolProperty(
        name="Auto-check for Update",
        description="If enabled, auto-check for updates using an interval",
        default=True
    )

    # Update interval settings
    updater_interval_months: IntProperty(
        name='Months',
        description="Number of months between checking for updates",
        default=0,
        min=0
    )

    updater_interval_days: IntProperty(
        name='Days',
        description="Number of days between checking for updates",
        default=1,
        min=0,
        max=31
    )

    updater_interval_hours: IntProperty(
        name='Hours',
        description="Number of hours between checking for updates",
        default=23,
        min=0,
        max=23
    )

    updater_interval_minutes: IntProperty(
        name='Minutes',
        description="Number of minutes between checking for updates",
        default=0,
        min=0,
        max=59
    )

    def draw(self, context):
        """Draw the preferences panel"""
        layout = self.layout
        
        # Create mock self object for the updater functions
        mock_self = MockSelf(layout)
        
        # Update notice box - shows if update is available
        addon_updater_ops.update_notice_box_ui(mock_self, context)
        
        # Update settings UI - shows update preferences and controls
        addon_updater_ops.update_settings_ui(mock_self, context)

def draw_updater(layout):
    """Draw updater UI in the given layout"""
    # Updater Section
    box = layout.box()
    box.label(text="Updater", icon="URL")
    
    # Create mock self object for the updater functions
    mock_self = MockSelf(box)
    
    # Update notice box - shows if update is available
    addon_updater_ops.update_notice_box_ui(mock_self, bpy.context)
    
    # Update settings UI - shows update preferences and controls
    addon_updater_ops.update_settings_ui(mock_self, bpy.context)

def register_updater():
    """Register updater preferences - now handled in main classes list"""
    pass

def unregister_updater():
    """Unregister updater preferences - now handled in main classes list"""
    pass 