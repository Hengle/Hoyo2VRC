import bpy
from bpy.types import Operator
from typing import Optional
from .game_detection import ModelInfo, get_model_info, GameDetector
from .armature import ArmatureUtils
from .model import ModelUtils
from .scene import SceneUtils

class HOYO2VRC_OT_Convert(Operator):
    """Convert the model to VRChat format"""
    bl_idname = "hoyo2vrc.convert"
    bl_label = "Convert Model"
    
    @classmethod
    def poll(cls, context):
        """Determine if the operator can be called"""
        model_info = GameDetector.get_model_name(context)[0]
        if not model_info:
            return False
        return GameDetector.is_game_supported(model_info.game)
    
    def execute(self, context):
        model_info = GameDetector.get_model_name(context)[0]
        if not model_info:
            self.report({'ERROR'}, "No valid model found to convert")
            context.window_manager.popup_menu(lambda self, context: self.layout.label(text="No valid model found to convert"), 
                                           title="Conversion Failed", icon='ERROR')
            return {'CANCELLED'}
            
        if not GameDetector.is_game_supported(model_info.game):
            self.report({'ERROR'}, f"Conversion for {model_info.game} is not yet supported")
            context.window_manager.popup_menu(lambda self, context: self.layout.label(text=f"Conversion for {model_info.game} is not yet supported"), 
                                           title="Unsupported Game", icon='ERROR')
            return {'CANCELLED'}
            
        try:
            success = converter.convert_model(context, model_info)
            if success:
                # Show success message with model info
                message = f"Successfully converted {model_info.clean_name}"
                if model_info.game:
                    message += f" ({model_info.game})"
                self.report({'INFO'}, message)
                context.window_manager.popup_menu(lambda self, context: self.layout.label(text=message), 
                                               title="Conversion Complete", icon='CHECKMARK')
                return {'FINISHED'}
            else:
                # Show error message with model info
                message = f"Failed to convert {model_info.clean_name}"
                if model_info.game:
                    message += f" ({model_info.game})"
                self.report({'ERROR'}, message)
                context.window_manager.popup_menu(lambda self, context: self.layout.label(text=message), 
                                               title="Conversion Failed", icon='ERROR')
                return {'CANCELLED'}
        except Exception as e:
            # Show detailed error message
            error_message = f"Error during conversion: {str(e)}"
            self.report({'ERROR'}, error_message)
            context.window_manager.popup_menu(lambda self, context: self.layout.label(text=error_message), 
                                           title="Conversion Error", icon='ERROR')
            return {'CANCELLED'}

