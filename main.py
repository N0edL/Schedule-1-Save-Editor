
import sys
import json
import os
import random
import string
import shutil
import tempfile
import urllib.request
import zipfile
import winreg  # Added import
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget, QWidget,
    QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QFormLayout, QLineEdit, QComboBox, QPushButton,
    QMessageBox, QTabWidget, QCheckBox, QGroupBox, QTextEdit, QHeaderView, QDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QRegularExpressionValidator, QIntValidator

def find_steam_path():
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam") as key:
            steam_path, _ = winreg.QueryValueEx(key, "InstallPath")
            return Path(steam_path)
    except FileNotFoundError:
        return None

def find_game_directory():
    steam_path = find_steam_path()
    if not steam_path:
        return None

    library_folders_vdf = steam_path / "steamapps" / "libraryfolders.vdf"
    if not library_folders_vdf.exists():
        return None

    with open(library_folders_vdf, 'r') as f:
        content = f.read()

    paths = re.findall(r'"path"\s+"([^"]+)"', content)
    for path in paths:
        library_path = Path(path.replace('\\\\', '\\'))
        game_dir = library_path / "steamapps" / "common" / "Schedule I"
        if game_dir.exists():
            return game_dir
    return None

def parse_npc_log(log_text: str) -> list[tuple[str, str]]:
    """
    Parse the NPC log text and extract (name, id) pairs.
    
    Args:
        log_text (str): The log text containing NPC entries.
    
    Returns:
        list[tuple[str, str]]: List of (name, id) pairs.
    """
    pattern = r"\[ConsoleUnlockerMod\] 👤 NPC Found: (.+?) \| ID: (.+)"
    matches = re.findall(pattern, log_text)
    return [(name.strip(), id.strip()) for name, id in matches]

