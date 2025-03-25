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
    
    def get_save_organisation_name(self, save_path: Path) -> str:
        """Get the organisation name from a save folder"""
        try:
            with open(save_path / "Game.json") as f:
                return json.load(f).get("OrganisationName", "Unknown Organization")
        except (FileNotFoundError, json.JSONDecodeError):
            return "Unknown Organization"

    def get_save_folders(self) -> List[Dict[str, str]]:
        """Get list of available save folders within the SteamID directory"""
        if not self.steamid_folder:
            return []
        
        return [{"name": x.name, "path": str(x), 
                "organisation_name": self.get_save_organisation_name(x)} 
                for x in self.steamid_folder.iterdir() 
                if x.is_dir() and x.name.startswith("SaveGame_")]

    def load_save(self, save_path: Union[str, Path]) -> bool:
        """Load a specific save folder"""
        self.current_save = Path(save_path)
        if not self.current_save.exists():
            return False
        
        self.save_data = {}
        try:
            self.save_data["game"] = self._load_json_file("Game.json")
            self.save_data["money"] = self._load_json_file("Money.json")
            self.save_data["rank"] = self._load_json_file("Rank.json")
            self.save_data["metadata"] = self._load_json_file("Metadata.json")
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

    def get_players_info(self, save_path: Optional[Path] = None) -> List[Dict]:
        """Get detailed information about all players in the save"""
        path = save_path or self.current_save
        if not path:
            return []

        players_dir = path / "Players"
        if not players_dir.exists():
            return []

        players = []
        for player_dir in sorted(players_dir.iterdir()):
            if player_dir.is_dir() and player_dir.name.startswith("Player_"):
                player_data = self._load_player_data(player_dir)
                if player_data:
                    players.append(player_data)
        return players

    def _load_player_data(self, player_dir: Path) -> Optional[Dict]:
        """Load all data for a specific player"""
        try:
            with open(player_dir / "Player.json", 'r', encoding='utf-8') as f:
                player_json = json.load(f)
            
            return {
                "id": player_dir.name,
                "steam_id": player_json.get("PlayerCode"),
                "name": self._get_steam_name(player_json.get("PlayerCode")),
                "bank_balance": player_json.get("BankBalance", 0),
                "appearance": self._load_json_file(player_dir / "Appearance.json"),
                "clothing": self._load_json_file(player_dir / "Clothing.json"),
                "inventory": self._parse_inventory(player_dir / "Inventory.json")
            }
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading player data: {e}")
            return None

    def _parse_inventory(self, inventory_path: Path) -> List[Dict]:
        """Parse the player's inventory into a structured format"""
        inventory_data = self._load_json_file(inventory_path)
        if not inventory_data:
            return []

        items = []
        for item_str in inventory_data.get("Items", []):
            try:
                item = json.loads(item_str)
                if item.get("Quantity", 0) <= 0:
                    continue
                    
                items.append({
                    "id": item.get("ID"),
                    "name": self._get_item_name(item.get("ID")),
                    "quantity": item.get("Quantity", 1),
                    "type": item.get("DataType", "Item").replace("Data", ""),
                    "quality": item.get("Quality", ""),
                    "value": item.get("CashBalance", item.get("CurrentFillAmount", 0))
                })
            except json.JSONDecodeError:
                continue
        return items

    def _get_steam_name(self, steam_id: Optional[str]) -> str:
        """Convert SteamID to display name"""
        return f"Steam User ({steam_id})" if steam_id else "Local Player"

    def _get_item_name(self, item_id: str) -> str:
        """Convert item ID to display name"""
        item_names = {
            "trimmers": "Trimmers",
            "wateringcan": "Watering Can",
            "speedgrow": "Speed-Grow",
            "ogkush": "OG Kush",
            "baggie": "Baggie",
            "trashbag": "Trash Bag",
            "cash": "Cash"
            # Add more items as needed
        }
        return item_names.get(item_id, item_id.title())


    def get_save_info(self) -> dict:
        """Get summary information about the loaded save"""
        if not self.save_data:
            return {}
        
        creation_date = self.save_data.get("metadata", {}).get("CreationDate", {})
        formatted_date = f"{creation_date.get('Year', 'Unknown')}-{creation_date.get('Month', 'Unknown'):02d}-{creation_date.get('Day', 'Unknown'):02d} " \
                f"{creation_date.get('Hour', 'Unknown'):02d}:{creation_date.get('Minute', 'Unknown'):02d}:{creation_date.get('Second', 'Unknown'):02d}"
        
        return {
            "game_version": self.save_data.get("game", {}).get("GameVersion", "Unknown"),
            "creation_date": formatted_date if creation_date else "Unknown",
            "organisation_name": self.save_data.get("game", {}).get("OrganisationName", "Unknown"),
            "online_balance": self.save_data.get("money", {}).get("OnlineBalance", 0),
            "networth": self.save_data.get("money", {}).get("NetWorth", 0)
        }

    def update_save_data(self, changes: dict) -> bool:
        """Update save data with changes"""
        # Still need to implement this :)_
        pass