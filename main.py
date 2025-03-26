import re

import sys, json
from lib.manager import SaveManager
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget, QWidget,
    QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QFormLayout, QLineEdit, QComboBox, QPushButton,
    QMessageBox, QTabWidget, QCheckBox, QGroupBox, QTextEdit
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QRegularExpressionValidator, QIntValidator

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
        
        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(8)
        form_layout.setHorizontalSpacing(15)
        form_layout.setContentsMargins(5, 5, 5, 10)

        self.property_combo = QComboBox()
        form_layout.addRow(QLabel("Property Type:"), self.property_combo)

        self.quantity_edit = QLineEdit()
        self.quantity_edit.setValidator(QIntValidator(0, 1000000))
        self.quantity_edit.setFixedHeight(28)
        form_layout.addRow(QLabel("Quantity:"), self.quantity_edit)

        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["Trash", "Poor", "Standard", "Premium", "Heavenly"])
        self.quality_combo.setFixedHeight(28)
        form_layout.addRow(QLabel("Quality:"), self.quality_combo)

        self.packaging_combo = QComboBox()
        self.packaging_combo.addItems(["none", "baggie", "jar"])
        self.packaging_combo.setFixedHeight(28)
        form_layout.addRow(QLabel("Packaging:"), self.packaging_combo)

        self.update_combo = QComboBox()
        self.update_combo.addItems(["both", "weed", "item"])
        self.update_combo.setFixedHeight(28)
        form_layout.addRow(QLabel("Update Type:"), self.update_combo)

        layout.addLayout(form_layout)
        
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
            
            self.property_combo.addItem("all", "all")
            
            for dir_name in dirs:
                normalized = dir_name.strip().lower()
                display_name = dir_mapping.get(normalized, dir_name)
                self.property_combo.addItem(display_name, dir_name)
            
            self.property_combo.model().sort(0)
                
        except Exception as e:
            print(f"Error loading properties: {str(e)}")
            self.property_combo.addItem("Error loading properties", "error")

    def update_properties(self):
        """Handle property update button click"""
        if not self.main_window or not self.main_window.manager.current_save:
            QMessageBox.critical(self, "Error", "No save file loaded")
            return

        try:
            property_type = self.property_combo.currentData()
            quantity = int(self.quantity_edit.text())
            packaging = self.packaging_combo.currentText()
            update_type = self.update_combo.currentText()
            quality = self.quality_combo.currentText()

            updated = self.main_window.manager.update_property_quantities(
                property_type, quantity, packaging, update_type, quality
            )
            QMessageBox.information(self, "Success", 
                                f"Updated {updated} property locations")
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", 
                            "Please enter a valid quantity")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update properties: {str(e)}")

