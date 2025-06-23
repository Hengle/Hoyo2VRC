import re
from dataclasses import dataclass
from typing import Optional, Tuple
import bpy

@dataclass
class ModelInfo:
    """Class to store model identification information"""
    game: Optional[str] = None
    body_type: Optional[str] = None
    model_name: Optional[str] = None
    clean_name: Optional[str] = None
    weapon_type: Optional[str] = None
    is_weapon: bool = False
    is_legacy: bool = False

class GameDetector:
    """Class to handle game detection and model identification"""
    
    # List of currently supported games
    SUPPORTED_GAMES = {
        "Genshin Impact",
        "Genshin Impact Weapon",
        "Honkai Star Rail",
        "Honkai Impact 3rd",
        "Zenless Zone Zero",
        "Wuthering Waves"
    }
    
    @staticmethod
    def is_game_supported(game: str) -> bool:
        """Check if a game is currently supported for conversion
        
        Args:
            game: Name of the game to check
            
        Returns:
            bool: True if the game is supported, False otherwise
        """
        return game in GameDetector.SUPPORTED_GAMES

    @staticmethod
    def is_legacy_hi3_model(context: bpy.types.Context) -> bool:
        """Check if this is a legacy HI3 model by looking for old mesh names"""
        legacy_mesh_names = {"Eye_L", "Eye_R", "Mouth"}
        scene_mesh_names = {obj.name for obj in context.scene.objects if obj.type == 'MESH'}
        return bool(legacy_mesh_names & scene_mesh_names)  # Check for any intersection

    @staticmethod
    def get_model_name(context: bpy.types.Context) -> tuple[ModelInfo, str, str]:
        """Get the model name and info from the active object
        
        Returns:
            tuple: (ModelInfo, display_name, icon)
        """
        if not context.active_object:
            return ModelInfo(), "No Model Selected", 'OBJECT_DATA'
            
        detector = GameDetector()
        model_info = detector.identify_model(context.active_object.name)
        
        # Check for legacy HI3 model if it's identified as HI3
        if model_info.game == "Honkai Impact 3rd":
            model_info.is_legacy = detector.is_legacy_hi3_model(context)
            
        # Set display name and icon
        if not model_info.game:
            display_name = "Unknown Model Type"
            icon = 'QUESTION'
        elif model_info.is_legacy:
            display_name = model_info.clean_name
            icon = 'ERROR'
        else:
            display_name = model_info.clean_name
            icon = 'OUTLINER_OB_ARMATURE'
            
        return model_info, display_name, icon

    @staticmethod
    def clean_name(name: str) -> str:
        """Remove common suffixes and modifiers from model names"""
        replacements = [
            (".001", ""),
            ("_Render", ""),
            ("_merge", ""),
            (" (merge)", ""),
            ("_Edit", ""),
            (".fbx", ""),
            (".FBX", ""),
            ("_LOD0", ""),
            ("_LOD1", ""),
            ("_LOD2", ""),
            ("_UI", ""),
            ("_Model", ""),
            ("_Skeleton", ""),
            ("Costume", " "),
            ("NPC_", ""),
            ("Kanban_", ""),
            ("Cs_", ""),
            ("Monster_", ""),
            ("#", ""),
            ("La_", "La "),
            ("_TK", ""),
        ]
        
        for old, new in replacements:
            name = name.replace(old, new)
        return name.strip()

    @staticmethod
    def extract_clean_name(name: str, game: str = None) -> str:
        """Extract just the character/weapon name without prefixes/suffixes"""
        # Remove common prefixes
        prefixes_to_remove = [
            "Cs_Avatar_",
            "Avatar_",
            "NPC_Avatar_",
            "Player_",
            "Art_",
            "Equip_",
            "CS_Item_",
            "NPC_Item_",
            "Assister_",
            "Standalone_",
            "Avatar_",
            "NPC_Avatar_",
            "Player_",
            "Art_",
            "Equip_",
            "CS_Item_",
            "NPC_Item_",
            "Assister_",
            "Md",
            "R2T1",
            "NH",
        ]
        
        # Remove body type prefixes
        body_types = ["Boy_", "Girl_", "Lady_", "Male_", "Loli_", "Female_Size\\d{2}_", "Male_Size\\d{2}_", "Size\\d{2}_" ]
        
        # Remove weapon type prefixes
        weapon_types = ["Sword_", "Bow_", "Claymore_", "Catalyst_", "Pole_", "Undefined_"]

        # Regex Prefixes
        regex_prefixes = [
            "[A-Z][0-9]{2}_",  # Things like C6_
            "[a-z][0-9]{2}_",  # Things like c6_
            "_[A-Z]{2}",       # Things like _AB
            "_[a-z]{2}",       # Things like _ab
        ]
        
        name = GameDetector.clean_name(name)
        
        # Special character name handling
        if game == "Genshin Impact":
            if "PlayerBoy" in name:
                return "Aether"
            elif "PlayerGirl" in name:
                return "Lumine"
        elif game == "Honkai Star Rail":
            if "PlayerBoy" in name:
                return "Caelus"
            elif "PlayerGirl" in name:
                return "Stelle"
            # Handle Trailblazer variants
            elif "Trailblazer" in name:
                if "Boy" in name or "Male" in name:
                    return "Caelus"
                elif "Girl" in name or "Female" in name:
                    return "Stelle"
        
        # Remove prefixes
        for prefix in prefixes_to_remove:
            name = re.sub(f"^{prefix}", "", name)
            
        # Remove body types
        for body_type in body_types:
            name = re.sub(f"^{body_type}", "", name)
            
        # Remove weapon types
        for weapon_type in weapon_types:
            name = re.sub(f"^{weapon_type}", "", name)

        # Remove Regex Prefixes
        for prefix in regex_prefixes:
            name = re.sub(f"^{prefix}", "", name)
        
        # Remove HI3 specific patterns
        if game == "Honkai Impact 3rd":
            # Remove _C followed by numbers (e.g., _C5)
            name = re.sub(r"_C\d+", "", name)
            # Remove _IN, _MC, etc.
            name = re.sub(r"_[A-Z]{2}$", "", name)
        
        # Remove any trailing numbers and underscores
        name = re.sub(r"_?\d+$", "", name)
        name = re.sub(r"^_|_$", "", name)
        
        return name

    @staticmethod
    def identify_genshin_character(match) -> ModelInfo:
        """Process Genshin Impact character matches"""
        body_type = match.group(2)
        weapon_type = match.group(3)
        model_name = match.group(4)
        original_name = match.group(0)
        
        return ModelInfo(
            game="Genshin Impact",
            body_type=body_type,
            model_name=model_name,
            clean_name=GameDetector.extract_clean_name(original_name, "Genshin Impact"),
            weapon_type=weapon_type
        )

    @staticmethod
    def identify_starrail_character(match) -> ModelInfo:
        """Process Honkai Star Rail character matches"""
        model_name = match.group(2)
        original_name = match.group(0)
        
        return ModelInfo(
            game="Honkai Star Rail",
            model_name=model_name,
            clean_name=GameDetector.extract_clean_name(original_name, "Honkai Star Rail")
        )

    @staticmethod
    def identify_hi3_character(match) -> ModelInfo:
        """Process Honkai Impact 3rd character matches"""
        model_name = match.group(1)
        variant = match.group(2)
        original_name = match.group(0)
        
        return ModelInfo(
            game="Honkai Impact 3rd",
            model_name=f"{model_name}{variant}",
            clean_name=GameDetector.extract_clean_name(original_name)
        )

    @staticmethod
    def identify_zzz_character(match) -> ModelInfo:
        """Process Zenless Zone Zero character matches"""
        gender = match.group(1)
        size = match.group(2)
        name = match.group(3)
        original_name = match.group(0)
        
        # Combine gender and size for body type (e.g., "Female Size 03")
        body_type = f"{gender}_Size{size}"
        
        return ModelInfo(
            game="Zenless Zone Zero",
            body_type=body_type,
            model_name=name,
            clean_name=GameDetector.extract_clean_name(original_name, "Zenless Zone Zero")
        )

    @staticmethod
    def identify_weapon(match) -> ModelInfo:
        """Process weapon matches"""
        original_name = match.group(0)
        
        # Extract weapon type from name if possible
        weapon_type = None
        weapon_types = ['Sword', 'Bow', 'Claymore', 'Catalyst', 'Pole']
        for wtype in weapon_types:
            if wtype in original_name:
                weapon_type = wtype
                break
        
        return ModelInfo(
            game="Genshin Impact Weapon",
            body_type=weapon_type,
            model_name=original_name,
            clean_name=GameDetector.extract_clean_name(original_name),
            is_weapon=True
        )

    @staticmethod
    def identify_wuthering_waves(match) -> ModelInfo:
        """Process Wuthering Waves character matches"""
        model_name = match.group(1)
        original_name = match.group(0)
        
        return ModelInfo(
            game="Wuthering Waves",
            model_name=model_name,
            clean_name=GameDetector.extract_clean_name(original_name)
        )

    @staticmethod
    def identify_unknown(match) -> ModelInfo:
        """Process unknown matches"""
        return ModelInfo(
            game="NPC",
            model_name=match,
            clean_name=GameDetector.extract_clean_name(match)
        )
    
    def identify_model(self, name: str) -> ModelInfo:
        """Identify the game and model details from a model name"""
        
        # Clean the name first
        name = self.clean_name(name)
        
        # Define patterns with their corresponding processing functions
        patterns = [
            # Genshin Impact Characters
            (
                r"^(Cs_Avatar|Cs_Monster|Avatar|NPC_Avatar)_(Boy|Girl|Lady|Male|Loli)_(Sword|Claymore|Bow|Catalyst|Pole|Undefined)_([a-zA-Z]+(?:\s+[a-zA-Z]+)?)(?<!_\d{2})$",
                self.identify_genshin_character
            ),
            # Zenless Zone Zero Characters
            (
                r"^Avatar_(Female|Male)_Size(\d{2})_([a-zA-Z]+)$",
                self.identify_zzz_character
            ),
            # Honkai Star Rail Characters
            (
                r"^(Player|Avatar|Art|NPC_Avatar)_([a-zA-Z]+)_?(?<!_\d{2})\d{2}$",
                self.identify_starrail_character
            ),
            # Honkai Impact 3rd Characters
            (
                r"^(Avatar|Assister)_\w+?_C\d+(_\w+[^_])$",
                self.identify_hi3_character
            ),
            # Wuthering Waves Characters
            (
                r"^(R2T1\w+|NH\w+)$",
                self.identify_wuthering_waves
            ),
            # Genshin Impact Weapons - More strict pattern
            (
                r"^(?:Equip_(?:Sword|Bow|Claymore|Catalyst|Pole)_(?!Dvalin)[a-zA-Z0-9_]+|CS_Item_(?:Sword|Bow|Claymore|Catalyst|Pole)_[a-zA-Z0-9]+|NPC_Item_[a-zA-Z0-9_]+)$",
                self.identify_weapon
            ),
            # Bow Controller - Special case
            (
                r"^.*ControllerBone$",
                self.identify_weapon
            )
        ]
        
        print(name)
        # Try to match against each pattern
        for pattern, processor in patterns:
            match = re.match(pattern, name)
            if match:
                print(match)
                return processor(match)
        
        # If no patterns match, return unknown
        return self.identify_unknown(name)

def get_model_info(obj_name: str) -> ModelInfo:
    """Helper function to get model info from an object name"""
    detector = GameDetector()
    return detector.identify_model(obj_name)
