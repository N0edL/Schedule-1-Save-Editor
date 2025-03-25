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