class ProductsTab(QWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        discovery_group = QGroupBox("Product Discovery")
        discovery_layout = QVBoxLayout()
        discovery_layout.setContentsMargins(10, 10, 10, 10)
        
        self.discover_cocaine_checkbox = QCheckBox("Cocaine")
        self.discover_meth_checkbox = QCheckBox("Meth")
        discovery_layout.addWidget(self.discover_cocaine_checkbox)
        discovery_layout.addWidget(self.discover_meth_checkbox)
        discovery_layout.addSpacing(5)
        
        discover_button = QPushButton("Discover Selected")
        discover_button.setFixedHeight(32)
        discover_button.clicked.connect(self.discover_selected_products)
        discovery_layout.addWidget(discover_button, 0, Qt.AlignCenter)
        discovery_group.setLayout(discovery_layout)

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

        layout.addWidget(discovery_group)
        layout.addWidget(generation_group)
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def discover_selected_products(self):
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
            self.main_window.manager.add_discovered_products(products_to_discover)
            QMessageBox.information(self, "Success", "Successfully discovered selected products!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to discover products: {str(e)}")

    def generate_products(self):
        if not self.main_window or not hasattr(self.main_window, 'manager'):
            QMessageBox.critical(self, "Error", "Save manager not available.")
            return

        try:
            count = int(self.count_input.text())
            id_length = int(self.id_length_input.text())
            price = int(self.price_input.text())
            add_to_listed = self.add_to_listed_checkbox.isChecked()
            
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

        unlock_group = QGroupBox("Unlock Actions")
        unlock_layout = QVBoxLayout()
        unlock_layout.setContentsMargins(10, 10, 10, 10)
        unlock_layout.setSpacing(10)

        items_weeds_btn = QPushButton("Unlock All Items and Weeds")
        items_weeds_btn.setFixedHeight(32)
        items_weeds_btn.clicked.connect(self.unlock_items_weeds)
        unlock_layout.addWidget(QLabel("Sets Rank & tier To 999 To Unlock All Items/Weeds:"))
        unlock_layout.addWidget(items_weeds_btn)
        unlock_layout.addSpacing(10)

        props_btn = QPushButton("Unlock All Properties")
        props_btn.setFixedHeight(32)
        props_btn.clicked.connect(self.unlock_properties)
        unlock_layout.addWidget(QLabel("Downloads & Enables All Property Types:"))
        unlock_layout.addWidget(props_btn)
        unlock_layout.addSpacing(10)

        business_btn = QPushButton("Unlock All Businesses")
        business_btn.setFixedHeight(32)
        business_btn.clicked.connect(self.unlock_businesses)
        unlock_layout.addWidget(QLabel("Downloads & Enables All Business Types:"))
        unlock_layout.addWidget(business_btn)

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
            
            result = self.main_window.manager.unlock_all_items_weeds()
            if result == 1:
                QMessageBox.information(self, "Success", "Unlocked all items and weeds!")
            else:
                QMessageBox.warning(self, "Warning", "Failed to unlock items and weeds.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to unlock items and weeds: {str(e)}")

    def unlock_properties(self):
        """Handle the unlock properties button click."""
        try:
            if not self.main_window or not self.main_window.manager.current_save:
                QMessageBox.critical(self, "Error", "No save file loaded")
                return
            
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
            
            updated = self.main_window.manager.unlock_all_businesses()
            QMessageBox.information(self, "Success", f"Unlocked {updated} businesses!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to unlock businesses: {str(e)}")

    def update_npc_relationships(self):
        try:
            if not self.main_window.manager.current_save:
                return
            
            updated = self.main_window.manager.update_npc_relationships_function()
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

        org_group = QGroupBox("Organization Settings")
        org_layout = QFormLayout()
        org_layout.setContentsMargins(10, 10, 10, 10)
        self.organisation_name_input = QLineEdit()
        org_layout.addRow(QLabel("Organization Name:"), self.organisation_name_input)
        org_group.setLayout(org_layout)
        layout.addWidget(org_group)

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

        vars_group = QGroupBox("Variable Management")
        vars_layout = QVBoxLayout()
        vars_layout.setContentsMargins(10, 10, 10, 10)
        vars_layout.addWidget(QLabel("WARNING: Modifies variables in:\n- Variables/\n- Players/Player_*/Variables/"))
        self.vars_btn = QPushButton("Modify All Variables")
        self.vars_btn.setFixedHeight(32)
        self.vars_btn.clicked.connect(self.modify_variables)
        vars_layout.addWidget(self.vars_btn)
        vars_group.setLayout(vars_layout)
        layout.addWidget(vars_group)

        layout.addStretch()
        self.setLayout(layout)

    def set_data(self, info):
        self.organisation_name_input.setText(info.get("organisation_name", ""))

    def get_data(self):
        return {
            "organisation_name": self.organisation_name_input.text()
        }

    def complete_all_quests(self):
        if not self.main_window or not self.main_window.manager.current_save:
            QMessageBox.critical(self, "Error", "No save file loaded")
            return

        try:
            quests_completed, objectives_completed = self.main_window.manager.complete_all_quests()
            QMessageBox.information(
                self,
                "Quests Completed",
                f"Marked {quests_completed} quests and {objectives_completed} objectives as completed!"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to complete quests:\n{str(e)}"
            )

    def modify_variables(self):
        if not hasattr(self, 'main_window') or not self.main_window.manager.current_save:
            QMessageBox.critical(self, "Error", "No save file loaded")
            return

        try:
            count = self.main_window.manager.modify_variables()
            QMessageBox.information(
                self,
                "Variables Modified",
                f"Successfully updated {count} variables!"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to modify variables:\n{str(e)}"
            )

class NPCsTab(QWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setPlaceholderText("Paste the NPC log here...")
        layout.addWidget(self.log_text)

        generate_button = QPushButton("Generate NPC Files")
        generate_button.clicked.connect(self.generate_npc_files)
        layout.addWidget(generate_button)

        recruit_button = QPushButton("Recruit  All Dealers")
        recruit_button.clicked.connect(self.recruit_all_dealers)
        layout.addWidget(recruit_button)

        self.setLayout(layout)
    
    def parse_npc_log(self, log_text: str) -> list[tuple[str, str]]:
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

    def generate_npc_files(self):
        """Handle the generate button click."""
        log_text = self.log_text.toPlainText()
        if not log_text:
            QMessageBox.warning(self, "No Log", "Please paste the NPC log.")
            return

        npcs = self.parse_npc_log(log_text)
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

class SaveEditorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Schedule I Save Editor")
        self.setGeometry(100, 100, 800, 600)
        self.manager = SaveManager()  # Assume SaveManager is defined elsewhere
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.save_selection_page = self.create_save_selection_page()
        self.save_info_page = self.create_save_info_page()
        self.edit_save_page = self.create_edit_save_page()

        self.stacked_widget.addWidget(self.save_selection_page)
        self.stacked_widget.addWidget(self.save_info_page)
        self.stacked_widget.addWidget(self.edit_save_page)

        self.populate_save_table()
        self.stacked_widget.setCurrentWidget(self.save_selection_page)

        self.apply_dark_theme()

    def apply_dark_theme(self):
        """Apply a dark theme to the application."""
        dark_stylesheet = """
        QWidget {
            background-color: #2b2b2b;
            color: #ffffff;
            font-family: Arial;
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
        QTableWidget::item:selected {
            background-color: #5c5f61;
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

    def create_save_selection_page(self):
        """Create the save selection page with a table and load button."""
        page = QWidget()
        layout = QVBoxLayout()

        self.save_table = QTableWidget()
        self.save_table.setColumnCount(2)
        self.save_table.setHorizontalHeaderLabels(["Organization Name", "Save Folders"])
        self.save_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.save_table.setSelectionMode(QTableWidget.SingleSelection)
        self.save_table.horizontalHeader().setStretchLastSection(True)

        load_button = QPushButton("Load Selected Save")
        load_button.clicked.connect(self.load_selected_save)

        layout.addWidget(self.save_table)
        layout.addWidget(load_button)
        page.setLayout(layout)
        return page

    def populate_save_table(self):
        """Populate the save table with data from save folders."""
        saves = self.manager.get_save_folders()
        self.save_table.setRowCount(len(saves))
        for row, save in enumerate(saves):
            self.save_table.setItem(row, 0, QTableWidgetItem(save['organisation_name']))
            self.save_table.setItem(row, 1, QTableWidgetItem(save['name']))
            self.save_table.item(row, 0).setData(Qt.UserRole, save['path'])
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

        self.game_version_label = QLabel()
        self.creation_date_label = QLabel()
        self.org_name_label = QLabel()
        self.online_money_label = QLabel()
        self.networth_label = QLabel()
        self.lifetime_earnings_label = QLabel()
        self.weekly_deposit_sum_label = QLabel()
        self.rank_label = QLabel()
        self.play_time_label = QLabel()

        layout.addRow("Game Version:", self.game_version_label)
        layout.addRow("Creation Date:", self.creation_date_label)
        layout.addRow("Organization Name:", self.org_name_label)
        layout.addRow("Online Money:", self.online_money_label)
        layout.addRow("Networth:", self.networth_label)
        layout.addRow("Lifetime Earnings:", self.lifetime_earnings_label)
        layout.addRow("Weekly Deposit Sum:", self.weekly_deposit_sum_label)
        layout.addRow("Rank:", self.rank_label)

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
        self.org_name_label.setText(info.get('organisation_name', 'Unknown'))
        self.online_money_label.setText(f"${info.get('online_money', 0):,}")
        self.networth_label.setText(f"${info.get('networth', 0):,}")
        self.lifetime_earnings_label.setText(f"${info.get('lifetime_earnings', 0):,}")
        self.weekly_deposit_sum_label.setText(f"${info.get('weekly_deposit_sum', 0):,}")
        self.rank_label.setText(f"{info.get('current_rank', 'Unknown')} (Rank: {info.get('rank_number', 0)}, Tier: {info.get('tier', 0)})")

    def create_edit_save_page(self):
            """Create the edit save page with tabs and buttons."""
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

            tab_widget.addTab(self.money_tab, "Money")
            tab_widget.addTab(self.rank_tab, "Rank")
            # tab_widget.addTab(self.products_tab, "Products")
            tab_widget.addTab(self.properties_tab, "Properties")
            # tab_widget.addTab(self.unlocks_tab, "Unlocks")
            tab_widget.addTab(self.misc_tab, "Misc")
            tab_widget.addTab(self.npcs_tab, "NPCs")

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
        self.stacked_widget.setCurrentWidget(self.edit_save_page)

    def update_edit_save_page(self):
        """Update the edit save page with current save data."""
        info = self.manager.get_save_info()
        self.money_tab.set_data(info)
        self.rank_tab.set_data(info)
        self.misc_tab.set_data(info)
        self.properties_tab.load_property_types()

    def apply_changes(self):
        """Apply changes from the edit save page to the save data."""
        try:
            money_data = self.money_tab.get_data()
            rank_data = self.rank_tab.get_data()
            misc_data = self.misc_tab.get_data()

            self.manager.set_online_money(money_data["online_money"])
            self.manager.set_networth(money_data["networth"])
            self.manager.set_lifetime_earnings(money_data["lifetime_earnings"])
            self.manager.set_weekly_deposit_sum(money_data["weekly_deposit_sum"])
            self.manager.set_rank(rank_data["current_rank"])
            self.manager.set_rank_number(rank_data["rank_number"])
            self.manager.set_tier(rank_data["tier"])
            self.manager.set_organisation_name(misc_data["organisation_name"])
            self.manager.set_play_time(misc_data["play_time_seconds"])

            QMessageBox.information(self, "Success", "Changes applied successfully!")
            self.update_save_info_page()
            self.stacked_widget.setCurrentWidget(self.save_info_page)
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter valid integer values for all fields.")

    def back_to_selection(self):
        """Refresh the save table and navigate back to the save selection page."""
        self.populate_save_table()
        self.stacked_widget.setCurrentWidget(self.save_selection_page)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = QWidget()
    window = SaveEditorWindow()
    window.show()
    sys.exit(app.exec())