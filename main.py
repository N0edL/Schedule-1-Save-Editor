# pyinstaller --noconfirm schedule1_editor.spec

import sys, json, os, random, string, shutil, tempfile, urllib.request, zipfile, winreg, re, subprocess, psutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget, QWidget,
    QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QFormLayout, QLineEdit, QComboBox, QPushButton,
    QMessageBox, QTabWidget, QCheckBox, QGroupBox, QTextEdit, QHeaderView, QDialog, QProgressDialog
)
from PySide6.QtCore import Qt, QUrl, QObject, Signal, QThread
from PySide6.QtGui import QRegularExpressionValidator, QIntValidator, QPalette, QColor, QDesktopServices, QIcon

CURRENT_VERSION = "1.0.5"

class UpdateChecker(QObject):
    finished = Signal(tuple) 

    def run(self):
        try:
            url = "https://api.github.com/repos/N0edL/Schedule-1-Save-Editor/releases/latest"
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Schedule-1-Save-Editor')
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                latest_version = data.get('tag_name', '')
                assets = data.get('assets', [])
                download_url = None
                for asset in assets:
                    if asset['name'].lower().endswith('.exe'):
                        download_url = asset.get('browser_download_url', '')
                        break
                self.finished.emit((latest_version, download_url))
        except Exception as e:
            print(f"Update check failed: {e}")
            self.finished.emit(('', ''))

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

def is_game_running():
    """Check if the game is running."""
    try:
        for proc in psutil.process_iter(['pid', 'name']):
            if "Schedule I" in proc.info['name']:
                return True
    except Exception as e:
        print(f"Error checking for running processes: {e}")
    return False

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

GOOFYAHHHNAMES = [
    "NoedLxCry4pt", "Nigger", "Fuck You", "Cry4pt", "NoedL", "I Love Kids", "I Love Children",
    "Bitch", "Fuck", "Retard", "Anal Destroyer", "Nigga", "Cum Shot", "Ass Blaster", "Cummy Wummy", 
    "Deez Nutz", "Supreme", "Big Chungus", "Shit", "Hell", "Ass", "Bastard", "Cunt", "Dick", 
    "Pussy", "Faggot", "Mother Fucker", "Son Of A Bitch", "Nazi", "Sex Offender", "KYS",
    # Added drug and medicine names
    "Abacavir", "Acetaminophen", "Acetazolamide", "Aciclovir", "Adalimumab", "Adenosine", "Adrenaline", 
    "Albendazole", "Albuterol", "Allopurinol", "Amlodipine", "Amoxicillin", "Amphotericin B", "Aspirin", 
    "Atorvastatin", "Atropine", "Azithromycin", "Baclofen", "Beclomethasone", "Benzocaine", "Betamethasone", 
    "Bupropion", "Buspirone", "Caffeine", "Calcitriol", "Captopril", "Carbamazepine", "Cefalexin", 
    "Ceftriaxone", "Celecoxib", "Cetirizine", "Chlorphenamine", "Ciprofloxacin", "Citalopram", "Clarithromycin", 
    "Clonazepam", "Clopidogrel", "Codeine", "Cyclophosphamide", "Dexamethasone", "Diazepam", "Diclofenac", 
    "Digoxin", "Diltiazem", "Diphenhydramine", "Doxycycline", "Enalapril", "Erythromycin", "Escitalopram", 
    "Esomeprazole", "Ezetimibe", "Famotidine", "Fentanyl", "Ferrous Sulfate", "Fluconazole", "Fluoxetine", 
    "Fluticasone", "Folic Acid", "Furosemide", "Gabapentin", "Gliclazide", "Heparin", "Hydrochlorothiazide", 
    "Hydrocortisone", "Ibuprofen", "Imatinib", "Insulin", "Ipratropium", "Irbesartan", "Isoniazid", 
    "Ketamine", "Ketoconazole", "Labetalol", "Lamotrigine", "Lansoprazole", "Levetiracetam", "Levofloxacin", 
    "Levothyroxine", "Lidocaine", "Lisinopril", "Loratadine", "Lorazepam", "Losartan", "Metformin", 
    "Methotrexate", "Methylprednisolone", "Metoprolol", "Metronidazole", "Mirtazapine", "Montelukast", 
    "Morphine", "Naproxen", "Nifedipine", "Nitroglycerin", "Omeprazole", "Ondansetron", "Oxycodone", 
    "Pantoprazole", "Paracetamol", "Paroxetine", "Penicillin", "Phenytoin", "Prazosin", "Prednisolone", 
    "Pregabalin", "Propranolol", "Quetiapine", "Rabeprazole", "Ramipril", "Ranitidine", "Risperidone", 
    "Rosuvastatin", "Salbutamol", "Sertraline", "Sildenafil", "Simvastatin", "Sodium Valproate", "Spironolactone", 
    "Sumatriptan", "Tacrolimus", "Tadalafil", "Tamoxifen", "Tamsulosin", "Terbinafine", "Testosterone", 
    "Tetracycline", "Thiamine", "Tiotropium", "Topiramate", "Tramadol", "Trazodone", "Valproic Acid", 
    "Vancomycin", "Venlafaxine", "Verapamil", "Warfarin", "Zidovudine", "Zolpidem"
]

