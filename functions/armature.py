import bpy
from typing import Optional, Union
import mathutils

class ArmatureUtils:
    """Utility class for armature operations"""
    
    @staticmethod
    def clear_rotation(context: Optional[bpy.types.Context] = None) -> bool :
        """Clear the rotation of the armature"""
        if not context:
            context = bpy.context
            
        armature = context.active_object
        if not armature or armature.type != 'ARMATURE':
            return False
        
        armature.rotation_euler = (0, 0, 0)
        return True
    
    @staticmethod
    def rename_bones(context: Optional[bpy.types.Context] = None) -> bool:
        """Rename bones from Bip naming scheme to Unity humanoid naming scheme
        
        Args:
            context: Optional context. If None, uses bpy.context
            
        Returns:
            bool: True if successful, False if no armature found
        """
        if not context:
            context = bpy.context
            
        armature = context.active_object
        if not armature or armature.type != 'ARMATURE':
            print("No armature found")
            return False
            
        # Dictionary mapping Bip names to Unity humanoid names
        bone_map = {
            "Bip001": "Root",
            "Bip001 Pelvis": "Hips",
            "Bip001Pelvis": "Hips",
            "Bip001 Spine": "Spine",
            "Bip001Spine": "Spine", 
            "Bip001 Spine1": "Chest",
            "Bip001Spine1": "Chest",
            "Bip001 Spine2": "Upper Chest",
            "Bip001Spine2": "Upper Chest",
            "Bip001 Neck": "Neck",
            "Bip001Neck": "Neck",
            "Bip001 Head": "Head",
            "Bip001Head": "Head",
            "Root_M": "Hips",
            "Spine1_M": "Spine",
            "Spine2_M": "Chest",
            "Chest_M": "Upper Chest",
            "Neck_M": "Neck",
            "Head_M": "Head",
            "joint_face": "Face",
            "breast_R": "Breast_R",
            "breast_L": "Breast_L",

            # Left arm
            "Bip001 L Clavicle": "Left Shoulder",
            "Bip001LClavicle": "Left Shoulder",
            "Bip001 L UpperArm": "Left Upper Arm",
            "Bip001LUpperArm": "Left Upper Arm",
            "Bip001 L Forearm": "Left Lower Arm",
            "Bip001LForearm": "Left Lower Arm",
            "Bip001 L Hand": "Left Hand",
            "Bip001LHand": "Left Hand",

            "Scapula_L": "Left Shoulder",   
            "Shoulder_L": "Left Upper Arm",
            "Elbow_L": "Left Lower Arm",
            "Wrist_L": "Left Hand",
            
            # Right arm
            "Bip001 R Clavicle": "Right Shoulder",
            "Bip001RClavicle": "Right Shoulder",
            "Bip001 R UpperArm": "Right Upper Arm",
            "Bip001RUpperArm": "Right Upper Arm", 
            "Bip001 R Forearm": "Right Lower Arm",
            "Bip001RForearm": "Right Lower Arm",
            "Bip001 R Hand": "Right Hand",
            "Bip001RHand": "Right Hand",

            "Scapula_R": "Right Shoulder",
            "Shoulder_R": "Right Upper Arm",
            "Elbow_R": "Right Lower Arm",
            "Wrist_R": "Right Hand",

            # Left leg
            "Bip001 L Thigh": "Left Upper Leg",
            "Bip001LThigh": "Left Upper Leg",
            "Bip001 L Calf": "Left Lower Leg",
            "Bip001LCalf": "Left Lower Leg",
            "Bip001 L Foot": "Left Foot",
            "Bip001LFoot": "Left Foot",
            "Bip001 L Toe0": "Left Toes",
            "Bip001LToe0": "Left Toes",

            "Hip_L": "Left Upper Leg",
            "Knee_L": "Left Lower Leg",
            "Ankle_L": "Left Foot",
            "Toes_L": "Left Toes",
            
            # Right leg  
            "Bip001 R Thigh": "Right Upper Leg",
            "Bip001RThigh": "Right Upper Leg",
            "Bip001 R Calf": "Right Lower Leg",
            "Bip001RCalf": "Right Lower Leg",
            "Bip001 R Foot": "Right Foot",
            "Bip001RFoot": "Right Foot",
            "Bip001 R Toe0": "Right Toes",
            "Bip001RToe0": "Right Toes",

            "Hip_R": "Right Upper Leg",
            "Knee_R": "Right Lower Leg",
            "Ankle_R": "Right Foot",
            "Toes_R": "Right Toes",

            # Fingers left
            "Bip001 L Finger0": "Left Thumb Proximal",
            "Bip001LFinger0": "Left Thumb Proximal",
            "Bip001 L Finger01": "Left Thumb Intermediate",
            "Bip001LFinger01": "Left Thumb Intermediate",
            "Bip001 L Finger02": "Left Thumb Distal",
            "Bip001LFinger02": "Left Thumb Distal",
            "Bip001 L Finger03": "Left Thumb Terminal",
            "Bip001LFinger03": "Left Thumb Terminal",
            "Bip001 L Finger1": "Left Index Proximal",
            "Bip001LFinger1": "Left Index Proximal",
            "Bip001 L Finger11": "Left Index Intermediate",
            "Bip001LFinger11": "Left Index Intermediate",
            "Bip001 L Finger12": "Left Index Distal",
            "Bip001LFinger12": "Left Index Distal",
            "Bip001 L Finger13": "Left Index Terminal",
            "Bip001LFinger13": "Left Index Terminal",
            "Bip001 L Finger2": "Left Middle Proximal",
            "Bip001LFinger2": "Left Middle Proximal",
            "Bip001 L Finger21": "Left Middle Intermediate",
            "Bip001LFinger21": "Left Middle Intermediate",
            "Bip001 L Finger22": "Left Middle Distal",
            "Bip001LFinger22": "Left Middle Distal",
            "Bip001 L Finger23": "Left Middle Terminal",
            "Bip001LFinger23": "Left Middle Terminal",
            "Bip001 L Finger3": "Left Ring Proximal",
            "Bip001LFinger3": "Left Ring Proximal",
            "Bip001 L Finger31": "Left Ring Intermediate",
            "Bip001LFinger31": "Left Ring Intermediate",
            "Bip001 L Finger32": "Left Ring Distal",
            "Bip001LFinger32": "Left Ring Distal",
            "Bip001 L Finger33": "Left Ring Terminal",
            "Bip001LFinger33": "Left Ring Terminal",
            "Bip001 L Finger4": "Left Little Proximal",
            "Bip001LFinger4": "Left Little Proximal",
            "Bip001 L Finger41": "Left Little Intermediate",
            "Bip001LFinger41": "Left Little Intermediate",
            "Bip001 L Finger42": "Left Little Distal",
            "Bip001LFinger42": "Left Little Distal",
            "Bip001 L Finger43": "Left Little Terminal",
            "Bip001LFinger43": "Left Little Terminal",


            "ThumbFinger1_L": "Left Thumb Proximal",
            "ThumbFinger2_L": "Left Thumb Intermediate",
            "ThumbFinger3_L": "Left Thumb Distal",
            "IndexFinger1_L": "Left Index Proximal", 
            "IndexFinger2_L": "Left Index Intermediate",
            "IndexFinger3_L": "Left Index Distal",
            "MiddleFinger1_L": "Left Middle Proximal",
            "MiddleFinger2_L": "Left Middle Intermediate", 
            "MiddleFinger3_L": "Left Middle Distal",
            "RingFinger1_L": "Left Ring Proximal",
            "RingFinger2_L": "Left Ring Intermediate",
            "RingFinger3_L": "Left Ring Distal",
            "PinkyFinger1_L": "Left Little Proximal",
            "PinkyFinger2_L": "Left Little Intermediate",
            "PinkyFinger3_L": "Left Little Distal",
            
            # Fingers right
            "Bip001 R Finger0": "Right Thumb Proximal",
            "Bip001RFinger0": "Right Thumb Proximal",
            "Bip001 R Finger01": "Right Thumb Intermediate",
            "Bip001RFinger01": "Right Thumb Intermediate",
            "Bip001 R Finger02": "Right Thumb Distal",
            "Bip001RFinger02": "Right Thumb Distal",
            "Bip001 R Finger03": "Right Thumb Terminal",    
            "Bip001RFinger03": "Right Thumb Terminal",
            "Bip001 R Finger1": "Right Index Proximal",
            "Bip001RFinger1": "Right Index Proximal",
            "Bip001 R Finger11": "Right Index Intermediate",
            "Bip001RFinger11": "Right Index Intermediate",
            "Bip001 R Finger12": "Right Index Distal",
            "Bip001RFinger12": "Right Index Distal",
            "Bip001 R Finger13": "Right Index Terminal",
            "Bip001RFinger13": "Right Index Terminal",
            "Bip001 R Finger2": "Right Middle Proximal",
            "Bip001RFinger2": "Right Middle Proximal",
            "Bip001 R Finger21": "Right Middle Intermediate",
            "Bip001RFinger21": "Right Middle Intermediate",
            "Bip001 R Finger22": "Right Middle Distal",
            "Bip001RFinger22": "Right Middle Distal",
            "Bip001 R Finger23": "Right Middle Terminal",
            "Bip001RFinger23": "Right Middle Terminal",
            "Bip001 R Finger3": "Right Ring Proximal",
            "Bip001RFinger3": "Right Ring Proximal",
            "Bip001 R Finger31": "Right Ring Intermediate",
            "Bip001RFinger31": "Right Ring Intermediate",
            "Bip001 R Finger32": "Right Ring Distal",
            "Bip001RFinger32": "Right Ring Distal",
            "Bip001 R Finger33": "Right Ring Terminal",
            "Bip001RFinger33": "Right Ring Terminal",
            "Bip001 R Finger4": "Right Little Proximal",
            "Bip001RFinger4": "Right Little Proximal",
            "Bip001 R Finger41": "Right Little Intermediate",
            "Bip001RFinger41": "Right Little Intermediate",
            "Bip001 R Finger42": "Right Little Distal",
            "Bip001RFinger42": "Right Little Distal",
            "Bip001 R Finger43": "Right Little Terminal",
            "Bip001RFinger43": "Right Little Terminal",


            "ThumbFinger1_R": "Right Thumb Proximal",
            "ThumbFinger2_R": "Right Thumb Intermediate",
            "ThumbFinger3_R": "Right Thumb Distal",
            "IndexFinger1_R": "Right Index Proximal",
            "IndexFinger2_R": "Right Index Intermediate", 
            "IndexFinger3_R": "Right Index Distal",
            "MiddleFinger1_R": "Right Middle Proximal",
            "MiddleFinger2_R": "Right Middle Intermediate",
            "MiddleFinger3_R": "Right Middle Distal",
            "RingFinger1_R": "Right Ring Proximal",
            "RingFinger2_R": "Right Ring Intermediate",
            "RingFinger3_R": "Right Ring Distal",
            "PinkyFinger1_R": "Right Little Proximal",
            "PinkyFinger2_R": "Right Little Intermediate",
            "PinkyFinger3_R": "Right Little Distal"
        }
        
        # Switch to edit mode
        bpy.ops.object.mode_set(mode='EDIT')
        
        # Rename bones based on mapping
        for bone in armature.data.edit_bones:
            if bone.name in bone_map:
                bone.name = bone_map[bone.name]
                
        # Switch back to object mode
        bpy.ops.object.mode_set(mode='OBJECT')
        
        print("Bone renaming complete")
        return True

    @staticmethod
    def reset_bone_roll(context: Optional[bpy.types.Context] = None) -> bool:
        """Reset the roll of the armature bones to align with the global axes"""
        if not context:
            context = bpy.context
            
        armature = context.active_object
        if not armature or armature.type != 'ARMATURE':
            return False
            
        # Need to be in edit mode to modify bone roll
        bpy.ops.object.mode_set(mode='EDIT')
        
        # Reset roll for each bone
        for bone in armature.data.edit_bones:
            bone.roll = 0
            
        # Return to object mode
        bpy.ops.object.mode_set(mode='OBJECT')
        
        print("Bone roll reset complete")
        return True

    @staticmethod
    def rename_armature_data(context: Optional[bpy.types.Context] = None, new_name: str = "Armature") -> bool:
        """Rename only the armature data object, not the parent object
        
        Args:
            context: Optional context. If None, uses bpy.context
            new_name: The new name for the armature data
            
        Returns:
            bool: True if successful, False if no armature found
        """
        if not context:
            context = bpy.context
            
        # Find armature object
        armature = context.active_object
        if not armature or armature.type != 'ARMATURE':
            print("No armature found")
            return False
            
        try:
            # Only rename the data, not the object
            armature.data.name = new_name
            print(f"Renamed armature data to '{new_name}'")
            return True
        except Exception as e:
            print(f"Error renaming armature data: {str(e)}")
            return False

    @staticmethod
    def clean_bones(context: Optional[bpy.types.Context] = None, bones_to_remove: dict = None) -> bool:
        """Remove specified bones from the armature
        
        Args:
            context: Optional context. If None, uses bpy.context
            bones_to_remove: Dictionary of bone names to remove
            
        Returns:
            bool: True if successful, False if no armature found
        """
        if not context:
            context = bpy.context
            
        if not bones_to_remove:
            return True
            
        armature = context.active_object
        if not armature or armature.type != 'ARMATURE':
            print("No armature found")
            return False
            
        try:
            # Need to be in edit mode to remove bones
            bpy.ops.object.mode_set(mode='EDIT')
            
            # Remove each bone in the dictionary
            for bone_name in bones_to_remove:
                if bone_name in armature.data.edit_bones:
                    bone = armature.data.edit_bones[bone_name]
                    armature.data.edit_bones.remove(bone)
                    print(f"Removed bone: {bone_name}")
            
            # Return to object mode
            bpy.ops.object.mode_set(mode='OBJECT')
            return True
            
        except Exception as e:
            print(f"Error removing bones: {str(e)}")
            return False

    @staticmethod
    def reparent_bones(context: Optional[bpy.types.Context] = None, bones_to_reparent: dict = None, new_parent: str = None) -> bool:
        """Reparent specified bones to a new parent bone
        
        Args:
            context: Optional context. If None, uses bpy.context
            bones_to_reparent: Dictionary of bone names to reparent
            new_parent: Name of the new parent bone
            
        Returns:
            bool: True if successful, False if no armature or bones found
        """
        if not context:
            context = bpy.context
            
        if not bones_to_reparent or not new_parent:
            return True
            
        armature = context.active_object
        if not armature or armature.type != 'ARMATURE':
            print("No armature found")
            return False
            
        try:
            # Need to be in edit mode to reparent bones
            bpy.ops.object.mode_set(mode='EDIT')
            
            # Get the new parent bone
            if new_parent not in armature.data.edit_bones:
                print(f"Parent bone {new_parent} not found")
                return False
                
            parent_bone = armature.data.edit_bones[new_parent]
            
            # Reparent each bone in the dictionary
            for bone_name in bones_to_reparent:
                if bone_name in armature.data.edit_bones:
                    bone = armature.data.edit_bones[bone_name]
                    bone.parent = parent_bone
                    print(f"Reparented bone {bone_name} to {new_parent}")
            
            # Return to object mode
            bpy.ops.object.mode_set(mode='OBJECT')
            return True
            
        except Exception as e:
            print(f"Error reparenting bones: {str(e)}")
            return False
    
    @staticmethod
    def position_bone(context: Optional[bpy.types.Context] = None,
                     target_bone: str = None,
                     reference_points: dict = None,
                     position_rules: dict = None) -> bool:
        """Position a bone based on reference points and positioning rules
        
        Args:
            context: Optional context. If None, uses bpy.context
            target_bone: Name of bone to position
            reference_points: Dictionary of reference bones/points, e.g.:
                {
                    "left": "Left Upper Leg",
                    "right": "Right Upper Leg",
                    "up": "Spine"
                }
            position_rules: Dictionary of positioning rules, e.g.:
                {
                    "head": {
                        "horizontal": {"method": "between", "points": ["left", "right"], "ratio": 0.5},
                        "vertical": {"method": "between", "points": ["left", "up"], "ratio": 0.33},
                        "min_offset": {"axis": "z", "reference": "left", "value": 0.1}
                    },
                    "tail": {
                        "follow_head": ["x", "y"],
                        "vertical": {"method": "offset", "reference": "up", "value": 0.03},
                        "min_length": 0.1
                    }
                }
            
        Returns:
            bool: True if successful, False if error occurs
        """
        if not context:
            context = bpy.context
            
        if not target_bone or not reference_points or not position_rules:
            return False
            
        armature = context.active_object
        if not armature or armature.type != 'ARMATURE':
            print("No armature found")
            return False
            
        try:
            # Get coordinate system
            x_cord, y_cord, z_cord, is_fbx = ArmatureUtils.get_orientations(context)
            axis_map = {'x': x_cord, 'y': y_cord, 'z': z_cord}
            
            # Switch to edit mode
            bpy.ops.object.mode_set(mode='EDIT')
            bones = armature.data.edit_bones
            
            # Get target bone
            if target_bone not in bones:
                print(f"Target bone {target_bone} not found")
                return False
            target = bones[target_bone]
            
            # Get reference bones
            refs = {}
            for key, bone_name in reference_points.items():
                if bone_name not in bones:
                    print(f"Reference bone {bone_name} not found")
                    return False
                refs[key] = bones[bone_name]
            
            # Position head
            if "head" in position_rules:
                head_rules = position_rules["head"]
                
                # Handle follow positioning (copy position from another bone's head or tail)
                if "follow" in head_rules:
                    rule = head_rules["follow"]
                    ref_bone = refs[rule["reference"]]
                    point = ref_bone.tail if rule["point"] == "tail" else ref_bone.head
                    for i in range(3):
                        target.head[i] = point[i]
                
                # Handle horizontal positioning
                if "horizontal" in head_rules:
                    rule = head_rules["horizontal"]
                    if rule["method"] == "between":
                        point1 = refs[rule["points"][0]].head
                        point2 = refs[rule["points"][1]].head
                        ratio = rule["ratio"]
                        target.head[x_cord] = point1[x_cord] + (point2[x_cord] - point1[x_cord]) * ratio
                        target.head[y_cord] = point1[y_cord] + (point2[y_cord] - point1[y_cord]) * ratio
                
                # Handle vertical positioning
                if "vertical" in head_rules:
                    rule = head_rules["vertical"]
                    if rule["method"] == "between":
                        point1 = refs[rule["points"][0]].head
                        point2 = refs[rule["points"][1]].head
                        ratio = rule["ratio"]
                        target.head[z_cord] = point1[z_cord] + (point2[z_cord] - point1[z_cord]) * ratio
                    elif rule["method"] == "offset":
                        ref_point = refs[rule["reference"]].head[z_cord]
                        target.head[z_cord] = ref_point + rule["value"]
                
                # Apply minimum offset if specified
                if "min_offset" in head_rules:
                    rule = head_rules["min_offset"]
                    axis = axis_map[rule["axis"]]
                    ref_point = refs[rule["reference"]].head[axis]
                    min_value = ref_point + rule["value"]
                    if target.head[axis] <= ref_point:
                        target.head[axis] = min_value
            
            # Position tail
            if "tail" in position_rules:
                tail_rules = position_rules["tail"]
                
                # Make tail follow head position
                if "follow_head" in tail_rules:
                    for axis in tail_rules["follow_head"]:
                        target.tail[axis_map[axis]] = target.head[axis_map[axis]]
                
                # Handle vertical positioning
                if "vertical" in tail_rules:
                    rule = tail_rules["vertical"]
                    if rule["method"] == "offset":
                        if rule["reference"] == "head":
                            ref_point = target.head[z_cord]
                        else:
                            ref_point = refs[rule["reference"]].head[z_cord]
                        target.tail[z_cord] = ref_point + rule["value"]
                
                # Handle forward/backward positioning
                if "forward" in tail_rules:
                    rule = tail_rules["forward"]
                    if rule["method"] == "offset":
                        if rule["reference"] == "head":
                            ref_point = target.head[y_cord]
                        else:
                            ref_point = refs[rule["reference"]].head[y_cord]
                        target.tail[y_cord] = ref_point + rule["value"]
                
                # Ensure minimum bone length
                if "min_length" in tail_rules:
                    min_length = tail_rules["min_length"]
                    if target.tail[z_cord] < target.head[z_cord] + min_length:
                        target.tail[z_cord] = target.head[z_cord] + min_length
            
            bpy.ops.object.mode_set(mode='OBJECT')
            return True
            
        except Exception as e:
            print(f"Error positioning bone: {str(e)}")
            return False

    @staticmethod
    def get_orientations(context: Optional[bpy.types.Context] = None) -> tuple:
        """Get the coordinate system orientations for the armature
        
        Args:
            context: Optional context. If None, uses bpy.context
            
        Returns:
            tuple: (x_cord, y_cord, z_cord, is_fbx)
        """
        if not context:
            context = bpy.context
            
        armature = context.active_object
        if not armature or armature.type != 'ARMATURE':
            return 0, 1, 2, False
            
        # Default orientations
        x_cord = 0  # Left/Right
        y_cord = 1  # Forward/Back
        z_cord = 2  # Up/Down
        is_fbx = False

        return x_cord, y_cord, z_cord, is_fbx

    @staticmethod
    def attach_bones(context: Optional[bpy.types.Context] = None,
                   bone_pairs: dict = None) -> bool:
        """Attach bones to their corresponding target bones
        
        Args:
            context: Optional context. If None, uses bpy.context
            bone_pairs: Dictionary mapping source bone names to target bone names, e.g.:
                {
                    "Left Shoulder": "Left Upper Arm",
                    "Neck": "Head"
                }
            
        Returns:
            bool: True if successful, False if error occurs
        """
        if not context:
            context = bpy.context
            
        if not bone_pairs:
            return False
            
        armature = context.active_object
        if not armature or armature.type != 'ARMATURE':
            print("No armature found")
            return False
            
        try:
            # Switch to edit mode
            bpy.ops.object.mode_set(mode='EDIT')
            
            # Process each bone pair
            for source, target in bone_pairs.items():
                source_bone = next(
                    (bone for bone in armature.data.edit_bones if bone.name == source), None
                )
                target_bone = next(
                    (bone for bone in armature.data.edit_bones if bone.name == target), None
                )
                
                if source_bone is None or target_bone is None:
                    print(f"Could not find bones for {source} or {target}")
                    continue
                    
                # Attach source tail to target head
                source_bone.tail.x = target_bone.head.x
                source_bone.tail.y = target_bone.head.y
                source_bone.tail.z = target_bone.head.z
            
            bpy.ops.object.mode_set(mode='OBJECT')
            return True
            
        except Exception as e:
            print(f"Error attaching bones: {str(e)}")
            return False

    @staticmethod
    def duplicate_bones_with_weights(context: Optional[bpy.types.Context] = None, bones_to_duplicate: dict[str, str] = None, weight_source_bones: dict[str, Union[str, list[str]]] = None, mesh_name: str = None) -> bool:
        """Duplicate bones and their vertex weights
        
        Args:
            context: Optional context. If None, uses bpy.context
            bones_to_duplicate: Dictionary mapping original bone names to new bone names, e.g.:
                {
                    "Left Hand": "Left Hand Twist",
                    "Right Hand": "Right Hand Twist"
                }
            weight_source_bones: Optional dictionary mapping new bone names to either a single bone name or list of bones to copy weights from.
                If not provided, weights are copied from the original bone. e.g.:
                {
                    "Left Eye": "+EyeBone L A02",  # Single source bone
                    "Right Eye": ["eyeEnd_R", "eyeEnd_01_R"]  # Multiple source bones
                }
            mesh_name: Name of the mesh object to copy weights from
            
        Returns:
            bool: True if successful, False if error occurs
        """
        if not context:
            context = bpy.context
            
        if not bones_to_duplicate or not mesh_name:
            return False
            
        # Store previous state
        prev_active = context.active_object
        prev_selected = {obj: obj.select_get() for obj in context.selected_objects}
            
        # Find and set up armature
        armature = context.active_object
        if not armature or armature.type != 'ARMATURE':
            # Try to find armature in scene
            armature = next((obj for obj in context.scene.objects if obj.type == 'ARMATURE'), None)
            if not armature:
                print("No armature found")
                return False
            
            # Set armature as active
            context.view_layer.objects.active = armature
            armature.select_set(True)
            
        try:
            # Switch to edit mode
            bpy.ops.object.mode_set(mode='EDIT')
            
            # Store original bone data
            original_bones = {}
            for orig_name, new_name in bones_to_duplicate.items():
                bone = armature.data.edit_bones.get(orig_name)
                if not bone:
                    print(f"Could not find bone: {orig_name}")
                    continue
                    
                original_bones[orig_name] = {
                    'new_name': new_name,
                    'head': bone.head.copy(),
                    'tail': bone.tail.copy(),
                    'roll': bone.roll,
                    'parent': bone.parent,
                    'use_connect': bone.use_connect,
                    'use_deform': bone.use_deform
                }
            
            # Create duplicates
            for orig_name, bone_data in original_bones.items():
                new_bone = armature.data.edit_bones.new(bone_data['new_name'])
                
                # Copy transform
                new_bone.head = bone_data['head']
                new_bone.tail = bone_data['tail']
                new_bone.roll = bone_data['roll']
                
                # Copy parent
                if bone_data['parent']:
                    new_bone.parent = bone_data['parent']
                    new_bone.use_connect = bone_data['use_connect']
                
                new_bone.use_deform = bone_data['use_deform']
                
            # Switch to object mode to handle weights
            bpy.ops.object.mode_set(mode='OBJECT')
            
            # Find target mesh in scene
            mesh_obj = context.scene.objects.get(mesh_name)
            if not mesh_obj or mesh_obj.type != 'MESH':
                print(f"Could not find mesh: {mesh_name}")
                return False
            
            # Select mesh and make it active for weight operations
            mesh_obj.select_set(True)
            context.view_layer.objects.active = mesh_obj
                
            # Copy weights for the specified mesh
            if mesh_obj.vertex_groups:
                for orig_name, bone_data in original_bones.items():
                    new_name = bone_data['new_name']
                    
                    # Get weight sources
                    weight_sources = [orig_name]  # Default to original bone
                    if weight_source_bones and new_name in weight_source_bones:
                        source = weight_source_bones[new_name]
                        # Handle both single bone name and list of bones
                        weight_sources = [source] if isinstance(source, str) else source
                        
                    # Create new vertex group
                    new_group = mesh_obj.vertex_groups.new(name=new_name)
                    
                    # Copy weights from all sources
                    for vert in mesh_obj.data.vertices:
                        total_weight = 0
                        for source_name in weight_sources:
                            source_group = mesh_obj.vertex_groups.get(source_name)
                            if not source_group:
                                print(f"Could not find vertex group: {source_name}")
                                continue
                                
                            try:
                                for group in vert.groups:
                                    if group.group == source_group.index:
                                        total_weight += group.weight
                                        break
                            except RuntimeError:
                                continue
                                
                        if total_weight > 0:
                            new_group.add([vert.index], total_weight, 'REPLACE')
                    
                    # Switch to pose mode to enable deform
                    context.view_layer.objects.active = armature
                    bpy.ops.object.mode_set(mode='POSE')
                    bone = armature.pose.bones.get(new_name)
                    if bone:
                        bone.bone.use_deform = True
                    bpy.ops.object.mode_set(mode='OBJECT')
            
            # Restore previous state
            for obj, was_selected in prev_selected.items():
                obj.select_set(was_selected)
            context.view_layer.objects.active = prev_active
                            
            return True
            
        except Exception as e:
            print(f"Error duplicating bones: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    @staticmethod
    def symmetrize_bones(context: Optional[bpy.types.Context] = None, side: str = "Left") -> bool:
        """Symmetrize bones by copying transforms from one side to the other using Blender's built-in symmetrize operator
        
        Args:
            context: Optional context. If None, uses bpy.context
            side: Source side, either "Left" or "Right". Will mirror to opposite side.
                
        Returns:
            bool: True if successful, False if error occurs
        """
        if not context:
            context = bpy.context
            
        if side not in ["Left", "Right"]:
            return False
            
        armature = context.active_object
        if not armature or armature.type != 'ARMATURE':
            print("No armature found")
            return False
            
        try:
            # Switch to edit mode
            bpy.ops.object.mode_set(mode='EDIT')
            
            # Deselect all bones first
            bpy.ops.armature.select_all(action='DESELECT')
            
            # Select bones with side naming scheme
            for bone in armature.data.edit_bones:
                # Check for Left/L or Right/R in name based on side parameter
                if side == "Left" and ("Left" in bone.name or "_L" in bone.name):
                    bone.select = True
                    bone.select_head = True
                    bone.select_tail = True
                elif side == "Right" and ("Right" in bone.name or "_R" in bone.name):
                    bone.select = True
                    bone.select_head = True
                    bone.select_tail = True
            
            # Symmetrize selected bones
            bpy.ops.armature.symmetrize(direction='NEGATIVE_X' if side == "Left" else 'POSITIVE_X')

            # Deselect all bones
            bpy.ops.armature.select_all(action='DESELECT')
            
            bpy.ops.object.mode_set(mode='OBJECT')
            return True
            

        except Exception as e:
            print(f"Error symmetrizing bones: {str(e)}")
            return False

    @staticmethod
    def fix_wuwa_fingers(context: Optional[bpy.types.Context] = None) -> bool:
        """Fix finger bone naming and hierarchy
        
        Args:
            context: Optional context. If None, uses bpy.context
            
        Returns:
            bool: True if successful, False if error occurs
        """
        if not context:
            context = bpy.context
            
        armature = context.active_object
        if not armature or armature.type != 'ARMATURE':
            print("No armature found")
            return False
            
        try:
            # Enter edit mode
            bpy.ops.object.mode_set(mode='EDIT')
            
            print("\nStarting finger renaming process...")
            
            # Rename thumb and finger bones
            finger_types = {
                "Thumb": "Thumb",
                "Index": "Index",
                "Middle": "Middle", 
                "Ring": "Ring",
                "Little": "Little"
            }
            
            for finger_old, finger_new in finger_types.items():
                for side in ["L", "R"]:
                    side_name = "Left" if side == "L" else "Right"
                    
                    # Check for terminal bone
                    terminal = armature.data.edit_bones.get(f"{side_name} {finger_new} Terminal")
                    if terminal:
                        # Start from terminal bone and rename up the chain
                        proximal = armature.data.edit_bones.get(f"{side_name} {finger_new} Proximal")
                        if proximal:
                            # Get the chain of bones in order
                            bone_chain = [
                                f"{side_name} {finger_new}",  # 1 becomes Terminal
                                f"{side_name} {finger_new} Proximal",  # 2 becomes Proximal
                                f"{side_name} {finger_new} Intermediate", # 3 becomes Intermediate
                                f"{side_name} {finger_new} Distal"  # 4 becomes Distal
                            ]
                            
                            # Rename bones in order
                            for i in range(4):
                                old_name = f"{side_name} {finger_new} {'Proximal' if i == 0 else 'Intermediate' if i == 1 else 'Distal' if i == 2 else 'Terminal'}"
                                if bone := armature.data.edit_bones.get(old_name):
                                    new_name = bone_chain[i]
                                    print(f"Renaming {bone.name} to {new_name}")
                                    bone.name = new_name
            
            print("\nFinger renaming completed")
            
            # Return to object mode
            bpy.ops.object.mode_set(mode='OBJECT')
            return True
            
        except Exception as e:
            print(f"Error fixing finger bones: {str(e)}")
            return False

    @staticmethod
    def create_eye_bones(context: bpy.types.Context, eye_meshes: dict[str, str]) -> bool:
        """Create and set up eye bones for the specified eye meshes
        
        Args:
            context: Blender context
            eye_meshes: Dictionary mapping eye mesh names to bone names to create, e.g.:
                {
                    "Left Eye": "Left Eye",
                    "Right Eye": "Right Eye"
                }
            
        Returns:
            bool: True if successful
        """
        try:
            # Find armature
            armature = context.active_object
            if not armature or armature.type != 'ARMATURE':
                armature = next((obj for obj in context.scene.objects if obj.type == 'ARMATURE'), None)
                if not armature:
                    print("No armature found")
                    return False
            
            # Store original mode and selection
            original_mode = context.mode
            original_active = context.active_object
            original_selected = {obj: obj.select_get() for obj in context.selected_objects}
            
            try:
                # Process each eye mesh
                for mesh_name, bone_name in eye_meshes.items():
                    # Get eye mesh
                    eye_obj = context.scene.objects.get(mesh_name)
                    if not eye_obj:
                        print(f"Eye mesh {mesh_name} not found")
                        continue
                    
                    # Select eye mesh and armature
                    context.view_layer.objects.active = eye_obj
                    eye_obj.select_set(True)
                    armature.select_set(True)
                    
                    # Get center vertex position
                    vertices = eye_obj.data.vertices
                    if not vertices:
                        print(f"No vertices found in {mesh_name}")
                        continue
                        
                    # Calculate center position from vertices
                    center = mathutils.Vector((0, 0, 0))
                    for vert in vertices:
                        center += vert.co
                    center /= len(vertices)
                    
                    # Transform to world space
                    center = eye_obj.matrix_world @ center
                    
                    # Switch to armature edit mode
                    context.view_layer.objects.active = armature
                    bpy.ops.object.mode_set(mode='EDIT')
                    
                    # Get head bone for reference
                    head_bone = armature.data.edit_bones.get("Head")
                    if not head_bone:
                        print("Head bone not found")
                        continue
                    
                    # Create new bone
                    new_bone = armature.data.edit_bones.new(bone_name)
                    
                    # Set head position at eye center and move back
                    new_bone.head = center
                    new_bone.head.y -= -0.03  # Move 3cm back
                    
                    # Set tail to point upward from the head position
                    new_bone.tail = new_bone.head.copy()
                    new_bone.tail.z += 0.05  # 5cm up
                    
                    # Parent to head bone
                    new_bone.parent = head_bone
                    
                    # Exit edit mode
                    bpy.ops.object.mode_set(mode='OBJECT')
                    
                    # Set up vertex group and weighting
                    context.view_layer.objects.active = eye_obj
                    
                    # Create vertex group
                    vertex_group = eye_obj.vertex_groups.get(bone_name)
                    if not vertex_group:
                        vertex_group = eye_obj.vertex_groups.new(name=bone_name)
                    
                    # Weight all vertices
                    vertex_indices = [v.index for v in eye_obj.data.vertices]
                    vertex_group.add(vertex_indices, 1.0, 'REPLACE')
                    
                    # Add armature modifier
                    mod = eye_obj.modifiers.get("Armature")
                    if not mod:
                        mod = eye_obj.modifiers.new(name="Armature", type='ARMATURE')
                    mod.object = armature
                    
                    # Cleanup
                    eye_obj.select_set(False)
                    armature.select_set(False)
                
                return True
                
            finally:
                # Restore original state
                context.view_layer.objects.active = original_active
                for obj, was_selected in original_selected.items():
                    obj.select_set(was_selected)
                if original_mode != context.mode:
                    bpy.ops.object.mode_set(mode=original_mode)
                
        except Exception as e:
            print(f"Error creating eye bones: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    @staticmethod
    def move_armature_to_ground(context: Optional[bpy.types.Context] = None) -> bool:
        """Move armature so that the lowest non-weapon mesh vertex is at Z=0
        
        Args:
            context: Optional context. If None, uses bpy.context
            
        Returns:
            bool: True if successful, False if error occurs
        """
        if not context:
            context = bpy.context
            
        try:
            lowest_z = float('inf')
            target_meshes = []
            
            # Find the lowest Z vertex among non-weapon meshes
            for obj in context.scene.objects:
                if obj.type == 'MESH' and "weapon" not in obj.name.lower() and "body" in obj.name.lower():
                    target_meshes.append(obj)
                    world_coords = [obj.matrix_world @ v.co for v in obj.data.vertices]
                    min_z_obj = min(coord.z for coord in world_coords)
                    lowest_z = min(lowest_z, min_z_obj)
            
            if not target_meshes:
                print("No non-weapon meshes found in the scene.")
                return False
                
            if lowest_z >= 0:
                print("All non-weapon meshes are already at or above Z=0.")
                return True
            
            # Find armature to move
            armature = context.active_object
            if not armature or armature.type != 'ARMATURE':
                # Try to find any armature in the scene
                armature = next((obj for obj in context.scene.objects if obj.type == 'ARMATURE'), None)
                if not armature:
                    print("No armature found in the scene.")
                    return False
            
            # Move the armature
            translation = mathutils.Vector((0, 0, -lowest_z))
            armature.location += translation
            print(f"Moved armature '{armature.name}' by {translation} to bring the lowest non-weapon vertex to Z=0.")
            
            return True
            
        except Exception as e:
            print(f"Error moving armature to ground: {str(e)}")
            return False
    
    @staticmethod
    def separate_bangs_by_armature(context: Optional[bpy.types.Context] = None,
                                  hair_obj = None,
                                  armature_obj = None, 
                                  bone_keywords: list = None,
                                  y_boundary: float = 0.0) -> bool:
        """Separate bangs by creating new mesh object and duplicating materials
        
        Args:
            context: Optional context. If None, uses bpy.context
            hair_obj: Hair mesh object or name string to separate bangs from
            armature_obj: Armature object or name string containing the bones
            bone_keywords: List of bone keywords to match for bangs
            y_boundary: World Y coordinate boundary - vertices beyond this are excluded (default 0.0 = X-axis line)
            
        Returns:
            bool: True if successful, False if error occurs
        """
        if not context:
            context = bpy.context
            
        if not bone_keywords:
            bone_keywords = ["HairL", "HairM", "HairR", "HairTop", "HairFM", "HairU"]
            
        # Convert string names to objects if needed
        if isinstance(hair_obj, str):
            hair_obj = bpy.data.objects.get(hair_obj)
        if isinstance(armature_obj, str):
            armature_obj = bpy.data.objects.get(armature_obj)
            
        if not hair_obj or not armature_obj:
            print("❌ Hair or Armature object not found.")
            return False

        def get_matching_bones(armature, substrings):
            matched = set()

            def match_name(name):
                lname = name.lower()
                return any(substr.lower() in lname for substr in substrings)

            for bone in armature.data.bones:
                if match_name(bone.name):
                    matched.add(bone.name)
                    def add_children_recursive(b):
                        for child in b.children:
                            matched.add(child.name)
                            add_children_recursive(child)
                    add_children_recursive(bone)

            return matched

        def get_vert_weights(obj):
            weights = {v.index: {} for v in obj.data.vertices}
            for vg in obj.vertex_groups:
                for v in obj.data.vertices:
                    for g in v.groups:
                        if g.group == vg.index:
                            weights[v.index][vg.name] = g.weight
            return weights



        matched_bones = get_matching_bones(armature_obj, bone_keywords)
        print(f"✅ Using all matched bones for bangs: {matched_bones}")

        # Store original selection and active object
        original_selection = [obj for obj in context.selected_objects]
        original_active = context.active_object

        # Clear selection and set only hair object as active and selected
        bpy.ops.object.select_all(action='DESELECT')
        hair_obj.select_set(True)
        context.view_layer.objects.active = hair_obj
        bpy.ops.object.mode_set(mode='OBJECT')

        weights = get_vert_weights(hair_obj)

        selected_verts = set()
        for v in hair_obj.data.vertices:
            vw = weights.get(v.index, {})
            if any(bone in vw for bone in matched_bones):
                # Check vertex position in world space (Y-axis is forward/backward)
                world_pos = hair_obj.matrix_world @ v.co
                if world_pos.y <= y_boundary:  # Only vertices not extending beyond boundary
                    selected_verts.add(v.index)
                # else:
                #     print(f"Filtered out vertex {v.index} at Y position {world_pos.y:.3f}m (beyond boundary)")

        if not selected_verts:
            print("⚠️ No vertices matched the specified bone weights.")
            return False

        # Use selected vertices directly without expansion
        final_verts = selected_verts

        # Store original hair material for duplication
        original_hair_material = None
        if hair_obj.data.materials:
            original_hair_material = hair_obj.data.materials[0]
        else:
            print("❌ Hair object has no materials to duplicate.")
            return False

        # Create bangs material by duplicating original hair material
        bangs_material = original_hair_material.copy()
        bangs_material.name = original_hair_material.name.replace("Hair", "Bangs")
        
        # Add bangs material to the hair object
        hair_obj.data.materials.append(bangs_material)
        bangs_material_index = len(hair_obj.data.materials) - 1

        # Make sure we're working with the hair object only
        bpy.ops.object.select_all(action='DESELECT')
        hair_obj.select_set(True)
        context.view_layer.objects.active = hair_obj

        # Switch to edit mode to assign materials to bang faces
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')

        # Switch to edit mode and work with faces from the start
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_mode(type='FACE')
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # Select faces that have bang vertices weighted to our bones
        for face in hair_obj.data.polygons:
            # Check if any vertices of this face are bang vertices
            any_vert_is_bang = any(v_idx in final_verts for v_idx in face.vertices)
            
            if any_vert_is_bang:
                face.select = True
        
        # Now go to edit mode and select all linked faces plus nearby disconnected geometry
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_linked()
        
        # Also select nearby faces that might be part of the same hair strand but disconnected
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # Get all currently selected faces as reference points
        selected_face_centers = []
        for face in hair_obj.data.polygons:
            if face.select:
                # Calculate face center in world space
                face_center = sum((hair_obj.matrix_world @ hair_obj.data.vertices[v_idx].co for v_idx in face.vertices), mathutils.Vector()) / len(face.vertices)
                selected_face_centers.append(face_center)
        
        # Select additional faces that are close to selected faces (likely same hair strand)
        proximity_threshold = 0.02  # 5cm threshold for considering faces as part of same strand
        for face in hair_obj.data.polygons:
            if not face.select:  # Only check unselected faces
                face_center = sum((hair_obj.matrix_world @ hair_obj.data.vertices[v_idx].co for v_idx in face.vertices), mathutils.Vector()) / len(face.vertices)
                
                # Check if this face is close to any selected face
                for selected_center in selected_face_centers:
                    distance = (face_center - selected_center).length
                    if distance <= proximity_threshold:
                        face.select = True
                        break  # Don't need to check other selected faces
        
        bpy.ops.object.mode_set(mode='EDIT')
        
        # Apply Y boundary filter after linked selection to prevent over-extension
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # Deselect faces that extend too far beyond the Y boundary
        for face in hair_obj.data.polygons:
            if face.select:
                # Check if any vertex of this face extends too far beyond the boundary
                any_vert_too_far = any(
                    (hair_obj.matrix_world @ hair_obj.data.vertices[v_idx].co).y > (y_boundary + 0.05)  # Allow 30cm buffer
                    for v_idx in face.vertices
                )
                
                if any_vert_too_far:
                    face.select = False
        
        bpy.ops.object.mode_set(mode='EDIT')
        
        # Assign bangs material to selected faces
        hair_obj.active_material_index = bangs_material_index
        bpy.ops.object.material_slot_assign()
        
        # Deselect all and return to object mode
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        
        print(f"✅ Created bangs material '{bangs_material.name}' and assigned to bang faces.")
        
        # Restore original selection and active object
        bpy.ops.object.select_all(action='DESELECT')
        for obj in original_selection:
            if obj and obj.name in bpy.data.objects:
                obj.select_set(True)
        if original_active and original_active.name in bpy.data.objects:
            context.view_layer.objects.active = original_active
        
        return True
    
    @staticmethod
    def adjust_bone_tails_to_connect(context: Optional[bpy.types.Context] = None,
                                   exclude_substrings: list = None) -> bool:
        """Automatically finds bone chains and adjusts the tail of each parent bone
        to meet the head of its child bone, keeping child heads fixed.
        The script stops processing a chain if it skips a numerical suffix.
        It avoids bones whose names contain any string from a specified exclusion list (case-insensitive).
        
        Args:
            context: Optional context. If None, uses bpy.context
            exclude_substrings: List of substrings to exclude from processing (case-insensitive).
                              If None, uses default exclusion list.
            
        Returns:
            bool: True if successful, False if error occurs
        """
        if not context:
            context = bpy.context
            
        if not exclude_substrings:
            exclude_substrings = ["pelvis", "waist", "spine", "arm", "leg", "chest", 
                                "neck", "head", "knee", "calf", "elbow", "skirt", 
                                "thigh", "twist"]
        
        # Convert to lowercase for case-insensitive comparison
        exclude_substrings = {s.lower() for s in exclude_substrings}
            
        armature = context.active_object
        if not armature or armature.type != 'ARMATURE':
            print("No armature found")
            return False
            
        try:
            import re
            
            # Switch to edit mode
            bpy.ops.object.mode_set(mode='EDIT')
            
            edit_bones = armature.data.edit_bones
            bone_chains = {}
            
            name_pattern = re.compile(r"^(.*?)(\d+)$")
            
            # Find bone chains based on naming pattern
            for bone in edit_bones:
                bone_name_lower = bone.name.lower()
                
                # Check exclusion list (case-insensitive)
                should_exclude = False
                for forbidden_substring in exclude_substrings:
                    if forbidden_substring in bone_name_lower:
                        print(f"  Skipping bone '{bone.name}': Contains '{forbidden_substring}' from the exclusion list.")
                        should_exclude = True
                        break
                
                if should_exclude:
                    continue
                
                # Match naming pattern (prefix + number)
                match = name_pattern.match(bone.name)
                if match:
                    prefix = match.group(1)
                    try:
                        suffix_num = int(match.group(2))
                        if prefix not in bone_chains:
                            bone_chains[prefix] = {}
                        bone_chains[prefix][suffix_num] = bone
                    except ValueError:
                        continue
            
            if not bone_chains:
                print(f"No potential bone chains (names ending with numbers) found in armature '{armature.name}' after exclusions.")
                bpy.ops.object.mode_set(mode='OBJECT')
                return True
            
            # Process each bone chain
            sorted_prefixes = sorted(bone_chains.keys())
            
            for prefix in sorted_prefixes:
                bones_in_chain = bone_chains[prefix]
                
                if len(bones_in_chain) < 2:
                    print(f"\nSkipping chain with prefix '{prefix}': Needs at least 2 bones.")
                    continue
                
                print(f"\n--- Starting to process bone chain with prefix: '{prefix}' (Adjusting only tails) ---")
                sorted_bone_keys = sorted(bones_in_chain.keys())
                
                # Check for continuity in the chain
                expected_next_key = sorted_bone_keys[0]
                is_continuous = True
                for key in sorted_bone_keys:
                    if key != expected_next_key:
                        print(f"  Gap detected in chain '{prefix}': Expected '{prefix}{expected_next_key}', but found '{prefix}{key}'. Stopping processing this chain.")
                        is_continuous = False
                        break
                    expected_next_key += 1
                
                if not is_continuous:
                    print(f"--- Aborted processing bone chain with prefix: '{prefix}' due to gap. ---")
                    continue
                
                # Warn if chain doesn't start with 0
                if sorted_bone_keys[0] != 0:
                    print(f"  Warning: Chain '{prefix}' does not start with index 0. It starts with '{prefix}{sorted_bone_keys[0]}'.")
                    print("  Connecting bones sequentially based on found indices.")
                
                # Process each bone in the chain
                for i in range(len(sorted_bone_keys) - 1):
                    current_bone_index = sorted_bone_keys[i]
                    next_bone_index = sorted_bone_keys[i + 1]
                    
                    current_bone = bones_in_chain[current_bone_index]
                    next_bone = bones_in_chain[next_bone_index]
                    
                    # Check if current_bone's tail is already at next_bone's head
                    is_already_correct = False
                    if (current_bone.tail - next_bone.head).length < 0.0001:
                        if next_bone.parent == current_bone and next_bone.use_connect:
                            is_already_correct = True
                    
                    if is_already_correct:
                        print(f"  Skipping '{current_bone.name}' tail: Already correctly positioned and '{next_bone.name}' connected.")
                        continue
                    
                    # Move the tail of the current_bone to the head of the next_bone
                    current_bone.tail = next_bone.head
                    print(f"  Moved tail of '{current_bone.name}' to head of '{next_bone.name}'.")
                    
                    # Set up parenting
                    if next_bone.parent != current_bone:
                        next_bone.parent = current_bone
                        print(f"  Parented '{next_bone.name}' to '{current_bone.name}'.")
                    
                    # Set connection
                    if not next_bone.use_connect:
                        next_bone.use_connect = True
                        print(f"  Set '{next_bone.name}' to be connected.")
                
                print(f"--- Finished processing bone chain with prefix: '{prefix}' ---")
            
            # Return to object mode
            bpy.ops.object.mode_set(mode='OBJECT')
            
            print("\nAutomated bone chain processing complete for all detected continuous chains.")
            return True
            
        except Exception as e:
            print(f"Error adjusting bone tails: {str(e)}")
            # Ensure we return to object mode even if there's an error
            try:
                bpy.ops.object.mode_set(mode='OBJECT')
            except:
                pass
            return False
    
