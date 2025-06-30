import bpy
import re
from typing import Optional
from .scene import SceneUtils
import bmesh
import mathutils

class ModelUtils:
    """Utility class for model operations"""
    
    @staticmethod
    def clean_meshes(context: Optional[bpy.types.Context] = None) -> bool:
        """Clean the meshes of the model by removing unwanted meshes"""
        if not context:
            context = bpy.context
            
        unwanted_meshes = ["EffectMesh", "Weapon_L", "Weapon_R"]
        
        for obj in bpy.data.objects:
            if obj.type != "MESH":
                continue
                
            # Check various conditions for removal
            should_remove = (
                obj.name in unwanted_meshes
                or "lod" in obj.name.lower()
                or "AO_Bip" in obj.name 
                or obj.name.endswith("_Low")
                or obj.name.endswith("_EffectMesh")
                or (obj.name == "EyeStar" and not context.scene.keep_star_eye_mesh)
            )
            
            if should_remove:
                bpy.data.objects.remove(obj, do_unlink=True)
        
        # Deselect all meshes
        for obj in bpy.data.objects:
            if obj.type == 'MESH':
                obj.select_set(False)
                

        return True
    
    @staticmethod
    def scale_model(context: Optional[bpy.types.Context] = None) -> bool:
        """Scale up models that are too small (dimensions near 0)"""
        if not context:
            context = bpy.context
            
        # Find armature
        armature = None
        for obj in context.scene.objects:
            if obj.type == 'ARMATURE':
                armature = obj
                break
                
        # If no armature, get all meshes
        objects_to_scale = []
        if armature:
            objects_to_scale = [armature]
        else:
            for obj in context.scene.objects:
                if obj.type == 'MESH':
                    objects_to_scale.append(obj)
                    
        if not objects_to_scale:
            print("No armature or meshes found in scene")
            return False
            
        # Get dimensions and calculate max from first object
        dimensions = objects_to_scale[0].dimensions
        max_dim = max(dimensions)
        print(f"Dimensions: X={dimensions.x:.8f}, Y={dimensions.y:.8f}, Z={dimensions.z:.8f}")
        print(f"Max dimension: {max_dim:.8f}")
        
        # Scale model based on size - using much smaller thresholds
        scale_factor = 1.0
        if max_dim <= 0.000002:  # 1e-6
            scale_factor = 1000000
            action = "up"
        elif max_dim <= 0.00002:  # 1e-5
            scale_factor = 100000
            action = "up"
        elif max_dim <= 0.0002:  # 1e-4
            scale_factor = 10000
            action = "up"
        elif max_dim <= 0.002:  # 1e-3
            scale_factor = 1000
            action = "up"
        elif max_dim <= 0.01:  # Restored to 0.01 since 0.02 was too high
            scale_factor = 100
            action = "up"
        elif max_dim > 100:
            scale_factor = 0.01
            action = "down"
        elif max_dim > 10:
            scale_factor = 0.1
            action = "down"
        elif 1 < max_dim < 3:
            print(f"Model is already a reasonable size (max dim: {max_dim:.8f})")
            return True
            
        # Apply scaling if needed
        if scale_factor != 1.0:
            print(f"Scaling model {action} by {scale_factor}x (from {max_dim:.8f})")
            
            # Store current selection
            selected_objects = context.selected_objects[:]
            active_object = context.active_object
            
            # Deselect all objects
            for obj in context.selected_objects:
                obj.select_set(False)
                
            # Scale each object
            for obj in objects_to_scale:
                obj.select_set(True)
                context.view_layer.objects.active = obj
                
                obj.scale *= scale_factor
                print(f"Scaled object: {obj.name}")
                
                # Apply scale
                bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
                
                # Print new dimensions
                new_dims = obj.dimensions
                print(f"New dimensions: X={new_dims.x:.8f}, Y={new_dims.y:.8f}, Z={new_dims.z:.8f}")
                print(f"New max dimension: {max(new_dims):.8f}")
                
                obj.select_set(False)
            
            # Restore previous selection
            for obj in selected_objects:
                obj.select_set(True)
            if active_object:
                context.view_layer.objects.active = active_object

        return True

    @staticmethod
    def generate_shape_keys(context: Optional[bpy.types.Context] = None,
                          shape_key_config: dict = None) -> bool:
        """Generate shape keys based on a flexible configuration
        
        Args:
            context: Optional context. If None, uses bpy.context
            shape_key_config: Dictionary containing shape key generation rules, e.g.:
                {
                    "target_objects": {  # Objects that should have shape keys
                        "Face": ["Mouth_A01", "Mouth_Fury01"],  # Required base keys
                        "Face_Eye": ["Eye_WinkA_L", "Eye_WinkA_R"]
                    },
                    "fallback_keys": [  # Optional fallbacks if required keys missing
                        {
                            "missing_key": "Mouth_Fury01",
                            "fallback_key": "Mouth_Open01",
                            "fallback_value": 0.5
                        }
                    ],
                    "generated_keys": {  # New keys to generate
                        "A": [  # New key name
                            {
                                "object": "Face",  # Target object
                                "source_key": "Mouth_A01",  # Source shape key
                                "value": 1.0  # Influence value
                            }
                        ],
                        "O": [
                            {
                                "object": "Face",
                                "source_key": "Mouth_Smile02",
                                "value": 0.5
                            },
                            {
                                "object": "Face",
                                "source_key": "Mouth_A01",
                                "value": 0.5
                            }
                        ]
                    }
                }
            
        Returns:
            bool: True if successful, False if error occurs
        """
        if not context:
            context = bpy.context
            
        if not shape_key_config:
            print("No shape key configuration provided")
            return True  # Not an error, just nothing to do
            
        try:
            # Validate required base shape keys and apply fallbacks
            if "target_objects" in shape_key_config:
                for obj_name, required_keys in shape_key_config["target_objects"].items():
                    obj = bpy.data.objects.get(obj_name)
                    if not obj:
                        print(f"Object {obj_name} not found, skipping its shape keys")
                        continue
                        
                    # Check required keys and apply fallbacks
                    if "fallback_keys" in shape_key_config:
                        for key in required_keys:
                            if not ModelUtils._has_shape_key(obj, key):
                                # Try to find a fallback
                                fallback = next(
                                    (fb for fb in shape_key_config["fallback_keys"] 
                                     if fb["missing_key"] == key 
                                     and ModelUtils._has_shape_key(obj, fb["fallback_key"])),
                                    None
                                )
                                if fallback:
                                    print(f"Using fallback {fallback['fallback_key']} for missing key {key}")
                                else:
                                    print(f"No fallback found for missing key {key}")
            
            # Generate new shape keys
            if "generated_keys" in shape_key_config:
                for new_key, sources in shape_key_config["generated_keys"].items():
                    # Get target object from first source
                    if not sources:
                        continue
                        
                    target_obj = bpy.data.objects.get(sources[0]["object"])
                    if not target_obj:
                        print(f"Target object {sources[0]['object']} not found for key {new_key}")
                        continue
                    
                    # Create the new shape key
                    if not ModelUtils.create_mixed_shape_key(target_obj, new_key, sources):
                        print(f"Failed to create shape key {new_key}")
                        
            return True
            
        except Exception as e:
            print(f"Error generating shape keys: {str(e)}")
            return False
    
    @staticmethod
    def _has_shape_key(obj: bpy.types.Object, key_name: str) -> bool:
        """Check if an object has a specific shape key"""
        if not obj.data.shape_keys:
            return False
        return key_name in obj.data.shape_keys.key_blocks
    
    @staticmethod
    def create_mixed_shape_key(obj: bpy.types.Object, 
                              key_name: str, 
                              sources: list) -> bool:
        """Create a new shape key by mixing existing ones
        
        Args:
            obj: Target object
            key_name: Name of new shape key
            sources: List of source keys and their values
        """
        try:
            # Create new shape key
            new_key = obj.shape_key_add(name=key_name)
            if not new_key:
                return False

            # Initialize vertex positions from basis
            basis = obj.data.shape_keys.key_blocks['Basis']
            for i in range(len(new_key.data)):
                new_key.data[i].co = basis.data[i].co.copy()

            # Group sources by object for simultaneous application
            sources_by_obj = {}
            for source in sources:
                source_obj = bpy.data.objects.get(source["object"])
                if not source_obj or not ModelUtils._has_shape_key(source_obj, source["source_key"]):
                    continue
                
                if source_obj not in sources_by_obj:
                    sources_by_obj[source_obj] = []
                sources_by_obj[source_obj].append(source)

            # Process each object's shape keys
            for source_obj, obj_sources in sources_by_obj.items():
                if source_obj == obj:
                    # Same object - direct vertex index mapping
                    for i in range(len(new_key.data)):
                        final_co = basis.data[i].co.copy()
                        # Apply all influences from this object
                        for source in obj_sources:
                            source_key = source_obj.data.shape_keys.key_blocks[source["source_key"]]
                            value = source["value"]
                            offset = source_key.data[i].co - basis.data[i].co
                            final_co += offset * value
                        new_key.data[i].co = final_co
                else:
                    # Different object - need position matching
                    for i, target_vert in enumerate(obj.data.vertices):
                        # Find closest vertex in source object
                        closest_vert = None
                        min_dist = float('inf')
                        for j, source_vert in enumerate(source_obj.data.vertices):
                            dist = (target_vert.co - source_vert.co).length
                            if dist < min_dist:
                                min_dist = dist
                                closest_vert = j

                        if closest_vert is not None and min_dist < 0.0001:  # Threshold for vertex matching
                            final_co = basis.data[i].co.copy()
                            # Apply all influences from this object
                            for source in obj_sources:
                                source_key = source_obj.data.shape_keys.key_blocks[source["source_key"]]
                                value = source["value"]
                                offset = source_key.data[closest_vert].co - source_obj.data.shape_keys.key_blocks['Basis'].data[closest_vert].co
                                final_co += offset * value
                            new_key.data[i].co = final_co

            return True

        except Exception as e:
            print(f"Error creating mixed shape key: {str(e)}")
            return False

    @staticmethod
    def merge_meshes_by_distance(context: Optional[bpy.types.Context] = None,
                               target_object: str = None,
                               objects_to_merge: list = None,
                               active_shape_key: str = None,
                               threshold: float = 0.0001) -> bool:
        """Merge multiple meshes into a target mesh and then merge vertices by distance
        
        Args:
            context: Optional context. If None, uses bpy.context
            target_object: Name of the target object to merge into
            objects_to_merge: List of object names to merge
            active_shape_key: Optional shape key to apply during the process
            threshold: Distance threshold for merging vertices
            
        Returns:
            bool: True if successful, False if error occurs
        """
        if not context:
            context = bpy.context
            
        if not target_object:
            print("No target object specified")
            return False
            
        try:
            # Store current mode
            prev_mode = SceneUtils.ensure_mode(context, 'OBJECT')
            
            # Get target object
            target = bpy.data.objects.get(target_object)
            if not target or target.type != 'MESH':
                print(f"Target object {target_object} not found or not a mesh")
                return False
            
            # Store shape key state if needed
            original_shape_key_index = None
            if active_shape_key and target.data.shape_keys:
                try:
                    original_shape_key_index = target.active_shape_key_index
                    key_index = target.data.shape_keys.key_blocks.keys().index(active_shape_key)
                    target.active_shape_key_index = key_index
                    target.data.shape_keys.key_blocks[active_shape_key].value = 1.0
                except (ValueError, KeyError):
                    print(f"Shape key {active_shape_key} not found")
            
            # Deselect all meshes
            for obj in bpy.data.objects:
                if obj.type == 'MESH':
                    obj.select_set(False)
            
            # Select target and set as active
            target.select_set(True)
            context.view_layer.objects.active = target
            
            # Select objects to merge
            if objects_to_merge:
                for obj_name in objects_to_merge:
                    obj = bpy.data.objects.get(obj_name)
                    if obj and obj.type == 'MESH':
                        obj.select_set(True)
                    else:
                        print(f"Object {obj_name} not found or not a mesh")
            
            # Join meshes if we have objects to merge
            if objects_to_merge:
                bpy.ops.object.join()
            
            # Switch to edit mode and merge vertices
            SceneUtils.ensure_mode(context, 'EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.remove_doubles(threshold=threshold)
            bpy.ops.mesh.select_all(action='DESELECT')
            
            # Reset shape key if it was applied
            if active_shape_key and target.data.shape_keys:
                target.data.shape_keys.key_blocks[active_shape_key].value = 0
                if original_shape_key_index is not None:
                    target.active_shape_key_index = original_shape_key_index
            
            # Restore original mode and cleanup
            SceneUtils.restore_mode(context, prev_mode)
            SceneUtils.cleanup_selection(context)
            
            return True
            
        except Exception as e:
            print(f"Error during mesh merge operation: {str(e)}")
            if 'prev_mode' in locals():
                SceneUtils.restore_mode(context, prev_mode)
            return False

    @staticmethod
    def merge_meshes(context: bpy.types.Context, target_name: str = None, rename: bool = False, mesh_names: list = None) -> bool:
        """Join specified meshes and optionally rename the result
        
        Args:
            context: Blender context
            target_name: Optional name for the merged mesh
            rename: Whether to rename the merged mesh
            mesh_names: Optional list of mesh names to merge. If None, uses selected meshes.
            
        Returns:
            bool: True if successful
        """
        try:
            # Get mesh objects to merge
            if mesh_names:
                mesh_objects = [obj for obj in context.scene.objects 
                              if obj.type == 'MESH' and obj.name in mesh_names]
            else:
                mesh_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
                
            if not mesh_objects:
                print("No mesh objects found to merge")
                return False

            # Deselect all objects first
            bpy.ops.object.select_all(action='DESELECT')
                
            # Select all mesh objects and set active
            for obj in mesh_objects:
                obj.select_set(True)
            context.view_layer.objects.active = mesh_objects[0]
            
            # Join meshes
            bpy.ops.object.join()
            
            # Rename if requested
            if rename and target_name:
                context.active_object.name = target_name
                if context.active_object.data:
                    context.active_object.data.name = target_name
                    
            return True
            
        except Exception as e:
            print(f"Error merging meshes: {str(e)}")
            return False

    @staticmethod
    def reorder_uv_maps(context: Optional[bpy.types.Context] = None) -> bool:
        """Reorder UV maps alphabetically for all mesh objects
        
        Returns:
            bool: True if successful, False if error occurs
        """
        if not context:
            context = bpy.context
            
        try:
            # Get all mesh objects
            mesh_objects = [obj for obj in bpy.data.objects if obj.type == 'MESH']
            
            for obj in mesh_objects:
                mesh = obj.data
                if len(mesh.uv_layers) <= 1:
                    continue
                    
                # Get current UV layers and their names
                uv_layers = [(i, layer.name) for i, layer in enumerate(mesh.uv_layers)]
                
                # Sort UV layers by name
                sorted_layers = sorted(uv_layers, key=lambda x: x[1])
                
                # Check if reordering is needed
                if [i for i, _ in uv_layers] != [i for i, _ in sorted_layers]:
                    # Create a copy of UV data in the new order
                    uv_data = {}
                    for old_idx, name in sorted_layers:
                        uv_data[name] = {
                            'data': [uvloop.uv[:] for uvloop in mesh.uv_layers[old_idx].data]
                        }
                    
                    # Remove all UV layers except the first one
                    while len(mesh.uv_layers) > 1:
                        mesh.uv_layers.remove(mesh.uv_layers[-1])
                    
                    # Recreate UV layers in the correct order
                    for name, data in uv_data.items():
                        if name != mesh.uv_layers[0].name:
                            new_layer = mesh.uv_layers.new(name=name)
                            for loop_idx, uv in enumerate(data['data']):
                                new_layer.data[loop_idx].uv = uv
                                
            return True
            
        except Exception as e:
            print(f"Error reordering UV maps: {str(e)}")
            return False
        
    @staticmethod
    def merge_all_meshes(context: Optional[bpy.types.Context] = None) -> bool:
        """Merge all mesh objects into a single mesh named 'Body'
        
        Args:
            context: Optional context. If None, uses bpy.context
            
        Returns:
            bool: True if successful, False if error occurs
        """
        if not context:
            context = bpy.context
            
        try:
            # Store current mode
            prev_mode = SceneUtils.ensure_mode(context, 'OBJECT')
            
            # Get all mesh objects
            mesh_objects = [obj for obj in bpy.data.objects if obj.type == 'MESH']
            if not mesh_objects:
                print("No mesh objects found to merge")
                return False
                
            # Deselect all meshes
            for obj in bpy.data.objects:
                if obj.type == 'MESH':
                    obj.select_set(False)
                
            # Select all mesh objects and set active
            for obj in mesh_objects:
                obj.select_set(True)
            context.view_layer.objects.active = mesh_objects[0]
            
            # Join meshes
            bpy.ops.object.join()
            
            # Rename result
            context.active_object.name = "Body"
            
            # Restore previous mode
            SceneUtils.ensure_mode(context, prev_mode)
            
            return True
            
        except Exception as e:
            print(f"Error merging meshes: {str(e)}")
            return False

    @staticmethod
    def get_shape_key(obj_name: str, modifier_name: str) -> Optional[bpy.types.ShapeKey]:
        """Get a shape key by object and modifier name
        
        Args:
            obj_name: Name of the object
            modifier_name: Name of the modifier used to create the shape key
            
        Returns:
            ShapeKey or None if not found
        """
        obj = bpy.data.objects.get(obj_name)
        if not obj or not obj.data.shape_keys:
            return None
            
        # The shape key name will be the modifier name
        return obj.data.shape_keys.key_blocks.get(modifier_name)

    @staticmethod
    def reset_pose(context: Optional[bpy.types.Context] = None, root_object: Optional[bpy.types.Object] = None) -> bool:
        """Reset the pose of an armature to its rest position
        
        Args:
            context: Optional context. If None, uses bpy.context
            root_object: Optional armature object. If None, uses active object
            
        Returns:
            bool: True if successful, False if error occurs
        """
        if not context:
            context = bpy.context
            
        if not root_object:
            root_object = context.active_object
            
        if not root_object or root_object.type != 'ARMATURE':
            print("No valid armature object provided")
            return False
            
        try:
            # Store current selection and mode
            prev_active = context.active_object
            prev_mode = SceneUtils.ensure_mode(context, 'OBJECT')
            
            # Set armature as active
            context.view_layer.objects.active = root_object
            
            # Enter pose mode
            bpy.ops.object.mode_set(mode='POSE')
            
            # Select all pose bones and clear transforms
            bpy.ops.pose.select_all(action='SELECT')
            bpy.ops.pose.transforms_clear()
            
            # Restore previous mode and selection
            SceneUtils.ensure_mode(context, prev_mode)
            if prev_active:
                context.view_layer.objects.active = prev_active
                
            return True
            
        except Exception as e:
            print(f"Error resetting pose: {str(e)}")
            return False

    @staticmethod
    def face_rig_to_shapekey(context: Optional[bpy.types.Context] = None, 
                            root_object: Optional[bpy.types.Object] = None,
                            mesh_name: str = "Face") -> bool:
        """Convert facial rig animations to shape keys
        
        Args:
            context: Optional context. If None, uses bpy.context
            root_object: Optional armature object. If None, uses active object or first armature
            mesh_name: Name of the mesh to convert animations to shape keys for
            
        Returns:
            bool: True if successful, False if error occurs
        """
        if not context:
            context = bpy.context
            
        # Find root armature if not provided
        if not root_object:
            root_object = context.active_object
            
        if root_object and root_object.type != 'ARMATURE':
            root_object = next((obj for obj in bpy.data.objects if obj.type == 'ARMATURE'), None)
            
        if not root_object:
            print("No armature found in scene")
            return False
            
        # Find target mesh
        face_obj = bpy.data.objects.get(mesh_name)
        if not face_obj:
            print(f"No object found with name {mesh_name}")
            return False
            
        # Check for animations
        if not bpy.data.actions:
            print("No animations found")
            return False
            
        try:
            # Store current state
            prev_active = context.active_object
            prev_mode = SceneUtils.ensure_mode(context, 'OBJECT')
            prev_action = root_object.animation_data.action if root_object.animation_data else None
            
            # Ensure armature has animation data
            if not root_object.animation_data:
                root_object.animation_data_create()
                
            # Process each action
            for action in bpy.data.actions:
                # Skip actions that don't match our patterns
                if not any(pattern in action.name for pattern in ["Emo_", "Ani_", "PhotoGraph_"]):
                    continue
                    
                # Skip numbered variations (like .001, .002, etc)
                if re.search(r"\.\d{2,}$", action.name):
                    continue
                    
                print(f"Processing action: {action.name}")
                
                # Extract shape key name from action name
                name_parts = action.name.split("_")
                if len(name_parts) < 3:
                    continue
                    
                # Get everything after the prefix (Emo_, Ani_, etc)
                shapekey_name = "_".join(name_parts[2:])
                
                # Apply the action
                root_object.animation_data.action = action
                bpy.ops.object.visual_transform_apply()
                
                # Create shape key from deformation
                context.view_layer.objects.active = face_obj
                if face_obj.modifiers:
                    bpy.ops.object.modifier_apply_as_shapekey(
                        keep_modifier=True,
                        modifier=face_obj.modifiers[0].name
                    )
                    
                    # Rename the shape key
                    shape_key = ModelUtils.get_shape_key(face_obj.name, face_obj.modifiers[0].name)
                    if shape_key:
                        shape_key.name = shapekey_name
                        print(f"Created shape key: {shapekey_name}")
                
                # Reset pose before next action
                ModelUtils.reset_pose(context, root_object)
                
                # Deselect all meshes
                for obj in bpy.data.objects:
                    if obj.type == 'MESH':
                        obj.select_set(False)
            
            # Restore previous state
            if prev_action:
                root_object.animation_data.action = prev_action
            SceneUtils.ensure_mode(context, prev_mode)
            if prev_active:
                context.view_layer.objects.active = prev_active
                
            return True
            
        except Exception as e:
            print(f"Error converting face rig to shape keys: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    @staticmethod
    def clear_animations(context: Optional[bpy.types.Context] = None) -> bool:
        """Clear all animation data from the armature
        
        Args:
            context: Optional context. If None, uses bpy.context
            
        Returns:
            bool: True if successful, False if no armature found
        """
        if not context:
            context = bpy.context
            
        # Find armature object
        armature = context.active_object
        if not armature or armature.type != 'ARMATURE':
            # Try finding armature in scene
            armature = next((obj for obj in context.scene.objects if obj.type == 'ARMATURE'), None)
            if not armature:
                print("No armature found")
                return False
            
        try:
            # Clear animation data
            if armature.animation_data:
                armature.animation_data_clear()
                print("Cleared armature animation data")
                
            # Clear action data
            for action in bpy.data.actions:
                if action.users == 0:
                    bpy.data.actions.remove(action)
                    
            print("Animation cleanup complete")
            return True
            
        except Exception as e:
            print(f"Error clearing animations: {str(e)}")
            return False

    @staticmethod
    def merge_and_weight_meshes(context: Optional[bpy.types.Context] = None, 
                               source_mesh: str = None,
                               target_mesh: str = None, 
                               reweight: bool = False,
                               bone_name: str = None,
                               vertex_group: str = None,
                               weight: float = 1.0) -> bool:
        """Merge two meshes and optionally reweight vertices to a bone or vertex group
        
        Args:
            context: Optional context. If None, uses bpy.context
            source_mesh: Name of the mesh to merge from
            target_mesh: Name of the mesh to merge into
            reweight: Whether to reweight the merged vertices
            bone_name: Name of bone to weight vertices to if reweighting
            vertex_group: Name of vertex group to add vertices to (overrides bone_name)
            weight: Weight value to assign (0.0-1.0)
            
        Returns:
            bool: True if successful, False if error occurs
        """
        if not context:
            context = bpy.context
            
        # Get the meshes
        source = context.scene.objects.get(source_mesh)
        target = context.scene.objects.get(target_mesh)
        
        if not source or not target:
            print(f"Could not find source mesh '{source_mesh}' or target mesh '{target_mesh}'")
            return False
            
        try:
            # Select meshes
            source.select_set(True)
            target.select_set(True)
            context.view_layer.objects.active = target
            
            # Join meshes
            bpy.ops.object.join()
            
            # Handle reweighting if requested
            if reweight and (bone_name or vertex_group):
                # Use vertex group name if provided, otherwise use bone name
                group_name = vertex_group if vertex_group else bone_name
                
                # Create vertex group or get existing one
                vgroup = target.vertex_groups.get(group_name)
                if not vgroup:
                    vgroup = target.vertex_groups.new(name=group_name)
                
                # Add all vertices with specified weight
                vertex_indices = [v.index for v in target.data.vertices]
                vgroup.add(vertex_indices, weight, 'REPLACE')
                
            return True
            
        except Exception as e:
            print(f"Error merging/weighting meshes: {str(e)}")
            return False

    @staticmethod
    def rename_meshes(context, auto_detect: bool = True, remove_prefixes: list = None) -> bool:
        """Rename meshes by automatically detecting and removing prefixes/strings from their names.
        
        Args:
            context: Blender context
            auto_detect: Whether to automatically detect common prefixes to remove
            remove_prefixes: Optional list of additional strings to remove from mesh names
            
        Returns:
            bool: True if successful, False if error occurs
        """
        if not context:
            context = bpy.context
            
        try:
            # Get all mesh objects
            mesh_objects = [obj for obj in context.scene.objects if obj.type == 'MESH']
            
            if not mesh_objects:
                return True
                
            # Auto-detect common prefixes if enabled
            prefixes_to_remove = set()
            if auto_detect:
                # Get all mesh names
                mesh_names = [obj.name for obj in mesh_objects]
                
                # Find common prefixes by looking for patterns like "Something_"
                for name in mesh_names:
                    # Split on underscores and dots
                    parts = name.replace('.', '_').split('_')
                    if len(parts) > 1:
                        # Add the prefix with underscore
                        prefix = parts[0] + '_'
                        # Only add if it appears in multiple names
                        if sum(1 for n in mesh_names if n.startswith(prefix)) > 1:
                            prefixes_to_remove.add(prefix)
            
            # Add any manually specified prefixes
            if remove_prefixes:
                prefixes_to_remove.update(remove_prefixes)
                
            # Early exit if no prefixes found
            if not prefixes_to_remove:
                return True
                
            # Rename objects
            for obj in mesh_objects:
                # Start with original name
                new_name = obj.name
                
                # Remove each prefix/string
                for prefix in prefixes_to_remove:
                    new_name = new_name.replace(prefix, '')
                    
                # Clean up any leading/trailing underscores
                new_name = new_name.strip('_')
                    
                # Set new name if changed
                if new_name != obj.name:
                    obj.name = new_name
                    # Also rename mesh data
                    if obj.data:
                        obj.data.name = new_name
                        
            return True
            
        except Exception as e:
            print(f"Error renaming meshes: {str(e)}")
            return False

    @staticmethod
    def rename_mesh(context: Optional[bpy.types.Context] = None, new_name: str = "Body", rename_all: bool = False) -> bool:
        """Rename the active mesh object and its data, or all mesh objects
        
        Args:
            context: Optional context. If None, uses bpy.context
            new_name: New name for the mesh. Defaults to "Body"
            rename_all: If True, renames all mesh objects. If False, only renames selected/active mesh
            
        Returns:
            bool: True if successful, False if error occurs
        """
        if not context:
            context = bpy.context
            
        try:
            if rename_all:
                # Get all mesh objects
                meshes_to_rename = [obj for obj in bpy.data.objects if obj.type == 'MESH']
            else:
                # Get selected mesh objects
                meshes_to_rename = [obj for obj in context.selected_objects if obj.type == 'MESH']
                
                if not meshes_to_rename:
                    # If nothing selected, try active object
                    active_obj = context.active_object
                    if active_obj and active_obj.type == 'MESH':
                        meshes_to_rename = [active_obj]
                    else:
                        print("No mesh objects selected or active")
                        return False
            
            # Rename each mesh
            for i, obj in enumerate(meshes_to_rename):
                # Add number suffix if multiple objects
                suffix = f".{i:03d}" if len(meshes_to_rename) > 1 and i > 0 else ""
                obj_name = f"{new_name}{suffix}"
                
                # Rename object and its data
                obj.name = obj_name
                if obj.data:
                    obj.data.name = obj_name
                    
            return True
            
        except Exception as e:
            print(f"Error renaming mesh: {str(e)}")
            return False

    @staticmethod
    def select_vertices_by_shape_key(context: bpy.types.Context, side: str, shape_key_name: str, tolerance: float = 1e-5) -> bool:
        """Select vertices affected by a shape key on specified side
        
        Args:
            context: Blender context
            side: Side to select ('L' or 'R')
            shape_key_name: Name of shape key to use
            tolerance: Minimum distance to consider vertex affected
            
        Returns:
            bool: True if successful
        """
        try:
            ob = context.edit_object
            me = ob.data
            bm = bmesh.from_edit_mesh(me)
            
            # Find the shape key
            shape_key = ob.data.shape_keys.key_blocks.get(shape_key_name)
            if not shape_key:
                print(f"Shape key '{shape_key_name}' not found")
                return False

            # Find eye material indices
            eye_material_indices = {
                i for i, mat in enumerate(ob.data.materials) 
                if mat and (mat.name.endswith('Eye') or mat.name.endswith('Eyes'))
            }

            # Get vertices connected to eye materials
            eye_verts = {
                v.index for face in bm.faces 
                if face.material_index in eye_material_indices 
                for v in face.verts
            }

            # Select vertices based on shape key and side
            for v in bm.verts:
                if v.index in eye_verts:
                    bv = me.vertices[v.index]
                    v.select = (shape_key.data[v.index].co - bv.co).length > tolerance
                    if side == 'L' and v.co[0] < 0:
                        v.select = False
                    elif side == 'R' and v.co[0] >= 0:
                        v.select = False

            bpy.ops.mesh.select_more(use_face_step=False)
            bmesh.update_edit_mesh(me)
            return True
            
        except Exception as e:
            print(f"Error selecting vertices: {str(e)}")
            return False

    @staticmethod
    def remove_materials(obj: bpy.types.Object, remove_suffixes: list = None, keep_suffixes: list = None) -> bool:
        """Remove materials from an object based on name suffixes
        
        Args:
            obj: Object to remove materials from
            remove_suffixes: List of suffixes - remove materials ending with these
            keep_suffixes: List of suffixes - keep only materials ending with these
            
        Returns:
            bool: True if successful
        """
        try:
            bpy.context.view_layer.objects.active = obj
            
            if remove_suffixes:
                # Remove materials with specified suffixes
                for i in reversed(range(len(obj.material_slots))):
                    mat = obj.material_slots[i].material
                    if mat and any(mat.name.endswith(suffix) for suffix in remove_suffixes):
                        obj.active_material_index = i
                        bpy.ops.object.material_slot_remove()
                        
            elif keep_suffixes:
                # Keep only materials with specified suffixes
                for i in reversed(range(len(obj.material_slots))):
                    mat = obj.material_slots[i].material
                    if mat and not any(mat.name.endswith(suffix) for suffix in keep_suffixes):
                        obj.active_material_index = i
                        bpy.ops.object.material_slot_remove()
                        
            return True
            
        except Exception as e:
            print(f"Error removing materials: {str(e)}")
            return False

    @staticmethod
    def remove_shape_keys(obj: bpy.types.Object, shape_key_names: list) -> bool:
        """Remove specified shape keys from an object
        
        Args:
            obj: Object to remove shape keys from
            shape_key_names: List of shape key names to remove
            
        Returns:
            bool: True if successful
        """
        try:
            if not obj or not obj.data.shape_keys:
                print(f"No shape keys found for object '{obj.name}'")
                return False

            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode='OBJECT')

            for name in shape_key_names:
                if name in obj.data.shape_keys.key_blocks:
                    obj.active_shape_key_index = obj.data.shape_keys.key_blocks.keys().index(name)
                    bpy.ops.object.shape_key_remove(all=False)
                    
            return True
            
        except Exception as e:
            print(f"Error removing shape keys: {str(e)}")
            return False

    @staticmethod
    def separate_wuwa_eyes(context: bpy.types.Context, 
                     shape_key_name: str,
                     body_mesh_name: str = "Body",
                     unused_shape_keys: list = None) -> bool:
        """Separate eye meshes from body mesh using shape key data
        
        Args:
            context: Blender context
            shape_key_name: Name of shape key to use for separation
            body_mesh_name: Name of body mesh object (default: "Body")
            unused_shape_keys: List of pupil shape keys to remove from body and keep on eye meshes
            
        Returns:
            bool: True if successful
        """
        try:
            # Get body mesh
            body_obj = next((obj for obj in context.scene.objects 
                           if obj.type == 'MESH' and body_mesh_name in obj.name), None)
            if not body_obj:
                print(f"Body mesh '{body_mesh_name}' not found")
                return False

            # Store original state
            context.view_layer.objects.active = body_obj
            body_obj.select_set(True)
            original_mode = context.mode
            
            # Store original shape key values
            original_values = {}
            if body_obj.data.shape_keys:
                original_values = {
                    sk.name: sk.value 
                    for sk in body_obj.data.shape_keys.key_blocks
                }

            try:
                # Process left eye
                # Reset state
                context.view_layer.objects.active = body_obj
                body_obj.select_set(True)
                for obj in context.selected_objects:
                    if obj != body_obj:
                        obj.select_set(False)
                
                # Set target shape key to 1.0
                if shape_key_name in body_obj.data.shape_keys.key_blocks:
                    body_obj.data.shape_keys.key_blocks[shape_key_name].value = 1.0

                # Enter edit mode
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='DESELECT')
                
                # Separate left eye
                ModelUtils.select_vertices_by_shape_key(context, 'L', shape_key_name)
                bpy.ops.mesh.separate(type='SELECTED')
                
                # Return to object mode and process left eye
                bpy.ops.object.mode_set(mode='OBJECT')
                left_eye = next((obj for obj in context.selected_objects if obj != body_obj), None)
                if left_eye:
                    left_eye.name = "Left Eye"
                    context.view_layer.objects.active = left_eye
                    
                    # Reset shape key values
                    if left_eye.data.shape_keys:
                        for sk_name, value in original_values.items():
                            if sk_name in left_eye.data.shape_keys.key_blocks:
                                left_eye.data.shape_keys.key_blocks[sk_name].value = value
                                
                        # Keep Basis (essential for proper eye mesh) and pupil shape keys only
                        shape_keys_to_remove = []
                        for shape_key in left_eye.data.shape_keys.key_blocks:
                            # Always preserve Basis - without it, pupil shapes become default
                            if shape_key.name == 'Basis':
                                continue
                            # Keep pupil shape keys on eye meshes
                            if unused_shape_keys and shape_key.name in unused_shape_keys:
                                continue
                            # Remove all other shape keys (facial expressions, etc.)
                            shape_keys_to_remove.append(shape_key.name)
                        
                        if shape_keys_to_remove:
                            ModelUtils.remove_shape_keys(left_eye, shape_keys_to_remove)
                                
                    # Remove non-eye materials
                    ModelUtils.remove_materials(left_eye, keep_suffixes=["Eye", "Eyes"])
                
                # Process right eye
                # Reset state
                context.view_layer.objects.active = body_obj
                body_obj.select_set(True)
                for obj in context.selected_objects:
                    if obj != body_obj:
                        obj.select_set(False)
                
                # Set target shape key to 1.0
                if shape_key_name in body_obj.data.shape_keys.key_blocks:
                    body_obj.data.shape_keys.key_blocks[shape_key_name].value = 1.0

                # Enter edit mode
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='DESELECT')
                
                # Separate right eye
                ModelUtils.select_vertices_by_shape_key(context, 'R', shape_key_name)
                bpy.ops.mesh.separate(type='SELECTED')
                
                # Return to object mode and process right eye
                bpy.ops.object.mode_set(mode='OBJECT')
                right_eye = next((obj for obj in context.selected_objects if obj != body_obj and obj != left_eye), None)
                if right_eye:
                    right_eye.name = "Right Eye"
                    context.view_layer.objects.active = right_eye
                    
                    # Reset shape key values
                    if right_eye.data.shape_keys:
                        for sk_name, value in original_values.items():
                            if sk_name in right_eye.data.shape_keys.key_blocks:
                                right_eye.data.shape_keys.key_blocks[sk_name].value = value
                                
                        # Keep Basis (essential for proper eye mesh) and pupil shape keys only
                        shape_keys_to_remove = []
                        for shape_key in right_eye.data.shape_keys.key_blocks:
                            # Always preserve Basis - without it, pupil shapes become default
                            if shape_key.name == 'Basis':
                                continue
                            # Keep pupil shape keys on eye meshes
                            if unused_shape_keys and shape_key.name in unused_shape_keys:
                                continue
                            # Remove all other shape keys (facial expressions, etc.)
                            shape_keys_to_remove.append(shape_key.name)
                        
                        if shape_keys_to_remove:
                            ModelUtils.remove_shape_keys(right_eye, shape_keys_to_remove)
                                
                    # Remove non-eye materials
                    ModelUtils.remove_materials(right_eye, keep_suffixes=["Eye", "Eyes"])

                # Reset body shape key values
                context.view_layer.objects.active = body_obj
                for sk_name, value in original_values.items():
                    if sk_name in body_obj.data.shape_keys.key_blocks:
                        body_obj.data.shape_keys.key_blocks[sk_name].value = value

                # Remove all pupil shape keys from body
                if unused_shape_keys:
                    ModelUtils.remove_shape_keys(body_obj, unused_shape_keys)

                # Cleanup
                bpy.ops.object.select_all(action='DESELECT')
                bpy.ops.object.mode_set(mode=original_mode)
                
                return True

            finally:
                # Restore shape key values if something went wrong
                for sk_name, value in original_values.items():
                    if sk_name in body_obj.data.shape_keys.key_blocks:
                        body_obj.data.shape_keys.key_blocks[sk_name].value = value

        except Exception as e:
            print(f"Error separating eyes: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    @staticmethod
    def convert_vertex_colors_to_uv(context: Optional[bpy.types.Context] = None,
                                   target_object: str = None,
                                   color_multiplier: float = 255.0) -> bool:
        """Convert vertex colors to UV coordinates and create eye-related materials
        
        Creates a new UV map populated with vertex color red channel data multiplied by the
        color_multiplier, and creates EyeHi_UI and EyeShadow_UI materials by duplicating
        the Eye_UI material. Assigns vertices to appropriate materials based on UV coordinates.
        
        Args:
            context: Optional context. If None, uses bpy.context
            target_object: Name of the target object. If None, uses active object
            color_multiplier: Value to multiply the red channel by (default: 255.0)
            
        Returns:
            bool: True if successful, False if error occurs
        """
        if not context:
            context = bpy.context
            
        # Get target object (case insensitive)
        if target_object:
            obj = None
            # Search for object case-insensitively
            for scene_obj in bpy.data.objects:
                if scene_obj.name.lower() == target_object.lower():
                    obj = scene_obj
                    break
            
            if not obj:
                print(f"No object found with name '{target_object}' (case insensitive)")
                return False
        else:
            obj = context.active_object
            
        if not obj or obj.type != 'MESH':
            print("No valid mesh object found")
            return False
            
        try:
            # Replicate the original script exactly
            mesh = obj.data
            bm = bmesh.new()
            bm.from_mesh(mesh)

            # Check if there's an active vertex color layer
            color_layer = bm.loops.layers.color.active
            if not color_layer:
                print(f"Object '{obj.name}' has no active vertex color layer.")
                bm.free()
                return False

            # Create new materials if they don't exist and assign them to the object
            material_prefix = ""
            eye_ui_material = None
            for mat in obj.data.materials:
                if "Eye_UI" in mat.name:
                    material_prefix = mat.name.split("Eye_UI")[0]
                    eye_ui_material = mat
                    break  # Stop after finding the first matching material

            eye_hi_material_name = material_prefix + "EyeHi_UI"
            eye_shadow_material_name = material_prefix + "EyeShadow_UI"

            if eye_ui_material:
                if eye_hi_material_name not in bpy.data.materials:
                    material_eye_hi = eye_ui_material.copy()  # Duplicate
                    material_eye_hi.name = eye_hi_material_name #rename
                else:
                    material_eye_hi = bpy.data.materials[eye_hi_material_name]
                if eye_hi_material_name not in obj.data.materials:
                    obj.data.materials.append(material_eye_hi)

                if eye_shadow_material_name not in bpy.data.materials:
                    material_eye_shadow = eye_ui_material.copy()  # Duplicate
                    material_eye_shadow.name = eye_shadow_material_name #rename
                else:
                    material_eye_shadow = bpy.data.materials[eye_shadow_material_name]
                if eye_shadow_material_name not in obj.data.materials:
                    obj.data.materials.append(material_eye_shadow)
            else:
                print("Error: 'Eye_UI' material not found.  Cannot duplicate.")
                bm.free()
                return False

            # Create a new UV layer
            uv_layer = bm.loops.layers.uv.new()
            new_uv_layer_index = len(mesh.uv_layers)  # Get the index before applying bmesh changes

            # Initialize all UV coordinates to (0, 0)
            for face in bm.faces:
                for loop in face.loops:
                    loop[uv_layer].uv = (0.0, 0.0)  # Initialize to (0, 0)

            # Iterate through the faces and loops to set the UV coordinates
            eye_ui_vertex_count = 0  # Initialize counter
            for face in bm.faces:
                # Check if the face has a material name containing "Eye_UI", "EyeHi_UI", or "EyeShadow_UI"
                if face.material_index < len(mesh.materials) and mesh.materials[face.material_index] and any(
                    eye_material in mesh.materials[face.material_index].name
                    for eye_material in ["Eye_UI", "EyeHi_UI", "EyeShadow_UI"]
                ):
                    for loop in face.loops:
                        color = loop[color_layer]
                        u = color[0] * color_multiplier  # Red channel multiplied
                        v = 0.5
                        loop[uv_layer].uv = (u, v)  # Set the final UV Coord
                        eye_ui_vertex_count += 1  # Increment counter

            # Update the mesh with the changes
            bm.to_mesh(mesh)

            # Now we can access the UV layer and check the coordinates.
            mesh = obj.data
            
            # Get the newly created UV layer.
            new_uv_layer = mesh.uv_layers[new_uv_layer_index]

            # Create a set to store unique vertices that need to be assigned to EyeHi_UI
            vertices_to_assign_eye_hi = set()
            vertices_to_assign_eye_shadow = set()

            # Iterate through the mesh data to find vertices with the target UV coordinates.
            for face in mesh.polygons:
                for loop_index in face.loop_indices:
                    uv_coords = new_uv_layer.data[loop_index].uv
                    # Check for each UV coordinate individually
                    if (uv_coords[0] == 0 and uv_coords[1] == 0.5) or \
                       (2.5 < uv_coords[0] < 3.5 and uv_coords[1] == 0.5) or \
                       (uv_coords[0] == 4.0 and uv_coords[1] == 0.5):
                        # Get the vertex index from the loop
                        vert_index = mesh.loops[loop_index].vertex_index
                        vertices_to_assign_eye_hi.add(vert_index)
                    elif (0.5 < uv_coords[0] < 2.5 and uv_coords[1] == 0.5):
                        # Get the vertex index from the loop
                        vert_index = mesh.loops[loop_index].vertex_index
                        vertices_to_assign_eye_shadow.add(vert_index)

            # Assign the vertices to the EyeHi_UI material using BMesh.
            if vertices_to_assign_eye_hi:
                
                #get the material index.
                material_eye_hi_index = obj.data.materials.find(eye_hi_material_name)
                
                if material_eye_hi_index != -1:
                    
                    # Assign the material to the selected faces.
                    for face in bm.faces:
                        for loop in face.loops:
                            if loop.vert.index in vertices_to_assign_eye_hi:
                                face.material_index = material_eye_hi_index                                          
                    
                    # Update the mesh with the changes from the bmesh.
                    bm.to_mesh(mesh)
                    print(f"Vertices with UV coordinates (0, 0.5), (3, 0.5), and (4, 0.5) assigned to material '{eye_hi_material_name}'.")
                else:
                    print(f"Error: Material '{eye_hi_material_name}' not found on object '{obj.name}'.")
            else:
                print(f"No vertices found with UV coordinates (0, 0.5), (3, 0.5), or (4, 0.5).")

            # Assign the vertices to the EyeShadow_UI material using BMesh.
            if vertices_to_assign_eye_shadow:
                
                #get the material index.
                material_eye_sdw_index = obj.data.materials.find(eye_shadow_material_name)
                
                if material_eye_sdw_index != -1:
                    
                    # Assign the material to the selected faces.
                    for face in bm.faces:
                        for loop in face.loops:
                            if loop.vert.index in vertices_to_assign_eye_shadow:
                                face.material_index = material_eye_sdw_index                                          
                    
                    # Update the mesh with the changes from the bmesh.
                    bm.to_mesh(mesh)
                    print(f"Vertices with UV coordinates (0.5 < x < 2.5, y = 0.5) assigned to material '{eye_shadow_material_name}'.")
                else:
                    print(f"Error: Material '{eye_shadow_material_name}' not found on object '{obj.name}'.")
            else:
                print(f"No vertices found with UV coordinates (0.5 < x < 2.5, y = 0.5).")
            print(f"Number of vertices found for EyeShadow_UI: {len(vertices_to_assign_eye_shadow)}") # Debug line

            bm.free()
            if len(mesh.uv_layers) > new_uv_layer_index:
                uv_layer_name = mesh.uv_layers[new_uv_layer_index].name
                print(f"Processing completed with temporary UV map on '{obj.name}'.")
                print(
                    f"Number of vertices processed for materials containing 'Eye_UI', 'EyeHi_UI', or 'EyeShadow_UI': {eye_ui_vertex_count}"
                )  # Print the count
                
                # Remove the temporary UV layer
                mesh.uv_layers.remove(mesh.uv_layers[new_uv_layer_index])
                print(f"Temporary UV layer removed from '{obj.name}'.")
            else:
                print(f"Error: Could not find the temporary UV layer on '{obj.name}'.")
                
            return True
            
        except Exception as e:
            print(f"Error converting vertex colors to UV: {str(e)}")
            if 'bm' in locals():
                bm.free()
            return False

    @staticmethod
    def assign_modified_material(context: Optional[bpy.types.Context] = None,
                                search_keywords = None,
                                new_suffix: str = "Bangs") -> bool:
        """Assign modified materials to meshes containing specific keywords in their names
        
        For meshes containing any of the search keywords in their name:
        - Duplicates the first material
        - Renames the duplicated material by taking the original name,
          removing characters from the end until a '_' is found, and appending the new suffix
        - Assigns the renamed material to all vertices of the mesh
        
        Args:
            context: Optional context. If None, uses bpy.context
            search_keywords: Keyword(s) to search for in mesh names (string or list of strings, case-insensitive)
            new_suffix: Suffix to append to the material name (default: "Bangs")
            
        Returns:
            bool: True if successful, False if error occurs
        """
        if not context:
            context = bpy.context
            
        if not search_keywords:
            print("Error: search_keywords must be provided")
            return False
            
        # Normalize search_keywords to list
        if isinstance(search_keywords, str):
            search_keywords = [search_keywords]
        elif not isinstance(search_keywords, list):
            print("Error: search_keywords must be a string or list of strings")
            return False
            
        try:
            # Store current mode and active object
            prev_active = context.active_object
            prev_mode = SceneUtils.ensure_mode(context, 'OBJECT')
            
            processed_objects = []
            
            # Find meshes containing any of the search keywords
            for obj in bpy.data.objects:
                if obj.type != 'MESH':
                    continue
                    
                # Check if object name contains any search keyword (case-insensitive)
                obj_name_lower = obj.name.lower()
                has_keyword = any(keyword.lower() in obj_name_lower for keyword in search_keywords)
                
                if not has_keyword:
                    continue
                    
                # Check if mesh has materials
                if not obj.data.materials:
                    print(f"Mesh '{obj.name}' has no material to duplicate")
                    continue
                    
                # Get first material
                original_material = obj.data.materials[0]
                original_name = original_material.name
                
                # Generate new material name
                last_underscore_index = original_name.rfind('_')
                if last_underscore_index != -1:
                    new_material_name = original_name[:last_underscore_index + 1] + new_suffix
                else:
                    new_material_name = original_name + "_" + new_suffix
                
                # Check if material with this name already exists
                if new_material_name in bpy.data.materials:
                    new_material = bpy.data.materials[new_material_name]
                    print(f"Using existing material '{new_material_name}' for '{obj.name}'")
                else:
                    # Duplicate the original material
                    new_material = original_material.copy()
                    new_material.name = new_material_name
                    print(f"Created new material '{new_material_name}' from '{original_name}'")
                
                # Set object as active
                context.view_layer.objects.active = obj
                
                # Clear existing materials and assign new one
                obj.data.materials.clear()
                obj.data.materials.append(new_material)
                
                # Enter edit mode to select all vertices
                SceneUtils.ensure_mode(context, 'EDIT')
                bpy.ops.mesh.select_all(action='SELECT')
                
                # Assign material to all faces (done automatically when only one material exists)
                # All faces will use material index 0 by default
                
                # Return to object mode
                SceneUtils.ensure_mode(context, 'OBJECT')
                
                processed_objects.append(obj.name)
                print(f"Material '{original_name}' duplicated and renamed to '{new_material.name}', assigned to '{obj.name}'")
            
            # Restore previous state
            if prev_active:
                context.view_layer.objects.active = prev_active
            SceneUtils.restore_mode(context, prev_mode)
            
            # Report results
            if processed_objects:
                print(f"Successfully processed {len(processed_objects)} objects: {', '.join(processed_objects)}")
            else:
                search_keywords_str = "', '".join(search_keywords)
                print(f"No mesh objects found containing keywords: '{search_keywords_str}'")
            
            return True
            
        except Exception as e:
            print(f"Error assigning modified materials: {str(e)}")
            # Restore state on error
            if 'prev_active' in locals() and prev_active:
                context.view_layer.objects.active = prev_active
            if 'prev_mode' in locals():
                SceneUtils.restore_mode(context, prev_mode)
            return False
    