class SaveManager:
    def __init__(self):
        self.savefile_dir = self._find_save_directory()
        self.current_save: Optional[Path] = None
        self.save_data: Dict[str, Union[dict, list]] = {}
        self.backup_path: Optional[Path] = None
        self.feature_backups: Optional[Path] = None

        self.used_names = set()
        self.available_names = []

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
            self.save_data["inventory"] = self._load_json_file("Players/Player_0/Inventory.json")
            self.backup_path = self.current_save.parent / (self.current_save.name + '_Backup')
            self.feature_backups = self.backup_path / 'feature_backups'
            self.create_initial_backup()

            # Add this block to initialize used_names and available_names
            self.used_names = set()
            products_path = self.current_save / "Products" / "CreatedProducts"
            if products_path.exists():
                for file in products_path.glob("*.json"):
                    try:
                        with open(file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            name = data.get("Name")
                            if name:
                                self.used_names.add(name)
                    except json.JSONDecodeError:
                        continue
            self.available_names = [name for name in GOOFYAHHHNAMES if name not in self.used_names]

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
        creation_date_data = self.save_data.get("metadata", {}).get("CreationDate", {})
        
        # Initialize formatted strings
        creation_date_str = "Unknown"
        creation_time_str = "Unknown"
        time_data = self.save_data.get("time", {})
        playtime_seconds = time_data.get("Playtime", 0)
        
        days = playtime_seconds // 86400  # 24*3600
        remaining_seconds = playtime_seconds % 86400
        hours = remaining_seconds // 3600
        remaining_seconds %= 3600
        minutes = remaining_seconds // 60
        seconds = remaining_seconds % 60
        playtime_str = f"{days}d, {hours}h, {minutes}m, {seconds}s"

        # Check if all required keys are present
        required_keys = ['Year', 'Month', 'Day', 'Hour', 'Minute', 'Second']
        if all(key in creation_date_data for key in required_keys):
            try:
                # Extract date/time components
                year = int(creation_date_data['Year'])
                month = int(creation_date_data['Month'])
                day = int(creation_date_data['Day'])
                hour = int(creation_date_data['Hour'])
                minute = int(creation_date_data['Minute'])
                second = int(creation_date_data['Second'])
                
                # Create datetime object
                dt = datetime(year, month, day, hour, minute, second)
                
                # Format date with ordinal suffix
                def get_ordinal(n):
                    if 11 <= (n % 100) <= 13:
                        return 'th'
                    return {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
                suffix = get_ordinal(day)
                creation_date_str = f"{day}{suffix} {dt.strftime('%B %Y')}"
                
                # Format time in 12-hour format with AM/PM and remove leading zero
                creation_time_str = dt.strftime("%I:%M:%S %p").lstrip('0')
                # Ensure 12 AM/PM shows correctly (replace leading space if needed)
                if creation_time_str.startswith(' '):
                    creation_time_str = creation_time_str[1:]
                
            except (ValueError, KeyError):
                # Handle invalid date/time values
                pass

        money_data = self.save_data.get("money", {})
        rank_data = self.save_data.get("rank", {})
        
        # Extract cash balance from inventory
        cash_balance = 0
        inventory = self.save_data.get("inventory", {})
        if "Items" in inventory:
            for item_str in inventory["Items"]:
                try:
                    item = json.loads(item_str)
                    if item.get("DataType") == "CashData":
                        cash_balance = int(item.get("CashBalance", 0))  # Ensure cash balance is an integer
                        break
                except json.JSONDecodeError:
                    continue

        return {
            "game_version": self.save_data.get("game", {}).get("GameVersion", "Unknown"),
            "creation_date": creation_date_str,
            "creation_time": creation_time_str,
            "playtime": playtime_str,
            "organisation_name": self.save_data.get("game", {}).get("OrganisationName", "Unknown"),
            "online_money": int(money_data.get("OnlineBalance", 0)),
            "networth": int(money_data.get("Networth", 0)),
            "lifetime_earnings": int(money_data.get("LifetimeEarnings", 0)),
            "weekly_deposit_sum": int(money_data.get("WeeklyDepositSum", 0)),
            "current_rank": rank_data.get("CurrentRank", "Unknown"),
            "rank_number": int(rank_data.get("Rank", 0)),
            "tier": int(rank_data.get("Tier", 0)),
            "cash_balance": cash_balance  # Ensure cash balance is an integer
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
                "GameVersion": "0.3.3f14",
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

    def generate_products(self, count: int, id_length: int, price: int, 
                        add_to_listed: bool = False, add_to_favourited: bool = False,
                        min_properties: int = 1, max_properties: int = 34, 
                        drug_type: int = 0, use_id_as_name: bool = False):
        products_path = self.current_save / "Products"
        os.makedirs(products_path, exist_ok=True)
        created_path = products_path / "CreatedProducts"
        os.makedirs(created_path, exist_ok=True)

        products_rel_path = "Products/Products.json"
        products_json = self.current_save / products_rel_path

        # Load or initialize products data
        if products_json.exists():
            data = self._load_json_file(products_rel_path)
        else:
            data = {
                "DataType": "ProductManagerData",
                "DataVersion": 0,
                "GameVersion": "0.3.3f14",
                "DiscoveredProducts": [],
                "ListedProducts": [],
                "ActiveMixOperation": {"ProductID": "", "IngredientID": ""},
                "IsMixComplete": False,
                "MixRecipes": [],
                "ProductPrices": [],
                "FavouritedProducts": []
            }

        new_product_ids = []
        discovered = data.setdefault("DiscoveredProducts", [])
        mix_recipes = data.setdefault("MixRecipes", [])
        prices = data.setdefault("ProductPrices", [])
        listed_products = data.setdefault("ListedProducts", [])
        favourited_products = data.setdefault("FavouritedProducts", [])

        property_pool = ["athletic", "balding", "gingeritis", "spicy", "jennerising", "thoughtprovoking",
                        "tropicthunder", "giraffying", "longfaced", "sedating", "smelly", "paranoia", "laxative",
                        "caloriedense", "energizing", "calming", "brighteyed", "foggy", "glowing", "antigravity",
                        "slippery", "munchies", "explosive", "refreshing", "shrinking", "euphoric", "disorienting",
                        "toxic", "zombifying", "cyclopean", "seizureinducing", "focused", "electrifying", "sneaky"]
        ingredients = ["flumedicine", "gasoline", "mouthwash", "horsesemen", "iodine", "chili", "paracetamol",
                    "energydrink", "donut", "banana", "viagra", "cuke", "motoroil", "addy", "megabean", "battery"]
        
        existing_ids = set(discovered)

        def generate_id(length):
            return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

        for _ in range(count):
            if use_id_as_name:
                # Generate unique product_id when using IDs as names
                product_id = generate_id(id_length)
                while product_id in existing_ids:
                    product_id = generate_id(id_length)
                existing_ids.add(product_id)
                product_name = product_id
                product_key = product_id
            else:
                # Select unique product_name when using random names
                if self.available_names:
                    product_name = self.available_names.pop(0)
                else:
                    base_name = GOOFYAHHHNAMES[0]
                    i = 1
                    while True:
                        candidate = f"{base_name} {i}"
                        if candidate not in self.used_names:
                            product_name = candidate
                            break
                        i += 1
                self.used_names.add(product_name)
                product_key = product_name

            # Add to discovered products
            discovered.append(product_key)

            # Create mix recipe
            ingredient = random.choice(ingredients)
            mix_recipes.append({
                "Product": ingredient,
                "Mixer": product_key,
                "Output": product_key
            })

            # Set price if specified
            if price is not None and price > 0:
                prices.append({"String": product_key, "Int": price})

            # Create product data
            properties = random.sample(property_pool, random.randint(min_properties, max_properties))
            product_data = {
                "DataType": "WeedProductData",
                "DataVersion": 0,
                "GameVersion": "0.3.3f14",
                "Name": product_name,
                "ID": product_key,  # Set "ID" to product_key
                "DrugType": drug_type,
                "Properties": properties,
                "AppearanceSettings": {
                    "MainColor": {"r": random.randint(0, 255), "g": random.randint(0, 255), "b": random.randint(0, 255), "a": 255},
                    "SecondaryColor": {"r": random.randint(0, 255), "g": random.randint(0, 255), "b": random.randint(0, 255), "a": 255},
                    "LeafColor": {"r": random.randint(0, 255), "g": random.randint(0, 255), "b": random.randint(0, 255), "a": 255},
                    "StemColor": {"r": random.randint(0, 255), "g": random.randint(0, 255), "b": random.randint(0, 255), "a": 255}
                }
            }

            # Save individual product file
            product_rel_path = f"Products/CreatedProducts/{product_key}.json"
            self._save_json_file(product_rel_path, product_data)

            # Collect new product keys
            new_product_ids.append(product_key)

        if add_to_listed:
            listed_products.extend(new_product_ids)
        if add_to_favourited:
            favourited_products.extend(new_product_ids)

        self._save_json_file(products_rel_path, data)
    
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
                        elif update_type == "weed" and item.get("DataType") in ("WeedData", "CocaineData", "MethData"):
                            modify = True
                        elif update_type == "item" and item.get("DataType") == "ItemData":
                            modify = True

                        if modify:
                            item["Quantity"] = quantity
                            if item.get("DataType") in ("WeedData", "CocaineData", "MethData"):
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
                    "https://github.com/N0edL/Schedule-1-Save-Editor/raw/refs/heads/main/NPCs/Properties.zip",
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
                "GameVersion": "0.3.3f14",
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
                    "https://github.com/N0edL/Schedule-1-Save-Editor/raw/refs/heads/main/NPCs/Businesses.zip",
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
                "GameVersion": "0.3.3f14",
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
                    "https://github.com/N0edL/Schedule-1-Save-Editor/raw/refs/heads/main/NPCs/NPCs.zip",
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

    def set_cash_balance(self, new_balance: int):
        if "inventory" in self.save_data:
            inventory = self.save_data["inventory"]
            if "Items" in inventory:
                for i, item_str in enumerate(inventory["Items"]):
                    try:
                        item = json.loads(item_str)
                        if item.get("DataType") == "CashData":
                            item["CashBalance"] = new_balance
                            inventory["Items"][i] = json.dumps(item)
                            self._save_json_file("Players/Player_0/Inventory.json", inventory)
                            return
                    except json.JSONDecodeError:
                        continue
                else:
                    print("No CashData item found in inventory.")
            else:
                print("No 'Items' key in inventory.")
        else:
            print("No 'inventory' in save_data.")

    def get_dealers(self) -> list[str]:
        """Retrieve a list of dealer names from the NPCs directory."""
        npcs_dir = self.current_save / "NPCs"
        if not npcs_dir.exists():
            return []
        dealers = []
        for npc_folder in npcs_dir.iterdir():
            if npc_folder.is_dir():
                npc_json_path = npc_folder / "NPC.json"
                if npc_json_path.exists():
                    try:
                        with open(npc_json_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        if data.get("DataType") == "DealerData":
                            dealers.append(npc_folder.name)
                    except json.JSONDecodeError:
                        continue
        return dealers

    def get_plastic_pots(self, property_type: Optional[str] = None):
        """Retrieve plastic pots filtered by property type if specified."""
        plastic_pots = []
        properties_path = self.current_save / "Properties"
        if not properties_path.exists():
            return plastic_pots
        
        # Get directories to process based on filter
        prop_dirs = []
        if property_type:
            target_dir = properties_path / property_type
            if target_dir.exists():
                prop_dirs.append(target_dir)
        else:
            prop_dirs = [d for d in properties_path.iterdir() if d.is_dir()]
        
        for prop_dir in prop_dirs:
            objects_path = prop_dir / "Objects"
            if objects_path.exists():
                for obj_dir in objects_path.iterdir():
                    if obj_dir.is_dir() and obj_dir.name.startswith("plasticpot_"):
                        data_path = obj_dir / "Data.json"
                        if data_path.exists():
                            with open(data_path, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                            plastic_pots.append({
                                'property_type': prop_dir.name,
                                'object_id': obj_dir.name,
                                'data': data
                            })
        return plastic_pots

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
        self.cash_balance_input = QLineEdit()  # Added CashBalance input
        self.cash_balance_input.setValidator(QRegularExpressionValidator(r"^\d{1,10}$"))
        layout.addRow("Cash Balance:", self.cash_balance_input)  # Added to layout
        layout.addRow("Online Money:", self.money_input)
        layout.addRow("Networth:", self.networth_input)
        layout.addRow("Lifetime Earnings:", self.lifetime_earnings_input)
        layout.addRow("Weekly Deposit Sum:", self.weekly_deposit_sum_input)
        self.setLayout(layout)

    def set_data(self, info):
        self.cash_balance_input.setText(str(info.get("cash_balance", 0)))  # Added
        self.money_input.setText(str(info.get("online_money", 0)))
        self.networth_input.setText(str(info.get("networth", 0)))
        self.lifetime_earnings_input.setText(str(info.get("lifetime_earnings", 0)))
        self.weekly_deposit_sum_input.setText(str(info.get("weekly_deposit_sum", 0)))

    def get_data(self):
        return {
            "cash_balance": int(self.cash_balance_input.text()),
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
        # Updated validator to allow up to 999
        self.rank_number_input.setValidator(QIntValidator(0, 999))
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

        self.properties_group = QGroupBox("Properties")
        properties_layout = QVBoxLayout()

        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(8)
        form_layout.setHorizontalSpacing(15)
        form_layout.setContentsMargins(5, 5, 5, 10)

        self.property_combo = QComboBox()
        self.property_combo.currentIndexChanged.connect(self.load_plastic_pots)  
        form_layout.addRow(QLabel("Property Type:"), self.property_combo)
        self.quantity_edit = QLineEdit()
        self.quantity_edit.setValidator(QIntValidator(0, 1000000))
        form_layout.addRow(QLabel("Quantity:"), self.quantity_edit)
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["Trash", "Poor", "Standard", "Premium", "Heavenly"])
        form_layout.addRow(QLabel("Quality:"), self.quality_combo)
        self.packaging_combo = QComboBox()
        self.packaging_combo.addItems(["none", "baggie", "jar"])
        form_layout.addRow(QLabel("Packaging:"), self.packaging_combo)
        self.update_combo = QComboBox()
        self.update_combo.addItems(["both", "weed", "item"])
        form_layout.addRow(QLabel("Update Type:"), self.update_combo)
        properties_layout.addLayout(form_layout)

        self.update_btn = QPushButton("Update Properties")
        self.update_btn.clicked.connect(self.update_properties)
        properties_layout.addWidget(self.update_btn)  # Corrected to add the update button to the layout

        self.properties_group.setLayout(properties_layout)
        layout.addWidget(self.properties_group)

        self.plastic_pots_group = QGroupBox("Plastic Pots")
        plastic_pots_layout = QVBoxLayout()

        self.plastic_pots_table = QTableWidget()
        self.plastic_pots_table.setColumnCount(6)
        self.plastic_pots_table.setHorizontalHeaderLabels([
            "Property Type", "Object ID", "SeedID", "QualityLevel", "GrowthProgress", "RemainingSoilUses"
        ])
        self.plastic_pots_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        plastic_pots_layout.addWidget(self.plastic_pots_table)
        self.save_plastic_pots_btn = QPushButton("Save Plastic Pots Changes")
        self.save_plastic_pots_btn.clicked.connect(self.save_plastic_pots_changes)
        plastic_pots_layout.addWidget(self.save_plastic_pots_btn)

        self.plastic_pots_group.setLayout(plastic_pots_layout)
        layout.addWidget(self.plastic_pots_group)

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
            self.property_combo.addItem("All Properties", "all")
            
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

    def load_plastic_pots(self):
        self.plastic_pots_table.setRowCount(0)
        selected_property = self.property_combo.currentData()
        plastic_pots = self.main_window.manager.get_plastic_pots(
            selected_property if selected_property != "all" else None
        )
        for pot in plastic_pots:
            row = self.plastic_pots_table.rowCount()
            self.plastic_pots_table.insertRow(row)
            self.plastic_pots_table.setItem(row, 0, QTableWidgetItem(pot['property_type']))
            self.plastic_pots_table.setItem(row, 1, QTableWidgetItem(pot['object_id']))
            
            # Access PlantData sub-object
            plant_data = pot['data'].get("PlantData", {})
            
            # SeedID
            seed_combo = QComboBox()
            seed_options = ["ogkushseed", "sourdieselseed", "greencrackseed", "granddaddypurpleseed"]
            seed_combo.addItems(seed_options)
            current_seed = plant_data.get("SeedID", "")
            if current_seed in seed_options:
                seed_combo.setCurrentText(current_seed)
            else:
                seed_combo.setCurrentIndex(0)  # Default to first option if invalid
            self.plastic_pots_table.setCellWidget(row, 2, seed_combo)
            
            # QualityLevel
            quality_combo = QComboBox()
            quality_labels = ["trash", "poor", "standard", "premium", "heavenly"]
            quality_combo.addItems(quality_labels)
            current_quality = plant_data.get("QualityLevel", 0.0)
            quality_label = self.get_quality_label(current_quality)
            if quality_label in quality_labels:
                quality_combo.setCurrentText(quality_label)
            else:
                quality_combo.setCurrentText("standard")  # Default if unknown
            self.plastic_pots_table.setCellWidget(row, 3, quality_combo)
            
            # GrowthProgress
            growth_combo = QComboBox()
            growth_labels = ["not grown", "abit grown", "medium grown", "near grown", "fully grown"]
            growth_combo.addItems(growth_labels)
            current_growth = plant_data.get("GrowthProgress", 0.0)
            growth_label = self.get_growth_label(current_growth)
            if growth_label in growth_labels:
                growth_combo.setCurrentText(growth_label)
            else:
                growth_combo.setCurrentText("not grown")  # Default if unknown
            self.plastic_pots_table.setCellWidget(row, 4, growth_combo)
            
            # RemainingSoilUses (still at root level)
            remaining_uses = str(pot['data'].get("RemainingSoilUses", 0))
            uses_edit = QLineEdit()
            uses_edit.setValidator(QIntValidator(0, 999))
            uses_edit.setText(remaining_uses)
            self.plastic_pots_table.setCellWidget(row, 5, uses_edit)

    def get_quality_label(self, value):
            if 0.1 <= value <= 0.2:
                return "trash"
            elif 0.3 <= value <= 0.4:
                return "poor"
            elif 0.5 <= value <= 0.6:
                return "standard"
            elif 0.7 <= value <= 0.8:
                return "premium"
            elif 0.9 <= value <= 1.0:
                return "heavenly"
            else:
                return "unknown"

    def get_growth_label(self, value):
        if 0.1 <= value <= 0.2:
            return "not grown"
        elif 0.3 <= value <= 0.4:
            return "abit grown"
        elif 0.5 <= value <= 0.6:
            return "medium grown"
        elif 0.7 <= value <= 0.8:
            return "near grown"
        elif 0.9 <= value <= 1.0:
            return "fully grown"
        else:
            return "unknown"

    def save_plastic_pots_changes(self):
        for row in range(self.plastic_pots_table.rowCount()):
            property_type = self.plastic_pots_table.item(row, 0).text()
            object_id = self.plastic_pots_table.item(row, 1).text()
            data_path = self.main_window.manager.current_save / "Properties" / property_type / "Objects" / object_id / "Data.json"
            if not data_path.exists():
                continue
            
            # Load the existing data
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Clean up any incorrect root-level fields (optional but recommended)
            for field in ["SeedID", "QualityLevel", "GrowthProgress"]:
                if field in data:
                    del data[field]
            
            # Ensure PlantData exists and update its fields
            if "PlantData" not in data:
                data["PlantData"] = {
                    "DataType": "PlantData",
                    "DataVersion": 0,
                    "GameVersion": "0.3.3f14",
                    "SeedID": "",
                    "GrowthProgress": 0.0,
                    "YieldLevel": 0.0,
                    "QualityLevel": 0.0,
                    "ActiveBuds": []
                }
            
            # Update SeedID
            seed_combo = self.plastic_pots_table.cellWidget(row, 2)
            data["PlantData"]["SeedID"] = seed_combo.currentText()
            
            # Update QualityLevel
            quality_combo = self.plastic_pots_table.cellWidget(row, 3)
            quality_label = quality_combo.currentText()
            quality_value = {
                "trash": 0.15,
                "poor": 0.35,
                "standard": 0.55,
                "premium": 0.75,
                "heavenly": 0.95
            }.get(quality_label, 0.0)
            data["PlantData"]["QualityLevel"] = quality_value
            
            # Update GrowthProgress
            growth_combo = self.plastic_pots_table.cellWidget(row, 4)
            growth_label = growth_combo.currentText()
            growth_value = {
                "not grown": 0.15,
                "abit grown": 0.35,
                "medium grown": 0.55,
                "near grown": 0.75,
                "fully grown": 0.95
            }.get(growth_label, 0.0)
            data["PlantData"]["GrowthProgress"] = growth_value
            
            # Update RemainingSoilUses (still at root level)
            uses_edit = self.plastic_pots_table.cellWidget(row, 5)
            try:
                remaining_uses = int(uses_edit.text())
            except ValueError:
                remaining_uses = 0
            data["RemainingSoilUses"] = remaining_uses
            
            # Save the updated data
            with open(data_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
        
        QMessageBox.information(self, "Success", "Plastic pots changes saved successfully!")

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
        discover_button.clicked.connect(self.discover_selected_products)
        buttons_layout.addWidget(discover_button)

        # Undiscover button
        undiscover_button = QPushButton("Undiscover Selected")
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

        self.id_length_input = QLineEdit()
        self.id_length_input.setValidator(QIntValidator(5, 20))

        self.price_input = QLineEdit()
        self.price_input.setValidator(QIntValidator(1, 1000000))

        form_layout.addRow("Number of Products:", self.count_input)
        form_layout.addRow("ID Length:", self.id_length_input)
        form_layout.addRow("Price:", self.price_input)

        self.drug_type_input = QLineEdit()
        self.drug_type_input.setValidator(QIntValidator(0, 2))  # Adjust range as needed
        self.drug_type_input.setText("0")  # Default to 0
        form_layout.addRow("Drug Type:", self.drug_type_input)

        # Add after existing form elements
        self.min_properties_input = QLineEdit()
        self.min_properties_input.setValidator(QIntValidator(1, 34))
        self.min_properties_input.setText("1")
        form_layout.addRow("Min Mixes Per Product:", self.min_properties_input)

        self.max_properties_input = QLineEdit()
        self.max_properties_input.setValidator(QIntValidator(1, 34))
        self.max_properties_input.setText("34")
        form_layout.addRow("Max Mixes Per Product:", self.max_properties_input)

        # Add checkbox for name generation type
        self.name_generation_checkbox = QCheckBox("Use Random Names Instead Of IDs")
        form_layout.addRow("", self.name_generation_checkbox)

        self.add_to_listed_checkbox = QCheckBox("Add to Listed Products")
        form_layout.addRow("", self.add_to_listed_checkbox)

        self.add_to_favourited_checkbox = QCheckBox("Add to Favourited Products")
        form_layout.addRow("", self.add_to_favourited_checkbox)

        # **Buttons for Generation** - Moved inside the form_layout
        button_layout = QHBoxLayout()
        generate_button = QPushButton("Generate Products")
        generate_button.clicked.connect(self.generate_products)
        button_layout.addWidget(generate_button)

        reset_button = QPushButton("Reset Products")
        reset_button.clicked.connect(self.delete_generated_products)
        button_layout.addWidget(reset_button)

        # Add the button layout to the form layout (inside the group box)
        form_layout.addRow(button_layout)

        generation_group.setLayout(form_layout)

        # Assemble main layout
        layout.addWidget(discovery_group)
        layout.addWidget(generation_group)
        layout.addStretch()  # Optional: adds stretch to main layout if needed
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
            
            # Handle ID length based on checkbox state
            if self.name_generation_checkbox.isChecked():
                # Using random names: ID length is optional, default to 10 if empty
                id_length_text = self.id_length_input.text().strip()
                id_length = int(id_length_text) if id_length_text else 10
            else:
                # Not using random names: ID length is required
                id_length_text = self.id_length_input.text().strip()
                if not id_length_text:
                    raise ValueError("ID Length is required when not using random names")
                id_length = int(id_length_text)
            
            # Handle price input
            price_text = self.price_input.text().strip()
            price = int(price_text) if price_text else None  # Allow empty price
            
            drug_type = int(self.drug_type_input.text()) if self.drug_type_input.text().strip() else 0
            
            add_to_listed = self.add_to_listed_checkbox.isChecked()
            add_to_favourited = self.add_to_favourited_checkbox.isChecked()
            use_id_as_name = not self.name_generation_checkbox.isChecked()

            min_props = int(self.min_properties_input.text())
            max_props = int(self.max_properties_input.text())
            
            if min_props > max_props:
                raise ValueError("Minimum properties cannot exceed maximum")
            if max_props > 34:
                raise ValueError("Maximum cannot exceed 34 (total available properties)")

            # Backup products FIRST
            products_path = self.main_window.manager.current_save / "Products"
            self.main_window.manager.create_feature_backup("Products", [products_path])
            self.main_window.backups_tab.refresh_backup_list()

            # SINGLE call to generate_products
            self.main_window.manager.generate_products(
                count, id_length, price, 
                add_to_listed, add_to_favourited,
                min_props, max_props, drug_type, use_id_as_name
            )

            QMessageBox.information(self, "Success", f"Generated {count} products successfully!")
        except ValueError as ve:
            QMessageBox.warning(self, "Invalid Input", f"Please enter valid numbers: {str(ve)}")
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
                    data = {"DiscoveredProducts": [], "ListedProducts": [], "MixRecipes": [], "ProductPrices": [], "FavouritedProducts": []}
                
                data["DiscoveredProducts"] = [pid for pid in data.get("DiscoveredProducts", []) if pid not in generated_ids]
                data["ListedProducts"] = [pid for pid in data.get("ListedProducts", []) if pid not in generated_ids]
                data["MixRecipes"] = [recipe for recipe in data.get("MixRecipes", []) if recipe.get("Output") not in generated_ids]
                data["ProductPrices"] = [price for price in data.get("ProductPrices", []) if price.get("String") not in generated_ids]
                data["FavouritedProducts"] = [pid for pid in data.get("FavouritedProducts", []) if pid not in generated_ids]
                
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
        items_weeds_btn.clicked.connect(self.unlock_items_weeds)
        unlock_layout.addWidget(QLabel("Sets Rank & tier To 999 To Unlock All Items/Weeds:"))
        unlock_layout.addWidget(items_weeds_btn)
        unlock_layout.addSpacing(10)

        # Properties Section
        props_btn = QPushButton("Unlock All Properties")
        props_btn.clicked.connect(self.unlock_properties)
        unlock_layout.addWidget(QLabel("Downloads & Enables All Property Types:"))
        unlock_layout.addWidget(props_btn)
        unlock_layout.addSpacing(10)

        # Businesses Section
        business_btn = QPushButton("Unlock All Businesses")
        business_btn.clicked.connect(self.unlock_businesses)
        unlock_layout.addWidget(QLabel("Downloads & Enables All Business Types:"))
        unlock_layout.addWidget(business_btn)

        # Add NPC Relationships Section
        npc_relation_btn = QPushButton("Unlock All NPCs")
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

class InventoryTab(QWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        layout = QVBoxLayout()

        # Type selection
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Dealers", "Vehicles"])
        self.type_combo.currentIndexChanged.connect(self.on_type_changed)
        layout.addWidget(QLabel("Select Type:"))
        layout.addWidget(self.type_combo)

        # Entity selection
        self.entity_combo = QComboBox()
        self.entity_combo.currentIndexChanged.connect(self.load_entity_inventory)
        layout.addWidget(QLabel("Select Entity:"))
        layout.addWidget(self.entity_combo)

        # Cash group for dealers
        self.cash_group = QGroupBox("Cash")
        cash_layout = QFormLayout()
        self.cash_input = QLineEdit()
        self.cash_input.setValidator(QRegularExpressionValidator(r"^\d{1,10}$"))
        cash_layout.addRow("Cash:", self.cash_input)
        self.cash_group.setLayout(cash_layout)
        layout.addWidget(self.cash_group)
        self.cash_group.setVisible(False)  # Hidden by default

        # Inventory table
        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(5)
        self.inventory_table.setHorizontalHeaderLabels(["Item Type", "ID", "Quantity", "Quality", "PackagingID"])
        self.inventory_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.inventory_table.setSelectionMode(QTableWidget.SingleSelection)
        self.inventory_table.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.EditKeyPressed)
        self.inventory_table.itemChanged.connect(self.on_item_changed)
        self.inventory_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.inventory_table, 1)

        # Buttons
        button_layout = QHBoxLayout()
        insert_button = QPushButton("Insert Row")
        insert_button.clicked.connect(self.insert_row)
        delete_button = QPushButton("Delete Selected Row")
        delete_button.clicked.connect(self.delete_selected_row)
        save_button = QPushButton("Save Changes")
        save_button.clicked.connect(self.save_changes)
        button_layout.addWidget(insert_button)
        button_layout.addWidget(delete_button)
        button_layout.addWidget(save_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)
        self.current_type = None
        self.current_entity = None
        self.load_entities()  # Initial load
        self.on_type_changed()  # Trigger initial display

    def refresh_data(self):
        """Refresh the entities and load the inventory for the first entity."""
        self.load_entities()
        self.on_type_changed()

    def load_entities(self):
        """Load dealers or vehicles into the entity combo based on the selected type."""
        if self.main_window.manager.current_save is None:
            self.entity_combo.clear()
            return
        self.entity_combo.clear()
        if self.type_combo.currentText() == "Dealers":
            dealers = self.main_window.manager.get_dealers()
            self.entity_combo.addItems(dealers)
        elif self.type_combo.currentText() == "Vehicles":
            vehicles_path = self.main_window.manager.current_save / "OwnedVehicles"
            if vehicles_path.exists():
                vehicles = [d.name for d in vehicles_path.iterdir() if d.is_dir()]
                self.entity_combo.addItems(vehicles)

    def on_type_changed(self):
        """Handle type change: update entity combo, hide/show cash group, and load inventory."""
        self.load_entities()
        self.cash_group.setVisible(self.type_combo.currentText() == "Dealers")
        self.inventory_table.setRowCount(0)
        self.cash_input.clear()
        # If entities exist, select the first one and load its inventory
        if self.entity_combo.count() > 0:
            self.entity_combo.setCurrentIndex(0)
            self.load_entity_inventory()
        else:
            self.current_type = self.type_combo.currentText()
            self.current_entity = None

    def load_entity_inventory(self):
        """Load the inventory and cash (if dealer) for the selected entity."""
        if self.main_window.manager.current_save is None:
            return
        self.current_type = self.type_combo.currentText()
        self.current_entity = self.entity_combo.currentText()
        if not self.current_entity:
            self.inventory_table.setRowCount(0)
            self.cash_input.clear()
            return
        if self.current_type == "Dealers":
            # Load inventory
            inventory_path = self.main_window.manager.current_save / "NPCs" / self.current_entity / "Inventory.json"
            items = self._load_items(inventory_path)
            self.display_inventory(items)
            # Load cash
            npc_json_path = self.main_window.manager.current_save / "NPCs" / self.current_entity / "NPC.json"
            if npc_json_path.exists():
                with open(npc_json_path, 'r', encoding='utf-8') as f:
                    npc_data = json.load(f)
                cash = round(npc_data.get("Cash", 0))
                self.cash_input.setText(str(cash))
            else:
                self.cash_input.setText("0")
        elif self.current_type == "Vehicles":
            # Load inventory
            contents_path = self.main_window.manager.current_save / "OwnedVehicles" / self.current_entity / "Contents.json"
            items = self._load_items(contents_path)
            self.display_inventory(items)

    def _load_items(self, path):
        """Helper method to load items from a JSON file."""
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get("Items", [])
        return []

    def display_inventory(self, items):
        """Display the inventory in the table."""
        self.inventory_table.blockSignals(True)
        self.inventory_table.setRowCount(0)
        for item_str in items:
            try:
                item = json.loads(item_str)
                item_type = item.get("DataType", "Unknown")
                item_id = item.get("ID", "Unknown")
                quantity = str(item.get("Quantity", 0))
                quality = item.get("Quality", "")
                packaging = item.get("PackagingID", "")
                row = self.inventory_table.rowCount()
                self.inventory_table.insertRow(row)
                self.inventory_table.setItem(row, 0, QTableWidgetItem(item_type))
                self.inventory_table.setItem(row, 1, QTableWidgetItem(item_id))
                quantity_item = QTableWidgetItem(quantity)
                quantity_item.setData(Qt.UserRole, item_str)
                self.inventory_table.setItem(row, 2, quantity_item)
                if item_type in ("WeedData", "CocaineData", "MethData"):
                    quality_combo = QComboBox()
                    quality_combo.addItems(["Trash", "Poor", "Standard", "Premium", "Heavenly"])
                    quality_combo.setCurrentText(quality if quality else "Standard")
                    quality_combo.currentTextChanged.connect(
                        lambda text, r=row: self.update_item_json(r, "Quality", text)
                    )
                    self.inventory_table.setCellWidget(row, 3, quality_combo)
                    packaging_combo = QComboBox()
                    packaging_combo.addItems(["none", "baggie", "jar"])
                    packaging_combo.setCurrentText(packaging if packaging else "none")
                    packaging_combo.currentTextChanged.connect(
                        lambda text, r=row: self.update_item_json(r, "PackagingID", text)
                    )
                    self.inventory_table.setCellWidget(row, 4, packaging_combo)
                else:
                    quality_item = QTableWidgetItem("N/A")
                    quality_item.setFlags(quality_item.flags() & ~Qt.ItemIsEditable)
                    self.inventory_table.setItem(row, 3, quality_item)
                    packaging_item = QTableWidgetItem("N/A")
                    packaging_item.setFlags(packaging_item.flags() & ~Qt.ItemIsEditable)
                    self.inventory_table.setItem(row, 4, packaging_item)
            except json.JSONDecodeError:
                continue
        self.inventory_table.blockSignals(False)

    def on_item_changed(self, item):
        """Handle changes to editable table cells."""
        row, column = item.row(), item.column()
        if column in (0, 1, 2):
            field = ["DataType", "ID", "Quantity"][column]
            value = item.text()
            if column == 2:
                try:
                    value = int(value)
                except ValueError:
                    QMessageBox.warning(self, "Invalid Quantity", "Quantity must be an integer.")
                    item.setText("0")
                    return
            self.update_item_json(row, field, value)
            if column == 0:
                self.update_quality_packaging_cells(row, value)

    def update_quality_packaging_cells(self, row, item_type):
        """Update Quality and PackagingID cells based on item type."""
        for col in (3, 4):
            self.inventory_table.removeCellWidget(row, col)
            self.inventory_table.setItem(row, col, None)
        if item_type in ("WeedData", "CocaineData", "MethData"):
            quality_combo = QComboBox()
            quality_combo.addItems(["Trash", "Poor", "Standard", "Premium", "Heavenly"])
            quality_combo.setCurrentText("Standard")
            quality_combo.currentTextChanged.connect(
                lambda text, r=row: self.update_item_json(r, "Quality", text)
            )
            self.inventory_table.setCellWidget(row, 3, quality_combo)
            packaging_combo = QComboBox()
            packaging_combo.addItems(["none", "baggie", "jar"])
            packaging_combo.setCurrentText("none")
            packaging_combo.currentTextChanged.connect(
                lambda text, r=row: self.update_item_json(r, "PackagingID", text)
            )
            self.inventory_table.setCellWidget(row, 4, packaging_combo)
        else:
            for col in (3, 4):
                na_item = QTableWidgetItem("N/A")
                na_item.setFlags(na_item.flags() & ~Qt.ItemIsEditable)
                self.inventory_table.setItem(row, col, na_item)
        quantity_item = self.inventory_table.item(row, 2)
        if quantity_item:
            item_str = quantity_item.data(Qt.UserRole)
            if item_str:
                try:
                    item = json.loads(item_str)
                    if item_type in ("WeedData", "CocaineData", "MethData"):
                        item.setdefault("Quality", "Standard")
                        item.setdefault("PackagingID", "none")
                    else:
                        item.pop("Quality", None)
                        item.pop("PackagingID", None)
                    quantity_item.setData(Qt.UserRole, json.dumps(item))
                except json.JSONDecodeError:
                    pass

    def update_item_json(self, row, field, value):
        """Update the JSON data for an item."""
        quantity_item = self.inventory_table.item(row, 2)
        if quantity_item:
            item_str = quantity_item.data(Qt.UserRole)
            if item_str:
                try:
                    item = json.loads(item_str)
                    item[field] = value
                    quantity_item.setData(Qt.UserRole, json.dumps(item))
                except json.JSONDecodeError:
                    QMessageBox.warning(self, "Error", "Invalid item data")

    def insert_row(self):
        """Insert a new row with default values."""
        self.inventory_table.blockSignals(True)
        row = self.inventory_table.rowCount()
        self.inventory_table.insertRow(row)
        item = {"DataType": "ItemData", "ID": "new_item", "Quantity": 1}
        item_str = json.dumps(item)
        self.inventory_table.setItem(row, 0, QTableWidgetItem("ItemData"))
        self.inventory_table.setItem(row, 1, QTableWidgetItem("new_item"))
        quantity_item = QTableWidgetItem("1")
        quantity_item.setData(Qt.UserRole, item_str)
        self.inventory_table.setItem(row, 2, quantity_item)
        for col in (3, 4):
            na_item = QTableWidgetItem("N/A")
            na_item.setFlags(na_item.flags() & ~Qt.ItemIsEditable)
            self.inventory_table.setItem(row, col, na_item)
        self.inventory_table.blockSignals(False)

    def delete_selected_row(self):
        """Delete the selected row from the table."""
        selected = self.inventory_table.selectedItems()
        if selected:
            row = selected[0].row()
            self.inventory_table.blockSignals(True)
            self.inventory_table.removeRow(row)
            self.inventory_table.blockSignals(False)
        else:
            QMessageBox.warning(self, "No Selection", "Please select a row to delete.")

    def save_changes(self):
        """Save changes to the selected entity's inventory and cash (if dealer)."""
        if self.main_window.manager.current_save is None:
            QMessageBox.warning(self, "No Save Loaded", "Please load a save first.")
            return
        if not self.current_entity:
            return
        items = [self.inventory_table.item(row, 2).data(Qt.UserRole) for row in range(self.inventory_table.rowCount())]
        if self.current_type == "Dealers":
            inventory_path = self.main_window.manager.current_save / "NPCs" / self.current_entity / "Inventory.json"
            npc_json_path = self.main_window.manager.current_save / "NPCs" / self.current_entity / "NPC.json"
            self.main_window.manager.create_feature_backup("NPCs", [inventory_path.parent])
            # Save inventory
            inventory_data = {"DataType": "InventoryData", "DataVersion": 0, "GameVersion": "0.3.3f14", "Items": items}
            with open(inventory_path, 'w', encoding='utf-8') as f:
                json.dump(inventory_data, f, indent=4)
            # Save cash
            cash_value = self.cash_input.text()
            if cash_value:
                try:
                    cash = int(cash_value)
                    with open(npc_json_path, 'r', encoding='utf-8') as f:
                        npc_data = json.load(f)
                    npc_data["Cash"] = cash
                    with open(npc_json_path, 'w', encoding='utf-8') as f:
                        json.dump(npc_data, f, indent=4)
                except ValueError:
                    QMessageBox.warning(self, "Invalid Cash", "Cash must be an integer.")
                    return
        elif self.current_type == "Vehicles":
            contents_path = self.main_window.manager.current_save / "OwnedVehicles" / self.current_entity / "Contents.json"
            self.main_window.manager.create_feature_backup("Vehicles", [contents_path.parent])
            data = {"DataType": "InventoryData", "DataVersion": 0, "GameVersion": "0.3.3f14", "Items": items}
            with open(contents_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
        QMessageBox.information(self, "Success", f"Inventory for {self.current_entity} saved successfully!")
        self.main_window.backups_tab.refresh_backup_list()

class MiscTab(QWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # Organisation Settings Group
        org_group = QGroupBox("Organization Settings")
        org_layout = QFormLayout()
        org_layout.setContentsMargins(10, 10, 10, 10)
        self.organisation_name_input = QLineEdit()
        org_layout.addRow(QLabel("Organization Name:"), self.organisation_name_input)
        
        # Add Console Enabled Checkbox
        self.console_enabled_cb = QCheckBox("Console Enabled")
        org_layout.addRow(self.console_enabled_cb)
        org_group.setLayout(org_layout)
        layout.addWidget(org_group)

        # Save Management Group
        save_mgmt_group = QGroupBox("Save Management")
        save_mgmt_layout = QFormLayout()
        save_mgmt_layout.setContentsMargins(10, 10, 10, 10)
        self.save_folder_combo = QComboBox()
        self.load_save_folders()  # Populate the combo box
        save_mgmt_layout.addRow("Select Save Folder:", self.save_folder_combo)
        self.delete_save_btn = QPushButton("Delete Selected Save Folder")
        self.delete_save_btn.clicked.connect(self.delete_selected_save)
        save_mgmt_layout.addRow(self.delete_save_btn)
        save_mgmt_group.setLayout(save_mgmt_layout)
        layout.addWidget(save_mgmt_group)

        # Quests Section (existing)
        quests_group = QGroupBox("Quest Management")
        quests_layout = QVBoxLayout()
        quests_layout.setContentsMargins(10, 10, 10, 10)
        quests_layout.addWidget(QLabel("WARNING: This will mark all quests and objectives as completed"))
        self.complete_quests_btn = QPushButton("Complete All Quests")
        self.complete_quests_btn.clicked.connect(self.complete_all_quests)
        quests_layout.addWidget(self.complete_quests_btn)
        quests_group.setLayout(quests_layout)
        layout.addWidget(quests_group)

        # Variables Section (existing)
        vars_group = QGroupBox("Variable Management")
        vars_layout = QVBoxLayout()
        vars_layout.setContentsMargins(10, 10, 10, 10)
        self.vars_warning_label = QLabel()
        vars_layout.addWidget(self.vars_warning_label)
        self.vars_btn = QPushButton("Modify All Variables")
        self.vars_btn.clicked.connect(self.modify_variables)
        vars_layout.addWidget(self.vars_btn)
        vars_group.setLayout(vars_layout)
        layout.addWidget(vars_group)

        # Mod Installation Section (existing)
        mod_group = QGroupBox("Achievement Unlocker")
        mod_layout = QVBoxLayout()
        mod_layout.setContentsMargins(10, 10, 10, 10)
        mod_layout.addWidget(QLabel("WARNING: This unlock all the achievements in the game when you start up Schedule 1"))
        self.install_mod_btn = QPushButton("Install Achievement Unlocker Mod")
        self.install_mod_btn.clicked.connect(self.install_mod)
        mod_layout.addWidget(self.install_mod_btn)
        mod_group.setLayout(mod_layout)
        layout.addWidget(mod_group)

        # New Save Generation Section (existing)
        new_save_group = QGroupBox("New Save Generation")
        new_save_layout = QFormLayout()
        new_save_layout.setContentsMargins(10, 10, 10, 10)
        self.new_org_name_input = QLineEdit()
        new_save_layout.addRow(QLabel("New Organization Name:"), self.new_org_name_input)
        self.generate_save_btn = QPushButton("Generate New Save Folder")
        self.generate_save_btn.clicked.connect(self.generate_new_save)
        new_save_layout.addRow(self.generate_save_btn)
        new_save_group.setLayout(new_save_layout)
        layout.addWidget(new_save_group)

        layout.addStretch()
        self.setLayout(layout)
        self.vars_warning_label.setText("WARNING: Modifies variables in:\n- Variables/\n- Players/Player_*/Variables/")

    def set_data(self, info):
        """Populate the input fields with data from the info dictionary."""
        self.organisation_name_input.setText(info.get("organisation_name", ""))
        # Get ConsoleEnabled from Settings
        game_data = self.main_window.manager._load_json_file("Game.json")
        console_enabled = game_data.get("Settings", {}).get("ConsoleEnabled", False)
        self.console_enabled_cb.setChecked(console_enabled)

    def get_data(self):
        """Retrieve data from the input fields."""
        return {
            "organisation_name": self.organisation_name_input.text(),
            "console_enabled": self.console_enabled_cb.isChecked()
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

            dll_url = "https://github.com/N0edL/Schedule-1-Save-Editor/raw/refs/heads/main/NPCs/AchievementUnlocker.dll"
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
                    "https://github.com/N0edL/Schedule-1-Save-Editor/raw/refs/heads/main/NPCs/SaveGame_1.zip",
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

    def load_save_folders(self):
            """Populate the save folder combo box with available saves."""
            saves = self.main_window.manager.get_save_folders()
            self.save_folder_combo.clear()
            for save in saves:
                self.save_folder_combo.addItem(save['name'], save['path'])

    def delete_selected_save(self):
        # Get the selected save folder path from the combo box
        save_path = self.save_folder_combo.currentData()
        if not save_path:
            QMessageBox.warning(self, "No Selection", "Please select a save folder to delete.")
            return

        # Construct the backup folder path (assumes backup is save folder name + '_Backup')
        backup_path = Path(save_path).parent / (Path(save_path).name + '_Backup')

        # Prepare a warning message, customized if it's the current save
        if Path(save_path) == self.main_window.manager.current_save:
            warning_msg = ("You are about to delete the currently loaded save folder and its backup.\n"
                        "This action cannot be undone and will close the editor.\n"
                        "Are you sure?")
        else:
            warning_msg = (f"Are you sure you want to delete the save folder "
                        f"'{self.save_folder_combo.currentText()}' and its backup?\n"
                        "This action cannot be undone.")

        # Show confirmation dialog
        reply = QMessageBox.warning(
            self,
            "Confirm Delete",
            warning_msg,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        # Proceed with deletion if user confirms
        if reply == QMessageBox.Yes:
            try:
                # Delete the main save folder
                shutil.rmtree(save_path)

                # Delete the backup folder if it exists
                if backup_path.exists():
                    shutil.rmtree(backup_path)

                # Notify user of success
                QMessageBox.information(self, "Success", "Save folder and its backup deleted successfully.")
                
                # Refresh UI elements
                self.load_save_folders()  # Update the combo box
                self.main_window.populate_save_table()  # Update the save selection table
                
                # If the deleted save was the current one, return to selection screen
                if Path(save_path) == self.main_window.manager.current_save:
                    self.main_window.back_to_selection()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete save folder or backup: {str(e)}")
                
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

class ThemeTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems([
            "System Default",
            "Dark Theme",
            "Light Theme",
            "Dracula",
            "Solarized Dark",
            "Solarized Light",
            "Blue Theme",
            "Green Theme"
        ])
        self.theme_combo.currentIndexChanged.connect(self.change_theme)
        
        layout.addWidget(QLabel("Application Theme:"))
        layout.addWidget(self.theme_combo)
        layout.addStretch()
        
        self.setLayout(layout)

    def change_theme(self, index):
        theme_map = {
            0: self.set_system_theme,
            1: self.set_dark_theme,
            2: self.set_light_theme,
            3: self.set_dracula_theme,
            4: self.set_solarized_dark,
            5: self.set_solarized_light,
            6: self.set_blue_theme,
            7: self.set_green_theme
        }
        theme_map.get(index, self.set_system_theme)()

    def set_system_theme(self):
        QApplication.setStyle("")
        QApplication.setPalette(QApplication.style().standardPalette())

    def set_dark_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(35, 35, 35))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Highlight, QColor(0, 122, 204))
        palette.setColor(QPalette.HighlightedText, Qt.black)
        QApplication.setStyle("Fusion")
        QApplication.setPalette(palette)

    def set_light_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(240, 240, 240))
        palette.setColor(QPalette.WindowText, Qt.black)
        palette.setColor(QPalette.Base, Qt.white)
        palette.setColor(QPalette.AlternateBase, QColor(240, 240, 240))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.black)
        palette.setColor(QPalette.Text, Qt.black)
        palette.setColor(QPalette.Button, QColor(240, 240, 240))
        palette.setColor(QPalette.ButtonText, Qt.black)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Highlight, QColor(0, 0, 255))
        palette.setColor(QPalette.HighlightedText, Qt.white)
        QApplication.setStyle("Fusion")
        QApplication.setPalette(palette)

    def set_dracula_theme(self):
        palette = QPalette()
        # Dracula color scheme
        palette.setColor(QPalette.Window, QColor(40, 42, 54))
        palette.setColor(QPalette.WindowText, QColor(248, 248, 242))
        palette.setColor(QPalette.Base, QColor(68, 71, 90))
        palette.setColor(QPalette.AlternateBase, QColor(40, 42, 54))
        palette.setColor(QPalette.ToolTipBase, QColor(40, 42, 54))
        palette.setColor(QPalette.ToolTipText, QColor(248, 248, 242))
        palette.setColor(QPalette.Text, QColor(248, 248, 242))
        palette.setColor(QPalette.Button, QColor(98, 114, 164))
        palette.setColor(QPalette.ButtonText, QColor(248, 248, 242))
        palette.setColor(QPalette.BrightText, QColor(255, 121, 198))
        palette.setColor(QPalette.Highlight, QColor(189, 147, 249))
        palette.setColor(QPalette.HighlightedText, Qt.black)
        QApplication.setStyle("Fusion")
        QApplication.setPalette(palette)

    def set_solarized_dark(self):
        palette = QPalette()
        # Solarized Dark
        palette.setColor(QPalette.Window, QColor(0, 43, 54))
        palette.setColor(QPalette.WindowText, QColor(147, 161, 161))
        palette.setColor(QPalette.Base, QColor(7, 54, 66))
        palette.setColor(QPalette.AlternateBase, QColor(0, 43, 54))
        palette.setColor(QPalette.ToolTipBase, QColor(7, 54, 66))
        palette.setColor(QPalette.ToolTipText, QColor(147, 161, 161))
        palette.setColor(QPalette.Text, QColor(147, 161, 161))
        palette.setColor(QPalette.Button, QColor(0, 43, 54))
        palette.setColor(QPalette.ButtonText, QColor(147, 161, 161))
        palette.setColor(QPalette.BrightText, QColor(220, 50, 47))
        palette.setColor(QPalette.Highlight, QColor(38, 139, 210))
        palette.setColor(QPalette.HighlightedText, Qt.black)
        QApplication.setStyle("Fusion")
        QApplication.setPalette(palette)

    def set_solarized_light(self):
        palette = QPalette()
        # Solarized Light
        palette.setColor(QPalette.Window, QColor(253, 246, 227))
        palette.setColor(QPalette.WindowText, QColor(101, 123, 131))
        palette.setColor(QPalette.Base, QColor(238, 232, 213))
        palette.setColor(QPalette.AlternateBase, QColor(253, 246, 227))
        palette.setColor(QPalette.ToolTipBase, QColor(238, 232, 213))
        palette.setColor(QPalette.ToolTipText, QColor(101, 123, 131))
        palette.setColor(QPalette.Text, QColor(101, 123, 131))
        palette.setColor(QPalette.Button, QColor(238, 232, 213))
        palette.setColor(QPalette.ButtonText, QColor(101, 123, 131))
        palette.setColor(QPalette.BrightText, QColor(220, 50, 47))
        palette.setColor(QPalette.Highlight, QColor(38, 139, 210))
        palette.setColor(QPalette.HighlightedText, Qt.white)
        QApplication.setStyle("Fusion")
        QApplication.setPalette(palette)

    def set_blue_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(23, 63, 95))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(15, 42, 64))
        palette.setColor(QPalette.AlternateBase, QColor(23, 63, 95))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(33, 87, 132))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, QColor(255, 163, 72))
        palette.setColor(QPalette.Highlight, QColor(0, 153, 204))
        palette.setColor(QPalette.HighlightedText, Qt.black)
        QApplication.setStyle("Fusion")
        QApplication.setPalette(palette)

    def set_green_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(34, 51, 34))
        palette.setColor(QPalette.WindowText, QColor(200, 225, 200))
        palette.setColor(QPalette.Base, QColor(51, 68, 51))
        palette.setColor(QPalette.AlternateBase, QColor(34, 51, 34))
        palette.setColor(QPalette.ToolTipBase, QColor(51, 68, 51))
        palette.setColor(QPalette.ToolTipText, QColor(200, 225, 200))
        palette.setColor(QPalette.Text, QColor(200, 225, 200))
        palette.setColor(QPalette.Button, QColor(68, 85, 68))
        palette.setColor(QPalette.ButtonText, QColor(200, 225, 200))
        palette.setColor(QPalette.BrightText, QColor(255, 105, 97))
        palette.setColor(QPalette.Highlight, QColor(85, 170, 85))
        palette.setColor(QPalette.HighlightedText, Qt.black)
        QApplication.setStyle("Fusion")
        QApplication.setPalette(palette)

class CreditsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # Credits Group
        credits_group = QGroupBox("Credits")
        credits_layout = QVBoxLayout()
        credits_layout.setContentsMargins(15, 15, 15, 15)
        credits_layout.setSpacing(12)

        # Title
        title = QLabel("Schedule I Save Editor")
        title.setAlignment(Qt.AlignCenter)
        title_font = title.font()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        credits_layout.addWidget(title)

        # Contributors
        contributors = [
            "Lead Developers: Cry4pt, NoedL",
            "UI Design: Cry4pt",
            "API Design: NoedL",
            "Achievement Unlocker: ArcturusS0",
            "Testing: Cry4pt, NoedL, Julefox",
            "Special Thanks:",
            "  - Schedule I Development Team",
            "  - Open Source Community",
            "  - Modding Community"
        ]
        
        for text in contributors:
            label = QLabel(text)
            label.setAlignment(Qt.AlignLeft)
            if "Special Thanks" in text:
                label_font = label.font()
                label_font.setBold(True)
                label.setFont(label_font)
            credits_layout.addWidget(label)

        # Version Info
        version = QLabel(f"Version: {CURRENT_VERSION}\nBuild Date: {datetime.now().strftime('%Y-%m-%d')}")
        version.setAlignment(Qt.AlignCenter)
        credits_layout.addWidget(version)

        # Repository Info
        repo_layout = QHBoxLayout()
        repo_layout.setContentsMargins(0, 10, 0, 0)
        repo_layout.setSpacing(10)  # Space between buttons
        
        # Create buttons with consistent width
        buttons = [
            ("Discord", "https://discord.gg/32r68Qm5Ba", 100),
            ("GitHub", "https://github.com/N0edL/Schedule-1-Save-Editor/tree/main", 100),
            ("Nexus Mods", "https://www.nexusmods.com/schedule1/mods/81", 100)
        ]

        # Add buttons with spacing
        repo_layout.addStretch()
        for text, url, width in buttons:
            btn = QPushButton(text)
            btn.setFixedWidth(width)
            btn.clicked.connect(lambda _, u=url: QDesktopServices.openUrl(QUrl(u)))
            repo_layout.addWidget(btn)
        repo_layout.addStretch()

        credits_layout.addLayout(repo_layout)
        credits_group.setLayout(credits_layout)
        layout.addWidget(credits_group)
        layout.addStretch()
        
        self.setLayout(layout)

class SaveEditorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Schedule I Save Editor")
        self.setGeometry(100, 100, 800, 600)
        self.center_window()

        def icon_path(relative_path):
            """ Get absolute path to resource, works for dev and for PyInstaller """
            try:
                # PyInstaller creates a temp folder and stores path in _MEIPASS
                base_path = sys._MEIPASS
            except Exception:
                base_path = os.path.abspath(".")
            return os.path.join(base_path, relative_path)
        
        self.setWindowIcon(QIcon(icon_path("icon.ico")))
        self.check_for_updates() 
        self.check_first_run()
        
    def center_window(self):
        """Center the window on the screen."""
        frame_geo = self.frameGeometry()
        screen_center = self.screen().availableGeometry().center()
        frame_geo.moveCenter(screen_center)
        self.move(frame_geo.topLeft())
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

    def check_for_updates(self):
        self.update_thread = QThread()
        self.update_worker = UpdateChecker()
        self.update_worker.moveToThread(self.update_thread)
        self.update_thread.started.connect(self.update_worker.run)
        self.update_worker.finished.connect(self.handle_update_result)
        self.update_worker.finished.connect(self.update_thread.quit)
        self.update_worker.finished.connect(self.update_worker.deleteLater)
        self.update_thread.finished.connect(self.update_thread.deleteLater)
        self.update_thread.start()

    def handle_update_result(self, result):
        latest_version, download_url = result
        if not latest_version or not download_url:
            return

        latest_clean = latest_version.lstrip('v')
        current_clean = CURRENT_VERSION.lstrip('v')

        if self.compare_versions(latest_clean, current_clean) > 0:
            reply = QMessageBox.question(
                self,
                "Update Available",
                f"New version {latest_version} is available (Current: v{CURRENT_VERSION}).\nWould you like to update now?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.download_and_apply_update(download_url)

    def download_and_apply_update(self, download_url):
        if not getattr(sys, 'frozen', False):
            QMessageBox.information(self, "Info", "Auto-update is only supported in the packaged executable.")
            return

        try:
            # Download the new executable
            downloads_dir = Path.home() / "Downloads"
            downloaded_exe = downloads_dir / os.path.basename(download_url)
            
            # Show download progress
            progress = QProgressDialog("Downloading update...", "Cancel", 0, 100, self)
            progress.setWindowTitle("Updating")
            progress.setWindowModality(Qt.WindowModal)
            
            def update_progress(count, block_size, total_size):
                percent = (count * block_size * 100) // total_size
                progress.setValue(percent)
                if progress.wasCanceled():
                    raise Exception("Download canceled")
            
            urllib.request.urlretrieve(download_url, downloaded_exe, update_progress)
            progress.close()

            # Create batch script
            current_exe = sys.executable
            current_dir = os.path.dirname(current_exe)
            bat_content = f"""@echo off
timeout /t 1 /nobreak >nul
taskkill /IM "{os.path.basename(current_exe)}" /F >nul 2>&1
del /F /Q "{current_exe}" >nul 2>&1
copy /Y "{downloaded_exe}" "{current_exe}" >nul 2>&1
start "" "{current_exe}"
del "%~f0"
"""
            # Write batch file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.bat', delete=False, encoding='utf-8') as bat_file:
                bat_file.write(bat_content)
                bat_path = bat_file.name

            subprocess.Popen(['cmd.exe', '/C', bat_path], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            sys.exit()

        except Exception as e:
            QMessageBox.critical(self, "Update Error", f"Failed to apply update: {str(e)}")

    def compare_versions(self, v1, v2):
        def parse_version(v):
            parts = []
            for part in v.split('.'):
                if part.isdigit():
                    parts.append(int(part))
                else:
                    break
            return parts
        
        parts1 = parse_version(v1)
        parts2 = parse_version(v2)

        for p1, p2 in zip(parts1, parts2):
            if p1 > p2:
                return 1
            elif p1 < p2:
                return -1

        if len(parts1) > len(parts2):
            return 1
        elif len(parts1) < len(parts2):
            return -1
        return 0

    def check_first_run(self):
        # Define the config directory in AppData
        config_dir = Path.home() / "AppData" / "Local" / "noedl.xyz" / "Schedule1Editor"
        config_dir.mkdir(parents=True, exist_ok=True)
        flag_file = config_dir / "first_run.flag"

        # Check if this is the first run
        if not flag_file.exists():
            # Show a dialog asking the user if they want to join Discord
            reply = QMessageBox.question(
                self,
                "Discord",
                "Would you like to join the Schedule I Save Editor Discord server?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No  # Default to "No"
            )
            
            # If the user clicks "Yes", open the Discord invite
            if reply == QMessageBox.Yes:
                QDesktopServices.openUrl(QUrl("https://discord.gg/32r68Qm5Ba"))
            
            # Create the flag file after the user's choice
            try:
                flag_file.touch()
            except Exception as e:
                print(f"Warning: Could not create first_run.flag: {e}")

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
        self.creation_time_label = QLabel()  # New time label
        self.playtime_label = QLabel()
        self.org_name_label = QLabel()
        self.online_money_label = QLabel()
        self.networth_label = QLabel()
        self.lifetime_earnings_label = QLabel()
        self.weekly_deposit_sum_label = QLabel()
        self.rank_label = QLabel()
        self.cash_balance_label = QLabel()

        # Add labels to layout
        layout.addRow("Game Version:", self.game_version_label)
        layout.addRow("Creation Date:", self.creation_date_label)
        layout.addRow("Creation Time:", self.creation_time_label)  # Add new row
        layout.addRow("Playtime:", self.playtime_label)
        layout.addRow("Organization Name:", self.org_name_label)
        layout.addRow("Cash Balance:", self.cash_balance_label)
        layout.addRow("Online Money:", self.online_money_label)
        layout.addRow("Networth:", self.networth_label)
        layout.addRow("Lifetime Earnings:", self.lifetime_earnings_label)
        layout.addRow("Weekly Deposit Sum:", self.weekly_deposit_sum_label)
        layout.addRow("Rank:", self.rank_label)

        # Button layout
        button_layout = QHBoxLayout()
        back_button = QPushButton("Back to Selection")
        back_button.clicked.connect(self.back_to_selection)
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
        self.creation_time_label.setText(info.get('creation_time', 'Unknown'))  # Set time
        self.org_name_label.setText(info.get('organisation_name', 'Unknown'))
        self.cash_balance_label.setText(f"${info.get('cash_balance', 0):,}")
        self.online_money_label.setText(f"${info.get('online_money', 0):,}")
        self.networth_label.setText(f"${info.get('networth', 0):,}")
        self.lifetime_earnings_label.setText(f"${info.get('lifetime_earnings', 0):,}")
        self.weekly_deposit_sum_label.setText(f"${info.get('weekly_deposit_sum', 0):,}")
        self.rank_label.setText(f"{info.get('current_rank', 'Unknown')} (Rank: {info.get('rank_number', 0)}, Tier: {info.get('tier', 0)})")
        self.playtime_label.setText(info.get('playtime', '0d, 0h, 0m, 0s'))

    def create_edit_save_page(self):
        page = QWidget()
        layout = QVBoxLayout()

        tab_widget = QTabWidget()
        self.money_tab = MoneyTab()
        self.rank_tab = RankTab()
        self.products_tab = ProductsTab(main_window=self)
        self.properties_tab = PropertiesTab(main_window=self)
        self.unlocks_tab = UnlocksTab(main_window=self)
        self.inventory_tab = InventoryTab(main_window=self)
        self.misc_tab = MiscTab(main_window=self)
        self.backups_tab = BackupsTab(main_window=self)
        self.theme_tab = ThemeTab()
        self.credits_tab = CreditsTab()
        
        tab_widget.addTab(self.money_tab, "Money")
        tab_widget.addTab(self.rank_tab, "Rank")
        tab_widget.addTab(self.products_tab, "Products")
        tab_widget.addTab(self.properties_tab, "Properties")
        tab_widget.addTab(self.unlocks_tab, "Unlocks")
        tab_widget.addTab(self.inventory_tab, "Inventory")
        tab_widget.addTab(self.misc_tab, "Misc")
        tab_widget.addTab(self.backups_tab, "Backups")
        tab_widget.addTab(self.theme_tab, "Themes")
        tab_widget.addTab(self.credits_tab, "Credits")

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
        if is_game_running():
            QMessageBox.information(
            self,
            "Game Running",
            "The game is currently running.\nEnsure you are on the main menu and not loaded in to a save before editing.",
            )
        self.update_edit_save_page()
        self.backups_tab.refresh_backup_list()
        self.stacked_widget.setCurrentWidget(self.edit_save_page)

    def update_edit_save_page(self):
            info = self.manager.get_save_info()
            self.money_tab.set_data(info)
            self.rank_tab.set_data(info)
            self.misc_tab.set_data(info)
            self.misc_tab.update_vars_warning()
            self.properties_tab.load_property_types()
            self.properties_tab.load_plastic_pots()
            self.backups_tab.refresh_backup_list()
            self.inventory_tab.refresh_data()
            self.misc_tab.load_save_folders()

    def apply_changes(self):
            try:
                money_data = self.money_tab.get_data()
                rank_data = self.rank_tab.get_data()
                misc_data = self.misc_tab.get_data()

                # Backup stats files
                stats_files = [
                    self.manager.current_save / "Money.json",
                    self.manager.current_save / "Rank.json",
                    self.manager.current_save / "Game.json",
                    self.manager.current_save / "Players/Player_0/Inventory.json"
                ]
                self.manager.create_feature_backup("Stats", stats_files)
                self.backups_tab.refresh_backup_list()

                # Apply money changes
                self.manager.set_online_money(money_data["online_money"])
                self.manager.set_networth(money_data["networth"])
                self.manager.set_lifetime_earnings(money_data["lifetime_earnings"])
                self.manager.set_weekly_deposit_sum(money_data["weekly_deposit_sum"])
                self.manager.set_cash_balance(money_data["cash_balance"])

                # Apply rank changes
                self.manager.set_rank(rank_data["current_rank"])
                self.manager.set_rank_number(rank_data["rank_number"])
                self.manager.set_tier(rank_data["tier"])

                self.manager.set_organisation_name(misc_data["organisation_name"])
                
                # Update ConsoleEnabled in Game.json Settings
                game_data = self.manager._load_json_file("Game.json")
                # Ensure Settings dictionary exists
                game_data.setdefault("Settings", {})
                game_data["Settings"]["ConsoleEnabled"] = misc_data["console_enabled"]
                self.manager._save_json_file("Game.json", game_data)

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