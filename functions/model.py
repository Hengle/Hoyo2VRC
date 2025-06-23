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
                    if not ModelUtils._create_mixed_shape_key(target_obj, new_key, sources):
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
    def _create_mixed_shape_key(obj: bpy.types.Object, 
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
                                
                        # Keep only pupil shape keys
                        shape_keys_to_remove = []
                        for shape_key in left_eye.data.shape_keys.key_blocks:
                            if shape_key.name == 'Basis' or shape_key.name in unused_shape_keys:
                                continue
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
                                
                        # Keep only pupil shape keys
                        shape_keys_to_remove = []
                        for shape_key in right_eye.data.shape_keys.key_blocks:
                            if shape_key.name == 'Basis' or shape_key.name in unused_shape_keys:
                                continue
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
    def separate_eye_ui_by_vertex_colors(
        context: Optional[bpy.types.Context] = None,
        mesh_name_contains: str = "Face",
        source_material_contains: str = "Eye_UI",
        shadow_material_name: str = "EyeShadow_UI", 
        highlight_material_name: str = "EyeHi_UI",
        debug_output: bool = True
    ) -> bool:
        """Separate eye UI meshes based on vertex colors and assign them to different materials.
        
        Args:
            context: Optional context. If None, uses bpy.context
            mesh_name_contains: String that mesh name should contain to be processed
            source_material_contains: String that source material name should contain
            shadow_material_name: Name for shadow material (0.05 < red*255 < 0.2)
            highlight_material_name: Name for highlight material (red*255 ≤ 0.05 or 0.2 ≤ red*255 < 0.5)
            debug_output: Whether to print debug information
            
        Returns:
            bool: True if successful, False if error occurs
        """
        if not context:
            context = bpy.context
            
        try:
            print("Starting eye UI separation process...")
            
            # Step 1: Find the target mesh
            face_mesh = None
            for obj in bpy.data.objects:
                if obj.type == 'MESH' and mesh_name_contains in obj.name:
                    face_mesh = obj
                    break
                    
            if not face_mesh:
                print(f"No mesh found containing '{mesh_name_contains}' in its name")
                return False
                
            print(f"Found target mesh: {face_mesh.name}")
                
            # Store original selection and mode
            original_mode = context.object.mode if context.object else 'OBJECT'
            original_active = context.view_layer.objects.active
            original_selection = {o: o.select_get() for o in context.selectable_objects}
            
            # Set up our working environment
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            face_mesh.select_set(True)
            context.view_layer.objects.active = face_mesh
            
            # Step 2: Find source materials
            source_materials = []
            source_material_indices = []
            
            for i, mat in enumerate(face_mesh.data.materials):
                if mat and source_material_contains in mat.name:
                    source_materials.append(mat)
                    source_material_indices.append(i)
                    
            if not source_materials:
                print(f"No materials containing '{source_material_contains}' found")
                return False
                
            print(f"Found source materials: {[m.name for m in source_materials]}")
            
            # Step 3: Create new materials - FULLY DUPLICATE the source material
            shadow_mat = None
            highlight_mat = None
            source_mat = source_materials[0]  # Use the first Eye_UI material as source
            
            # Check if materials already exist and delete them to start fresh
            for mat in bpy.data.materials:
                if mat.name == shadow_material_name:
                    bpy.data.materials.remove(mat)
                if mat.name == highlight_material_name:
                    bpy.data.materials.remove(mat)
                    
            # Now create the new materials by copying the source
            shadow_mat = source_mat.copy()
            shadow_mat.name = shadow_material_name
            
            highlight_mat = source_mat.copy()
            highlight_mat.name = highlight_material_name
            
            # Add materials to mesh if needed
            if shadow_material_name not in face_mesh.data.materials:
                face_mesh.data.materials.append(shadow_mat)
            if highlight_material_name not in face_mesh.data.materials:
                face_mesh.data.materials.append(highlight_mat)
                
            # Get material indices
            shadow_idx = face_mesh.data.materials.find(shadow_material_name)
            highlight_idx = face_mesh.data.materials.find(highlight_material_name)
            
            print(f"Created materials: {shadow_material_name} (index {shadow_idx}), {highlight_material_name} (index {highlight_idx})")
            
            # Step 4: Process the mesh in Edit Mode
            bpy.ops.object.mode_set(mode='EDIT')
            
            # Get BMesh for edit operations
            bm = bmesh.from_edit_mesh(face_mesh.data)
            
            # Ensure vertex colors exist
            if not bm.loops.layers.color:
                print("No vertex colors found on the mesh")
                bm.free()
                bpy.ops.object.mode_set(mode='OBJECT')
                return False
            
            vcol_layer = bm.loops.layers.color.active
            
            # Count statistics
            count_source = 0
            count_shadow = 0
            count_highlight = 0
            
            # Initial analysis for debugging
            if debug_output:
                # Define the EXACT thresholds as specified by the user
                threshold_low = 0.05
                threshold_mid = 0.2
                threshold_high = 0.5
                
                print("\nUsing these EXACT thresholds as specified:")
                print(f"- Shadow material: {threshold_low} < red < {threshold_mid}")
                print(f"- Highlight material: red ≤ {threshold_low} OR {threshold_mid} ≤ red < {threshold_high}")
                print(f"- Original material: red ≥ {threshold_high}")
                
                # Collect sample red values
                red_values = []
                for face in bm.faces:
                    if face.material_index in source_material_indices:
                        for loop in face.loops:
                            red = loop[vcol_layer][0]  # Red channel (0-1 range)
                            red_values.append(red)
                
                if red_values:
                    red_values.sort()
                    num_values = len(red_values)
                    print("\nRed channel distribution (raw values):")
                    print(f"Min value: {red_values[0]:.6f}")
                    print(f"10% value: {red_values[int(num_values*0.1)]:.6f}")
                    print(f"25% value: {red_values[int(num_values*0.25)]:.6f}")
                    print(f"Median value: {red_values[int(num_values*0.5)]:.6f}")
                    print(f"75% value: {red_values[int(num_values*0.75)]:.6f}")
                    print(f"90% value: {red_values[int(num_values*0.9)]:.6f}")
                    print(f"Max value: {red_values[-1]:.6f}")
                    print("")
            
            # Step 5: Categorize face material assignments based on vertex colors
            print("\nProcessing faces based on vertex colors...")
            shadow_faces = []
            highlight_faces = []
            original_faces = []
            
            for face in bm.faces:
                # Only process faces with the source material
                if face.material_index not in source_material_indices:
                    continue
                
                # Track what category this face falls into based on its vertices
                face_is_shadow = False
                face_is_highlight = False
                face_is_original = False
                
                # Check each vertex color
                for loop in face.loops:
                    # Get the RED channel of the vertex color (0-1 range)
                    red = loop[vcol_layer][0]
                    
                    # Debug output for some vertices
                    if debug_output and face.index % 500 == 0:
                        print(f"Face {face.index}, vertex red value: {red:.6f}")
                    
                    # DIRECTLY apply the user-specified thresholds:
                    # - If red >= 0.5: keep original material
                    # - If 0.05 < red < 0.2: assign to EyeShadow_UI material 
                    # - If red <= 0.05 OR 0.2 <= red < 0.5: assign to EyeHi_UI material
                    
                    if red >= 0.5:
                        face_is_original = True
                    elif 0.05 < red < 0.2:
                        face_is_shadow = True
                    elif red <= 0.05 or (0.2 <= red < 0.5):
                        face_is_highlight = True
                
                # Determine the final category for this face
                # Priority: Shadow > Highlight > Original
                if face_is_shadow:
                    shadow_faces.append(face)
                elif face_is_highlight:
                    highlight_faces.append(face)
                else:
                    original_faces.append(face)
            
            # Step 6: Apply material assignments
            # Assign shadow material
            print(f"Found {len(shadow_faces)} faces for shadow material")
            for face in shadow_faces:
                face.material_index = shadow_idx
                count_shadow += 1
                
            # Assign highlight material
            print(f"Found {len(highlight_faces)} faces for highlight material")
            for face in highlight_faces:
                face.material_index = highlight_idx
                count_highlight += 1
                
            # Count remaining source faces
            count_source = len(original_faces)
                
            # Update the mesh
            bmesh.update_edit_mesh(face_mesh.data)
            bm.free()
            
            # Return to Object mode
            bpy.ops.object.mode_set(mode='OBJECT')
            
            print("\nResults:")
            print(f"Faces assigned to {shadow_material_name}: {count_shadow}")
            print(f"Faces assigned to {highlight_material_name}: {count_highlight}")
            print(f"Faces remaining with source material: {count_source}")
            
            # Step 7: Restore original context
            for o, selected in original_selection.items():
                if o is not None and o.name in bpy.data.objects:
                    o.select_set(selected)
            if original_active and original_active.name in bpy.data.objects:
                context.view_layer.objects.active = original_active
            if original_mode != 'OBJECT':
                bpy.ops.object.mode_set(mode=original_mode)
                
            return True
            
        except Exception as e:
            print(f"Error separating eye UI by vertex colors: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
