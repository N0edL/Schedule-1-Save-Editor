# Schedule I Save File Editor

![Banner](https://github.com/user-attachments/assets/55a8e085-f339-49cb-8ea6-31a5945d4095)

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)
![Version](https://img.shields.io/github/v/release/N0edL/Schedule-1-Save-Editor?display_name=release&label=version)
![PySide6](https://img.shields.io/badge/PySide6-GUI%20Framework-success)

## Overview
The **Schedule I Save File Editor** is a comprehensive graphical tool for modifying save files in the game "Schedule I." Built with PySide6, it offers advanced editing capabilities with a user-friendly interface and dark theme support. Key features include:

- Complete game state management
- Deep customization of all game aspects
- Non-destructive editing with smart backups
- Safe mod integration
- Multi-theme support

## Features

### 💰 Financial Control
- Edit cash balance in player inventory
- Modify online money, net worth, and lifetime earnings
- Adjust weekly deposit limits and financial history
- Set custom net worth and earnings values
- Modify banking system parameters

### ⚡ Rank & Progression
- Set organization name and current rank
- Modify rank number (0-999) and tier level
- Unlock all items/weeds by maxing rank (999)
- Complete all quests and objectives instantly
- Reset progression parameters

### 🧪 Product Management
- Discover/undiscover cocaine and meth
- Generate custom products with:
  - Custom IDs/Names (18k+ name variations)
  - Drug type selection (0-2)
  - Property combinations (1-34 traits)
  - Pricing and bulk listing options
- Bulk delete generated products
- Manage product discovery states

### 🏘️ Property & Business
- Set quantities/quality for all properties
- Mass-update storage containers (weed/items)
- One-click unlock for all properties
- Instant business acquisition
- Modify packaging types and quality levels
- Bulk edit property configurations

### 🤝 NPC Relationships
- Import NPCs from game logs
- Recruit all dealers instantly
- Max relationship levels with all characters
- Generate NPC files from detected IDs
- Full relationship data customization
- Bulk NPC status modifications

### 🔄 Backup & Restore
- Automatic initial backup on load
- Feature-specific version history
- Single-feature restoration
- Full save rollback capability
- Backup management interface
- Selective backup deletion

### 🧺 Inventory Management
- Edit dealer inventories (cash/items/drugs)
- Modify vehicle storage contents
- Bulk edit quantities/quality/packaging
- Add/remove inventory items
- Real-time inventory preview

### 🎯 Quest Management
- Complete all quests instantly
- Mark all objectives as finished
- Reset quest progress
- Bulk quest state modifications

### 🔧 Variable Editor
- Mass-edit boolean variables
- Modify numerical variables
- Toggle game flags and switches
- Safe variable modification protocols

### 🔌 Mod Support
- Achievement Unlocker mod installer
- MelonLoader integration
- Safe mod installation verification
- Mod compatibility checks

### 🆕 Save Management
- Generate new save files
- Delete existing saves
- Manage multiple save slots
- Custom organization naming
- Save file integrity checks

### 🎨 UI Customization
- Multiple theme options:
  - Dark/Light modes
  - Dracula/Solarized themes
  - Custom color schemes
- System theme integration
- Responsive interface design

### 📜 Credits & Info
- Contributor acknowledgments
- Detailed version information
- Direct GitHub repository link
- Build date tracking
- Community recognition

## ⚠️ Security Notes

### Antivirus Considerations
Security solutions may flag the editor due to:
- PyInstaller executable packaging
- Memory manipulation capabilities
- File operation patterns
- Mod installation processes

| Security Aspect       | Recommendation                |
|-----------------------|-------------------------------|
| False Positives       | Add exception to antivirus    |
| Source Verification   | Review code on GitHub         |
| Mod Installations     | Verify mod sources            |
| Safe Alternative      | Run Python version directly   |

### Verification Steps
1. Check [VirusTotal analysis](https://www.virustotal.com/)
2. Compare hashes with GitHub release
3. Inspect source code integrity
4. Verify MelonLoader mod signatures
5. Validate backup file integrity

## 🚀 Getting Started

### Requirements
- Python 3.9+
- Windows 10/11
- Schedule I game installation
- 500MB free disk space

### Installation
```bash
# Clone repository
git clone https://github.com/N0edL/Schedule-1-Save-Editor.git
cd Schedule-1-Save-Editor

# Install dependencies
pip install -r requirements.txt

# Launch editor
python main.py
