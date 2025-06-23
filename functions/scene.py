import bpy
from typing import Optional, List
from .game_detection import GameDetector
import os

class SceneUtils:
    """Utility class for scene operations"""
    
    @staticmethod
    def remove_empties(context: Optional[bpy.types.Context] = None) -> List[str]:
        """Remove all empty objects from the scene
        
        Args:
            context: Optional context. If None, uses bpy.context
            
        Returns:
            List[str]: Names of removed empty objects
        """
        if not context:
            context = bpy.context
            
        removed_names = []
        
        # Get all empty objects
        empty_objects = [obj for obj in context.scene.objects if obj.type == 'EMPTY']
        
        # Remove each empty
        for empty in empty_objects:
            name = empty.name
            bpy.data.objects.remove(empty, do_unlink=True)
            removed_names.append(name)
            print(f"Removed empty object: {name}")
            
        if not removed_names:
            print("No empty objects found to remove")
            
        return removed_names
    
    @staticmethod
    def set_wireframe_display(context: Optional[bpy.types.Context] = None) -> bool:
        """Set the active object to wireframe display mode and show in front
        
        Args:
            context: Optional context. If None, uses bpy.context
            
        Returns:
            bool: True if successful, False if no active object
        """
        if not context:
            context = bpy.context
            
        if not context.object:
            print("No active object found")
            return False
            
        if context.object.type == 'MESH':
            return False
            
        context.object.display_type = "WIRE"
        context.object.show_in_front = True
        return True
    
    @staticmethod
    def set_material_view(context: Optional[bpy.types.Context] = None, mode: str = "MATERIAL") -> bool:
        """Set viewport shading to material preview mode
        
        Args:
            context: Optional context. If None, uses bpy.context
            mode: Shading mode to set. One of: WIREFRAME, SOLID, MATERIAL, RENDERED
            
        Returns:
            bool: True if successful, False if no 3D view found
        """
        if not context:
            context = bpy.context
            
        # Set viewport shading to Material Preview mode
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces[0].shading.type = mode
                return True
                
        return False

    @staticmethod
    def set_root_name(context: Optional[bpy.types.Context] = None) -> bool:
        """Set the root object name while preserving model info"""
        if not context:
            context = bpy.context
            
        # Find and select root armature or mesh
        root = None
        for obj in context.scene.objects:
            if obj.type == 'ARMATURE':
                root = obj
                break
        
        # If no armature found, look for mesh
        if not root:
            for obj in context.scene.objects:
                if obj.type == 'MESH':
                    root = obj
                    break
                    
        if not root:
            print("No armature or mesh found")
            return False
            
        # Select and make active
        for obj in context.selected_objects:
            obj.select_set(False)
        root.select_set(True)
        context.view_layer.objects.active = root
            
        model_info, display_name, icon = GameDetector.get_model_name(context)
        if model_info and context.active_object:
            # Store original name to preserve model info
            original_name = context.active_object.name
            # Set display name
            if context.active_object.type == 'ARMATURE':
                context.active_object.name = "Armature"
                # Set internal armature name
                if context.active_object.data:
                    context.active_object.data.name = "Armature"
            else:
                context.active_object.name = display_name
            # Store original name for game detection
            context.active_object["original_name"] = original_name
        return True

    @staticmethod
    def ensure_mode(context: Optional[bpy.types.Context] = None, mode: str = 'OBJECT') -> str:
        """Ensure we're in the correct mode and return previous mode
        
        Args:
            context: Optional context. If None, uses bpy.context
            mode: Target mode to switch to
            
        Returns:
            str: Previous mode that was active
        """
        if not context:
            context = bpy.context
            
        # Store previous mode
        prev_mode = context.mode
        
        # Only switch if needed
        if context.mode != mode:
            bpy.ops.object.mode_set(mode=mode)
            
        return prev_mode
    
    @staticmethod
    def restore_mode(context: Optional[bpy.types.Context] = None, mode: str = 'OBJECT'):
        """Restore to a specific mode
        
        Args:
            context: Optional context. If None, uses bpy.context
            mode: Mode to restore to
        """
        if not context:
            context = bpy.context
            
        if context.mode != mode:
            bpy.ops.object.mode_set(mode=mode)
    
    @staticmethod
    def cleanup_selection(context: Optional[bpy.types.Context] = None):
        """Cleanup selection state
        
        Args:
            context: Optional context. If None, uses bpy.context
        """
        if not context:
            context = bpy.context
            
        # Ensure object mode
        SceneUtils.ensure_mode(context, 'OBJECT')
        
        # Deselect all objects
        for obj in context.selected_objects:
            obj.select_set(False)
            
        # Clear active object
        context.view_layer.objects.active = None

    @staticmethod
    def fix_materials(context: Optional[bpy.types.Context] = None) -> bool:
        """Set all material base color alpha settings to none and normal map strength to 0
        
        Compatible with Blender 3.6+ and 4.x
        
        Args:
            context: Optional context. If None, uses bpy.context
            
        Returns:
            bool: True if successful
        """
        if not context:
            context = bpy.context
            
        try:
            # Get Blender version
            version = bpy.app.version

            # Iterate through all materials in the blend file
            for material in bpy.data.materials:
                if not material.use_nodes:
                    continue
                    
                try:
                    # Set alpha blend mode to none - these properties exist in 3.6+
                    if hasattr(material, "blend_method"):
                        material.blend_method = 'OPAQUE'
                    if hasattr(material, "shadow_method"):
                        material.shadow_method = 'NONE'
                    
                    # Get node tree
                    nodes = material.node_tree.nodes
                    links = material.node_tree.links
                    
                    # Find Principled BSDF node
                    principled = None
                    for node in nodes:
                        if node.type == 'BSDF_PRINCIPLED':
                            principled = node
                            break
                            
                    if principled:
                        # Safely expand base color input if possible
                        if hasattr(principled.inputs[0], "show_expanded"):
                            principled.inputs[0].show_expanded = True
                        
                        # Find and remove normal map connections
                        normal_input = None
                        for input in principled.inputs:
                            if input.name == "Normal":
                                normal_input = input
                                break
                                
                        if normal_input and normal_input.is_linked:
                            # Find all links connected to the normal input
                            links_to_remove = [link for link in normal_input.links]
                            for link in links_to_remove:
                                links.remove(link)
                                print(f"Removed normal map connection from {material.name}")
                except Exception as mat_error:
                    print(f"Error processing material {material.name}: {str(mat_error)}")
                    continue
            
            # Set alpha mode to none for all images
            for image in bpy.data.images:
                if hasattr(image, "alpha_mode"):
                    image.alpha_mode = 'NONE'
                            
            return True
            
        except Exception as e:
            print(f"Error fixing material alpha: {str(e)}")
            return False

    @staticmethod
    def fix_material_textures(context: Optional[bpy.types.Context] = None, imported_directory: Optional[str] = None) -> bool:
        """Fix material texture paths by searching in the Textures folder
        
        Compatible with Blender 3.6+ and 4.x
        
        Args:
            context: Optional context. If None, uses bpy.context
            imported_directory: Directory path where the model was imported from
            
        Returns:
            bool: True if successful
        """
        if not context:
            context = bpy.context
            
        try:
            # If no import directory provided, try to get it from armature or mesh
            if not imported_directory:
                print("No import directory provided, searching in objects...")
                for obj in context.scene.objects:
                    if (obj.type in {'ARMATURE', 'MESH'}) and "import_dir" in obj:
                        imported_directory = obj["import_dir"]
                        print(f"Found import directory from {obj.type.lower()}: {imported_directory}")
                        break
            
            if not imported_directory:
                print("Error: Could not find import directory")
                return False
                
            print(f"Using import directory: {imported_directory}")
            textures_dir = os.path.join(imported_directory, "Textures")
            print(f"Looking for textures in: {textures_dir}")
            
            fixed_textures = []
            missing_textures = []
            modified_images = set()  # Track modified images to reload
            
            # Iterate through all materials in the blend file
            for material in bpy.data.materials:
                if not material.use_nodes:
                    continue
                    
                try:
                    print(f"\nChecking material: {material.name}")
                    # Get node tree safely
                    if not material.node_tree:
                        print(f"Material {material.name} has no node tree, skipping")
                        continue
                        
                    nodes = material.node_tree.nodes
                    
                    # Find all image texture nodes
                    for node in nodes:
                        if node.type != 'TEX_IMAGE':
                            continue
                            
                        # Safely get image
                        image = getattr(node, "image", None)
                        if not image:
                            continue
                            
                        print(f"Found image node: {image.name}")
                        print(f"Current filepath: {image.filepath}")
                        
                        # Skip if image is packed
                        if getattr(image, "packed_file", None):
                            print(f"Skipping packed image: {image.name}")
                            continue
                            
                        # Check if current path exists
                        abs_path = bpy.path.abspath(image.filepath)
                        if not os.path.exists(abs_path):
                            print(f"Image path not found: {abs_path}")
                            # Try to find texture in Textures folder
                            texture_name = os.path.basename(image.filepath)
                            new_path = os.path.join(textures_dir, texture_name)
                            print(f"Trying path: {new_path}")
                            
                            if os.path.exists(new_path):
                                # Update image path
                                try:
                                    # Store original filepath to check if it changed
                                    original_path = image.filepath
                                    
                                    # Set the new filepath
                                    image.filepath = bpy.path.relpath(new_path)
                                    
                                    # If filepath actually changed
                                    if original_path != image.filepath:
                                        # Force image to be marked as updated
                                        image.update_tag()
                                        # Mark image for reload
                                        modified_images.add(image)
                                        # Add to fixed list
                                        fixed_textures.append((material.name, texture_name))
                                        print(f"Fixed path: {image.filepath}")
                                        
                                        # Force node update
                                        node.image = None
                                        node.image = image
                                except Exception as path_error:
                                    print(f"Error updating path for {texture_name}: {str(path_error)}")
                                    missing_textures.append((material.name, texture_name))
                            else:
                                missing_textures.append((material.name, texture_name))
                                print(f"Could not find texture: {texture_name}")
                except Exception as mat_error:
                    print(f"Error processing material {material.name}: {str(mat_error)}")
                    continue
            
            # Reload all modified images
            for image in modified_images:
                try:
                    # Force reload the image
                    if hasattr(image, "reload"):
                        image.reload()
                    # Mark the image as dirty to ensure it's saved
                    if hasattr(image, "is_dirty"):
                        image.is_dirty = True
                except Exception as reload_error:
                    print(f"Error reloading image {image.name}: {str(reload_error)}")
            
            # Print results
            if fixed_textures:
                print("\nFixed texture paths:")
                for mat_name, tex_name in fixed_textures:
                    print(f"Material '{mat_name}': Found '{tex_name}' in Textures folder")
                    
            if missing_textures:
                print("\nMissing textures:")
                for mat_name, tex_name in missing_textures:
                    print(f"Material '{mat_name}': Could not find '{tex_name}'")
            
            return True
            
        except Exception as e:
            print(f"Error fixing material textures: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
