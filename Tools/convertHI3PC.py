import bpy
from bpy.types import Operator
import os
import math
import re
from . import blender_utils, model_utils, armature_utils, shapekey_utils

BlenderVersion = blender_utils.GetBlenderVersion()


class ConvertHonkaiImpactPlayerCharacter(Operator):
    """Convert Model"""

    bl_idname = "hoyo2vrc.converthi3pc"
    bl_label = "OperatorLabel"

    def execute(self, context):

        # Iterate over all objects in the scene
        for obj in bpy.context.scene.objects:
            # Check if the object is a valid model
            if model_utils.IsValidModel(obj):
                Model = obj
                break

        # Identify the model
        game, body_type, model_name = model_utils.IdentifyModel(Model.name)
        print(game, body_type, model_name)
        print(BlenderVersion)

        global armature
        armature = armature_utils.GetArmature()

        def SetupArmature():

            # Rename the armature
            armature.name = "Armature"

            x_cord, y_cord, z_cord, fbx = model_utils.GetOrientations(armature)

            bpy.context.object.display_type = "WIRE"
            bpy.context.object.show_in_front = True

            # Switch to edit mode
            blender_utils.ChangeMode("EDIT")

            if context.scene.humanoid_armature_fix:
                # Check if the first bone in the hierarchy is 'Hips'
                if armature.data.edit_bones[0].name != "Hips":
                    # Rename the first bone to 'Hips'
                    armature.data.edit_bones[0].name = "Hips"

                armature_utils.SetHipAsParent(armature)

                armature_utils.RenameSpines(armature, ["Spine", "Chest", "Upper Chest"])

                bone_names = [
                    "Hips",
                    "Spine",
                    "Chest",
                    "Upper Chest",
                    "Head",
                    "Left leg",
                    "Right leg",
                    "Left knee",
                    "Right knee",
                ]
                (
                    hips,
                    spine,
                    chest,
                    upperchest,
                    head,
                    left_leg,
                    right_leg,
                    left_knee,
                    right_knee,
                ) = armature_utils.GetBones(armature, bone_names).values()

                # Fixing the hips
                armature_utils.FixHips(
                    hips, right_leg, left_leg, spine, x_cord, y_cord, z_cord
                )

                armature_utils.FixSpine(spine, hips, x_cord, y_cord, z_cord)
                armature_utils.FixChest(chest, spine, x_cord, y_cord, z_cord)
                armature_utils.FixUpperChest(upperchest, chest, x_cord, y_cord, z_cord)
                armature_utils.AdjustLegs(
                    left_leg, right_leg, left_knee, right_knee, y_cord
                )
                armature_utils.StraightenHead(armature, head, x_cord, y_cord, z_cord)
                armature_utils.FixMissingNeck(
                    armature, chest, head, x_cord, y_cord, z_cord
                )
                armature_utils.SetBoneRollToZero(armature)

            blender_utils.ChangeMode("OBJECT")

        def GenShapekey():
            # Check if 'Face' and 'EyeShape' objects exist
            if "Face" not in bpy.data.objects or "EyeShape" not in bpy.data.objects:
                print("Face or EyeShape object does not exist. Skipping shape key generation.")
                return

            # Check if the required shape keys are present
            required_shape_keys = {
                "Face": ["Mouth_A01", "Mouth_O01", "Mouth_Angry02"],
                "EyeShape": ["Eye_Wink02_L", "Eye_Wink02_R", "Eye_Wink01_L", "Eye_Wink01_R"]
            }
            fallback_shapekeys = [
                ("Mouth_Angry02", "Mouth_N01", 1),
            ]

            fallback_dict = {key: value for key, value, _ in fallback_shapekeys}

            for obj_name, keys in required_shape_keys.items():
                obj = bpy.data.objects.get(obj_name)
                if obj is None:
                    print(f"Object {obj_name} not found. Skipping its shape keys.")
                    continue

                for key in keys:
                    if shapekey_utils.getKeyBlock(key, obj) is None:
                        if key in fallback_dict and shapekey_utils.getKeyBlock(fallback_dict[key], obj) is not None:
                            print(f"Replaced missing shape key {key} with fallback {fallback_dict[key]} in {obj_name}")
                        else:
                            print(f"Required shape key {key} is not present in {obj_name} and no fallback available.")

            # Generate additional shape keys
            shapekey_data = {
                "A": [("Face", "Mouth_A01", 1.0)],
                "O": [("Face", "Mouth_O01", 1.0)],
                "CH": [("Face", "Mouth_Angry02", 1.0)],
                "vrc.v_aa": [("Face", "A", 0.9998)],
                "vrc.v_ch": [("Face", "CH", 0.9996)],
                "vrc.v_dd": [("Face", "A", 0.3), ("Face", "CH", 0.7)],
                "vrc.v_e": [("Face", "CH", 0.7), ("Face", "O", 0.3)],
                "vrc.v_ff": [("Face", "A", 0.2), ("Face", "CH", 0.4)],
                "vrc.v_ih": [("Face", "A", 0.5), ("Face", "CH", 0.2)],
                "vrc.v_kk": [("Face", "A", 0.7), ("Face", "CH", 0.4)],
                "vrc.v_nn": [("Face", "A", 0.2), ("Face", "CH", 0.7)],
                "vrc.v_oh": [("Face", "A", 0.2), ("Face", "O", 0.8)],
                "vrc.v_ou": [("Face", "O", 0.9994)],
                "vrc.v_pp": [("Face", "A", 0.0004), ("Face", "O", 0.0004)],
                "vrc.v_rr": [("Face", "CH", 0.5), ("Face", "O", 0.3)],
                "vrc.v_sil": [("Face", "A", 0.0002), ("Face", "CH", 0.0002)],
                "vrc.v_ss": [("Face", "CH", 0.8)],
                "vrc.v_th": [("Face", "A", 0.4), ("Face", "O", 0.15)],
                "Blink": [("EyeShape", "Eye_Wink02_L", 1), ("EyeShape", "Eye_Wink02_R", 1)],
                "Happy Blink": [("EyeShape", "Eye_Wink01_L", 1), ("EyeShape", "Eye_Wink01_R", 1)],
            }

            for shapekey_name, mix in shapekey_data.items():
                # Determine the target object based on the first item in the mix
                target_object_name = mix[0][0]
                try:
                    shapekey_utils.GenerateShapeKey(target_object_name, shapekey_name, mix, fallback_shapekeys)
                    print(f"Successfully generated shape key: {shapekey_name}")
                except Exception as e:
                    print(f"Error generating shape key {shapekey_name}: {str(e)}")

            blender_utils.ChangeMode("OBJECT")

        def FixEyes():
            armature.select_set(True)
            blender_utils.ChangeMode("EDIT")
            bpy.ops.armature.select_all(action="DESELECT")

            for eye_bone_name in ["Eye_L", "Eye_R"]:
                armature_utils.MoveEyes(armature, eye_bone_name, BlenderVersion)

            bpy.ops.armature.select_all(action="DESELECT")

            # Exit edit mode
            blender_utils.ChangeMode("OBJECT")

        def ConnectArmature():

            bone_pairs = [
                ("Left knee", "Left ankle"),
                ("Right knee", "Right ankle"),
                ("Right shoulder", "Right arm"),
                ("Left shoulder", "Left arm"),
                ("Left leg", "Left knee"),
                ("Right leg", "Right knee"),
                ("Neck", "Head"),
                ("UpperArmTwist_L_01", "UpperArmTwist_L_02"),
                ("UpperArmTwist_R_01", "UpperArmTwist_R_02"),
                ("LUpperArmTwist", "LUpperArmTwist1"),
                ("RUpperArmTwist", "RUpperArmTwist1"),
                ("L_UpperArm_Twist_01", "L_UpperArm_Twist_02"),
                ("R_UpperArm_Twist_01", "R_UpperArm_Twist_02"),
            ]

            if bpy.context.scene.connect_twist_to_limbs:
                bone_pairs.append(("UpperArmTwist_R_02", "Right elbow"))
                bone_pairs.append(("UpperArmTwist_L_02", "Left elbow"))
                bone_pairs.append(("Twist_R", "Right wrist"))
                bone_pairs.append(("Twist_L", "Left wrist"))
                bone_pairs.append(("Elbow_L", "Left wrist"))
                bone_pairs.append(("Elbow_R", "Right wrist"))
                bone_pairs.append(("R_ForeArm_Twist_02", "Right wrist"))
                bone_pairs.append(("L_ForeArm_Twist_02", "Left wrist"))
                bone_pairs.append(("L_Calf_Twist_02", "Left ankle"))
                bone_pairs.append(("R_Calf_Twist_02", "Right ankle"))
                bone_pairs.append(("Knee_L", "Left ankle"))
                bone_pairs.append(("Knee_R", "Right ankle"))
                bone_pairs.append(("Right arm", "Elbow_R"))
                bone_pairs.append(("Left arm", "Elbow_L"))
                bone_pairs.append(("Right leg", "Knee_R"))
                bone_pairs.append(("Left leg", "Knee_L"))
            else:
                bone_pairs.append(("Right arm", "Right elbow"))
                bone_pairs.append(("Left arm", "Left elbow"))
                bone_pairs.append(("Right elbow", "Right wrist"))
                bone_pairs.append(("Left elbow", "Left wrist"))

            if bpy.context.scene.connect_chest_to_neck:
                bone_pairs.append(("Chest", "Neck"))
            else:
                bone_pairs.append(("Upper Chest", "Neck"))

            blender_utils.ChangeMode("EDIT")
            armature_utils.ToggleArmatureSelection(armature, select=False)

            for bone_name1, bone_name2 in bone_pairs:
                armature_utils.attachbones(
                    armature, bone_name1, bone_name2, exact_match=True
                )

            blender_utils.ChangeMode("OBJECT")

        def ReparentBones():

            blender_utils.ChangeMode("EDIT")

            # Define bone pairs to reparent
            bone_pairs = [
                ("Twist_L", "Left elbow"),
                ("Twist_R", "Right elbow"),
                ("UpperArmTwist_L", "Left arm"),
                ("UpperArmTwist_R", "Right arm"),
                ("LUpperArmTwist", "Left arm"),
                ("RUpperArmTwist", "Right arm"),
                ("L_UpperArm_Twist", "Left arm"),
                ("R_UpperArm_Twist", "Right arm"),
            ]

            # Reparent bones
            for bone_name, parent_name in bone_pairs:
                armature_utils.ReparentBone(armature, bone_name, parent_name)

            blender_utils.ChangeMode("OBJECT")

        def Run():
            model_utils.RemoveEmpties()
            model_utils.ScaleModel()
            model_utils.ClearRotations()
            model_utils.ScaleModel()
            model_utils.CleanMeshes()
            armature_utils.CleanBones()
            armature_utils.RenameBones(game, armature)
            SetupArmature()
            if bpy.context.scene.reconnect_armature:
                ConnectArmature()
            if bpy.context.scene.generate_shape_keys:
                GenShapekey()
            if bpy.context.scene.generate_shape_keys:
                model_utils.MergeFaceByDistance("Face", ["EyeShape", "Eyebrow"], "A")
            else:
                model_utils.MergeFaceByDistance("Face", ["EyeShape", "Eyebrow"], "Mouth_A01")
            model_utils.MergeMeshes()

        Run()

        return {"FINISHED"}