class SaveManager:
    def __init__(self):
        self.savefile_dir = self._find_save_directory()
        self.current_save: Optional[Path] = None
        self.save_data: Dict[str, Union[dict, list]] = {}
        self.backup_path: Optional[Path] = None
        self.feature_backups: Optional[Path] = None

    @staticmethod
    def _is_steamid_folder(name: str) -> bool:
        return re.fullmatch(r'[0-9]{17}', name) is not None

    def _find_save_directory(self) -> Optional[Path]:
        base_path = Path.home() / "AppData" / "LocalLow" / "TVGS" / "Schedule I" / "saves"
        if not base_path.exists():
            return None
        steamid_folders = [f for f in base_path.iterdir() if f.is_dir() and self._is_steamid_folder(f.name)]
        if not steamid_folders:
            return None
        self.steamid_folder = steamid_folders[0]
        for item in self.steamid_folder.iterdir():
            if item.is_dir() and item.name.startswith("SaveGame_"):
                return item
        return None

    def get_save_organisation_name(self, save_path: Path) -> str:
        try:
            with open(save_path / "Game.json") as f:
                return json.load(f).get("OrganisationName", "Unknown Organization")
        except (FileNotFoundError, json.JSONDecodeError):
            return "Unknown Organization"

    def get_save_folders(self) -> List[Dict[str, str]]:
        if not hasattr(self, 'steamid_folder') or not self.steamid_folder:
            return []
        return [{"name": x.name, "path": str(x), "organisation_name": self.get_save_organisation_name(x)}
                for x in self.steamid_folder.iterdir()
                if x.is_dir() and re.fullmatch(r"SaveGame_[1-9]", x.name)]

    def load_save(self, save_path: Union[str, Path]) -> bool:
        self.current_save = Path(save_path)
        if not self.current_save.exists():
            return False
        self.save_data = {}
        try:
            self.save_data["game"] = self._load_json_file("Game.json")
            self.save_data["money"] = self._load_json_file("Money.json")
            self.save_data["rank"] = self._load_json_file("Rank.json")
            self.save_data["time"] = self._load_json_file("Time.json")
            self.save_data["metadata"] = self._load_json_file("Metadata.json")
            self.save_data["properties"] = self._load_folder_data("Properties")
            self.save_data["vehicles"] = self._load_folder_data("OwnedVehicles")
            self.save_data["businesses"] = self._load_folder_data("Businesses")
            # Set backup paths
            self.backup_path = self.current_save.parent / (self.current_save.name + '_Backup')
            self.feature_backups = self.backup_path / 'feature_backups'
            self.create_initial_backup()
            return True
        except Exception as e:
            print(f"Error loading save: {e}")
            return False

    def _load_json_file(self, filename: str) -> dict:
        file_path = self.current_save / filename
        if not file_path.exists():
            return {}
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_folder_data(self, folder_name: str) -> list:
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
        if not self.save_data:
            return {}
        creation_date = self.save_data.get("metadata", {}).get("CreationDate", {})
        formatted_date = (f"{creation_date.get('Year', 'Unknown')}-{creation_date.get('Month', 'Unknown'):02d}-"
                          f"{creation_date.get('Day', 'Unknown'):02d} {creation_date.get('Hour', 'Unknown'):02d}:"
                          f"{creation_date.get('Minute', 'Unknown'):02d}:{creation_date.get('Second', 'Unknown'):02d}")
        money_data = self.save_data.get("money", {})
        rank_data = self.save_data.get("rank", {})
        return {
            "game_version": self.save_data.get("game", {}).get("GameVersion", "Unknown"),
            "creation_date": formatted_date if creation_date else "Unknown",
            "organisation_name": self.save_data.get("game", {}).get("OrganisationName", "Unknown"),
            "online_money": int(money_data.get("OnlineBalance", 0)),
            "networth": int(money_data.get("Networth", 0)),
            "lifetime_earnings": int(money_data.get("LifetimeEarnings", 0)),
            "weekly_deposit_sum": int(money_data.get("WeeklyDepositSum", 0)),
            "current_rank": rank_data.get("CurrentRank", "Unknown"),
            "rank_number": int(rank_data.get("Rank", 0)),
            "tier": int(rank_data.get("Tier", 0)),
        }

    def _save_json_file(self, filename: str, data: dict):
        file_path = self.current_save / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

    def set_online_money(self, new_amount: int):
        if "money" in self.save_data:
            self.save_data["money"]["OnlineBalance"] = new_amount
            self._save_json_file("Money.json", self.save_data["money"])

    def set_networth(self, new_networth: int):
        if "money" in self.save_data:
            self.save_data["money"]["Networth"] = new_networth
            self._save_json_file("Money.json", self.save_data["money"])

    def set_lifetime_earnings(self, new_earnings: int):
        if "money" in self.save_data:
            self.save_data["money"]["LifetimeEarnings"] = new_earnings
            self._save_json_file("Money.json", self.save_data["money"])

    def set_weekly_deposit_sum(self, new_sum: int):
        if "money" in self.save_data:
            self.save_data["money"]["WeeklyDepositSum"] = new_sum
            self._save_json_file("Money.json", self.save_data["money"])

    def set_rank(self, new_rank: str):
        if "rank" in self.save_data:
            self.save_data["rank"]["CurrentRank"] = new_rank
            self._save_json_file("Rank.json", self.save_data["rank"])

    def set_rank_number(self, new_rank: int):
        if "rank" in self.save_data:
            self.save_data["rank"]["Rank"] = new_rank
            self._save_json_file("Rank.json", self.save_data["rank"])

    def set_tier(self, new_tier: int):
        if "rank" in self.save_data:
            self.save_data["rank"]["Tier"] = new_tier
            self._save_json_file("Rank.json", self.save_data["rank"])

    def set_organisation_name(self, new_name: str):
        if "game" in self.save_data:
            self.save_data["game"]["OrganisationName"] = new_name
            self._save_json_file("Game.json", self.save_data["game"])

    def add_discovered_products(self, product_ids: list):
        products_path = self.current_save / "Products"
        products_json = products_path / "Products.json"
        os.makedirs(products_path, exist_ok=True)

        if products_json.exists():
            with open(products_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {
                "DataType": "ProductManagerData",
                "DataVersion": 0,
                "GameVersion": "0.2.9f4",
                "DiscoveredProducts": [],
                "ListedProducts": [],
                "ActiveMixOperation": {"ProductID": "", "IngredientID": ""},
                "IsMixComplete": False,
                "MixRecipes": [],
                "ProductPrices": []
            }

        discovered = data.setdefault("DiscoveredProducts", [])
        for pid in product_ids:
            if pid not in discovered:
                discovered.append(pid)

        with open(products_json, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

    def generate_products(self, count: int, id_length: int, price: int, add_to_listed: bool = False):
        products_path = self.current_save / "Products"
        os.makedirs(products_path, exist_ok=True)
        created_path = products_path / "CreatedProducts"
        os.makedirs(created_path, exist_ok=True)

        products_json = products_path / "Products.json"
        if products_json.exists():
            data = self._load_json_file(products_json.name)
        else:
            data = {
                "DataType": "ProductManagerData",
                "DataVersion": 0,
                "GameVersion": "0.2.9f4",
                "DiscoveredProducts": [],
                "ListedProducts": [],
                "ActiveMixOperation": {"ProductID": "", "IngredientID": ""},
                "IsMixComplete": False,
                "MixRecipes": [],
                "ProductPrices": []
            }

        discovered = data.setdefault("DiscoveredProducts", [])
        mix_recipes = data.setdefault("MixRecipes", [])
        prices = data.setdefault("ProductPrices", [])
        listed_products = data.setdefault("ListedProducts", [])

        property_pool = ["athletic", "balding", "gingeritis", "spicy", "jennerising", "thoughtprovoking",
                        "tropicthunder", "giraffying", "longfaced", "sedating", "smelly", "paranoia", "laxative",
                        "caloriedense", "energizing"]
        ingredients = ["flumedicine", "gasoline", "mouthwash", "horsesemen", "iodine", "chili", "paracetamol",
                    "energydrink", "donut", "banana", "viagra", "cuke", "motoroil"]
        product_set = set(discovered)
        new_products = []

        def generate_id(length):
            return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

        for _ in range(count):
            product_id = generate_id(id_length)
            while product_id in product_set:
                product_id = generate_id(id_length)
            product_set.add(product_id)
            discovered.append(product_id)
            new_products.append(product_id)
            mixer = random.choice(discovered)
            ingredient = random.choice(ingredients)
            mix_recipes.append({"Product": ingredient, "Mixer": mixer, "Output": product_id})
            prices.append({"String": product_id, "Int": price})
            properties = random.sample(property_pool, 7)
            product_data = {
                "DataType": "WeedProductData", "DataVersion": 0, "GameVersion": "0.2.9f4",
                "Name": product_id, "ID": product_id, "DrugType": 0, "Properties": properties,
                "AppearanceSettings": {
                    "MainColor": {"r": random.randint(0, 255), "g": random.randint(0, 255), "b": random.randint(0, 255), "a": 255},
                    "SecondaryColor": {"r": random.randint(0, 255), "g": random.randint(0, 255), "b": random.randint(0, 255), "a": 255},
                    "LeafColor": {"r": random.randint(0, 255), "g": random.randint(0, 255), "b": random.randint(0, 255), "a": 255},
                    "StemColor": {"r": random.randint(0, 255), "g": random.randint(0, 255), "b": random.randint(0, 255), "a": 255}
                }
            }
            self._save_json_file(created_path / f"{product_id}.json", product_data)

        if add_to_listed:
            listed_products.extend(new_products)

        self._save_json_file(products_json.name, data)

    def update_property_quantities(self, property_type: str, quantity: int, 
                                packaging: str, update_type: str, quality: str) -> int:
        """Update quantities and quality in property Data.json files"""
        updated_count = 0
        properties_path = self.current_save / "Properties"
        
        if not properties_path.exists():
            return 0

        # Determine directories to process
        directories = []
        if property_type == "all":
            # Get all property directories
            directories = [d for d in properties_path.iterdir() if d.is_dir()]
        else:
            # Use specified directory if it exists
            target_dir = properties_path / property_type
            if target_dir.exists() and target_dir.is_dir():
                directories = [target_dir]

        for prop_dir in directories:
            objects_path = prop_dir / "Objects"
            if not objects_path.exists():
                continue

            # Process all Data.json files
            for data_file in objects_path.rglob("Data.json"):
                try:
                    with open(data_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    if "Contents" not in data or "Items" not in data["Contents"]:
                        continue

                    modified = False
                    items = data["Contents"]["Items"]
                    for i, item_str in enumerate(items):
                        item = json.loads(item_str)
                        
                        # Determine if we should modify this item
                        modify = False
                        if update_type == "both":
                            modify = True
                        elif update_type == "weed" and item.get("DataType") == "WeedData":
                            modify = True
                        elif update_type == "item" and item.get("DataType") == "ItemData":
                            modify = True

                        if modify:
                            item["Quantity"] = quantity
                            if item.get("DataType") == "WeedData":
                                if packaging != "none":
                                    item["PackagingID"] = packaging
                                item["Quality"] = quality  # Set quality here
                            items[i] = json.dumps(item)
                            modified = True

                    if modified:
                        with open(data_file, 'w', encoding='utf-8') as f:
                            json.dump(data, f, indent=4)
                        updated_count += 1

                except Exception as e:
                    print(f"Error processing {data_file}: {str(e)}")

        return updated_count

    def complete_all_quests(self) -> tuple[int, int]:
        """Mark all quests and objectives as completed. Returns (quests_completed, objectives_completed)"""
        quests_path = self.current_save / "Quests"
        if not quests_path.exists():
            return 0, 0

        quests_completed = 0
        objectives_completed = 0

        # Process all quest files
        for file_path in quests_path.rglob("*.json"):
            try:
                rel_path = file_path.relative_to(self.current_save)
                data = self._load_json_file(str(rel_path))
                
                if data.get("DataType") != "QuestData":
                    continue

                modified = False
                current_state = data.get("State")
                if current_state in (0, 1):  # 0 = Not started, 1 = In progress
                    data["State"] = 2  # 2 = Completed
                    quests_completed += 1
                    modified = True

                # Update objectives
                if "Entries" in data:
                    for entry in data["Entries"]:
                        current_entry_state = entry.get("State")
                        if current_entry_state in (0, 1):
                            entry["State"] = 2
                            objectives_completed += 1
                            modified = True

                if modified:
                    self._save_json_file(str(rel_path), data)

            except Exception as e:
                print(f"Error processing {file_path}: {str(e)}")
                continue

        return quests_completed, objectives_completed

    def modify_variables(self) -> int:
        """Modify variables in both root and player Variables folders"""
        if not self.current_save:
            raise ValueError("No save loaded")

        count = 0
        variables_dirs = []

        # Add root Variables directory
        root_vars = self.current_save / "Variables"
        if root_vars.exists():
            variables_dirs.append(root_vars)

        # Add player Variables directories that exist
        for i in range(10):
            player_vars = self.current_save / f"Players/Player_{i}/Variables"
            if player_vars.exists():
                variables_dirs.append(player_vars)

        # Process all found Variables directories
        for var_dir in variables_dirs:
            # Process JSON files
            for json_file in var_dir.glob("*.json"):
                rel_path = json_file.relative_to(self.current_save)
                data = self._load_json_file(str(rel_path))
                
                if "Value" in data:
                    original = data["Value"]
                    if data["Value"] == "False":
                        data["Value"] = "True"
                        count += 1
                    elif data["Value"] not in ["True", "False"]:
                        data["Value"] = "999999999"
                        count += 1
                    
                    if data["Value"] != original:
                        self._save_json_file(str(rel_path), data)

        return count

    def unlock_all_items_weeds(self):
            """Unlock all items and weeds by setting rank and tier to 999."""
            try:
                self.current_save / "Rank.json"
                data = self._load_json_file("Rank.json")
                data["Rank"] = 999
                data["Tier"] = 999
                self._save_json_file("Rank.json", data)
                return 1
            except Exception as e:
                raise RuntimeError(f"Failed to unlock items and weeds: {str(e)}")

    def unlock_all_properties(self):
        """Unlock all properties by downloading and updating property data."""
        try:
            properties_path = self.current_save / "Properties"
            
            with tempfile.TemporaryDirectory() as temp_dir:
                zip_path = Path(temp_dir) / "Properties.zip"
                extract_path = Path(temp_dir) / "extracted"
                extract_path.mkdir()
                
                urllib.request.urlretrieve(
                    "https://github.com/qwertyyuiopasdfghjklzxcvbnmqq/NPCs/raw/refs/heads/main/Properties.zip",
                    zip_path
                )
                
                with zipfile.ZipFile(zip_path, 'r') as zf:
                    zf.extractall(extract_path)
                
                extracted_props = extract_path / "Properties"
                if extracted_props.exists():
                    for prop_type in extracted_props.iterdir():
                        if prop_type.is_dir():
                            dst_dir = properties_path / prop_type.name
                            if not dst_dir.exists():
                                shutil.copytree(prop_type, dst_dir)
            
            updated = 0
            missing_template = {
                "DataType": "PropertyData",
                "DataVersion": 0,
                "GameVersion": "0.3.3f11",
                "PropertyCode": "",
                "IsOwned": True,
                "SwitchStates": [True, True, True, True],
                "ToggleableStates": [True, True]
            }
            
            for prop_type in properties_path.iterdir():
                if prop_type.is_dir():
                    json_path = prop_type / "Property.json"
                    if not json_path.exists():
                        template = missing_template.copy()
                        template["PropertyCode"] = prop_type.name.lower()
                        self._save_json_file(json_path.relative_to(self.current_save), template)
                        updated += 1
                    else:
                        data = self._load_json_file(json_path.relative_to(self.current_save))
                        data["IsOwned"] = True
                        for key in missing_template:
                            if key not in data:
                                data[key] = missing_template[key]
                        data["SwitchStates"] = [True, True, True, True]
                        data["ToggleableStates"] = [True, True]
                        self._save_json_file(json_path.relative_to(self.current_save), data)
                        updated += 1
            
            return updated
        except Exception as e:
            raise RuntimeError(f"Operation failed: {str(e)}")

    def unlock_all_businesses(self):
        """Unlock all businesses by downloading and updating business data."""
        try:
            businesses_path = self.current_save / "Businesses"
            
            with tempfile.TemporaryDirectory() as temp_dir:
                zip_path = Path(temp_dir) / "Businesses.zip"
                extract_path = Path(temp_dir) / "extracted"
                extract_path.mkdir()
                
                urllib.request.urlretrieve(
                    "https://github.com/qwertyyuiopasdfghjklzxcvbnmqq/NPCs/raw/refs/heads/main/Businesses.zip",
                    zip_path
                )
                
                with zipfile.ZipFile(zip_path, 'r') as zf:
                    zf.extractall(extract_path)
                
                extracted_bus = extract_path / "Businesses"
                if extracted_bus.exists():
                    for bus_type in extracted_bus.iterdir():
                        if bus_type.is_dir():
                            dst_dir = businesses_path / bus_type.name
                            if not dst_dir.exists():
                                shutil.copytree(bus_type, dst_dir)
            
            updated = 0
            missing_template = {
                "DataType": "BusinessData",
                "DataVersion": 0,
                "GameVersion": "0.3.3f11",
                "PropertyCode": "",
                "IsOwned": True,
                "SwitchStates": [True, True, True, True],
                "ToggleableStates": [True, True]
            }
            
            for bus_type in businesses_path.iterdir():
                if bus_type.is_dir():
                    json_path = bus_type / "Business.json"
                    if not json_path.exists():
                        template = missing_template.copy()
                        template["PropertyCode"] = bus_type.name.lower()
                        self._save_json_file(json_path.relative_to(self.current_save), template)
                        updated += 1
                    else:
                        data = self._load_json_file(json_path.relative_to(self.current_save))
                        data["IsOwned"] = True
                        for key in missing_template:
                            if key not in data:
                                data[key] = missing_template[key]
                        data["SwitchStates"] = [True, True, True, True]
                        data["ToggleableStates"] = [True, True]
                        self._save_json_file(json_path.relative_to(self.current_save), data)
                        updated += 1
            
            return updated
        except Exception as e:
            raise RuntimeError(f"Operation failed: {str(e)}")

    def generate_npc_files(self, npcs: list[tuple[str, str]]):
            """
            Generate NPC folders and JSON files in the NPCs directory of the current save.
            
            Args:
                npcs (list[tuple[str, str]]): List of (name, id) pairs for NPCs.
            
            Raises:
                ValueError: If no save is loaded.
            """
            if not self.current_save:
                raise ValueError("No save loaded")
            
            npcs_dir = self.current_save / "NPCs"
            if not npcs_dir.exists():
                npcs_dir.mkdir()

            for name, npc_id in npcs:
                folder_path = npcs_dir / name
                if not folder_path.exists():
                    folder_path.mkdir()

                # Define paths for JSON files
                npc_json_path = folder_path / "NPC.json"
                relationship_json_path = folder_path / "Relationship.json"

                # NPC.json data
                npc_data = {
                    "DataType": "NPCData",
                    "DataVersion": 0,
                    "GameVersion": "0.3.3f11",
                    "ID": npc_id
                }

                # Relationship.json data
                relationship_data = {
                    "DataType": "RelationshipData",
                    "DataVersion": 0,
                    "GameVersion": "0.3.3f11",
                    "RelationDelta": 999,
                    "Unlocked": True,
                    "UnlockType": 1
                }

                # Write NPC.json
                with open(npc_json_path, "w", encoding="utf-8") as f:
                    json.dump(npc_data, f, indent=4)

                # Write Relationship.json
                with open(relationship_json_path, "w", encoding="utf-8") as f:
                    json.dump(relationship_data, f, indent=4)

    def recruit_all_dealers(self):
        """Set 'Recruited' to true for all NPCs with 'DataType': 'DealerData'."""
        if not self.current_save:
            raise ValueError("No save loaded")
        
        npcs_dir = self.current_save / "NPCs"
        if not npcs_dir.exists():
            return 0  # No NPCs directory exists, so no dealers to recruit
        
        updated_count = 0
        for npc_folder in npcs_dir.iterdir():
            if npc_folder.is_dir():
                npc_json_path = npc_folder / "NPC.json"
                if npc_json_path.exists():
                    try:
                        with open(npc_json_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        # Check if NPC is a dealer and has a 'Recruited' field
                        if data.get("DataType") == "DealerData" and "Recruited" in data:
                            data["Recruited"] = True
                            with open(npc_json_path, 'w', encoding='utf-8') as f:
                                json.dump(data, f, indent=4)
                            updated_count += 1
                    except json.JSONDecodeError:
                        continue  # Skip malformed JSON files
        return updated_count

    def update_npc_relationships_function(self):
        """Update NPC relationships and recruit dealers using proper path handling and error reporting."""
        try:
            if not self.current_save:
                raise ValueError("No save loaded")

            npcs_dir = self.current_save / "NPCs"
            npcs_dir.mkdir(parents=True, exist_ok=True)

            # Download and extract NPC templates
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                zip_file = temp_path / "NPCs.zip"
                extract_path = temp_path / "extracted"
                
                # Download NPC template archive
                urllib.request.urlretrieve(
                    "https://github.com/qwertyyuiopasdfghjklzxcvbnmqq/NPCs/raw/refs/heads/main/NPCs.zip",
                    str(zip_file)
                )

                # Extract ZIP contents
                with zipfile.ZipFile(zip_file, 'r') as zf:
                    zf.extractall(str(extract_path))

                # Copy missing NPCs from template
                template_dir = extract_path / "NPCs"
                if not template_dir.exists():
                    raise FileNotFoundError("NPC template directory missing in archive")

                existing_npcs = {npc.name for npc in npcs_dir.iterdir() if npc.is_dir()}
                for npc_template in template_dir.iterdir():
                    if npc_template.is_dir() and npc_template.name not in existing_npcs:
                        shutil.copytree(npc_template, npcs_dir / npc_template.name)

            # Process all NPC relationships
            updated_count = 0
            for npc_folder in npcs_dir.iterdir():
                if not npc_folder.is_dir():
                    continue

                # Update Relationship.json
                relationship_file = npc_folder / "Relationship.json"
                if relationship_file.exists():
                    rel_data = self._load_json_file(relationship_file.relative_to(self.current_save))
                    rel_data.update({
                        "RelationDelta": 999,
                        "Unlocked": True,
                        "UnlockType": 1
                    })
                    self._save_json_file(relationship_file.relative_to(self.current_save), rel_data)
                    updated_count += 1

                # Update DealerData in NPC.json
                npc_file = npc_folder / "NPC.json"
                if npc_file.exists():
                    npc_data = self._load_json_file(npc_file.relative_to(self.current_save))
                    if npc_data.get("DataType") == "DealerData":
                        npc_data["Recruited"] = True
                        self._save_json_file(npc_file.relative_to(self.current_save), npc_data)

            return updated_count

        except Exception as e:
            raise RuntimeError(f"NPC relationship update failed: {str(e)}")

    def create_initial_backup(self):
        """Create an initial backup of the save folder if it doesn't exist."""
        if not self.backup_path.exists():
            shutil.copytree(self.current_save, self.backup_path)

    def create_feature_backup(self, feature_name: str, paths: list[Path]):
        """Create a timestamped backup for specific files or directories."""
        from datetime import datetime  # Ensure datetime is imported
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        backup_dir = self.feature_backups / feature_name / timestamp
        backup_dir.mkdir(parents=True, exist_ok=True)
        for path in paths:
            if path.is_file():
                rel_path = path.relative_to(self.current_save)
                dest = backup_dir / rel_path
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, dest)
            elif path.is_dir():
                rel_path = path.relative_to(self.current_save)
                dest = backup_dir / rel_path
                shutil.copytree(path, dest, dirs_exist_ok=True)

    def list_feature_backups(self) -> dict[str, list[str]]:
        """List all feature backups with their timestamps."""
        if not self.feature_backups.exists():
            return {}
        backups = {}
        for feature_dir in self.feature_backups.iterdir():
            if feature_dir.is_dir():
                timestamps = [d.name for d in feature_dir.iterdir() if d.is_dir()]
                if timestamps:
                    backups[feature_dir.name] = sorted(timestamps, reverse=True)
        return backups

    def revert_feature(self, feature: str, timestamp: str):
        """Revert a specific feature to a given backup timestamp."""
        backup_dir = self.feature_backups / feature / timestamp
        if not backup_dir.exists():
            raise FileNotFoundError(f"Backup not found: {backup_dir}")
        
        feature_dir = self.current_save / feature
        if feature_dir.exists():
            shutil.rmtree(feature_dir)  # Remove existing feature directory
        shutil.copytree(backup_dir / feature, feature_dir)  # Copy entire backup directory

    def revert_all_changes(self):
        """Revert all changes by restoring the initial backup."""
        if not self.backup_path.exists():
            raise FileNotFoundError("Initial backup not found")
        shutil.rmtree(self.current_save)
        shutil.copytree(self.backup_path, self.current_save)

    def remove_discovered_products(self, product_ids: list) -> list:
        products_path = self.current_save / "Products"
        products_json = products_path / "Products.json"
        if not products_json.exists():
            return []

        with open(products_json, 'r', encoding='utf-8') as f:
            data = json.load(f)

        discovered = data.get("DiscoveredProducts", [])
        removed = []
        for pid in product_ids:
            if pid in discovered:
                discovered.remove(pid)
                removed.append(pid)

        with open(products_json, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

        return removed

    def get_next_save_folder_name(self) -> str:
        if not hasattr(self, 'steamid_folder') or not self.steamid_folder:
            raise ValueError("Steam ID folder not found")
        
        # Get existing save numbers (ignoring backups)
        existing_nums = []
        for folder in self.steamid_folder.iterdir():
            if folder.is_dir() and re.fullmatch(r'SaveGame_[1-5]', folder.name):
                try:
                    num = int(folder.name.split('_')[1])
                    existing_nums.append(num)
                except (IndexError, ValueError):
                    continue

        # Check if all slots are full (1-5)
        if len(existing_nums) >= 5:
            return None

        # Find first available slot between 1-5
        for i in range(1, 6):
            if i not in existing_nums:
                return f"SaveGame_{i}"

        return None

class FeatureRevertDialog(QDialog):
    def __init__(self, parent=None, manager=None):
        super().__init__(parent)
        self.manager = manager
        self.setWindowTitle("Revert Changes")
        layout = QVBoxLayout()

        self.feature_combo = QComboBox()
        self.load_backup_options()
        layout.addWidget(self.feature_combo)

        revert_selected_btn = QPushButton("Revert Selected Feature")
        revert_selected_btn.clicked.connect(self.revert_selected)
        layout.addWidget(revert_selected_btn)

        revert_all_btn = QPushButton("Revert All Changes")
        revert_all_btn.clicked.connect(self.revert_all_changes)
        layout.addWidget(revert_all_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)

        self.setLayout(layout)
        self.setFixedWidth(350)

    def load_backup_options(self):
        backups = self.manager.list_feature_backups()
        for feature, timestamps in backups.items():
            if timestamps:
                latest = timestamps[0]
                display_text = f"{feature} ({datetime.strptime(latest, '%Y%m%d%H%M%S').strftime('%c')})"
                self.feature_combo.addItem(display_text, (feature, latest))

    def revert_selected(self):
        """Revert the selected feature to its latest backup."""
        if self.feature_combo.count() == 0:
            QMessageBox.warning(self, "No Backups", "No feature backups available to revert.")
            return
        feature, timestamp = self.feature_combo.currentData()
        reply = QMessageBox.warning(
            self,
            "Warning",
            "Reverting a single feature may lead to inconsistencies in your save file.\n"
            "It is recommended to use 'Revert All Changes' for a complete restoration.\n"
            "Do you want to proceed?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                self.main_window.manager.revert_feature(feature, timestamp)
                QMessageBox.information(self, "Success", f"Reverted {feature} to backup from {timestamp}")
                self.refresh_backup_list()  # Already present, ensures list updates
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to revert feature: {str(e)}")

    def revert_all_changes(self):
        reply = QMessageBox.question(self, "Confirm Revert",
                                     "This will revert ALL changes since the initial backup. Continue?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                self.manager.revert_all_changes()
                QMessageBox.information(self, "Success", "All changes reverted to initial backup.")
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to revert all changes: {str(e)}")

class MoneyTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QFormLayout()
        self.money_input = QLineEdit()
        self.money_input.setValidator(QRegularExpressionValidator(r"^\d{1,10}$"))
        self.networth_input = QLineEdit()
        self.networth_input.setValidator(QRegularExpressionValidator(r"^\d{1,10}$"))
        self.lifetime_earnings_input = QLineEdit()
        self.lifetime_earnings_input.setValidator(QRegularExpressionValidator(r"^\d{1,10}$"))
        self.weekly_deposit_sum_input = QLineEdit()
        self.weekly_deposit_sum_input.setValidator(QRegularExpressionValidator(r"^\d{1,10}$"))
        layout.addRow("Online Money:", self.money_input)
        layout.addRow("Networth:", self.networth_input)
        layout.addRow("Lifetime Earnings:", self.lifetime_earnings_input)
        layout.addRow("Weekly Deposit Sum:", self.weekly_deposit_sum_input)
        self.setLayout(layout)

    def set_data(self, info):
        self.money_input.setText(str(info.get("online_money", 0)))
        self.networth_input.setText(str(info.get("networth", 0)))
        self.lifetime_earnings_input.setText(str(info.get("lifetime_earnings", 0)))
        self.weekly_deposit_sum_input.setText(str(info.get("weekly_deposit_sum", 0)))

    def get_data(self):
        return {
            "online_money": int(self.money_input.text()),
            "networth": int(self.networth_input.text()),
            "lifetime_earnings": int(self.lifetime_earnings_input.text()),
            "weekly_deposit_sum": int(self.weekly_deposit_sum_input.text())
        }

class RankTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QFormLayout()
        self.rank_combo = QComboBox()
        self.rank_combo.addItems(["Street", "Dealer", "Supplier", "Distributor", "Kingpin"])
        self.rank_number_input = QLineEdit()
        self.rank_number_input.setValidator(QIntValidator(0, 100))
        self.tier_input = QLineEdit()
        self.tier_input.setValidator(QIntValidator(0, 100))
        layout.addRow("Current Rank:", self.rank_combo)
        layout.addRow("Rank Number:", self.rank_number_input)
        layout.addRow("Tier:", self.tier_input)
        self.setLayout(layout)

    def set_data(self, info):
        self.rank_combo.setCurrentText(info.get("current_rank", "Street"))
        self.rank_number_input.setText(str(info.get("rank_number", 0)))
        self.tier_input.setText(str(info.get("tier", 0)))

    def get_data(self):
        return {
            "current_rank": self.rank_combo.currentText(),
            "rank_number": int(self.rank_number_input.text()),
            "tier": int(self.tier_input.text())
        }

class PropertiesTab(QWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        layout = QVBoxLayout()
        
        # Create form layout for input fields
        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(8)
        form_layout.setHorizontalSpacing(15)
        form_layout.setContentsMargins(5, 5, 5, 10)

        # Property Type Selection
        self.property_combo = QComboBox()
        form_layout.addRow(QLabel("Property Type:"), self.property_combo)

        # Quantity Input
        self.quantity_edit = QLineEdit()
        self.quantity_edit.setValidator(QIntValidator(0, 1000000))
        self.quantity_edit.setFixedHeight(28)
        form_layout.addRow(QLabel("Quantity:"), self.quantity_edit)

        # Quality Selection
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["Trash", "Poor", "Standard", "Premium", "Heavenly"])
        self.quality_combo.setFixedHeight(28)
        form_layout.addRow(QLabel("Quality:"), self.quality_combo)

        # Packaging Selection
        self.packaging_combo = QComboBox()
        self.packaging_combo.addItems(["none", "baggie", "jar"])
        self.packaging_combo.setFixedHeight(28)
        form_layout.addRow(QLabel("Packaging:"), self.packaging_combo)

        # Update Type Selection
        self.update_combo = QComboBox()
        self.update_combo.addItems(["both", "weed", "item"])
        self.update_combo.setFixedHeight(28)
        form_layout.addRow(QLabel("Update Type:"), self.update_combo)

        layout.addLayout(form_layout)
        
        # Update Button with connection
        self.update_btn = QPushButton("Update Properties")
        self.update_btn.setFixedHeight(32)
        self.update_btn.clicked.connect(self.update_properties)  # Added connection
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.update_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        self.setLayout(layout)
        
        self.load_property_types()

    def load_property_types(self):
        self.property_combo.clear()
        try:
            if not self.main_window or not self.main_window.manager.current_save:
                return

            properties_path = self.main_window.manager.current_save / "Properties"
            if not properties_path.exists():
                return

            dirs = [d.name for d in properties_path.iterdir() if d.is_dir()]
            
            dir_mapping = {
                "barn": "Barn",
                "bungalow": "Bungalow", 
                "motel": "Motel Room",
                "sweatshop": "Sweatshop",
                "rv": "RV",
                "warehouse": "Docks Warehouse"
            }
            
            # Add "all" option first
            self.property_combo.addItem("all", "all")
            
            # Process each directory
            for dir_name in dirs:
                normalized = dir_name.strip().lower()
                display_name = dir_mapping.get(normalized, dir_name)  # Use original if not mapped
                self.property_combo.addItem(display_name, dir_name)
                
            # Sort the combo box items alphabetically, excluding "all"
            self.property_combo.model().sort(0)
                
        except Exception as e:
            print(f"Error loading properties: {str(e)}")
            self.property_combo.addItem("Error loading properties", "error")

    def update_properties(self):
        if not self.main_window or not self.main_window.manager.current_save:
            QMessageBox.critical(self, "Error", "No save file loaded")
            return
        try:
            property_type = self.property_combo.currentData()
            quantity = int(self.quantity_edit.text())
            packaging = self.packaging_combo.currentText()
            update_type = self.update_combo.currentText()
            quality = self.quality_combo.currentText()

            # Backup properties
            properties_path = self.main_window.manager.current_save / "Properties"
            self.main_window.manager.create_feature_backup("Properties", [properties_path])

            updated = self.main_window.manager.update_property_quantities(
                property_type, quantity, packaging, update_type, quality
            )
            self.main_window.backups_tab.refresh_backup_list()
            QMessageBox.information(self, "Success", f"Updated {updated} property locations")
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid quantity")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update properties: {str(e)}")

class ProductsTab(QWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # **Discovery Section**
        discovery_group = QGroupBox("Product Discovery")
        discovery_layout = QVBoxLayout()
        discovery_layout.setContentsMargins(10, 10, 10, 10)

        # Instruction label
        discovery_layout.addWidget(QLabel("Select products:"))

        # Checkboxes for product selection
        self.discover_cocaine_checkbox = QCheckBox("Cocaine")
        self.discover_meth_checkbox = QCheckBox("Meth")
        discovery_layout.addWidget(self.discover_cocaine_checkbox)
        discovery_layout.addWidget(self.discover_meth_checkbox)
        discovery_layout.addSpacing(5)

        # Horizontal layout for buttons
        buttons_layout = QHBoxLayout()

        # Discover button
        discover_button = QPushButton("Discover Selected")
        discover_button.setFixedHeight(32)
        discover_button.clicked.connect(self.discover_selected_products)
        buttons_layout.addWidget(discover_button)

        # Undiscover button
        undiscover_button = QPushButton("Undiscover Selected")
        undiscover_button.setFixedHeight(32)
        undiscover_button.clicked.connect(self.undiscover_selected_products)
        buttons_layout.addWidget(undiscover_button)

        discovery_layout.addLayout(buttons_layout)
        discovery_layout.addStretch()
        discovery_group.setLayout(discovery_layout)

        # **Generation Section**
        generation_group = QGroupBox("Product Generation")
        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(8)
        form_layout.setHorizontalSpacing(15)
        form_layout.setContentsMargins(10, 10, 10, 10)

        self.count_input = QLineEdit()
        self.count_input.setValidator(QIntValidator(1, 1000))
        self.count_input.setFixedHeight(28)

        self.id_length_input = QLineEdit()
        self.id_length_input.setValidator(QIntValidator(5, 20))
        self.id_length_input.setFixedHeight(28)

        self.price_input = QLineEdit()
        self.price_input.setValidator(QIntValidator(1, 1000000))
        self.price_input.setFixedHeight(28)

        form_layout.addRow("Number of Products:", self.count_input)
        form_layout.addRow("ID Length:", self.id_length_input)
        form_layout.addRow("Price ($):", self.price_input)

        self.add_to_listed_checkbox = QCheckBox("Add to Listed Products")
        form_layout.addRow("", self.add_to_listed_checkbox)

        generation_group.setLayout(form_layout)

        # **Buttons for Generation**
        button_layout = QHBoxLayout()
        generate_button = QPushButton("Generate Products")
        generate_button.setFixedHeight(32)
        generate_button.clicked.connect(self.generate_products)

        reset_button = QPushButton("Reset Products")
        reset_button.setFixedHeight(32)
        reset_button.clicked.connect(self.delete_generated_products)

        button_layout.addStretch()
        button_layout.addWidget(generate_button)
        button_layout.addWidget(reset_button)
        button_layout.addStretch()

        # Assemble main layout
        layout.addWidget(discovery_group)
        layout.addWidget(generation_group)
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def discover_selected_products(self):
        """Handle the discovery of selected products."""
        if not self.main_window or not hasattr(self.main_window, 'manager'):
            QMessageBox.critical(self, "Error", "Save manager not available.")
            return

        products_to_discover = []
        if self.discover_cocaine_checkbox.isChecked():
            products_to_discover.append("cocaine")
        if self.discover_meth_checkbox.isChecked():
            products_to_discover.append("meth")

        if not products_to_discover:
            QMessageBox.warning(self, "No Selection", "Please select at least one product to discover.")
            return

        try:
            # Create backup before modification
            products_path = self.main_window.manager.current_save / "Products"
            self.main_window.manager.create_feature_backup("Products", [products_path])
            self.main_window.backups_tab.refresh_backup_list()

            self.main_window.manager.add_discovered_products(products_to_discover)
            QMessageBox.information(self, "Success", "Successfully discovered selected products!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to discover products: {str(e)}")

    def undiscover_selected_products(self):
        """Handle the undiscovery of selected products."""
        if not self.main_window or not hasattr(self.main_window, 'manager'):
            QMessageBox.critical(self, "Error", "Save manager not available.")
            return

        products_to_undiscover = []
        if self.discover_cocaine_checkbox.isChecked():
            products_to_undiscover.append("cocaine")
        if self.discover_meth_checkbox.isChecked():
            products_to_undiscover.append("meth")

        if not products_to_undiscover:
            QMessageBox.warning(self, "No Selection", "Please select at least one product to undiscover.")
            return

        try:
            # Create backup before modification
            products_path = self.main_window.manager.current_save / "Products"
            self.main_window.manager.create_feature_backup("Products", [products_path])
            self.main_window.backups_tab.refresh_backup_list()

            removed = self.main_window.manager.remove_discovered_products(products_to_undiscover)
            if removed:
                QMessageBox.information(self, "Success", f"Successfully undiscovered: {', '.join(removed)}")
            else:
                QMessageBox.information(self, "Info", "No selected products were discovered.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to undiscover products: {str(e)}")

    def generate_products(self):
        if not self.main_window or not hasattr(self.main_window, 'manager'):
            QMessageBox.critical(self, "Error", "Save manager not available.")
            return
        try:
            count = int(self.count_input.text())
            id_length = int(self.id_length_input.text())
            price = int(self.price_input.text())
            add_to_listed = self.add_to_listed_checkbox.isChecked()

            # Backup products
            products_path = self.main_window.manager.current_save / "Products"
            self.main_window.manager.create_feature_backup("Products", [products_path])
            self.main_window.backups_tab.refresh_backup_list()  # Add this line

            self.main_window.manager.generate_products(count, id_length, price, add_to_listed)
            QMessageBox.information(self, "Success", f"Generated {count} products successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate products: {str(e)}")

    def delete_generated_products(self):
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "This will delete all generated products and remove them from all lists. Continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                products_path = self.main_window.manager.current_save / "Products"
                created_path = products_path / "CreatedProducts"
                products_json = products_path / "Products.json"
                
                if not created_path.exists():
                    QMessageBox.information(self, "Info", "No generated products to delete.")
                    return
                
                generated_ids = [f.stem for f in created_path.glob("*.json") if f.is_file()]
                
                if not generated_ids:
                    QMessageBox.information(self, "Info", "No generated products to delete.")
                    return
                
                if products_json.exists():
                    with open(products_json, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                else:
                    data = {"DiscoveredProducts": [], "ListedProducts": [], "MixRecipes": [], "ProductPrices": []}
                
                data["DiscoveredProducts"] = [pid for pid in data.get("DiscoveredProducts", []) if pid not in generated_ids]
                data["ListedProducts"] = [pid for pid in data.get("ListedProducts", []) if pid not in generated_ids]
                data["MixRecipes"] = [recipe for recipe in data.get("MixRecipes", []) if recipe.get("Output") not in generated_ids]
                data["ProductPrices"] = [price for price in data.get("ProductPrices", []) if price.get("String") not in generated_ids]
                
                with open(products_json, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4)
                
                for file_path in created_path.glob("*.json"):
                    file_path.unlink()
                
                QMessageBox.information(self, "Success", f"Deleted {len(generated_ids)} generated products.")
            
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Deletion failed: {str(e)}")

class UnlocksTab(QWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # Unlock Actions Group
        unlock_group = QGroupBox("Unlock Actions")
        unlock_layout = QVBoxLayout()
        unlock_layout.setContentsMargins(10, 10, 10, 10)
        unlock_layout.setSpacing(10)

        # Items and Weeds Section
        items_weeds_btn = QPushButton("Unlock All Items and Weeds")
        items_weeds_btn.setFixedHeight(32)
        items_weeds_btn.clicked.connect(self.unlock_items_weeds)
        unlock_layout.addWidget(QLabel("Sets Rank & tier To 999 To Unlock All Items/Weeds:"))
        unlock_layout.addWidget(items_weeds_btn)
        unlock_layout.addSpacing(10)

        # Properties Section
        props_btn = QPushButton("Unlock All Properties")
        props_btn.setFixedHeight(32)
        props_btn.clicked.connect(self.unlock_properties)
        unlock_layout.addWidget(QLabel("Downloads & Enables All Property Types:"))
        unlock_layout.addWidget(props_btn)
        unlock_layout.addSpacing(10)

        # Businesses Section
        business_btn = QPushButton("Unlock All Businesses")
        business_btn.setFixedHeight(32)
        business_btn.clicked.connect(self.unlock_businesses)
        unlock_layout.addWidget(QLabel("Downloads & Enables All Business Types:"))
        unlock_layout.addWidget(business_btn)

        # Add NPC Relationships Section
        npc_relation_btn = QPushButton("Unlock All NPCs")
        npc_relation_btn.setFixedHeight(32)
        npc_relation_btn.clicked.connect(self.update_npc_relationships)
        unlock_layout.addWidget(QLabel("Downloads & Updates All NPCs:"))
        unlock_layout.addWidget(npc_relation_btn)
        unlock_layout.addSpacing(10)

        unlock_group.setLayout(unlock_layout)
        layout.addWidget(unlock_group)
        layout.addStretch()
        self.setLayout(layout)

    def unlock_items_weeds(self):
        """Handle the unlock items and weeds button click."""
        try:
            if not self.main_window or not self.main_window.manager.current_save:
                QMessageBox.critical(self, "Error", "No save file loaded")
                return
            
            # Backup Rank.json
            rank_path = self.main_window.manager.current_save / "Rank.json"
            self.main_window.manager.create_feature_backup("ItemsWeeds", [rank_path])
            self.main_window.backups_tab.refresh_backup_list()
            
            result = self.main_window.manager.unlock_all_items_weeds()
            if result == 1:
                QMessageBox.information(self, "Success", "Unlocked all items and weeds!")
            else:
                QMessageBox.warning(self, "Warning", "Failed to unlock items and weeds.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to unlock items and weeds: {str(e)}")

    def unlock_properties(self):
        try:
            if not self.main_window or not self.main_window.manager.current_save:
                QMessageBox.critical(self, "Error", "No save file loaded")
                return

            # Backup properties
            properties_path = self.main_window.manager.current_save / "Properties"
            self.main_window.manager.create_feature_backup("Properties", [properties_path])
            self.main_window.backups_tab.refresh_backup_list()  # Add this line

            updated = self.main_window.manager.unlock_all_properties()
            QMessageBox.information(self, "Success", f"Unlocked {updated} properties!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to unlock properties: {str(e)}")

    def unlock_businesses(self):
        """Handle the unlock businesses button click."""
        try:
            if not self.main_window or not self.main_window.manager.current_save:
                QMessageBox.critical(self, "Error", "No save file loaded")
                return
            
            # Backup businesses
            businesses_path = self.main_window.manager.current_save / "Businesses"
            self.main_window.manager.create_feature_backup("Businesses", [businesses_path])
            
            updated = self.main_window.manager.unlock_all_businesses()
            self.main_window.backups_tab.refresh_backup_list()
            QMessageBox.information(self, "Success", f"Unlocked {updated} businesses!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to unlock businesses: {str(e)}")

    def update_npc_relationships(self):
        try:
            if not self.main_window.manager.current_save:
                QMessageBox.critical(self, "Error", "No save file loaded")
                return
            
            # Backup NPCs
            npcs_path = self.main_window.manager.current_save / "NPCs"
            self.main_window.manager.create_feature_backup("NPCs", [npcs_path])
            
            updated = self.main_window.manager.update_npc_relationships_function()
            self.main_window.backups_tab.refresh_backup_list()
            QMessageBox.information(
                self, "Success",
                f"Updated relationships for {updated} NPCs and recruited dealers!"
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Error",
                f"Failed to update NPC relationships:\n{str(e)}"
            )

class MiscTab(QWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # Organisation Name Section
        org_group = QGroupBox("Organization Settings")
        org_layout = QFormLayout()
        org_layout.setContentsMargins(10, 10, 10, 10)
        self.organisation_name_input = QLineEdit()
        org_layout.addRow(QLabel("Organization Name:"), self.organisation_name_input)
        org_group.setLayout(org_layout)
        layout.addWidget(org_group)

        # Quests Section
        quests_group = QGroupBox("Quest Management")
        quests_layout = QVBoxLayout()
        quests_layout.setContentsMargins(10, 10, 10, 10)
        quests_layout.addWidget(QLabel("WARNING: This will mark all quests and objectives as completed"))
        self.complete_quests_btn = QPushButton("Complete All Quests")
        self.complete_quests_btn.setFixedHeight(32)
        self.complete_quests_btn.clicked.connect(self.complete_all_quests)
        quests_layout.addWidget(self.complete_quests_btn)
        quests_group.setLayout(quests_layout)
        layout.addWidget(quests_group)

        # Variables Section
        vars_group = QGroupBox("Variable Management")
        vars_layout = QVBoxLayout()
        vars_layout.setContentsMargins(10, 10, 10, 10)
        self.vars_warning_label = QLabel()
        vars_layout.addWidget(self.vars_warning_label)
        self.vars_btn = QPushButton("Modify All Variables")
        self.vars_btn.setFixedHeight(32)
        self.vars_btn.clicked.connect(self.modify_variables)
        vars_layout.addWidget(self.vars_btn)
        vars_group.setLayout(vars_layout)
        layout.addWidget(vars_group)

        # Mod Installation Section
        mod_group = QGroupBox("Achievement Unlocker")
        mod_layout = QVBoxLayout()
        mod_layout.setContentsMargins(10, 10, 10, 10)
        mod_layout.addWidget(QLabel("WARNING: This unlock all the achievements in the game when you start up Schedule 1"))
        self.install_mod_btn = QPushButton("Install AchievementUnlocker Mod")
        self.install_mod_btn.setFixedHeight(32)
        self.install_mod_btn.clicked.connect(self.install_mod)
        mod_layout.addWidget(self.install_mod_btn)
        mod_group.setLayout(mod_layout)
        layout.addWidget(mod_group)

        # New Save Generation Section
        new_save_group = QGroupBox("New Save Generation")
        new_save_layout = QFormLayout()
        new_save_layout.setContentsMargins(10, 10, 10, 10)
        self.new_org_name_input = QLineEdit()
        new_save_layout.addRow(QLabel("New Organization Name:"), self.new_org_name_input)
        self.generate_save_btn = QPushButton("Generate New Save Folder")
        self.generate_save_btn.setFixedHeight(32)
        self.generate_save_btn.clicked.connect(self.generate_new_save)
        new_save_layout.addRow(self.generate_save_btn)
        new_save_group.setLayout(new_save_layout)
        layout.addWidget(new_save_group)

        layout.addStretch()
        self.setLayout(layout)
        self.vars_warning_label.setText("WARNING: Modifies variables in:\n- Variables/\n- Players/Player_*/Variables/")

    def set_data(self, info):
        """Populate the input field with data from the info dictionary."""
        self.organisation_name_input.setText(info.get("organisation_name", ""))

    def get_data(self):
        """Retrieve data from the input field."""
        return {
            "organisation_name": self.organisation_name_input.text()
        }

    def complete_all_quests(self):
        if not self.main_window or not self.main_window.manager.current_save:
            QMessageBox.critical(self, "Error", "No save file loaded")
            return
        try:
            # Backup quests
            quests_path = self.main_window.manager.current_save / "Quests"
            self.main_window.manager.create_feature_backup("Quests", [quests_path])

            quests_completed, objectives_completed = self.main_window.manager.complete_all_quests()
            self.main_window.backups_tab.refresh_backup_list()
            QMessageBox.information(self, "Quests Completed",
                                    f"Marked {quests_completed} quests and {objectives_completed} objectives as completed!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to complete quests: {str(e)}")

    def modify_variables(self):
        if not hasattr(self, 'main_window') or not self.main_window.manager.current_save:
            QMessageBox.critical(self, "Error", "No save file loaded")
            return
        try:
            # Backup variables
            variables_paths = [self.main_window.manager.current_save / "Variables"]
            for i in range(10):
                player_vars = self.main_window.manager.current_save / f"Players/Player_{i}/Variables"
                if player_vars.exists():
                    variables_paths.append(player_vars)
            self.main_window.manager.create_feature_backup("Variables", variables_paths)

            count = self.main_window.manager.modify_variables()
            self.main_window.backups_tab.refresh_backup_list()
            QMessageBox.information(self, "Variables Modified",
                                    f"Successfully updated {count} variables!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to modify variables: {str(e)}")

    def update_vars_warning(self):
        """Update the variables warning message with detected player directories."""
        if not self.main_window or not self.main_window.manager.current_save:
            return  # No save loaded

        players_path = self.main_window.manager.current_save / "Players"
        player_dirs = []
        # Check for Player_0 to Player_9
        for i in range(10):
            dir_path = players_path / f"Player_{i}"
            if dir_path.exists():
                player_dirs.append(f"Player_{i}")

        # Build the warning message lines
        lines = ["- Variables/"]
        if player_dirs:
            for dir_name in player_dirs:
                lines.append(f"- Players/{dir_name}/Variables/")
        else:
            lines.append("- Players/Player_*/Variables/ (no player directories found)")

        warning_text = "WARNING: Modifies variables in:\n" + "\n".join(lines)
        self.vars_warning_label.setText(warning_text)

    def install_mod(self):
            """
            Download AchievementUnlocker.dll and place it in the game's Mods folder.
            Checks for MelonLoader and prompts the user if it's not installed.
            """
            if not self.main_window or not self.main_window.manager.current_save:
                QMessageBox.critical(self, "Error", "No save file loaded")
                return

            game_dir = find_game_directory()
            if not game_dir:
                QMessageBox.critical(self, "Error", "Could not find Schedule I installation directory.")
                return

            mods_dir = game_dir / "Mods"
            if not mods_dir.exists():
                QMessageBox.warning(
                    self,
                    "MelonLoader Not Installed",
                    "MelonLoader is required to use mods but is not installed.\n"
                    "Please download and install MelonLoader from https://melonwiki.xyz/\n"
                    "and run the game once to create the Mods folder."
                )
                return

            dll_url = "https://github.com/qwertyyuiopasdfghjklzxcvbnmqq/NPCs/raw/refs/heads/main/AchievementUnlocker.dll"
            dll_path = mods_dir / "AchievementUnlocker.dll"

            if dll_path.exists():
                reply = QMessageBox.question(
                    self,
                    "File Exists",
                    "AchievementUnlocker.dll already exists in the Mods folder. Overwrite?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return

            try:
                urllib.request.urlretrieve(dll_url, dll_path)
                QMessageBox.information(
                    self,
                    "Success",
                    "AchievementUnlocker.dll has been successfully installed to the Mods folder!"
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to install mod: {str(e)}")

    def generate_new_save(self):
        new_org_name = self.new_org_name_input.text().strip()
        if not new_org_name:
            QMessageBox.warning(self, "Invalid Input", "Please enter an organization name for the new save.")
            return
        
        try:
            next_save_name = self.main_window.manager.get_next_save_folder_name()
            if not next_save_name:
                QMessageBox.warning(
                    self,
                    "Maximum Saves Reached",
                    "You have reached the maximum of 5 save slots.\n"
                    "Please delete an existing save folder before creating a new one.",
                    QMessageBox.Ok
                )
                return
            
            new_save_path = self.main_window.manager.steamid_folder / next_save_name
            
            with tempfile.TemporaryDirectory() as temp_dir:
                zip_path = Path(temp_dir) / "SaveGame_1.zip"
                urllib.request.urlretrieve(
                    "https://github.com/qwertyyuiopasdfghjklzxcvbnmqq/NPCs/raw/refs/heads/main/SaveGame_1.zip",
                    zip_path
                )
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    for member in zip_ref.namelist():
                        if member.endswith('/'):
                            continue
                        relative_path = Path(member).relative_to('SaveGame_1')
                        target_path = new_save_path / relative_path
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        with zip_ref.open(member) as source, open(target_path, 'wb') as target:
                            target.write(source.read())
            
            game_json_path = new_save_path / "Game.json"
            if game_json_path.exists():
                with open(game_json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                data["OrganisationName"] = new_org_name
                with open(game_json_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4)
            else:
                raise FileNotFoundError("Game.json not found in the new save folder")
            
            QMessageBox.information(
                self,
                "Success",
                f"New save folder '{next_save_name}' created with organization name '{new_org_name}'.\n"
                "Return to the save selection page to load it."
            )
            # Refresh the save selection list
            self.main_window.populate_save_table()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate new save folder: {str(e)}")
 
class NPCsTab(QWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        layout = QVBoxLayout()

        # Text area for pasting the log
        self.log_text = QTextEdit()
        self.log_text.setPlaceholderText("Paste the NPC log here...")
        layout.addWidget(self.log_text)

        # Button to generate files
        generate_button = QPushButton("Generate NPC Files")
        generate_button.clicked.connect(self.generate_npc_files)
        layout.addWidget(generate_button)

        # Button to recruit all dealers
        recruit_button = QPushButton("Recruit  All Dealers")
        recruit_button.clicked.connect(self.recruit_all_dealers)
        layout.addWidget(recruit_button)

        self.setLayout(layout)

    def generate_npc_files(self):
        """Handle the generate button click."""
        log_text = self.log_text.toPlainText()
        if not log_text:
            QMessageBox.warning(self, "No Log", "Please paste the NPC log.")
            return

        npcs = parse_npc_log(log_text)
        if not npcs:
            QMessageBox.warning(self, "No NPCs", "No NPCs found in the log.")
            return

        try:
            self.main_window.manager.generate_npc_files(npcs)
            QMessageBox.information(self, "Success", f"Generated files for {len(npcs)} NPCs.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate NPC files: {str(e)}")

    def recruit_all_dealers(self):
        """Handle the recruit all dealers button click."""
        reply = QMessageBox.question(
            self,
            "Confirm",
            "This will set 'Recruited' to true for all dealers. Continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if not self.main_window or not self.main_window.manager.current_save:
                QMessageBox.critical(self, "Error", "No save file loaded")
                return
            try:
                updated = self.main_window.manager.recruit_all_dealers()
                QMessageBox.information(self, "Success", f"Recruited {updated} dealers!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to recruit dealers: {str(e)}")

class BackupsTab(QWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # Revert Changes Section
        revert_group = QGroupBox("Revert Changes")
        revert_layout = QVBoxLayout()
        revert_layout.setContentsMargins(10, 10, 10, 10)

        self.feature_combo = QComboBox()
        self.refresh_backup_list()  # Load backups initially
        revert_layout.addWidget(self.feature_combo)

        revert_selected_btn = QPushButton("Revert Selected Feature")
        revert_selected_btn.clicked.connect(self.revert_selected)
        revert_layout.addWidget(revert_selected_btn)

        revert_all_btn = QPushButton("Revert All Changes")
        revert_all_btn.clicked.connect(self.revert_all_changes)
        revert_layout.addWidget(revert_all_btn)

        revert_group.setLayout(revert_layout)
        layout.addWidget(revert_group)

        # Delete Backups Section
        delete_group = QGroupBox("Delete Backups")
        delete_layout = QVBoxLayout()
        delete_layout.setContentsMargins(10, 10, 10, 10)
        delete_all_btn = QPushButton("Delete All Backups")
        delete_all_btn.clicked.connect(self.delete_all_backups)
        delete_layout.addWidget(delete_all_btn)
        delete_group.setLayout(delete_layout)
        layout.addWidget(delete_group)

        layout.addStretch()
        self.setLayout(layout)

    def refresh_backup_list(self):
        """Refresh the list of available backups in the combo box."""
        self.feature_combo.clear()
        if not self.main_window or not self.main_window.manager.current_save:
            return
        backups = self.main_window.manager.list_feature_backups()
        for feature, timestamps in backups.items():
            if timestamps:
                latest = timestamps[0]
                display_text = f"{feature} ({datetime.strptime(latest, '%Y%m%d%H%M%S').strftime('%c')})"
                self.feature_combo.addItem(display_text, (feature, latest))

    def revert_selected(self):
        """Revert the selected feature to its latest backup."""
        if self.feature_combo.count() == 0:
            QMessageBox.warning(self, "No Backups", "No feature backups available to revert.")
            return
        feature, timestamp = self.feature_combo.currentData()
        try:
            self.main_window.manager.revert_feature(feature, timestamp)
            QMessageBox.information(self, "Success", f"Reverted {feature} to backup from {timestamp}")
            self.refresh_backup_list()  # Refresh after reverting
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to revert feature: {str(e)}")

    def revert_all_changes(self):
        """Revert all changes to the initial backup."""
        reply = QMessageBox.question(self, "Confirm Revert",
                                     "This will revert ALL changes since the initial backup. Continue?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                self.main_window.manager.revert_all_changes()
                QMessageBox.information(self, "Success", "All changes reverted to initial backup.")
                self.refresh_backup_list()  # Refresh after reverting
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to revert all changes: {str(e)}")

    def delete_all_backups(self):
        """Delete all backups for the current save."""
        if not self.main_window or not self.main_window.manager.current_save:
            QMessageBox.critical(self, "Error", "No save file loaded")
            return
        reply = QMessageBox.question(self, "Confirm Delete",
                                     "Delete all backups for this save?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                shutil.rmtree(self.main_window.manager.backup_path)
                QMessageBox.information(self, "Success", "All backups deleted successfully")
                self.refresh_backup_list()  # Refresh after deletion
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete backups: {str(e)}")

class SaveEditorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Schedule I Save Editor")
        self.setGeometry(100, 100, 800, 600)
        self.manager = SaveManager()  # Assume SaveManager is defined elsewhere
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Create pages
        self.save_selection_page = self.create_save_selection_page()
        self.save_info_page = self.create_save_info_page()
        self.edit_save_page = self.create_edit_save_page()

        # Add pages to stacked widget
        self.stacked_widget.addWidget(self.save_selection_page)
        self.stacked_widget.addWidget(self.save_info_page)
        self.stacked_widget.addWidget(self.edit_save_page)

        # Populate the save table initially and set the initial page
        self.populate_save_table()
        self.stacked_widget.setCurrentWidget(self.save_selection_page)

        # Apply dark theme
        self.apply_dark_theme()

    def apply_dark_theme(self):
        """Apply a dark theme to the application."""
        dark_stylesheet = """
        QWidget {
            background-color: #2b2b2b;
            color: #ffffff;
            font-family: Arial;
        }
        QTableWidget {
            background-color: #3c3f41;
            color: #ffffff;
            gridline-color: #555555;
        }
        QHeaderView::section {
            background-color: #3c3f41; /* Changed to match organization names box */
            color: #ffffff;
            border: 1px solid #555555;
            padding: 4px;
        }
        QTableWidget::item {
            background-color: #3c3f41;
            color: #ffffff;
        }
        QTableWidget::item:selected {
            background-color: #5c5f61;
            color: #ffffff;
        }
        QPushButton {
            background-color: #3c3f41;
            border: 1px solid #555555;
            padding: 5px;
            border-radius: 3px;
        }
        QPushButton:hover {
            background-color: #4c4f51;
        }
        QLineEdit, QComboBox, QTableWidget, QCheckBox {
            background-color: #3c3f41;
            border: 1px solid #555555;
            padding: 3px;
            border-radius: 2px;
        }
        QTabWidget::pane {
            border: 1px solid #555555;
            background-color: #2b2b2b;
        }
        QTabBar::tab {
            background: #3c3f41;
            color: #ffffff;
            padding: 5px;
            border: 1px solid #555555;
            border-bottom: none;
        }
        QTabBar::tab:selected {
            background: #4c4f51;
        }
        QGroupBox {
            border: 1px solid #555555;
            margin-top: 10px;
            padding-top: 15px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 3px;
        }
        """
        self.setStyleSheet(dark_stylesheet)
        # Add this line to force Fusion style which handles dark themes better
        QApplication.setStyle("Fusion")

    def create_save_selection_page(self):
        """Create the save selection page with a table and load button."""
        page = QWidget()
        layout = QVBoxLayout()

        # Setup save table
        self.save_table = QTableWidget()
        self.save_table.setColumnCount(2)
        self.save_table.setHorizontalHeaderLabels(["Organization Names", "Save Folders"])
        self.save_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.save_table.setSelectionMode(QTableWidget.SingleSelection)
        
        # Set header styling
        self.save_table.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color: #3c3f41;
                color: #ffffff;
                border: 1px solid #555555;
                font-weight: normal;
            }
        """)
        
        # Set table item styling
        self.save_table.setStyleSheet("""
            QTableWidget {
                background-color: #3c3f41;
                color: #ffffff;
                gridline-color: #555555;
                font-weight: normal;
            }
            QTableWidget::item {
                border: 1px solid #555555;
                padding: 4px;
            }
            QTableWidget::item:selected {
                background-color: #5c5f61;
                color: #ffffff;
                font-weight: normal;
            }
        """)
        
        # Configure header resize behavior
        self.save_table.horizontalHeader().setStretchLastSection(True)
        self.save_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)

        # Disable cell editing and cell selection
        self.save_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.save_table.setFocusPolicy(Qt.NoFocus)
        self.save_table.setSelectionMode(QTableWidget.SingleSelection)
        self.save_table.setSelectionBehavior(QTableWidget.SelectRows)

        # Load button
        load_button = QPushButton("Load Selected Save")
        load_button.clicked.connect(self.load_selected_save)

        # Add widgets to layout
        layout.addWidget(self.save_table)
        layout.addWidget(load_button)
        page.setLayout(layout)
        return page

    def populate_save_table(self):
        """Populate the save table with data from save folders."""
        saves = self.manager.get_save_folders()
        self.save_table.setRowCount(len(saves))
        for row, save in enumerate(saves):
            # Organization name item
            org_item = QTableWidgetItem(save['organisation_name'])
            org_item.setFlags(org_item.flags() & ~Qt.ItemIsEditable)
            org_item.setData(Qt.UserRole, save['path'])
            
            # Save folder name item
            folder_item = QTableWidgetItem(save['name'])
            folder_item.setFlags(folder_item.flags() & ~Qt.ItemIsEditable)

            # Add items to table
            self.save_table.setItem(row, 0, org_item)
            self.save_table.setItem(row, 1, folder_item)
        
        self.save_table.resizeColumnsToContents()

    def load_selected_save(self):
        """Load the selected save and switch to the save info page."""
        selected_items = self.save_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a save to load.")
            return
        row = selected_items[0].row()
        save_path = self.save_table.item(row, 0).data(Qt.UserRole)
        if self.manager.load_save(save_path):
            self.update_save_info_page()
            self.stacked_widget.setCurrentWidget(self.save_info_page)
        else:
            QMessageBox.critical(self, "Load Failed", "Failed to load the selected save.")

    def create_save_info_page(self):
        """Create the save info page with save details and navigation buttons."""
        page = QWidget()
        layout = QFormLayout()

        # Labels for save info
        self.game_version_label = QLabel()
        self.creation_date_label = QLabel()
        self.org_name_label = QLabel()
        self.online_money_label = QLabel()
        self.networth_label = QLabel()
        self.lifetime_earnings_label = QLabel()
        self.weekly_deposit_sum_label = QLabel()
        self.rank_label = QLabel()
        self.play_time_label = QLabel()

        # Add labels to layout
        layout.addRow("Game Version:", self.game_version_label)
        layout.addRow("Creation Date:", self.creation_date_label)
        layout.addRow("Organization Name:", self.org_name_label)
        layout.addRow("Online Money:", self.online_money_label)
        layout.addRow("Networth:", self.networth_label)
        layout.addRow("Lifetime Earnings:", self.lifetime_earnings_label)
        layout.addRow("Weekly Deposit Sum:", self.weekly_deposit_sum_label)
        layout.addRow("Rank:", self.rank_label)

        # Button layout
        button_layout = QHBoxLayout()
        back_button = QPushButton("Back to Selection")
        back_button.clicked.connect(self.back_to_selection)  # Connect to new method
        edit_button = QPushButton("Edit Save")
        edit_button.clicked.connect(self.show_edit_page)
        button_layout.addWidget(back_button)
        button_layout.addWidget(edit_button)

        layout.addRow(button_layout)
        page.setLayout(layout)
        return page

    def update_save_info_page(self):
        """Update the save info page with current save data."""
        info = self.manager.get_save_info()
        self.game_version_label.setText(info.get('game_version', 'Unknown'))
        self.creation_date_label.setText(info.get('creation_date', 'Unknown'))
        self.org_name_label.setText(info.get('organisation_name', 'Unknown'))
        self.online_money_label.setText(f"${info.get('online_money', 0):,}")
        self.networth_label.setText(f"${info.get('networth', 0):,}")
        self.lifetime_earnings_label.setText(f"${info.get('lifetime_earnings', 0):,}")
        self.weekly_deposit_sum_label.setText(f"${info.get('weekly_deposit_sum', 0):,}")
        self.rank_label.setText(f"{info.get('current_rank', 'Unknown')} (Rank: {info.get('rank_number', 0)}, Tier: {info.get('tier', 0)})")

    def create_edit_save_page(self):
        page = QWidget()
        layout = QVBoxLayout()

        tab_widget = QTabWidget()
        self.money_tab = MoneyTab()
        self.rank_tab = RankTab()
        self.products_tab = ProductsTab(main_window=self)
        self.properties_tab = PropertiesTab(main_window=self)
        self.unlocks_tab = UnlocksTab(main_window=self)
        self.misc_tab = MiscTab(main_window=self)
        self.npcs_tab = NPCsTab(main_window=self)
        self.backups_tab = BackupsTab(main_window=self)  # Add BackupsTab

        tab_widget.addTab(self.money_tab, "Money")
        tab_widget.addTab(self.rank_tab, "Rank")
        tab_widget.addTab(self.products_tab, "Products")
        tab_widget.addTab(self.properties_tab, "Properties")
        tab_widget.addTab(self.unlocks_tab, "Unlocks")
        tab_widget.addTab(self.misc_tab, "Misc")
        tab_widget.addTab(self.npcs_tab, "NPCs")
        tab_widget.addTab(self.backups_tab, "Backups")  # Add to tab widget

        layout.addWidget(tab_widget)

        button_layout = QHBoxLayout()
        apply_button = QPushButton("Apply Changes")
        apply_button.clicked.connect(self.apply_changes)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.save_info_page))
        button_layout.addWidget(apply_button)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)
        page.setLayout(layout)
        return page

    def show_edit_page(self):
        """Show the edit save page and update its data."""
        self.update_edit_save_page()
        self.backups_tab.refresh_backup_list()
        self.stacked_widget.setCurrentWidget(self.edit_save_page)

    def update_edit_save_page(self):
        """Update the edit save page with current save data."""
        info = self.manager.get_save_info()
        self.money_tab.set_data(info)
        self.rank_tab.set_data(info)
        self.misc_tab.set_data(info) 
        self.misc_tab.update_vars_warning() 
        self.properties_tab.load_property_types()
        self.backups_tab.refresh_backup_list()

    def apply_changes(self):
        try:
            money_data = self.money_tab.get_data()
            rank_data = self.rank_tab.get_data()
            misc_data = self.misc_tab.get_data()

            # Backup stats files
            stats_files = [
                self.manager.current_save / "Money.json",
                self.manager.current_save / "Rank.json",
                self.manager.current_save / "Game.json"
            ]
            self.manager.create_feature_backup("Stats", stats_files)
            self.backups_tab.refresh_backup_list()  # Add this line

            self.manager.set_online_money(money_data["online_money"])
            self.manager.set_networth(money_data["networth"])
            self.manager.set_lifetime_earnings(money_data["lifetime_earnings"])
            self.manager.set_weekly_deposit_sum(money_data["weekly_deposit_sum"])
            self.manager.set_rank(rank_data["current_rank"])
            self.manager.set_rank_number(rank_data["rank_number"])
            self.manager.set_tier(rank_data["tier"])
            self.manager.set_organisation_name(misc_data["organisation_name"])

            QMessageBox.information(self, "Success", "Changes applied successfully!")
            self.update_save_info_page()
            self.stacked_widget.setCurrentWidget(self.save_info_page)
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter valid integer values.")

    def back_to_selection(self):
        """Refresh the save table and navigate back to the save selection page."""
        self.populate_save_table()  # Refresh table with latest data
        self.stacked_widget.setCurrentWidget(self.save_selection_page)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = QWidget()
    window = SaveEditorWindow()
    window.show()
    sys.exit(app.exec())
