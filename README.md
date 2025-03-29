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

### Save Management
- **Save Selection:**
  - View all saves in a sortable table
  - Display organization names and folder structures
  - Load saves with one click

- **Save Information:**
  - Detailed save metadata display:
    - Game version compatibility check
    - Creation timestamp analysis
    - Financial overview (money, networth, earnings)
    - Rank progression tracking

### Editing Capabilities
- **Core Modifications:**
  - 💰 Money Editor: 
    - Modify online balance (up to $999,999,999)
    - Adjust networth and lifetime earnings
    - Configure weekly deposit sums
  
  - 🏆 Rank System: 
    - Set rank tier (Street → Kingpin)
    - Modify numerical rank values (0-100)
    - Customize tier progression

- **Property Management:**
  - Bulk edit item properties:
    - Quantities (0-1,000,000 units)
    - Quality levels (Trash ➔ Heavenly)
    - Packaging types (Baggies/Jars)
  - Apply changes to:
    - Specific property types
    - Weed/items/both categories
    - All properties simultaneously

- **Product System:**
  - 🧪 Generate custom products:
    - Customizable ID lengths (5-20 chars)
    - Set market prices
    - Add to discovery/listings
  - Manage existing products:
    - Discover/undiscover cocaine/meth
    - Delete generated products

- **Unlockables:**
  - 🔓 One-click unlocks:
    - All items/weeds (Rank 999)
    - Complete property collection
    - Unlock all business/properties types
    - Unlock all NPCs
  - Quest Management:
    - Instant complete all quests
    - Auto-finish objectives

- **NPC Tools:**
  - 👥 NPC Generator:
    - Create from game logs
    - Recruit all dealers
    - Max relationship levels
  - Dealer Management:
    - Bulk recruit dealers
    - Configure dealer statuses

### Safety Features
- 🔄 Backup System:
  - Automatic initial backups
  - Feature-specific versioning
  - One-click restore points
  - Bulk backup deletion

### Utilities
- 🛠️ Advanced Tools:
  - Organization name editor
  - Variable modifier (bool/numeric)
  - Achievement Unlocker mod installer
  - New save generator (5 slot limit)

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