class converter:
    """Class to handle file conversion operations"""
    
    @staticmethod
    def convert_model(context, model_info: Optional[ModelInfo] = None) -> bool:
        """Convert the model based on its detected game and settings
        
        Args:
            context: Blender context
            model_info: Optional ModelInfo object. If None, will detect from active object
            
        Returns:
            bool: True if conversion was successful
        """
        if not model_info:
            # Get model info from active object or scene
            if not context.active_object:
                print("No active object found")
                return False
                
            model_info = get_model_info(context.active_object.name)
            
        if not model_info:
            print("No valid model found to convert")
            return False
            
        # Get conversion settings from scene
        settings = {
            'merge_all_meshes': context.scene.merge_all_meshes,
            'generate_shape_keys': context.scene.generate_shape_keys,
            'generate_shape_keys_mmd': context.scene.generate_shape_keys_mmd,
            'keep_star_eye_mesh': context.scene.keep_star_eye_mesh,
        }
        
        try:
            success = False
            # Convert based on game
            if model_info.game == "Genshin Impact":
                success = converter.convert_genshin(context, model_info, settings)
            elif model_info.game == "Genshin Impact Weapon":
                success = converter.convert_genshin_weapons(context, model_info, settings)
            elif model_info.game == "Honkai Star Rail":
                success = converter.convert_starrail(context, model_info, settings)
            elif model_info.game == "Honkai Impact 3rd":
                success = converter.convert_hi3(context, model_info, settings)
            elif model_info.game == "Zenless Zone Zero":
                success = converter.convert_zzz(context, model_info, settings)
            elif model_info.game == "Wuthering Waves":
                success = converter.convert_wuwa(context, model_info, settings)
            else:
                print(f"Unsupported game: {model_info.game}")
                return False
                
            # Mark as converted if successful
            if success and context.active_object:
                context.active_object.hoyo2vrc_converted = True
                
            return success
        except Exception as e:
            print(f"Error during conversion: {str(e)}")
            return False
            
    @staticmethod
    def convert_genshin(context, model_info: ModelInfo, settings: dict) -> bool:
        """Convert Genshin Impact models"""
        print(f"Converting Genshin model: {model_info.clean_name}")
        
        # Store model info on armature
        armature = context.active_object
        if armature and armature.type == 'ARMATURE':
            armature["hoyo2vrc_model_name"] = model_info.clean_name
            armature["hoyo2vrc_game"] = model_info.game
            if model_info.body_type:
                armature["hoyo2vrc_body_type"] = model_info.body_type
            armature["hoyo2vrc_converted"] = True
            
        SceneUtils.remove_empties(context)
        # Clear rotation
        ArmatureUtils.clear_rotation(context)
        # Clean Meshes
        ModelUtils.clean_meshes(context)
        # Set Wireframe Display
        SceneUtils.set_wireframe_display(context)
        # Set Material View
        SceneUtils.set_material_view(context, "MATERIAL")
        # Rename Bones
        ArmatureUtils.rename_bones(context)
        # Rename Armature Data
        ArmatureUtils.rename_armature_data(context, "Armature")
        # Reset bone roll
        ArmatureUtils.reset_bone_roll(context)
        # Remove bones
        bones_to_remove = {"Root"}
        ArmatureUtils.clean_bones(context, bones_to_remove)
        # Reparent bones
        bones_to_reparent = {"+PelvisTwist CF A01": "Hips"}
        ArmatureUtils.reparent_bones(context, bones_to_reparent, "Hips")

        # Position Hips
        ArmatureUtils.position_bone(
            context=context,
            target_bone="Hips",
            reference_points={
                "left": "Left Upper Leg",
                "right": "Right Upper Leg",
                "up": "Spine"
            },
            position_rules={
                "head": {
                    "horizontal": {"method": "between", "points": ["left", "right"], "ratio": 0.5},
                    "vertical": {"method": "between", "points": ["left", "up"], "ratio": 0.33},
                    "min_offset": {"axis": "z", "reference": "right", "value": 0.01}
                },
                "tail": {
                    "follow_head": ["x", "y"],
                    "vertical": {"method": "offset", "reference": "up", "value": 0.005},
                    "min_length": 0.05
                }
            }
        )
        # Position Spine
        ArmatureUtils.position_bone(
            context=context,
            target_bone="Spine",
            reference_points={
                "hips": "Hips"
            },
            position_rules={
                "head": {
                    "follow": {"reference": "hips", "point": "tail"}  # Align head with hips tail
                },
                "tail": {
                    "follow_head": ["x", "y"],  # Keep x and y same as head
                    "vertical": {"method": "offset", "reference": "head", "value": 0.075}  # Point straight up by 0.065
                }
            }
        )
        # Position Chest
        ArmatureUtils.position_bone(
            context=context,
            target_bone="Chest",
            reference_points={
                "spine": "Spine"
            },
            position_rules={
                "head": {
                    "follow": {"reference": "spine", "point": "tail"}  # Align head with spine tail
                },
                "tail": {
                    "follow_head": ["x", "y"],  # Keep x and y same as head
                    "vertical": {"method": "offset", "reference": "head", "value": 0.075}  # Point straight up by 0.065
                }
            }
        )
        # Position Upper Chest
        ArmatureUtils.position_bone(
            context=context,
            target_bone="Upper Chest",
            reference_points={
                "chest": "Chest"
            },
            position_rules={
                "head": {
                    "follow": {"reference": "chest", "point": "tail"}
                },
                "tail": {
                    "follow_head": ["x", "y"],
                    "vertical": {"method": "offset", "reference": "head", "value": 0.125}
                }
            }
        )

        # Reattach bones
        bone_pairs = {
            "Left Shoulder": "Left Upper Arm",
            "Right Shoulder": "Right Upper Arm",
            "Upper Chest": "Neck",
            "Left Upper Arm": "Left Lower Arm",
            "Right Upper Arm": "Right Lower Arm",
            "Left Lower Arm": "Left Hand",
            "Right Lower Arm": "Right Hand",
            "Right Upper Leg": "Right Lower Leg",
            "Left Upper Leg": "Left Lower Leg",
            "Right Lower Leg": "Right Foot",
            "Left Lower Leg": "Left Foot",
            "Right Foot": "Right Toes",
            "Left Foot": "Left Toes"
        }
        ArmatureUtils.attach_bones(context, bone_pairs)
        
        # Generate shape keys if enabled
        if settings.get('generate_shape_keys', False):
            shape_key_config = {
                "target_objects": {
                    "Face": ["Mouth_A01", "Mouth_Fury01", "Mouth_Open01"],
                    "Face_Eye": ["Eye_WinkA_L", "Eye_WinkA_R", "Eye_WinkB_L", "Eye_WinkB_R", "Eye_WinkC_L", "Eye_WinkC_R"]
                },
                "fallback_keys": [
                    {
                        "missing_key": "Mouth_Fury01",
                        "fallback_key": "Mouth_Open01",
                        "fallback_value": 0.5
                    }
                ],
                "generated_keys": {
                    "A": [
                        {"object": "Face", "source_key": "Mouth_A01", "value": 1.0}
                    ],
                    "O": [
                        {"object": "Face", "source_key": "Mouth_Line02", "value": 1},
                        {"object": "Face", "source_key": "Mouth_A01", "value": 0.5}
                    ],
                    "CH": [
                        {"object": "Face", "source_key": "Mouth_Open01", "value": 1.0}
                    ],
                    "vrc.v_aa": [
                        {"object": "Face", "source_key": "A", "value": 0.9998}
                    ],
                    "vrc.v_ch": [
                        {"object": "Face", "source_key": "CH", "value": 0.9996}
                    ],
                    "vrc.v_dd": [
                        {"object": "Face", "source_key": "A", "value": 0.3},
                        {"object": "Face", "source_key": "CH", "value": 0.7}
                    ],
                    "vrc.v_e": [
                        {"object": "Face", "source_key": "CH", "value": 0.7},
                        {"object": "Face", "source_key": "O", "value": 0.3}
                    ],
                    "vrc.v_ff": [
                        {"object": "Face", "source_key": "A", "value": 0.2},
                        {"object": "Face", "source_key": "CH", "value": 0.4}
                    ],
                    "vrc.v_ih": [
                        {"object": "Face", "source_key": "A", "value": 0.5},
                        {"object": "Face", "source_key": "CH", "value": 0.2}
                    ],
                    "vrc.v_kk": [
                        {"object": "Face", "source_key": "A", "value": 0.7},
                        {"object": "Face", "source_key": "CH", "value": 0.4}
                    ],
                    "vrc.v_nn": [
                        {"object": "Face", "source_key": "A", "value": 0.2},
                        {"object": "Face", "source_key": "CH", "value": 0.7}
                    ],
                    "vrc.v_oh": [
                        {"object": "Face", "source_key": "A", "value": 0.2},
                        {"object": "Face", "source_key": "O", "value": 0.8}
                    ],
                    "vrc.v_ou": [
                        {"object": "Face", "source_key": "O", "value": 0.9994}
                    ],
                    "vrc.v_pp": [
                        {"object": "Face", "source_key": "A", "value": 0.0004},
                        {"object": "Face", "source_key": "O", "value": 0.0004}
                    ],
                    "vrc.v_rr": [
                        {"object": "Face", "source_key": "CH", "value": 0.5},
                        {"object": "Face", "source_key": "O", "value": 0.3}
                    ],
                    "vrc.v_sil": [
                        {"object": "Face", "source_key": "A", "value": 0.0002},
                        {"object": "Face", "source_key": "CH", "value": 0.0002}
                    ],
                    "vrc.v_ss": [
                        {"object": "Face", "source_key": "CH", "value": 0.8}
                    ],
                    "vrc.v_th": [
                        {"object": "Face", "source_key": "A", "value": 0.4},
                        {"object": "Face", "source_key": "O", "value": 0.15}
                    ],
                    "Blink": [
                        {"object": "Face_Eye", "source_key": "Eye_WinkB_L", "value": 1.0},
                        {"object": "Face_Eye", "source_key": "Eye_WinkB_R", "value": 1.0}
                    ],
                    "Happy Blink": [
                        {"object": "Face_Eye", "source_key": "Eye_WinkA_L", "value": 1.0},
                        {"object": "Face_Eye", "source_key": "Eye_WinkA_R", "value": 1.0}
                    ],
                    "Pensive Blink": [
                        {"object": "Face_Eye", "source_key": "Eye_WinkC_L", "value": 1.0},
                        {"object": "Face_Eye", "source_key": "Eye_WinkC_R", "value": 1.0}
                    ]
                }
            }
            ModelUtils.generate_shape_keys(context, shape_key_config)
        
        # Generate MMD shape keys if enabled
        if settings.get('generate_shape_keys_mmd', False):
            shape_key_configMMD = {
                "target_objects": {
                    "Face": ["Mouth_A01", "Mouth_Fury01", "Mouth_Open01"],
                    "Face_Eye": ["Eye_WinkA_L", "Eye_WinkA_R", "Eye_WinkB_L", "Eye_WinkB_R", "Eye_WinkC_L", "Eye_WinkC_R"]
                },
                "fallback_keys": [
                    {
                        "missing_key": "Mouth_Fury01",
                        "fallback_key": "Mouth_Open01",
                        "fallback_value": 0.5
                    }
                ],
                "generated_keys": {
                    "真面目": [
                        {"object": "Face", "source_key": "Brow_Angry_L", "value": 0.5},
                        {"object": "Face", "source_key": "Brow_Angry_R", "value": 0.5}
                    ],
                    "困る": [
                        {"object": "Face", "source_key": "Brow_Trouble_L", "value": 1},
                        {"object": "Face", "source_key": "Brow_Trouble_R", "value": 1}
                    ],
                    "にこり": [
                        {"object": "Face", "source_key": "Brow_Smily_L", "value": 1.0},
                        {"object": "Face", "source_key": "Brow_Smily_R", "value": 1.0}
                    ],
                    "怒り": [
                        {"object": "Face", "source_key": "Brow_Angry_L", "value": 1},
                        {"object": "Face", "source_key": "Brow_Angry_R", "value": 1}
                    ],
                    "上": [
                        {"object": "Face", "source_key": "Brow_Up_L", "value": 1},
                        {"object": "Face", "source_key": "Brow_Up_R", "value": 1}
                    ],
                    "下": [
                        {"object": "Face", "source_key": "Brow_Down_L", "value": 1},
                        {"object": "Face", "source_key": "Brow_Down_R", "value": 1}
                    ],
                    "まばたき": [
                        {"object": "Face_Eye", "source_key": "Eye_WinkB_L", "value": 1.0},
                        {"object": "Face_Eye", "source_key": "Eye_WinkB_R", "value": 1.0}
                    ],
                    "ウィンク２": [
                        {"object": "Face_Eye", "source_key": "Eye_WinkB_L", "value": 1.0},
                    ],
                    "ｳｨﾝｸ２右": [
                        {"object": "Face_Eye", "source_key": "Eye_WinkB_R", "value": 1.0},
                    ],
                    "笑い": [
                        {"object": "Face_Eye", "source_key": "Eye_WinkA_L", "value": 1.0},
                        {"object": "Face_Eye", "source_key": "Eye_WinkA_R", "value": 1.0}
                    ],
                     "ウィンク": [
                        {"object": "Face_Eye", "source_key": "Eye_WinkA_L", "value": 1.0},
                    ],
                    "ウィンク右": [
                        {"object": "Face_Eye", "source_key": "Eye_WinkA_R", "value": 1.0},
                    ],
                    "なごみ": [
                        {"object": "Face_Eye", "source_key": "Eye_WinkC_L", "value": 1.0},
                        {"object": "Face_Eye", "source_key": "Eye_WinkC_R", "value": 1.0}
                    ],
                    "びっくり": [
                        {"object": "Face_Eye", "source_key": "Eye_Ha", "value": 1.0},
                    ],
                    "じと目": [
                        {"object": "Face_Eye", "source_key": "Eye_Jito", "value": 1.0},
                    ],
                    "細目": [
                        {"object": "Face_Eye", "source_key": "Eye_Lowereyelid", "value": 1.0},
                    ],
                    "あ": [
                        {"object": "Face", "source_key": "Mouth_A01", "value": 1.0}
                    ],
                    "い": [
                        {"object": "Face_Eye", "source_key": "Mouth_Angry02", "value": 0.5},
                    ],
                    "う": [
                        {"object": "Face_Eye", "source_key": "Mouth_Line02", "value": 1.0},
                        {"object": "Face_Eye", "source_key": "Mouth_Open01", "value": 1.0},
                    ],
                    "え": [
                        {"object": "Face_Eye", "source_key": "Mouth_A01", "value": 0.5},
                    ],
                    "お": [
                        {"object": "Face", "source_key": "Mouth_Line02", "value": 1},
                        {"object": "Face", "source_key": "Mouth_A01", "value": 0.5}
                    ],
                    "▲": [
                        {"object": "Face_Eye", "source_key": "Mouth_Line02", "value": 1.0},
                        {"object": "Face_Eye", "source_key": "Mouth_Open01", "value": 0.25},
                    ],
                    "∧": [
                        {"object": "Face_Eye", "source_key": "Mouth_Line02", "value": 1.0},
                    ],
                    "ω": [
                        {"object": "Face_Eye", "source_key": "Mouth_Neko01", "value": 1.0},
                    ],
                    "にやり": [
                        {"object": "Face_Eye", "source_key": "Mouth_Smile01", "value": 1.0},
                    ],
                    "はんっ！": [
                        {"object": "Face_Eye", "source_key": " ", "value": 1.0},
                    ],
                    "ぎゃーす": [
                        {"object": "Face_Eye", "source_key": "Mouth_Angry01", "value": 1.0},
                    ],
                    "がーん": [
                        {"object": "Face_Eye", "source_key": " ", "value": 1.0},
                    ],
                    "ギギギ": [
                        {"object": "Face_Eye", "source_key": "Mouth_Angry02", "value": 1.0},
                    ],
                    "ぺろっ": [
                        {"object": "Face_Eye", "source_key": "Mouth_Pero02", "value": 1.0},
                    ]
                }
            }
            ModelUtils.generate_shape_keys(context, shape_key_configMMD)

        # Convert Eyes
        bones_to_duplicate = {
            "+EyeBone L A01": "Left Eye",
            "+EyeBone R A01": "Right Eye"
        }

        weight_source_bones = {
            "Left Eye": "+EyeBone L A02",
            "Right Eye": "+EyeBone R A02"
        }
        # Check if Pupil mesh exists, otherwise use Body
        target_mesh = "Pupil" if bpy.data.objects.get("Pupil") else "Body"
        ArmatureUtils.duplicate_bones_with_weights(context, bones_to_duplicate, weight_source_bones, target_mesh)
        
        for eye_bone in ["Left Eye", "Right Eye"]:


            ArmatureUtils.position_bone(
                context=context,
                target_bone=eye_bone,
                reference_points={
                    "self": eye_bone  # Use the bone itself as reference
                },
                position_rules={
                    "tail": {
                        "follow_head": ["x", "y"],  # Keep x and y same as head (straight up)
                        "vertical": {"method": "offset", "reference": "head", "value": 0.05}  # Small fixed length up
                    }
                }
            )

        # Merge by distance
        if settings.get('generate_shape_keys', False):
            ModelUtils.merge_meshes_by_distance(context, "Face", ["Face_Eye", "Brow"], "A")
        else:
            ModelUtils.merge_meshes_by_distance(context, "Face", ["Face_Eye", "Brow"], "Mouth_A01")  

        # Modify Bangs Materials
        ModelUtils.assign_modified_material(context, search_keywords=["Bang", "Bangs"], new_suffix="Bangs")
        # Reorder UV Maps
        ModelUtils.reorder_uv_maps(context)
        # Move Armature to Ground
        ArmatureUtils.move_armature_to_ground(context)
        # Merge All Meshes
        if settings.get('merge_all_meshes', False):
            ModelUtils.merge_all_meshes(context)
        # Fix material alpha settings
        SceneUtils.fix_materials(context)
        # Get import directory from armature if available
        SceneUtils.fix_material_textures(context)
        # Duplicate material json
        SceneUtils.duplicate_material_json(context, search_keywords="Hair", new_keywords="Bangs")
        # Set root name before cleanup
        SceneUtils.set_root_name(context)
        # Clean up selection state last
        SceneUtils.cleanup_selection(context)
        return True

    @staticmethod
    def convert_genshin_weapons(context, model_info: ModelInfo, settings: dict) -> bool:
        """Convert Genshin Impact weapons"""
        print(f"Converting Genshin Impact weapon: {model_info.clean_name}")

        # Store model info on armature or mesh
        obj = context.active_object
        if obj:
            if obj.type == 'ARMATURE' or obj.type == 'MESH':
                obj["hoyo2vrc_model_name"] = model_info.clean_name
                obj["hoyo2vrc_game"] = model_info.game
                if model_info.body_type:
                    obj["hoyo2vrc_body_type"] = model_info.body_type
                obj["hoyo2vrc_converted"] = True
        
        # Remove empties
        SceneUtils.remove_empties(context)
        # Clear rotation
        ArmatureUtils.clear_rotation(context)
        # Clean Meshes
        ModelUtils.clean_meshes(context)
        # Set Wireframe Display
        SceneUtils.set_wireframe_display(context)
        # Set Material View
        SceneUtils.set_material_view(context, "MATERIAL")
        # Reset bone roll
        ArmatureUtils.reset_bone_roll(context)
        # Reorder UV Maps
        ModelUtils.reorder_uv_maps(context)
        # Merge All Meshes
        if settings.get('merge_all_meshes', False):
            ModelUtils.merge_all_meshes(context)
        # Fix material alpha settings
        SceneUtils.fix_materials(context)
        # Get import directory from armature if available
        SceneUtils.fix_material_textures(context)
        # Set root name before cleanup
        SceneUtils.set_root_name(context)
        # Clean up selection state last
        SceneUtils.cleanup_selection(context)

        return True
    
    @staticmethod
    def convert_starrail(context, model_info: ModelInfo, settings: dict) -> bool:
        """Convert Star Rail models"""
        print(f"Converting Star Rail model: {model_info.clean_name}")
        
        # Store model info on armature
        armature = context.active_object
        if armature and armature.type == 'ARMATURE':
            armature["hoyo2vrc_model_name"] = model_info.clean_name
            armature["hoyo2vrc_game"] = model_info.game
            if model_info.body_type:
                armature["hoyo2vrc_body_type"] = model_info.body_type
            armature["hoyo2vrc_converted"] = True
            
        SceneUtils.remove_empties(context)
        # Clear rotation
        ArmatureUtils.clear_rotation(context)
        # Clean Meshes
        ModelUtils.clean_meshes(context)
        # Set Wireframe Display
        SceneUtils.set_wireframe_display(context)
        # Set Material View
        SceneUtils.set_material_view(context, "MATERIAL")
        # Convert Animations to Shapekey
        ModelUtils.face_rig_to_shapekey(context, mesh_name="Face") 
        # Generate shape keys if enabled
        if settings.get('generate_shape_keys', False):
            shape_key_config = {
                "target_objects": {
                    "Face": ["Mouth_00_A", "Mouth_00_O", "Mouth_00_Delta02"],
              },
                "fallback_keys": [
                    {
                        "missing_key": "Mouth_00_A",
                        "fallback_key": "Mouth_01_A",
                        "fallback_value": 0.5
                    },
                    {
                        "missing_key": "Mouth_00_O",
                        "fallback_key": "Mouth_01_O",
                        "fallback_value": 0.5
                    },
                    {
                        "missing_key": "Mouth_00_Delta02",
                        "fallback_key": "Mouth_01_Delta02",
                        "fallback_value": 0.5
                    }
                ],
                "generated_keys": {
                    "A": [
                        {"object": "Face", "source_key": "Mouth_00_A", "value": 1.0}
                    ],
                    "O": [
                        {"object": "Face", "source_key": "Mouth_00_O", "value": 1},
                    ],
                    "CH": [
                        {"object": "Face", "source_key": "Mouth_00_Delta02", "value": 1.0}
                    ],
                    "vrc.v_aa": [
                        {"object": "Face", "source_key": "A", "value": 0.9998}
                    ],
                    "vrc.v_ch": [
                        {"object": "Face", "source_key": "CH", "value": 0.9996}
                    ],
                    "vrc.v_dd": [
                        {"object": "Face", "source_key": "A", "value": 0.3},
                        {"object": "Face", "source_key": "CH", "value": 0.7}
                    ],
                    "vrc.v_e": [
                        {"object": "Face", "source_key": "CH", "value": 0.7},
                        {"object": "Face", "source_key": "O", "value": 0.3}
                    ],
                    "vrc.v_ff": [
                        {"object": "Face", "source_key": "A", "value": 0.2},
                        {"object": "Face", "source_key": "CH", "value": 0.4}
                    ],
                    "vrc.v_ih": [
                        {"object": "Face", "source_key": "A", "value": 0.5},
                        {"object": "Face", "source_key": "CH", "value": 0.2}
                    ],
                    "vrc.v_kk": [
                        {"object": "Face", "source_key": "A", "value": 0.7},
                        {"object": "Face", "source_key": "CH", "value": 0.4}
                    ],
                    "vrc.v_nn": [
                        {"object": "Face", "source_key": "A", "value": 0.2},
                        {"object": "Face", "source_key": "CH", "value": 0.7}
                    ],
                    "vrc.v_oh": [
                        {"object": "Face", "source_key": "A", "value": 0.2},
                        {"object": "Face", "source_key": "O", "value": 0.8}
                    ],
                    "vrc.v_ou": [
                        {"object": "Face", "source_key": "O", "value": 0.9994}
                    ],
                    "vrc.v_pp": [
                        {"object": "Face", "source_key": "A", "value": 0.0004},
                        {"object": "Face", "source_key": "O", "value": 0.0004}
                    ],
                    "vrc.v_rr": [
                        {"object": "Face", "source_key": "CH", "value": 0.5},
                        {"object": "Face", "source_key": "O", "value": 0.3}
                    ],
                    "vrc.v_sil": [
                        {"object": "Face", "source_key": "A", "value": 0.0002},
                        {"object": "Face", "source_key": "CH", "value": 0.0002}
                    ],
                    "vrc.v_ss": [
                        {"object": "Face", "source_key": "CH", "value": 0.8}
                    ],
                    "vrc.v_th": [
                        {"object": "Face", "source_key": "A", "value": 0.4},
                        {"object": "Face", "source_key": "O", "value": 0.15}
                    ],
                    "Blink": [
                        {"object": "Face_Eye", "source_key": "00_Close01_Eye", "value": 1.0},
                    ],
                    "Happy Blink": [
                        {"object": "Face_Eye", "source_key": "00_Close02_Eye", "value": 1.0},
                    ],
                    "Pensive Blink": [
                        {"object": "Face_Eye", "source_key": "00_Close03_Eye", "value": 1.0},
                    ]
                }
            }
            ModelUtils.generate_shape_keys(context, shape_key_config)
        
        # Generate MMD shape keys if enabled
        if settings.get('generate_shape_keys_mmd', False):
            shape_key_configMMD = {
                "target_objects": {
                    "Face": ["Mouth_00_A", "Mouth_00_O", "Mouth_00_Delta02"],
                },
                "fallback_keys": [
                    {
                        "missing_key": "Mouth_00_A",
                        "fallback_key": "Mouth_01_A",
                        "fallback_value": 0.5
                    },
                    {
                        "missing_key": "Mouth_00_O",
                        "fallback_key": "Mouth_01_O",
                        "fallback_value": 0.5
                    },
                    {
                        "missing_key": "Mouth_00_Delta02",
                        "fallback_key": "Mouth_01_Delta02",
                        "fallback_value": 0.5
                    }
                ],
                "generated_keys": {
                    "真面目": [
                        {"object": "Face", "source_key": "Brow_00_Angry", "value": 0.5},
                    ],
                    "困る": [
                        {"object": "Face", "source_key": "Brow_00_Trouble", "value": 1},
                    ],
                    "にこり": [
                        {"object": "Face", "source_key": "Brow_00_Gentle", "value": 1.0},
                    ],
                    "怒り": [
                        {"object": "Face", "source_key": "Brow_00_Angry", "value": 1},
                    ],
                    "上": [
                        {"object": "Face", "source_key": "Brow_00_Up", "value": 1},
                    ],
                    "下": [
                        {"object": "Face", "source_key": "Brow_00_Down", "value": 1},
                    ],
                    "まばたき": [
                        {"object": "Face", "source_key": "00_Close01_Eye", "value": 1.0},
                    ],
                    "ウィンク２": [
                        {"object": "Face", "source_key": " ", "value": 1.0},
                    ],
                    "ｳｨﾝｸ２右": [
                        {"object": "Face", "source_key": " ", "value": 1.0},
                    ],
                    "笑い": [
                        {"object": "Face", "source_key": "00_Close02_Eye", "value": 1.0},
                    ],
                     "ウィンク": [
                        {"object": "Face", "source_key": " ", "value": 1.0},
                    ],
                    "ウィンク右": [
                        {"object": "Face", "source_key": " ", "value": 1.0},
                    ],
                    "なごみ": [
                        {"object": "Face", "source_key": "00_Close01_Eye", "value": 1.0},
                        {"object": "Face", "source_key": "00_Close01_Eye", "value": 1.0}
                    ],
                    "びっくり": [
                        {"object": "Face", "source_key": "Eye_00_Surprise01", "value": 1.0},
                    ],
                    "じと目": [
                        {"object": "Face", "source_key": "Eye_00_Doubt01", "value": 1.0},
                    ],
                    "細目": [
                        {"object": "Face", "source_key": " ", "value": 1.0},
                    ],
                    "あ": [
                        {"object": "Face", "source_key": "Mouth_00_A", "value": 1.0}
                    ],
                    "い": [
                        {"object": "Face", "source_key": "Mouth_00_I", "value": 0.5},
                    ],
                    "う": [
                        {"object": "Face", "source_key": "Mouth_00_U", "value": 1.0},
                    ],
                    "え": [
                        {"object": "Face", "source_key": "Mouth_00_E", "value": 0.5},
                    ],
                    "お": [
                        {"object": "Face", "source_key": "Mouth_00_O", "value": 1},
                    ],
                    "▲": [
                        {"object": "Face", "source_key": "Mouth_00_Narrow", "value": 1.0},
                        {"object": "Face", "source_key": "Mouth_00_O", "value": 0.5},
                    ],
                    "∧": [
                        {"object": "Face", "source_key": "Mouth_00_Narrow", "value": 1.0},
                    ],
                    "ω": [
                        {"object": "Face", "source_key": "Mouth_01_Angry01", "value": -1.0},
                    ],
                    "にやり": [
                        {"object": "Face", "source_key": "Mouth_00_Smile01", "value": 1.0},
                    ],
                    "はんっ！": [
                        {"object": "Face", "source_key": " ", "value": 1.0},
                    ],
                    "ぎゃーす": [
                        {"object": "Face", "source_key": " ", "value": 1.0},
                    ],
                    "がーん": [
                        {"object": "Face", "source_key": " ", "value": 1.0},
                    ],
                    "ギギギ": [
                        {"object": "Face", "source_key": " ", "value": 1.0},
                    ],
                    "ぺろっ": [
                        {"object": "Face", "source_key": " ", "value": 1.0},
                    ]
                }
            }
            ModelUtils.generate_shape_keys(context, shape_key_configMMD)

        # Clear Animations
        ModelUtils.clear_animations(context)
        # Rename Bones
        ArmatureUtils.rename_bones(context)
        # Symmetrize Bones
        ArmatureUtils.symmetrize_bones(context, side="Right")
         # Rename Armature Data
        ArmatureUtils.rename_armature_data(context, "Armature")
        # Reset bone roll
        ArmatureUtils.reset_bone_roll(context)
        # Clean Bones
        bones_to_remove = {"Main", "joint_skin_GRP"}
        ArmatureUtils.clean_bones(context, bones_to_remove)
         # Position Hips
        ArmatureUtils.position_bone(
            context=context,
            target_bone="Hips",
            reference_points={
                "left": "Left Upper Leg",
                "right": "Right Upper Leg",
                "up": "Spine"
            },
            position_rules={
                "head": {
                    "horizontal": {"method": "between", "points": ["left", "right"], "ratio": 0.5},
                    "vertical": {"method": "between", "points": ["left", "up"], "ratio": 0.33},
                    "min_offset": {"axis": "z", "reference": "right", "value": 0.01}
                },
                "tail": {
                    "follow_head": ["x", "y"],
                    "vertical": {"method": "offset", "reference": "up", "value": 0.005},
                    "min_length": 0.05
                }
            }
        )
        # Position Spine
        ArmatureUtils.position_bone(
            context=context,
            target_bone="Spine",
            reference_points={
                "hips": "Hips"
            },
            position_rules={
                "head": {
                    "follow": {"reference": "hips", "point": "tail"}  # Align head with hips tail
                },
                "tail": {
                    "follow_head": ["x", "y"],  # Keep x and y same as head
                    "vertical": {"method": "offset", "reference": "head", "value": 0.075}  # Point straight up by 0.065
                }
            }
        )
        # Position Chest
        ArmatureUtils.position_bone(
            context=context,
            target_bone="Chest",
            reference_points={
                "spine": "Spine"
            },
            position_rules={
                "head": {
                    "follow": {"reference": "spine", "point": "tail"}  # Align head with spine tail
                },
                "tail": {
                    "follow_head": ["x", "y"],  # Keep x and y same as head
                    "vertical": {"method": "offset", "reference": "head", "value": 0.075}  # Point straight up by 0.065
                }
            }
        )
        # Position Upper Chest
        ArmatureUtils.position_bone(
            context=context,
            target_bone="Upper Chest",
            reference_points={
                "chest": "Chest"
            },
            position_rules={
                "head": {
                    "follow": {"reference": "chest", "point": "tail"}
                },
                "tail": {
                    "follow_head": ["x", "y"],
                    "vertical": {"method": "offset", "reference": "head", "value": 0.125}
                }
            }
        )

        # Reattach bones
        bone_pairs = {
            "Neck": "Head",
            "Left Shoulder": "Left Upper Arm",
            "Right Shoulder": "Right Upper Arm",
            "Upper Chest": "Neck",
            "Left Upper Arm": "Left Lower Arm",
            "Right Upper Arm": "Right Lower Arm",
            "Left Lower Arm": "Left Hand",
            "Right Lower Arm": "Right Hand",
            "Right Upper Leg": "Right Lower Leg",
            "Left Upper Leg": "Left Lower Leg",
            "Right Lower Leg": "Right Foot",
            "Left Lower Leg": "Left Foot",
            "Right Foot": "Right Toes",
            "Left Foot": "Left Toes"
        }
        ArmatureUtils.attach_bones(context, bone_pairs)

        # Convert Eyes
        bones_to_duplicate = {
            "eye_L": "Left Eye",
            "eye_R": "Right Eye"
        }
        weight_source_bones = {
            "Left Eye": ["eyeEnd_L", "eyeEnd_01_L"],
            "Right Eye": ["eyeEnd_R", "eyeEnd_01_R"]
        }
        ArmatureUtils.duplicate_bones_with_weights(context, bones_to_duplicate, weight_source_bones, "Face")

        for eye_bone in ["Left Eye", "Right Eye"]:

            ArmatureUtils.position_bone(
                context=context,
                target_bone=eye_bone,
                reference_points={
                    "self": eye_bone  # Use the bone itself as reference
                },
                position_rules={
                    "tail": {
                        "follow_head": ["x", "y"],  # Keep x and y same as head (straight up)
                        "vertical": {"method": "offset", "reference": "head", "value": 0.05}  # Small fixed length up
                    }
                }
            )

        bones_to_reparent = {"Left Eye": "Head", "Right Eye": "Head"}
        ArmatureUtils.reparent_bones(context, bones_to_reparent, "Head")

         # Reorder UV Maps
        ModelUtils.reorder_uv_maps(context)
        # Apply Face Mask
        ModelUtils.merge_and_weight_meshes(context, source_mesh="Face_Mask", target_mesh="Face", reweight=True, bone_name="Head", weight=1.0, vertex_group="Head")
        # Separate Bangs
        ArmatureUtils.separate_bangs_by_armature(context, hair_obj="Hair", armature_obj=armature, bone_keywords=["Hair"], y_boundary=-0.04)
        # Fix material alpha settings
        SceneUtils.fix_materials(context)
        # Get import directory from armature if available
        SceneUtils.fix_material_textures(context)
        # Duplicate material json
        SceneUtils.duplicate_material_json(context, search_keywords="Hair", new_keywords="Bangs")
        # Move Armature to Ground
        ArmatureUtils.move_armature_to_ground(context)
        # Merge All Meshes
        if settings.get('merge_all_meshes', False):
            ModelUtils.merge_all_meshes(context)
        # Set root name before cleanup
        SceneUtils.set_root_name(context)
        # Clean up selection state last
        SceneUtils.cleanup_selection(context)
        return True
        
    @staticmethod
    def convert_hi3(context, model_info: ModelInfo, settings: dict) -> bool:
        """Convert Honkai Impact 3rd models"""
        print(f"Converting HI3 model: {model_info.clean_name}")
        
        # Check for legacy model
        if model_info.is_legacy:
            print("Legacy HI3 model detected (Eye_L, Eye_R, or Mouth mesh present). These models are not supported.")
            return False
        
        # Store model info on armature
        armature = context.active_object
        if armature and armature.type == 'ARMATURE':
            armature["hoyo2vrc_model_name"] = model_info.clean_name
            armature["hoyo2vrc_game"] = model_info.game
            if model_info.body_type:
                armature["hoyo2vrc_body_type"] = model_info.body_type
            armature["hoyo2vrc_converted"] = True
            
        SceneUtils.remove_empties(context)
        # Clear rotation
        ArmatureUtils.clear_rotation(context)
        # Clean Meshes
        ModelUtils.clean_meshes(context)
        # Set Wireframe Display
        SceneUtils.set_wireframe_display(context)
        # Set Material View
        SceneUtils.set_material_view(context, "MATERIAL")
        # Rename Bones
        ArmatureUtils.rename_bones(context)
        # Rename Armature Data
        ArmatureUtils.rename_armature_data(context, "Armature")
        # Reset bone roll
        ArmatureUtils.reset_bone_roll(context)
        # Remove bones
        bones_to_remove = {"Root"}
        ArmatureUtils.clean_bones(context, bones_to_remove)
        # Reparent bones
        bones_to_reparent = {"Bone_C1_Bip_Root": "Hips", "Bone_PelvisTwist": "Hips", "Bone_Pelvis_Twist": "Hips"}
        ArmatureUtils.reparent_bones(context, bones_to_reparent, "Hips")

        # Position Hips
        ArmatureUtils.position_bone(
            context=context,
            target_bone="Hips",
            reference_points={
                "left": "Left Upper Leg",
                "right": "Right Upper Leg",
                "up": "Spine"
            },
            position_rules={
                "head": {
                    "horizontal": {"method": "between", "points": ["left", "right"], "ratio": 0.5},
                    "vertical": {"method": "between", "points": ["left", "up"], "ratio": 0.33},
                    "min_offset": {"axis": "z", "reference": "right", "value": 0.01}
                },
                "tail": {
                    "follow_head": ["x", "y"],
                    "vertical": {"method": "offset", "reference": "up", "value": 0.005},
                    "min_length": 0.05
                }
            }
        )
        # Position Spine
        ArmatureUtils.position_bone(
            context=context,
            target_bone="Spine",
            reference_points={
                "hips": "Hips"
            },
            position_rules={
                "head": {
                    "follow": {"reference": "hips", "point": "tail"}  # Align head with hips tail
                },
                "tail": {
                    "follow_head": ["x", "y"],  # Keep x and y same as head
                    "vertical": {"method": "offset", "reference": "head", "value": 0.075}  # Point straight up by 0.065
                }
            }
        )
        # Position Chest
        ArmatureUtils.position_bone(
            context=context,
            target_bone="Chest",
            reference_points={
                "spine": "Spine"
            },
            position_rules={
                "head": {
                    "follow": {"reference": "spine", "point": "tail"}  # Align head with spine tail
                },
                "tail": {
                    "follow_head": ["x", "y"],  # Keep x and y same as head
                    "vertical": {"method": "offset", "reference": "head", "value": 0.075}  # Point straight up by 0.065
                }
            }
        )
        # Position Upper Chest
        ArmatureUtils.position_bone(
            context=context,
            target_bone="Upper Chest",
            reference_points={
                "chest": "Chest"
            },
            position_rules={
                "head": {
                    "follow": {"reference": "chest", "point": "tail"}
                },
                "tail": {
                    "follow_head": ["x", "y"],
                    "vertical": {"method": "offset", "reference": "head", "value": 0.125}
                }
            }
        )

        # Reattach bones
        bone_pairs = {
            "Left Shoulder": "Left Upper Arm",
            "Right Shoulder": "Right Upper Arm",
            "Upper Chest": "Neck",
            "Left Upper Arm": "Left Lower Arm",
            "Right Upper Arm": "Right Lower Arm",
            "Left Lower Arm": "Left Hand",
            "Right Lower Arm": "Right Hand",
            "Right Upper Leg": "Right Lower Leg",
            "Left Upper Leg": "Left Lower Leg",
            "Right Lower Leg": "Right Foot",
            "Left Lower Leg": "Left Foot",
            "Right Foot": "Right Toes",
            "Left Foot": "Left Toes"
        }
        ArmatureUtils.attach_bones(context, bone_pairs)
        
        # Generate shape keys if enabled
        if settings.get('generate_shape_keys', False):
            shape_key_config = {
                "target_objects": {
                    "Face": ["Mouth_A01", "Mouth_O01", "Mouth_Angry02"],
                    "EyeShape": ["Eye_Wink02_L", "Eye_Wink02_R", "Eye_Wink01_L", "Eye_Wink01_R"]
                },
                "fallback_keys": [
                    {
                        "missing_key": "Mouth_Angry02",
                        "fallback_key": "Mouth_N01",
                        "fallback_value": 1
                    }
                ],
                "generated_keys": {
                    "A": [
                        {"object": "Face", "source_key": "Mouth_A01", "value": 1.0}
                    ],
                    "O": [
                        {"object": "Face", "source_key": "Mouth_O01", "value": 1.0},
                    ],

                    "CH": [
                        {"object": "Face", "source_key": "Mouth_Angry02", "value": 1.0},
                    ],

                    "vrc.v_aa": [
                        {"object": "Face", "source_key": "A", "value": 0.9998}
                    ],
                    "vrc.v_ch": [
                        {"object": "Face", "source_key": "CH", "value": 0.9996}
                    ],
                    "vrc.v_dd": [
                        {"object": "Face", "source_key": "A", "value": 0.3},
                        {"object": "Face", "source_key": "CH", "value": 0.7}
                    ],
                    "vrc.v_e": [
                        {"object": "Face", "source_key": "CH", "value": 0.7},
                        {"object": "Face", "source_key": "O", "value": 0.3}
                    ],
                    "vrc.v_ff": [
                        {"object": "Face", "source_key": "A", "value": 0.2},
                        {"object": "Face", "source_key": "CH", "value": 0.4}
                    ],
                    "vrc.v_ih": [
                        {"object": "Face", "source_key": "A", "value": 0.5},
                        {"object": "Face", "source_key": "CH", "value": 0.2}
                    ],
                    "vrc.v_kk": [
                        {"object": "Face", "source_key": "A", "value": 0.7},
                        {"object": "Face", "source_key": "CH", "value": 0.4}
                    ],
                    "vrc.v_nn": [
                        {"object": "Face", "source_key": "A", "value": 0.2},
                        {"object": "Face", "source_key": "CH", "value": 0.7}
                    ],
                    "vrc.v_oh": [
                        {"object": "Face", "source_key": "A", "value": 0.2},
                        {"object": "Face", "source_key": "O", "value": 0.8}
                    ],
                    "vrc.v_ou": [
                        {"object": "Face", "source_key": "O", "value": 0.9994}
                    ],
                    "vrc.v_pp": [
                        {"object": "Face", "source_key": "A", "value": 0.0004},
                        {"object": "Face", "source_key": "O", "value": 0.0004}
                    ],
                    "vrc.v_rr": [
                        {"object": "Face", "source_key": "CH", "value": 0.5},
                        {"object": "Face", "source_key": "O", "value": 0.3}
                    ],
                    "vrc.v_sil": [
                        {"object": "Face", "source_key": "A", "value": 0.0002},
                        {"object": "Face", "source_key": "CH", "value": 0.0002}
                    ],
                    "vrc.v_ss": [
                        {"object": "Face", "source_key": "CH", "value": 0.8}
                    ],
                    "vrc.v_th": [
                        {"object": "Face", "source_key": "A", "value": 0.4},
                        {"object": "Face", "source_key": "O", "value": 0.15}
                    ],
                    "Blink": [
                        {"object": "EyeShape", "source_key": "Eye_Wink02_L", "value": 1.0},
                        {"object": "EyeShape", "source_key": "Eye_Wink02_R", "value": 1.0}
                    ],
                    "Happy Blink": [
                        {"object": "EyeShape", "source_key": "Eye_Wink01_L", "value": 1.0},
                        {"object": "EyeShape", "source_key": "Eye_Wink01_R", "value": 1.0}
                    ]
                }
            }
            ModelUtils.generate_shape_keys(context, shape_key_config)

        # Generate MMD shape keys if enabled
        if settings.get('generate_shape_keys_mmd', False):
            shape_key_configMMD = {
                "target_objects": {
                    "Face": ["Mouth_00_A", "Mouth_00_O", "Mouth_00_Delta02"],
                },
                "fallback_keys": [
                    {
                        "missing_key": "Mouth_00_A",
                        "fallback_key": "Mouth_01_A",
                        "fallback_value": 0.5
                    },
                    {
                        "missing_key": "Mouth_00_O",
                        "fallback_key": "Mouth_01_O",
                        "fallback_value": 0.5
                    },
                    {
                        "missing_key": "Mouth_00_Delta02",
                        "fallback_key": "Mouth_01_Delta02",
                        "fallback_value": 0.5
                    }
                ],
                "generated_keys": {
                    "真面目": [
                        {"object": "Face", "source_key": "Eyebrow_Serious", "value": 1.0},
                    ],
                    "困る": [
                        {"object": "Face", "source_key": "Eyebrow_Trouble", "value": 1},
                    ],
                    "にこり": [
                        {"object": "Face", "source_key": "Eyebrow_Smily", "value": 1.0},
                    ],
                    "怒り": [
                        {"object": "Face", "source_key": "Eyebrow_Angry", "value": 1},
                    ],
                    "上": [
                        {"object": "Face", "source_key": "Eyebrow_Up", "value": 1},
                    ],
                    "下": [
                        {"object": "Face", "source_key": "Eyebrow_Down", "value": 1},
                    ],
                    "まばたき": [
                         {"object": "Face", "source_key": "Eye_Wink02_L", "value": 1.0},
                         {"object": "Face", "source_key": "Eye_Wink02_R", "value": 1.0}
                    ],
                    "ウィンク２": [
                        {"object": "Face", "source_key": "Eye_Wink02_L", "value": 1.0},
                    ],
                    "ｳｨﾝｸ２右": [
                        {"object": "Face", "source_key": "Eye_Wink02_R", "value": 1.0},
                    ],
                    "笑い": [
                        {"object": "Face", "source_key": "Eye_Wink01_L", "value": 1.0},
                        {"object": "Face", "source_key": "Eye_Wink01_R", "value": 1.0}
                    ],
                     "ウィンク": [
                        {"object": "Face", "source_key": "Eye_Wink01_L", "value": 1.0},
                    ],
                    "ウィンク右": [
                        {"object": "Face", "source_key": "Eye_Wink01_R", "value": 1.0},
                    ],
                    "なごみ": [
                        {"object": "Face", "source_key": "Eye_Contempt", "value": 1.0},
                    ],
                    "びっくり": [
                        {"object": "Face", "source_key": "Eye_Surprised03", "value": 1.0},
                    ],
                    "じと目": [
                        {"object": "Face", "source_key": "Eye_Hostitlity", "value": 1.0},
                    ],
                    "細目": [
                        {"object": "Face", "source_key": "Eye_Half01", "value": 1.0},
                    ],
                    "あ": [
                        {"object": "Face", "source_key": "Mouth_A01", "value": 1.0}
                    ],
                    "い": [
                        {"object": "Face", "source_key": "Mouth_I01", "value": 0.5},
                    ],
                    "う": [
                        {"object": "Face", "source_key": "Mouth_U01", "value": 1.0},
                    ],
                    "え": [
                        {"object": "Face", "source_key": "Mouth_E01", "value": 0.5},
                    ],
                    "お": [
                        {"object": "Face", "source_key": "Mouth_O01", "value": 1},
                    ],
                    "▲": [
                        {"object": "Face", "source_key": "Mouth_N01", "value": 1.0},
                        {"object": "Face", "source_key": "Mouth_Line02", "value": 0.5},
                    ],
                    "∧": [
                        {"object": "Face", "source_key": "Mouth_Line02", "value": 1.0},
                    ],
                    "ω": [
                        {"object": "Face", "source_key": "Mouth_Line02", "value": 0.5},
                        {"object": "Face", "source_key": "Mouth_Smile01", "value": 1.0}
                    ],
                    "にやり": [
                        {"object": "Face", "source_key": "Mouth_Smile01", "value": 1.0},
                    ]
                }
            }
            ModelUtils.generate_shape_keys(context, shape_key_configMMD)

        # Convert Eyes
        bones_to_duplicate = {
            "Bone_Eye_L_01": "Left Eye",
            "Bone_Eye_R_01": "Right Eye"
        }

        weight_source_bones = {
            "Left Eye": "Bone_Eye_L_End",
            "Right Eye": "Bone_Eye_R_End"
        }
        ArmatureUtils.duplicate_bones_with_weights(context, bones_to_duplicate, weight_source_bones, "EyeShape")
        


        for eye_bone in ["Left Eye", "Right Eye"]:


            ArmatureUtils.position_bone(
                context=context,
                target_bone=eye_bone,
                reference_points={
                    "self": eye_bone  # Use the bone itself as reference
                },
                position_rules={
                    "tail": {
                        "follow_head": ["x", "y"],  # Keep x and y same as head (straight up)
                        "vertical": {"method": "offset", "reference": "head", "value": 0.05}  # Small fixed length up
                    }
                }
            )

        # Merge by distance
        if settings.get('generate_shape_keys', False):
            ModelUtils.merge_meshes_by_distance(context, "Face", ["EyeShape", "Eyebrow"], "A")
        else:
            ModelUtils.merge_meshes_by_distance(context, "Face", ["EyeShape", "Eyebrow"], "Mouth_A01")  


        # Reorder UV Maps
        ModelUtils.reorder_uv_maps(context)
        # Move Armature to Ground
        ArmatureUtils.move_armature_to_ground(context)
        # Merge All Meshes
        if settings.get('merge_all_meshes', False):
            ModelUtils.merge_all_meshes(context)
        # Fix material alpha settings
        SceneUtils.fix_materials(context)
        # Get import directory from armature if available
        SceneUtils.fix_material_textures(context)
        # Set root name before cleanup
        SceneUtils.set_root_name(context)
        # Clean up selection state last
        SceneUtils.cleanup_selection(context)
        return True
        
    @staticmethod
    def convert_zzz(context, model_info: ModelInfo, settings: dict) -> bool:
        """Convert ZZZ models"""
        print(f"Converting ZZZ model: {model_info.clean_name}")
        
        # Store model info on armature
        armature = context.active_object
        if armature and armature.type == 'ARMATURE':
            armature["hoyo2vrc_model_name"] = model_info.clean_name
            armature["hoyo2vrc_game"] = model_info.game
            if model_info.body_type:
                armature["hoyo2vrc_body_type"] = model_info.body_type
            armature["hoyo2vrc_converted"] = True
            
        SceneUtils.remove_empties(context)
        # Clear rotation
        ArmatureUtils.clear_rotation(context)
        # Clean Meshes
        ModelUtils.clean_meshes(context)
        # Rename Meshes
        ModelUtils.rename_meshes(context)
        # Set Wireframe Display
        SceneUtils.set_wireframe_display(context)
        # Set Material View
        SceneUtils.set_material_view(context, "MATERIAL")
        # Rename Bones
        ArmatureUtils.rename_bones(context)
        # Rename Armature Data
        ArmatureUtils.rename_armature_data(context, "Armature")
        # Reset bone roll
        ArmatureUtils.reset_bone_roll(context)
        # Remove bones
        bones_to_remove = {"Root.001", "Root", "Root.002", "FX_Root", "FaceShadowPoint"}
        # Check if first bone is not Hips and add it to removal list
        if context.active_object and context.active_object.type == 'ARMATURE':
            armature = context.active_object
            if armature.data.bones and armature.data.bones[0].name != "Hips":
                bones_to_remove.add(armature.data.bones[0].name)
        ArmatureUtils.clean_bones(context, bones_to_remove)

        # Position Hips
        ArmatureUtils.position_bone(
            context=context,
            target_bone="Hips",
            reference_points={
                "left": "Left Upper Leg",
                "right": "Right Upper Leg",
                "up": "Spine"
            },
            position_rules={
                "head": {
                    "horizontal": {"method": "between", "points": ["left", "right"], "ratio": 0.5},
                    "vertical": {"method": "between", "points": ["left", "up"], "ratio": 0.33},
                    "min_offset": {"axis": "z", "reference": "right", "value": 0.01}
                },
                "tail": {
                    "follow_head": ["x", "y"],
                    "vertical": {"method": "offset", "reference": "up", "value": 0.005},
                    "min_length": 0.05
                }
            }
        )
        # Position Spine
        ArmatureUtils.position_bone(
            context=context,
            target_bone="Spine",
            reference_points={
                "hips": "Hips"
            },
            position_rules={
                "head": {
                    "follow": {"reference": "hips", "point": "tail"}  # Align head with hips tail
                },
                "tail": {
                    "follow_head": ["x", "y"],  # Keep x and y same as head
                    "vertical": {"method": "offset", "reference": "head", "value": 0.075}  # Point straight up by 0.065
                }
            }
        )
        # Position Chest
        ArmatureUtils.position_bone(
            context=context,
            target_bone="Chest",
            reference_points={
                "spine": "Spine"
            },
            position_rules={
                "head": {
                    "follow": {"reference": "spine", "point": "tail"}  # Align head with spine tail
                },
                "tail": {
                    "follow_head": ["x", "y"],  # Keep x and y same as head
                    "vertical": {"method": "offset", "reference": "head", "value": 0.075}  # Point straight up by 0.065
                }
            }
        )
        # Position Upper Chest
        ArmatureUtils.position_bone(
            context=context,
            target_bone="Upper Chest",
            reference_points={
                "chest": "Chest"
            },
            position_rules={
                "head": {
                    "follow": {"reference": "chest", "point": "tail"}
                },
                "tail": {
                    "follow_head": ["x", "y"],
                    "vertical": {"method": "offset", "reference": "head", "value": 0.125}
                }
            }
        )

        # Reattach bones
        bone_pairs = {
            "Left Shoulder": "Left Upper Arm",
            "Right Shoulder": "Right Upper Arm",
            "Upper Chest": "Neck",
            "Neck": "Head",
            "Left Upper Arm": "Left Lower Arm",
            "Right Upper Arm": "Right Lower Arm",
            "Left Lower Arm": "Left Hand",
            "Right Lower Arm": "Right Hand",
            "Right Upper Leg": "Right Lower Leg",
            "Left Upper Leg": "Left Lower Leg",
            "Right Lower Leg": "Right Foot",
            "Left Lower Leg": "Left Foot",
            "Right Foot": "Right Toes",
            "Left Foot": "Left Toes"
        }
        ArmatureUtils.attach_bones(context, bone_pairs)
        # Using custom exclusion list
        custom_exclusions = ["hair", "cloth", "accessory", "pelvis", "waist", "skirt", "spine", "arm", "leg", "chest", "neck", "head", "knee", "calf", "elbow", "skirt", "thigh", "twist"]
        ArmatureUtils.adjust_bone_tails_to_connect(
            context=context, 
            exclude_substrings=custom_exclusions
        )
        # Generate shape keys if enabled
        if settings.get('generate_shape_keys', False):
            shape_key_config = {
                "target_objects": {
                    "Face": ["Fac_Mth_AaTalk", "Fac_Mth_BPM", "Fac_Mth_Oo", "Fac_Eye_Close", "Fac_Eye_R_Wink", "Fac_Eye_L_Wink"]
                },
                "fallback_keys": [
                    {
                        "missing_key": "Fac_Mth_BPM",
                        "fallback_key": "Fac_Mth_Ee",
                        "fallback_value": 1
                    },

                ],
                "generated_keys": {
                    "A": [
                        {"object": "Face", "source_key": "Fac_Mth_AaTalk", "value": 1.0}
                    ],
                    "O": [
                        {"object": "Face", "source_key": "Fac_Mth_Oo", "value": 1},
                    ],
                    "CH": [
                        {"object": "Face", "source_key": "Fac_Mth_Oo", "value": 0.5},
                        {"object": "Face", "source_key": "Fac_Mth_BPM", "value": 0.5}
                    ],
                    "vrc.v_aa": [
                        {"object": "Face", "source_key": "A", "value": 0.9998}
                    ],
                    "vrc.v_ch": [
                        {"object": "Face", "source_key": "CH", "value": 0.9996}
                    ],
                    "vrc.v_dd": [
                        {"object": "Face", "source_key": "A", "value": 0.3},
                        {"object": "Face", "source_key": "CH", "value": 0.7}
                    ],
                    "vrc.v_e": [
                        {"object": "Face", "source_key": "CH", "value": 0.7},
                        {"object": "Face", "source_key": "O", "value": 0.3}
                    ],
                    "vrc.v_ff": [
                        {"object": "Face", "source_key": "A", "value": 0.2},
                        {"object": "Face", "source_key": "CH", "value": 0.4}
                    ],
                    "vrc.v_ih": [
                        {"object": "Face", "source_key": "A", "value": 0.5},
                        {"object": "Face", "source_key": "CH", "value": 0.2}
                    ],
                    "vrc.v_kk": [
                        {"object": "Face", "source_key": "A", "value": 0.7},
                        {"object": "Face", "source_key": "CH", "value": 0.4}
                    ],
                    "vrc.v_nn": [
                        {"object": "Face", "source_key": "A", "value": 0.2},
                        {"object": "Face", "source_key": "CH", "value": 0.7}
                    ],
                    "vrc.v_oh": [
                        {"object": "Face", "source_key": "A", "value": 0.2},
                        {"object": "Face", "source_key": "O", "value": 0.8}
                    ],
                    "vrc.v_ou": [
                        {"object": "Face", "source_key": "O", "value": 0.9994}
                    ],
                    "vrc.v_pp": [
                        {"object": "Face", "source_key": "A", "value": 0.0004},
                        {"object": "Face", "source_key": "O", "value": 0.0004}
                    ],
                    "vrc.v_rr": [
                        {"object": "Face", "source_key": "CH", "value": 0.5},
                        {"object": "Face", "source_key": "O", "value": 0.3}
                    ],
                    "vrc.v_sil": [
                        {"object": "Face", "source_key": "A", "value": 0.0002},
                        {"object": "Face", "source_key": "CH", "value": 0.0002}
                    ],
                    "vrc.v_ss": [
                        {"object": "Face", "source_key": "CH", "value": 0.8}
                    ],
                    "vrc.v_th": [
                        {"object": "Face", "source_key": "A", "value": 0.4},
                        {"object": "Face", "source_key": "O", "value": 0.15}
                    ],
                    "Blink": [
                        {"object": "Face", "source_key": "Fac_Eye_Close", "value": 1.0}
                    ],
                    "Happy Blink": [
                        {"object": "Face", "source_key": "Fac_Eye_L_Wink", "value": 1.0},
                        {"object": "Face", "source_key": "Fac_Eye_R_Wink", "value": 1.0}
                    ]
                }
            }
            ModelUtils.generate_shape_keys(context, shape_key_config)

        # Generate MMD shape keys if enabled
        if settings.get('generate_shape_keys_mmd', False):
            shape_key_configMMD = {
                "target_objects": {
                    "Face": ["Fac_Mth_AaTalk", "Mouth_Oo1", "Mouth_00_Delta02"],
                },
                "fallback_keys": [
                    {
                        "missing_key": "Fac_Eye_HalfClose",
                        "fallback_key": "Fac_Eye_Close",
                        "fallback_value": 0.5
                    },
                    {
                        "missing_key": "Fac_Eye_HalfClose",
                        "fallback_key": "Eye_Close",
                        "fallback_value": 0.5
                    },
                    {
                        "missing_key": "Fac_Mth_R_Down",
                        "fallback_key": "Fac_Mth_Down_R",
                        "fallback_value": 1.0
                    },
                    {
                        "missing_key": "Fac_Mth_L_Down",
                        "fallback_key": "Fac_Mth_Down_L",
                        "fallback_value": 1.0
                    },
                    {
                        "missing_key": "Fac_Eye_R_Wink",
                        "fallback_key": "Fac_Eye_Wink_R",
                        "fallback_value": 1.0
                    },
                    {
                        "missing_key": "Fac_Eye_R_Wink",
                        "fallback_key": "Eye_Wink_R",
                        "fallback_value": 1.0
                    },
                    {
                        "missing_key": "Fac_Eye_L_Wink",
                        "fallback_key": "Fac_Eye_Wink_L",
                        "fallback_value": 1.0
                    },
                    {
                        "missing_key": "Fac_Eye_Wink_L",
                        "fallback_key": "Eye_Wink_L",
                        "fallback_value": 1.0
                    },
                    {
                        "missing_key": "Fac_Eye_L_Open",
                        "fallback_key": "Fac_Eye_Open_L",
                        "fallback_value": 1.0
                    },
                    {
                        "missing_key": "Fac_Eye_L_Open",
                        "fallback_key": "Eye_Open_L",
                        "fallback_value": 1.0
                    },
                    {
                        "missing_key": "Fac_Eye_R_Open",
                        "fallback_key": "Fac_Eye_Open_R",
                        "fallback_value": 1.0
                    },
                    {
                        "missing_key": "Fac_Eye_R_Open",
                        "fallback_key": "Eye_Open_R",
                        "fallback_value": 1.0
                    },
                    {
                        "missing_key": "Fac_Ebr_Sad",
                        "fallback_key": "Eyebrow_困扰",
                        "fallback_value": 1.0
                    },
                    {
                        "missing_key": "Fac_Ebr_Relax",
                        "fallback_key": "Eyebrow_Relax",
                        "fallback_value": 1.0
                    },
                    {
                        "missing_key": "Fac_Ebr_Angry",
                        "fallback_key": "Eyebrow_Angry",
                        "fallback_value": 1.0
                    },                    
                    {
                        "missing_key": "Fac_Ebr_Up",
                        "fallback_key": "Eyebrow_↓",
                        "fallback_value": -1.0
                    },                    
                    {
                        "missing_key": "Fac_Ebr_Down",
                        "fallback_key": "Eyebrow_↓",
                        "fallback_value": 1.0
                    },                   
                    {
                        "missing_key": "Fac_Mth_Triangle",
                        "fallback_key": "Mouth_△",
                        "fallback_value": 1.0
                    },                  
                    {
                        "missing_key": "Fac_Mth_AaTalk",
                        "fallback_key": "Mouth_Talk_B",
                        "fallback_value": 1.0
                    },                 
                    {
                        "missing_key": "Fac_Mth_Ii",
                        "fallback_key": "Mouth_Ii1",
                        "fallback_value": 1.0
                    },
                    {
                        "missing_key": "Fac_Mth_Uu",
                        "fallback_key": "Mouth_U2",
                        "fallback_value": 1.0
                    },
                    {
                        "missing_key": "Fac_Mth_Ee",
                        "fallback_key": "Mouth_E",
                        "fallback_value": 1.0
                    },
                    {
                        "missing_key": "Fac_Mth_UuOo",
                        "fallback_key": "Mouth_Oo1",
                        "fallback_value": 1.0
                    },
                    {
                        "missing_key": "Fac_Mth_L_Down",
                        "fallback_key": "Mouth_oo↘",
                        "fallback_value": 1.0
                    },
                    {
                        "missing_key": "Fac_Mth_R_Down",
                        "fallback_key": "Mouth_↙oo",
                        "fallback_value": 1.0
                    },
                    {
                        "missing_key": "Fac_Mth_R_In",
                        "fallback_key": "Mouth_→oo",
                        "fallback_value": 1.0
                    },
                    {
                        "missing_key": "Fac_Mth_L_In",
                        "fallback_key": "Mouth_oo←",
                        "fallback_value": 1.0
                    },
                    {
                        "missing_key": "Fac_Mth_L_Up",
                        "fallback_key": "Mouth_oo↗",
                        "fallback_value": 1.0
                    },
                    {
                        "missing_key": "Fac_Mth_R_Up",
                        "fallback_key": "Mouth_↖oo",
                        "fallback_value": 1.0
                    },
                ],
                "generated_keys": {
                    "真面目": [ # Serious
                        {"object": "Face", "source_key": "Fac_Ebr_Angry", "value": 0.5},
                    ],
                    "困る": [ # Trouble
                        {"object": "Face", "source_key": "Fac_Ebr_Sad", "value": 1},
                    ],
                    "にこり": [ # Smily
                        {"object": "Face", "source_key": "Fac_Ebr_Relax", "value": 1.0},
                    ],
                    "怒り": [ # Angry
                        {"object": "Face", "source_key": "Fac_Ebr_Angry", "value": 1},
                    ],
                    "上": [ # Up
                        {"object": "Face", "source_key": "Fac_Ebr_Up", "value": 1},
                    ],
                    "下": [ # Down
                        {"object": "Face", "source_key": "Fac_Ebr_Down", "value": 1},
                    ],
                    "まばたき": [ # Blink
                        {"object": "Face", "source_key": "Fac_Eye_Close", "value": 1.0},
                    ],
                    "ウィンク２": [ # Wink 2 L
                        {"object": "Face", "source_key": " ", "value": 1.0},
                    ],
                    "ｳｨﾝｸ２右": [ # Wink 2 R
                        {"object": "Face", "source_key": " ", "value": 1.0},
                    ],
                    "笑い": [ # Smile
                        {"object": "Face", "source_key": "Fac_Eye_L_Wink", "value": 1.0},
                        {"object": "Face", "source_key": "Fac_Eye_R_Wink", "value": 1.0},
                    ],
                    "ウィンク": [ # Wink L
                        {"object": "Face", "source_key": "Fac_Eye_L_Wink", "value": 1.0},
                    ],
                    "ウィンク右": [ # Wink R
                        {"object": "Face", "source_key": "Fac_Eye_R_Wink", "value": 1.0},
                    ],
                    "なごみ": [ # Howawa
                        {"object": "Face", "source_key": "Fac_Eye_Close", "value": 1.0},
                    ],
                    "びっくり": [ # Surprise
                        {"object": "Face", "source_key": "Fac_Eye_R_Open", "value": 1.0}, 
                        {"object": "Face", "source_key": "Fac_Eye_L_Open", "value": 1.0} 
                    ],
                    "じと目": [ # Doubt
                        {"object": "Face", "source_key": "Fac_Eye_HalfClose", "value": 1.0},
                    ],
                    "細目": [ # Half Closed
                        {"object": "Face", "source_key": "Fac_Eye_HalfClose", "value": 0.5},
                    ],
                    "あ": [ # A
                        {"object": "Face", "source_key": "Fac_Mth_AaTalk", "value": 1.0}
                    ],
                    "い": [ # I
                        {"object": "Face", "source_key": "Fac_Mth_Ii", "value": 0.5},
                    ],
                    "う": [ # U
                        {"object": "Face", "source_key": "Fac_Mth_Uu", "value": 1.0},
                    ],
                    "え": [ # E
                        {"object": "Face", "source_key": "Fac_Mth_Ee", "value": 0.5},
                    ],
                    "お": [ # O
                        {"object": "Face", "source_key": "Fac_Mth_UuOo", "value": 1},
                    ],
                    "▲": [ # Triangle Open
                        {"object": "Face", "source_key": "Fac_Mth_Triangle", "value": 1.0},
                    ],
                    "∧": [ # Triangle Closed
                        {"object": "Face", "source_key": "Fac_Mth_L_Down", "value": 0.5},
                        {"object": "Face", "source_key": "Fac_Mth_R_Down", "value": 0.5},
                        {"object": "Face", "source_key": "Fac_Mth_R_In", "value": 1.0},
                        {"object": "Face", "source_key": "Fac_Mth_L_In", "value": 1.0},
                    ],
                    "ω": [ # :3
                        {"object": "Face", "source_key": "Fac_Mth_L_Up", "value": 1.0},
                        {"object": "Face", "source_key": "Fac_Mth_R_Up", "value": 1.0},
                    ],
                    "にやり": [ # Smily 
                        {"object": "Face", "source_key": "Fac_Mth_L_Up", "value": 1.0},
                        {"object": "Face", "source_key": "Fac_Mth_R_Up", "value": 1.0},
                    ]
                }
            }
            ModelUtils.generate_shape_keys(context, shape_key_configMMD)

        # Convert Eyes
        # Check if first set of bones exist
        if any(bone in context.active_object.data.bones for bone in ["Skn_L_Eye", "Skn_R_Eye"]):
            bones_to_duplicate = {
                "Skn_L_Eye": "Left Eye",
                "Skn_R_Eye": "Right Eye"
            }
            weight_source_bones = {
                "Left Eye": ["Skn_L_Eye", "Skn_L_Highlights"], 
                "Right Eye": ["Skn_R_Eye", "Skn_R_Highlights"]
            }
        else:
            bones_to_duplicate = {
                "Bdy_R_Eye": "Right Eye",
                "Bdy_L_Eye": "Left Eye"
            }
            weight_source_bones = {
                "Left Eye": ["Bdy_L_Eye", "Bdy_L_Highlights"],
                "Right Eye": ["Bdy_R_Eye", "Bdy_R_Highlights"] 
            }
        ArmatureUtils.duplicate_bones_with_weights(context, bones_to_duplicate, weight_source_bones, "Face")

        for eye_bone in ["Left Eye", "Right Eye"]:


            ArmatureUtils.position_bone(
                context=context,
                target_bone=eye_bone,
                reference_points={
                    "self": eye_bone  # Use the bone itself as reference
                },
                position_rules={
                    "tail": {
                        "follow_head": ["x", "y"],  # Keep x and y same as head (straight up)
                        "vertical": {"method": "offset", "reference": "head", "value": 0.05}  # Small fixed length up
                    }
                }
            )

        # Convert vertex colors to UV for eye materials
        ModelUtils.convert_vertex_colors_to_uv(context, target_object="Face", color_multiplier=255)
        # Reorder UV Maps
        ModelUtils.reorder_uv_maps(context)
        # Move Armature to Ground
        ArmatureUtils.move_armature_to_ground(context)
        # Merge All Meshes
        if settings.get('merge_all_meshes', False):
            ModelUtils.merge_all_meshes(context)
        # Fix material alpha settings
        SceneUtils.fix_materials(context)
        # Get import directory from armature if available
        SceneUtils.fix_material_textures(context)
        # Duplicate material json
        SceneUtils.duplicate_material_json(context, search_keywords=["Eye"], new_keywords=["EyeHi", "EyeShadow"], exclude_keywords=["Eyebrow"])
        # Set root name before cleanup
        SceneUtils.set_root_name(context)
        # Clean up selection state last
        SceneUtils.cleanup_selection(context)
        return True
        
    @staticmethod
    def convert_wuwa(context, model_info: ModelInfo, settings: dict) -> bool:
        """Convert Wuthering Waves models"""
        print(f"Converting Wuthering Waves model: {model_info.clean_name}")
        
        # Store model info on armature
        armature = context.active_object
        if armature and armature.type == 'ARMATURE':
            armature["hoyo2vrc_model_name"] = model_info.clean_name
            armature["hoyo2vrc_game"] = model_info.game
            if model_info.body_type:
                armature["hoyo2vrc_body_type"] = model_info.body_type
            armature["hoyo2vrc_converted"] = True


        # Resize Model
        ModelUtils.scale_model(context)
        # Set Wireframe Display
        SceneUtils.set_wireframe_display(context)
        # Set Material View
        SceneUtils.set_material_view(context, "MATERIAL")
        # Rename Bones
        ArmatureUtils.rename_bones(context)
        # Rename Armature Data
        ArmatureUtils.rename_armature_data(context, "Armature")
        # Reset bone roll
        ArmatureUtils.reset_bone_roll(context)
        # Remove bones
        bones_to_remove = {f"WeaponProp{i:02d}" for i in range(100)} | {"Root.001"} | {bone for bone in context.active_object.data.bones.keys() if "Case" in bone or "Position" in bone or "Suspension" in bone}
        # Check if first bone is not Hips and add it to removal list
        if context.active_object and context.active_object.type == 'ARMATURE':
            armature = context.active_object
            if armature.data.bones and armature.data.bones[0].name != "Hips":
                bones_to_remove.add(armature.data.bones[0].name)
        ArmatureUtils.clean_bones(context, bones_to_remove)

        # Position Hips
        ArmatureUtils.position_bone(
            context=context,
            target_bone="Hips",
            reference_points={
                "left": "Left Upper Leg",
                "right": "Right Upper Leg",
                "up": "Spine"
            },
            position_rules={
                "head": {
                    "horizontal": {"method": "between", "points": ["left", "right"], "ratio": 0.5},
                    "vertical": {"method": "between", "points": ["left", "up"], "ratio": 0.33},
                    "min_offset": {"axis": "z", "reference": "right", "value": 0.01}
                },
                "tail": {
                    "follow_head": ["x", "y"],
                    "vertical": {"method": "offset", "reference": "up", "value": 0.005},
                    "min_length": 0.05
                }
            }
        )
        # Position Spine
        ArmatureUtils.position_bone(
            context=context,
            target_bone="Spine",
            reference_points={
                "hips": "Hips"
            },
            position_rules={
                "head": {
                    "follow": {"reference": "hips", "point": "tail"}  # Align head with hips tail
                },
                "tail": {
                    "follow_head": ["x", "y"],  # Keep x and y same as head
                    "vertical": {"method": "offset", "reference": "head", "value": 0.075}  # Point straight up by 0.065
                }
            }
        )
        # Position Chest
        ArmatureUtils.position_bone(
            context=context,
            target_bone="Chest",
            reference_points={
                "spine": "Spine"
            },
            position_rules={
                "head": {
                    "follow": {"reference": "spine", "point": "tail"}  # Align head with spine tail
                },
                "tail": {
                    "follow_head": ["x", "y"],  # Keep x and y same as head
                    "vertical": {"method": "offset", "reference": "head", "value": 0.075}  # Point straight up by 0.065
                }
            }
        )
        # Position Upper Chest
        ArmatureUtils.position_bone(
            context=context,
            target_bone="Upper Chest",
            reference_points={
                "chest": "Chest"
            },
            position_rules={
                "head": {
                    "follow": {"reference": "chest", "point": "tail"}
                },
                "tail": {
                    "follow_head": ["x", "y"],
                    "vertical": {"method": "offset", "reference": "head", "value": 0.125}
                }
            }
        )

        # Reattach bones
        bone_pairs = {
            "Left Shoulder": "Left Upper Arm",
            "Right Shoulder": "Right Upper Arm",
            "Upper Chest": "Neck",
            "Neck": "Head",
            "Left Upper Arm": "Left Lower Arm",
            "Right Upper Arm": "Right Lower Arm",
            "Left Lower Arm": "Left Hand",
            "Right Lower Arm": "Right Hand",
            "Right Upper Leg": "Right Lower Leg",
            "Left Upper Leg": "Left Lower Leg",
            "Right Lower Leg": "Right Foot",
            "Left Lower Leg": "Left Foot",
            "Right Foot": "Right Toes",
            "Left Foot": "Left Toes"
        }
        ArmatureUtils.attach_bones(context, bone_pairs)
        # Fix Wuthering fingers
        ArmatureUtils.fix_wuwa_fingers(context)
        # Rename Mesh
        ModelUtils.rename_mesh(context, "Body", True)
        # Create Eyes
        ModelUtils.separate_wuwa_eyes(
            context=context,
            shape_key_name="Pupil_Scale",
            body_mesh_name="Body",
            unused_shape_keys=["Pupil_Up", "Pupil_Down", "Pupil_R", "Pupil_L", "Pupil_Scale"])
        
        # Create and set up eye bones
        eye_bones = {
            "Left Eye": "Left Eye",
            "Right Eye": "Right Eye"
        }
        ArmatureUtils.create_eye_bones(context, eye_bones)
        # Merge Eyes
        ModelUtils.merge_meshes(context, "Eyes", True, ["Left Eye", "Right Eye"])
        
        # Generate shape keys if enabled
        if settings.get('generate_shape_keys', False):
            shape_key_config = {
                "target_objects": {
                    "Body": ["A", "O", "I", "E", "U", "E_Close"]
                },
                "fallback_keys": [
                    {
                        "missing_key": "A",
                        "fallback_key": "Aa",
                        "fallback_value": 0.75
                    }
                ],
                "generated_keys": {
                    "CH": [
                        {"object": "Body", "source_key": "E", "value": 0.3},
                        {"object": "Body", "source_key": "I", "value": 1},
                        {"object": "Body", "source_key": "U", "value": 0.05}
                    ],
                    "vrc.v_aa": [
                        {"object": "Body", "source_key": "A", "value": 0.9998}
                    ],
                    "vrc.v_ch": [
                        {"object": "Body", "source_key": "CH", "value": 0.9996}
                    ],
                    "vrc.v_dd": [
                        {"object": "Body", "source_key": "A", "value": 0.3},
                        {"object": "Body", "source_key": "CH", "value": 0.7}
                    ],
                    "vrc.v_e": [
                        {"object": "Body", "source_key": "CH", "value": 0.7},
                        {"object": "Body", "source_key": "O", "value": 0.3}
                    ],
                    "vrc.v_ff": [
                        {"object": "Body", "source_key": "A", "value": 0.2},
                        {"object": "Body", "source_key": "CH", "value": 0.4}
                    ],
                    "vrc.v_ih": [
                        {"object": "Body", "source_key": "A", "value": 0.5},
                        {"object": "Body", "source_key": "CH", "value": 0.2}
                    ],
                    "vrc.v_kk": [
                        {"object": "Body", "source_key": "A", "value": 0.7},
                        {"object": "Body", "source_key": "CH", "value": 0.4}
                    ],
                    "vrc.v_nn": [
                        {"object": "Body", "source_key": "A", "value": 0.2},
                        {"object": "Body", "source_key": "CH", "value": 0.7}
                    ],
                    "vrc.v_oh": [
                        {"object": "Body", "source_key": "A", "value": 0.2},
                        {"object": "Body", "source_key": "O", "value": 0.8}
                    ],
                    "vrc.v_ou": [
                        {"object": "Body", "source_key": "O", "value": 0.9994}
                    ],
                    "vrc.v_pp": [
                        {"object": "Body", "source_key": "A", "value": 0.0004},
                        {"object": "Body", "source_key": "O", "value": 0.0004}
                    ],
                    "vrc.v_rr": [
                        {"object": "Body", "source_key": "CH", "value": 0.5},
                        {"object": "Body", "source_key": "O", "value": 0.3}
                    ],
                    "vrc.v_sil": [
                        {"object": "Body", "source_key": "A", "value": 0.0002},
                        {"object": "Body", "source_key": "CH", "value": 0.0002}
                    ],
                    "vrc.v_ss": [
                        {"object": "Body", "source_key": "CH", "value": 0.8}
                    ],
                    "vrc.v_th": [
                        {"object": "Body", "source_key": "A", "value": 0.4},
                        {"object": "Body", "source_key": "O", "value": 0.15}
                    ],
                    "Blink": [
                        {"object": "Body", "source_key": "E_Close", "value": 1.0}
                    ]
                }
            }
            ModelUtils.generate_shape_keys(context, shape_key_config)
        
        # Generate MMD shape keys if enabled
        if settings.get('generate_shape_keys_mmd', False):
            shape_key_configMMD = {
                "target_objects": {
                    "Face": ["Fac_Mth_AaTalk", "Mouth_Oo1", "Mouth_00_Delta02"],
                },
                "fallback_keys": [
                    {
                        "missing_key": "Fac_Eye_HalfClose",
                        "fallback_key": "Fac_Eye_Close",
                        "fallback_value": 0.5
                    },
                    {
                        "missing_key": "Fac_Eye_HalfClose",
                        "fallback_key": "Eye_Close",
                        "fallback_value": 0.5
                    },
                    {
                        "missing_key": "Fac_Mth_R_Down",
                        "fallback_key": "Fac_Mth_Down_R",
                        "fallback_value": 1.0
                    },
                ],
                "generated_keys": {
                    "真面目": [ # Serious
                        {"object": "Face", "source_key": "B_Anger", "value": 0.5},
                    ],
                    "困る": [ # Trouble
                        {"object": "Face", "source_key": "B_Sad", "value": 1},
                    ],
                    "にこり": [ # Smily
                        {"object": "Face", "source_key": "B_Happy", "value": 1.0},
                    ],
                    "怒り": [ # Angry
                        {"object": "Face", "source_key": "B_Anger", "value": 1},
                    ],
                    "上": [ # Up
                        {"object": "Face", "source_key": "B_Up_Add", "value": 1},
                    ],
                    "下": [ # Down
                        {"object": "Face", "source_key": "B_Down_Add", "value": 1},
                    ],
                    "まばたき": [ # Blink
                        {"object": "Face", "source_key": "E_Close", "value": 1.0},
                    ],
                    "ウィンク２": [ # Wink 2 L
                        {"object": "Face", "source_key": " ", "value": 1.0},
                    ],
                    "ｳｨﾝｸ２右": [ # Wink 2 R
                        {"object": "Face", "source_key": " ", "value": 1.0},
                    ],
                    "笑い": [ # Smile
                        {"object": "Face", "source_key": "E_Smile_R", "value": 1.0},
                        {"object": "Face", "source_key": "E_Smile_L", "value": 1.0},
                    ],
                    "ウィンク": [ # Wink L
                        {"object": "Face", "source_key": "E_Smile_L", "value": 1.0},
                    ],
                    "ウィンク右": [ # Wink R
                        {"object": "Face", "source_key": "E_Smile_R", "value": 1.0},
                    ],
                    "なごみ": [ # Howawa
                        {"object": "Face", "source_key": "E_Insipid", "value": 1.0},
                    ],
                    "びっくり": [ # Surprise
                        {"object": "Face", "source_key": "E_Stare", "value": 1.0}, 
                    ],
                    "じと目": [ # Doubt
                        {"object": "Face", "source_key": "E_Insipid", "value": 1.0},
                    ],
                    "細目": [ # Half Closed
                        {"object": "Face", "source_key": "E_Close", "value": 0.5},
                    ],
                    "あ": [ # A
                        {"object": "Face", "source_key": "Aa", "value": 1.0}
                    ],
                    "い": [ # I
                        {"object": "Face", "source_key": "I", "value": 0.5},
                    ],
                    "う": [ # U
                        {"object": "Face", "source_key": "U", "value": 1.0},
                    ],
                    "え": [ # E
                        {"object": "Face", "source_key": "E", "value": 0.5},
                    ],
                    "お": [ # O
                        {"object": "Face", "source_key": "O", "value": 1},
                    ],
                    "▲": [ # Triangle Open
                        {"object": "Face", "source_key": "M_OpenSmall", "value": 1.0},
                    ],
                    "∧": [ # Triangle Closed
                        {"object": "Face", "source_key": "M_Nutcracker", "value": 1.0},
                    ],
                    "ω": [ # :3
                        {"object": "Face", "source_key": "M_Smile_R", "value": 1.0},
                        {"object": "Face", "source_key": "M_Smile_L", "value": 1.0}
                    ],
                    "にやり": [ # Smily 
                        {"object": "Face", "source_key": "M_Smile_R", "value": 1.0},
                        {"object": "Face", "source_key": "M_Smile_L", "value": 1.0}
                    ]
                }
            }
            ModelUtils.generate_shape_keys(context, shape_key_configMMD)

        # Move Armature to Ground
        ArmatureUtils.move_armature_to_ground(context)
        # Reorder UV Maps
        ModelUtils.reorder_uv_maps(context)
        # Set root name before cleanup
        SceneUtils.set_root_name(context)
        # Clean up selection state last
        SceneUtils.cleanup_selection(context)

        return True 
    
    @staticmethod
    def convert_npc(context, model_info: ModelInfo, settings: dict) -> bool:
        """Convert NPC models"""
        print(f"Converting NPC model: {model_info.clean_name}")

        # Store model info on armature
        armature = context.active_object
        if armature and armature.type == 'ARMATURE':
            armature["hoyo2vrc_model_name"] = model_info.clean_name
            armature["hoyo2vrc_game"] = model_info.game
            if model_info.body_type:
                armature["hoyo2vrc_body_type"] = model_info.body_type
            armature["hoyo2vrc_converted"] = True

        # Remove empties
        SceneUtils.remove_empties(context)
        # Clear rotation
        ArmatureUtils.clear_rotation(context)
        # Clean Meshes
        ModelUtils.clean_meshes(context)
        # Scale Model
        ModelUtils.scale_model(context)
        # Set Wireframe Display
        SceneUtils.set_wireframe_display(context)
        # Set Material View
        SceneUtils.set_material_view(context, "MATERIAL")
        # Rename Bones
        ArmatureUtils.rename_bones(context)
        # Rename Armature Data
        ArmatureUtils.rename_armature_data(context, "Armature")
        # Reset bone roll
        ArmatureUtils.reset_bone_roll(context)
        # Remove bones
        bones_to_remove = {"Root", "NPC_Kanban_Paimon_Model"}
        ArmatureUtils.clean_bones(context, bones_to_remove)
        # Reparent bones
        bones_to_reparent = {"+PelvisTwist CF A01": "Hips"}
        ArmatureUtils.reparent_bones(context, bones_to_reparent, "Hips")

        # Position Hips
        ArmatureUtils.position_bone(
            context=context,
            target_bone="Hips",
            reference_points={
                "left": "Left Upper Leg",
                "right": "Right Upper Leg",
                "up": "Spine"
            },
            position_rules={
                "head": {
                    "horizontal": {"method": "between", "points": ["left", "right"], "ratio": 0.5},
                    "vertical": {"method": "between", "points": ["left", "up"], "ratio": 0.33},
                    "min_offset": {"axis": "z", "reference": "right", "value": 0.01}
                },
                "tail": {
                    "follow_head": ["x", "y"],
                    "vertical": {"method": "offset", "reference": "up", "value": 0.005},
                    "min_length": 0.05
                }
            }
        )
        # Position Spine
        ArmatureUtils.position_bone(
            context=context,
            target_bone="Spine",
            reference_points={
                "hips": "Hips"
            },
            position_rules={
                "head": {
                    "follow": {"reference": "hips", "point": "tail"}  # Align head with hips tail
                },
                "tail": {
                    "follow_head": ["x", "y"],  # Keep x and y same as head
                    "vertical": {"method": "offset", "reference": "head", "value": 0.075}  # Point straight up by 0.065
                }
            }
        )
        # Position Chest
        ArmatureUtils.position_bone(
            context=context,
            target_bone="Chest",
            reference_points={
                "spine": "Spine"
            },
            position_rules={
                "head": {
                    "follow": {"reference": "spine", "point": "tail"}  # Align head with spine tail
                },
                "tail": {
                    "follow_head": ["x", "y"],  # Keep x and y same as head
                    "vertical": {"method": "offset", "reference": "head", "value": 0.075}  # Point straight up by 0.065
                }
            }
        )
        # Position Upper Chest
        ArmatureUtils.position_bone(
            context=context,
            target_bone="Upper Chest",
            reference_points={
                "chest": "Chest"
            },
            position_rules={
                "head": {
                    "follow": {"reference": "chest", "point": "tail"}
                },
                "tail": {
                    "follow_head": ["x", "y"],
                    "vertical": {"method": "offset", "reference": "head", "value": 0.125}
                }
            }
        )

        # Reattach bones
        if "Upper Chest" in context.active_object.data.edit_bones:
            neck_pair = {
                "Upper Chest": "Neck"
            }
        else:
            neck_pair = {
                "Chest": "Neck"
            }
        bone_pairs = {
            "Left Shoulder": "Left Upper Arm",
            "Right Shoulder": "Right Upper Arm",
            "Left Upper Arm": "Left Lower Arm",
            "Right Upper Arm": "Right Lower Arm",
            "Left Lower Arm": "Left Hand",
            "Right Lower Arm": "Right Hand",
            "Right Upper Leg": "Right Lower Leg",
            "Left Upper Leg": "Left Lower Leg",
            "Right Lower Leg": "Right Foot",
            "Left Lower Leg": "Left Foot",
            "Right Foot": "Right Toes",
            "Left Foot": "Left Toes"
        }
        ArmatureUtils.attach_bones(context, bone_pairs)
        ArmatureUtils.attach_bones(context, neck_pair)
        
        # Generate shape keys if enabled
        if settings.get('generate_shape_keys', False):
            shape_key_config = {
                "target_objects": {
                    "Face": ["Mouth_A01", "Mouth_Fury01", "Mouth_Open01"],
                    "Face_Eye": ["Eye_WinkA_L", "Eye_WinkA_R", "Eye_WinkB_L", "Eye_WinkB_R", "Eye_WinkC_L", "Eye_WinkC_R"]
                },
                "fallback_keys": [
                    {
                        "missing_key": "Mouth_Fury01",
                        "fallback_key": "Mouth_Open01",
                        "fallback_value": 0.5
                    }
                ],
                "generated_keys": {
                    "A": [
                        {"object": "Face", "source_key": "Mouth_A01", "value": 1.0}
                    ],
                    "O": [
                        {"object": "Face", "source_key": "Mouth_Smile02", "value": 0.5},
                        {"object": "Face", "source_key": "Mouth_A01", "value": 0.5}
                    ],
                    "CH": [
                        {"object": "Face", "source_key": "Mouth_Open01", "value": 1.0},
                        {"object": "Face", "source_key": "Mouth_A01", "value": 0.115}
                    ],
                    "vrc.v_aa": [
                        {"object": "Face", "source_key": "A", "value": 0.9998}
                    ],
                    "vrc.v_ch": [
                        {"object": "Face", "source_key": "CH", "value": 0.9996}
                    ],
                    "vrc.v_dd": [
                        {"object": "Face", "source_key": "A", "value": 0.3},
                        {"object": "Face", "source_key": "CH", "value": 0.7}
                    ],
                    "vrc.v_e": [
                        {"object": "Face", "source_key": "CH", "value": 0.7},
                        {"object": "Face", "source_key": "O", "value": 0.3}
                    ],
                    "vrc.v_ff": [
                        {"object": "Face", "source_key": "A", "value": 0.2},
                        {"object": "Face", "source_key": "CH", "value": 0.4}
                    ],
                    "vrc.v_ih": [
                        {"object": "Face", "source_key": "A", "value": 0.5},
                        {"object": "Face", "source_key": "CH", "value": 0.2}
                    ],
                    "vrc.v_kk": [
                        {"object": "Face", "source_key": "A", "value": 0.7},
                        {"object": "Face", "source_key": "CH", "value": 0.4}
                    ],
                    "vrc.v_nn": [
                        {"object": "Face", "source_key": "A", "value": 0.2},
                        {"object": "Face", "source_key": "CH", "value": 0.7}
                    ],
                    "vrc.v_oh": [
                        {"object": "Face", "source_key": "A", "value": 0.2},
                        {"object": "Face", "source_key": "O", "value": 0.8}
                    ],
                    "vrc.v_ou": [
                        {"object": "Face", "source_key": "O", "value": 0.9994}
                    ],
                    "vrc.v_pp": [
                        {"object": "Face", "source_key": "A", "value": 0.0004},
                        {"object": "Face", "source_key": "O", "value": 0.0004}
                    ],
                    "vrc.v_rr": [
                        {"object": "Face", "source_key": "CH", "value": 0.5},
                        {"object": "Face", "source_key": "O", "value": 0.3}
                    ],
                    "vrc.v_sil": [
                        {"object": "Face", "source_key": "A", "value": 0.0002},
                        {"object": "Face", "source_key": "CH", "value": 0.0002}
                    ],
                    "vrc.v_ss": [
                        {"object": "Face", "source_key": "CH", "value": 0.8}
                    ],
                    "vrc.v_th": [
                        {"object": "Face", "source_key": "A", "value": 0.4},
                        {"object": "Face", "source_key": "O", "value": 0.15}
                    ],
                    "Blink": [
                        {"object": "Face_Eye", "source_key": "Eye_WinkB_L", "value": 1.0},
                        {"object": "Face_Eye", "source_key": "Eye_WinkB_R", "value": 1.0}
                    ],
                    "Happy Blink": [
                        {"object": "Face_Eye", "source_key": "Eye_WinkA_L", "value": 1.0},
                        {"object": "Face_Eye", "source_key": "Eye_WinkA_R", "value": 1.0}
                    ],
                    "Pensive Blink": [
                        {"object": "Face_Eye", "source_key": "Eye_WinkC_L", "value": 1.0},
                        {"object": "Face_Eye", "source_key": "Eye_WinkC_R", "value": 1.0}
                    ]
                }
            }
            ModelUtils.generate_shape_keys(context, shape_key_config)

        # Point eye bones straight up
        for eye_bone in ["Eye_R", "Eye_L"]:
            ArmatureUtils.position_bone(
                context=context,
                target_bone=eye_bone,
                reference_points={
                    "self": eye_bone  # Use the bone itself as reference
                },
                position_rules={
                    "tail": {
                        "follow_head": ["x", "y"],  # Keep x and y same as head (straight up)
                        "vertical": {"method": "offset", "reference": "head", "value": 0.05}  # Small fixed length up
                    }
                }
            )

        # Merge by distance
        if settings.get('generate_shape_keys', False):
            ModelUtils.merge_meshes_by_distance(context, "Face", ["Face_Eye", "Brow"], "A")
        else:
            ModelUtils.merge_meshes_by_distance(context, "Face", ["Face_Eye", "Brow"], "Mouth_A01")  

        # Reorder UV Maps
        ModelUtils.reorder_uv_maps(context)
        # Merge All Meshes
        if settings.get('merge_all_meshes', False):
            ModelUtils.merge_all_meshes(context)
        # Move Armature to Ground
        ArmatureUtils.move_armature_to_ground(context)
        # Fix material alpha settings
        SceneUtils.fix_materials(context)
        # Get import directory from armature if available
        SceneUtils.fix_material_textures(context)
        # Set root name before cleanup
        SceneUtils.set_root_name(context)

        ModelUtils.scale_model(context)
        # Clean up selection state last
        SceneUtils.cleanup_selection(context)
        return True
