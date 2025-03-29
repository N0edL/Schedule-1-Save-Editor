# Schedule I Save File Editor

![Banner](https://github.com/user-attachments/assets/55a8e085-f339-49cb-8ea6-31a5945d4095)

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)
![Version](https://img.shields.io/badge/version-1.0.3-green)
![PySide6](https://img.shields.io/badge/PySide6-GUI%20Framework-success)

## Overview
The **Schedule I Save File Editor** is a powerful graphical tool for modifying save files in the game "Schedule I." Built with PySide6, it offers advanced editing capabilities with a user-friendly dark theme interface. Key features include:

- Comprehensive financial and progression management
- Deep NPC relationship customization
- Advanced product generation system
- Bulk property/business operations
- Smart backup system with version control

## Features

### 💰 Financial Control
- Edit cash balance in player inventory
- Modify online money, net worth, and lifetime earnings
- Adjust weekly deposit limits and financial history

### ⚡ Rank & Progression
- Set organization name and current rank
- Modify rank number (0-999) and tier level
- Unlock all items/weeds by maxing rank (999)
- Complete all quests and objectives instantly

### 🧪 Product Management
- Discover/undiscover cocaine and meth
- Generate custom products with:
  - Custom IDs/Names (18k+ name variations)
  - Drug type selection (0-2)
  - Property combinations (1-34 traits)
  - Pricing and bulk listing options
- Bulk delete generated products

### 🏘️ Property & Business
- Set quantities/quality for all properties
- Mass-update storage containers (weed/items)
- One-click unlock for all properties
- Instant business acquisition
- Modify packaging types and quality levels

### 🤝 NPC Relationships
- Import NPCs from game logs
- Recruit all dealers instantly
- Max relationship levels with all characters
- Generate NPC files from detected IDs
- Full relationship data customization

### 🔄 Backup & Restore
- Automatic initial backup on load
- Feature-specific version history
- Single-feature restoration
- Full save rollback capability
- Backup management interface

### ⚙️ Advanced Tools
- Boolean variable mass-editing
- Achievement unlocker mod installer
- New save file generation
- Playtime statistics editing
- Game version modification
- MelonLoader integration

## ⚠️ Security Notes

### Antivirus Considerations
Some security solutions may flag the editor due to:
- PyInstaller executable packaging
- Memory manipulation capabilities
- Unusual file operations patterns

| Security Aspect       | Recommendation                |
|-----------------------|-------------------------------|
| False Positives       | Add exception to antivirus    |
| Source Verification   | Review code on GitHub         |
| Safe Alternative      | Run Python version directly   |

### Verification Steps
1. Check [VirusTotal analysis](https://www.virustotal.com/)
2. Compare hashes with GitHub release
3. Inspect source code integrity
4. Verify MelonLoader mod signatures

## 🚀 Getting Started

### Requirements
- Python 3.9+
- Windows 10/11
- Schedule I game installation

### Installation
```bash
# Clone repository
git clone https://github.com/N0edL/Schedule-1-Save-Editor.git
cd Schedule-1-Save-Editor

# Install dependencies
pip install -r requirements.txt

# Launch editor
python main.py
