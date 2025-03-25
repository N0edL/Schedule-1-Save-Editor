import json, re
from pathlib import Path
from typing import Dict, List, Optional, Union

class SaveManager:
    def __init__(self):
        self.savefile_dir = self._find_save_directory()
        self.current_save: Optional[Path] = None
        self.save_data: Dict[str, Union[dict, list]] = {}

    @staticmethod
    def _is_steamid_folder(name: str) -> bool:
        """Check if folder name looks like a SteamID (17 digits)"""
        return re.fullmatch(r'[0-9]{17}', name) is not None

    def _find_save_directory(self) -> Optional[Path]:
        """Locate the game's save directory, navigating through SteamID folder"""
        base_path = Path.home() / "AppData" / "LocalLow" / "TVGS" / "Schedule I" / "saves"
        
        if not base_path.exists():
            return None
            
        steamid_folders = [
            f for f in base_path.iterdir() 
            if f.is_dir() and self._is_steamid_folder(f.name)
        ]
        
        if not steamid_folders:
            return None
            
        self.steamid_folder = steamid_folders[0]
        
        for item in self.steamid_folder.iterdir():
            if item.is_dir() and item.name.startswith("SaveGame_"):
                return item
                
        return None

    def get_save_folders(self) -> List[Dict[str, str]]:
        """Get list of available save folders within the SteamID directory"""
        if not self.steamid_folder:
            return []
            
        return [{"name": x.name, "path": str(x)} 
                for x in self.steamid_folder.iterdir() 
                if x.is_dir() and x.name.startswith("SaveGame_")]

    def load_save(self, save_path: Union[str, Path]) -> bool:
        """Load a specific save folder"""
        self.current_save = Path(save_path)
        if not self.current_save.exists():
            return False
            
        self.save_data = {}
        try:
            # Load key JSON files
            self.save_data["game"] = self._load_json_file("Game.json")
            self.save_data["money"] = self._load_json_file("Money.json")
            self.save_data["rank"] = self._load_json_file("Rank.json")
            self.save_data["time"] = self._load_json_file("Time.json")
            self.save_data["metadata"] = self._load_json_file("Metadata.json")
            
            # Load other important data
            self.save_data["properties"] = self._load_folder_data("Properties")
            self.save_data["vehicles"] = self._load_folder_data("OwnedVehicles")
            self.save_data["businesses"] = self._load_folder_data("Businesses")
            
            return True
        except Exception as e:
            print(f"Error loading save: {e}")
            return False

    def _load_json_file(self, filename: str) -> dict:
        """Load a JSON file from the current save"""
        file_path = self.current_save / filename
        if not file_path.exists():
            return {}
            
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_folder_data(self, folder_name: str) -> list:
        """Load all JSON files from a subfolder"""
        folder_path = self.current_save / folder_name
        if not folder_path.exists():
            return []
            
        data = []
        for file in folder_path.glob("*.json"):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data.append(json.load(f))
            except json.JSONDecodeError:
                continue
                
        return data

    def get_save_info(self) -> dict:
        """Get summary information about the loaded save"""
        if not self.save_data:
            return {}
            
        return {
            "game_version": self.save_data.get("game", {}).get("GameVersion", "Unknown"),
        }

    def update_save_data(self, changes: dict) -> bool:
        """Update save data with changes"""
        # Still need to implement this :)_
        pass