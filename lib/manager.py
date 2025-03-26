import json, re, os, string, random, urllib.request, shutil, rarfile, tempfile
from pathlib import Path
from typing import Dict, List, Optional, Union

class SaveManager:
    def __init__(self):
        self.savefile_dir = self._find_save_directory()
        self.current_save: Optional[Path] = None
        self.save_data: Dict[str, Union[dict, list]] = {}

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

        directories = []
        if property_type == "all":
            directories = [d for d in properties_path.iterdir() if d.is_dir()]
        else:
            target_dir = properties_path / property_type
            if target_dir.exists() and target_dir.is_dir():
                directories = [target_dir]

        for prop_dir in directories:
            objects_path = prop_dir / "Objects"
            if not objects_path.exists():
                continue

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
                                item["Quality"] = quality
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

        root_vars = self.current_save / "Variables"
        if root_vars.exists():
            variables_dirs.append(root_vars)

        for i in range(10):
            player_vars = self.current_save / f"Players/Player_{i}/Variables"
            if player_vars.exists():
                variables_dirs.append(player_vars)

        for var_dir in variables_dirs:
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
                rar_path = Path(temp_dir) / "Properties.rar"
                extract_path = Path(temp_dir) / "extracted"
                extract_path.mkdir()
                
                urllib.request.urlretrieve(
                    "https://github.com/N0edL/Schedule-1-Save-Editor/raw/refs/heads/main/files/Properties.rar",
                    rar_path
                )
                
                with rarfile.RarFile(rar_path) as rf:
                    rf.extractall(extract_path)
                
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
                "GameVersion": "0.2.9f4",
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
                rar_path = Path(temp_dir) / "Businesses.rar"
                extract_path = Path(temp_dir) / "extracted"
                extract_path.mkdir()
                
                urllib.request.urlretrieve(
                    "https://github.com/N0edL/Schedule-1-Save-Editor/raw/refs/heads/main/files/Businesses.rar",
                    rar_path
                )
                
                with rarfile.RarFile(rar_path) as rf:
                    rf.extractall(extract_path)
                
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
                "GameVersion": "0.2.9f4",
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

                npc_json_path = folder_path / "NPC.json"
                relationship_json_path = folder_path / "Relationship.json"

                npc_data = {
                    "DataType": "NPCData",
                    "DataVersion": 0,
                    "GameVersion": "0.3.3f10",
                    "ID": npc_id
                }

                relationship_data = {
                    "DataType": "RelationshipData",
                    "DataVersion": 0,
                    "GameVersion": "0.3.3f10",
                    "RelationDelta": 999,
                    "Unlocked": True,
                    "UnlockType": 1
                }

                with open(npc_json_path, "w", encoding="utf-8") as f:
                    json.dump(npc_data, f, indent=4)

                with open(relationship_json_path, "w", encoding="utf-8") as f:
                    json.dump(relationship_data, f, indent=4)

    def recruit_all_dealers(self):
        """Set 'Recruited' to true for all NPCs with 'DataType': 'DealerData'."""
        if not self.current_save:
            raise ValueError("No save loaded")
        
        npcs_dir = self.current_save / "NPCs"
        if not npcs_dir.exists():
            return 0
        
        updated_count = 0
        for npc_folder in npcs_dir.iterdir():
            if npc_folder.is_dir():
                npc_json_path = npc_folder / "NPC.json"
                if npc_json_path.exists():
                    try:
                        with open(npc_json_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        if data.get("DataType") == "DealerData" and "Recruited" in data:
                            data["Recruited"] = True
                            with open(npc_json_path, 'w', encoding='utf-8') as f:
                                json.dump(data, f, indent=4)
                            updated_count += 1
                    except json.JSONDecodeError:
                        continue
        return updated_count

    def update_npc_relationships_function(self):
        """Update NPC relationships and recruit dealers using proper path handling and error reporting."""
        try:
            if not self.current_save:
                raise ValueError("No save loaded")

            npcs_dir = self.current_save / "NPCs"
            npcs_dir.mkdir(parents=True, exist_ok=True)

            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                rar_file = temp_path / "NPCs.rar"
                extract_path = temp_path / "extracted"
                
                urllib.request.urlretrieve(
                    "https://github.com/N0edL/Schedule-1-Save-Editor/raw/refs/heads/main/files/NPCs.rar",
                    str(rar_file)
                )

                try:
                    with rarfile.RarFile(rar_file) as rf:
                        rf.extractall(str(extract_path))
                except rarfile.RarCannotExec:
                    raise RuntimeError("UnRAR utility required - install unrar and ensure it's in PATH")

                template_dir = extract_path / "NPCs"
                if not template_dir.exists():
                    raise FileNotFoundError("NPC template directory missing in archive")

                existing_npcs = {npc.name for npc in npcs_dir.iterdir() if npc.is_dir()}
                for npc_template in template_dir.iterdir():
                    if npc_template.is_dir() and npc_template.name not in existing_npcs:
                        shutil.copytree(npc_template, npcs_dir / npc_template.name)

            updated_count = 0
            for npc_folder in npcs_dir.iterdir():
                if not npc_folder.is_dir():
                    continue

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

                npc_file = npc_folder / "NPC.json"
                if npc_file.exists():
                    npc_data = self._load_json_file(npc_file.relative_to(self.current_save))
                    if npc_data.get("DataType") == "DealerData":
                        npc_data["Recruited"] = True
                        self._save_json_file(npc_file.relative_to(self.current_save), npc_data)

            return updated_count

        except Exception as e:
            raise RuntimeError(f"NPC relationship update failed: {str(e)}")

        """Update save data with changes"""
        # Still need to implement this :)_
        pass