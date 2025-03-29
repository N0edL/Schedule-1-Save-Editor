# Schedule I Save File Editor

![Banner](https://github.com/user-attachments/assets/55a8e085-f339-49cb-8ea6-31a5945d4095)


## Overview
The **Schedule I Save File Editor** is a graphical user interface (GUI) tool designed to modify save files for the game "Schedule I." Built with PySide6, it features:

- Dark theme interface with tabbed navigation
- Advanced game data modification capabilities
- Built-in backup system with version control
- NPC relationship management tools
- Safe editing workflow with automatic backups

## Features

### 💰 Financial Control
- Edit online money balance, net worth, lifetime earnings, and weekly deposits
- Modify cash balance directly in player inventory

### 📈 Rank & Progression
- Adjust organization name, current rank, rank number, and tier
- Unlock all items/weeds by maxing rank (999)

### 🧪 Product Management
- Discover/undiscover cocaine and meth
- Generate custom products with unique IDs/names, properties, and pricing
- Bulk delete generated products

### 🏠 Property & Business
- Set quantities/quality for all properties
- Unlock all properties and businesses with one click
- Modify storage container contents (weed/items)

### 🤝 NPC Relationships
- Import NPCs from game logs
- Recruit all dealers instantly
- Max relationship levels with all NPCs

### 🔄 Backup & Restore
- Automatic initial backup
- Feature-specific versioning
- Full restore capability

### ⚙️ Advanced Tools
- Complete all quests/objectives
- Toggle boolean variables
- Install achievement unlocker mod
- Generate new save files

## ⚠️ Security Notes

### Antivirus Considerations
Some security solutions may flag the `.exe` version due to:
- PyInstaller packaging
- Memory editing capabilities
- Unusual file operations

| Security Aspect       | Recommendation                |
|-----------------------|-------------------------------|
| False Positives       | Whitelist in antivirus        |
| Source Verification   | Review code on GitHub         |
| Safe Alternative      | Use Python version directly   |

### Verification Steps
1. Check [VirusTotal analysis](https://www.virustotal.com/)
2. Compare hashes with GitHub release
3. Inspect source code integrity

## 🚀 Getting Started

### Requirements
- Python 3.9+

### Installation
```bash
# Clone repository
git clone https://github.com/N0edL/Schedule-1-Save-Editor.git
cd Schedule-1-Save-Editor

# Install dependencies from requirments.txt
pip install -r requirements.txt

# Launch editor
python main.py
