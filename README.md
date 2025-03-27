# Schedule I Save File Editor

## Overview
The **Schedule I Save File Editor** is a graphical user interface (GUI) tool designed to edit save files for the game "Schedule I." Built with PySide6, it allows users to select save files, view detailed information, and modify various game data including money, rank, properties, products, NPCs, and more. The editor features a dark theme, a tabbed interface, and built-in backup functionality for a seamless and safe editing experience.

## Features
- **Save Selection:**
  - View a table of save files with organization names and folder names.
  - Load a selected save to proceed.

- **Save Information:**
  - Displays details about the selected save:
    - Game version
    - Creation date
    - Organization name
    - Online money, networth, lifetime earnings, weekly deposit sum
    - Rank (current rank, rank number, tier)
  - Navigate back to save selection or proceed to edit.

- **Edit Save Data:**
  - **Money:** Modify online money, networth, lifetime earnings, and weekly deposit sum (up to 10-digit integers).
  - **Rank:** Adjust current rank (Street, Dealer, Supplier, Distributor, Kingpin), rank number (0-100), and tier (0-100).
  - **Properties:** 
    - Update item quantities (0-1,000,000), qualities (Trash, Poor, Standard, Premium, Heavenly), and packaging (none, baggie, jar).
    - Apply changes to weed, items, or both across selected or all properties.
  - **Products:**
    - Discover or undiscover products like cocaine and meth.
    - Generate custom products with specified quantities, ID lengths, and prices.
  - **Unlocks:**
    - Unlock all items and weeds by setting rank and tier to 999.
    - Unlock all properties by downloading and enabling all property types.
    - Unlock all businesses by downloading and enabling all business types.
    - Update NPC relationships and recruit dealers.
  - **Miscellaneous:**
    - Edit organization name.
    - Complete all quests and objectives.
    - Modify variables (booleans to "True," numerics to "999999999") in `Variables/` and `Players/Player_*/Variables/`.
    - Install an Achievement Unlocker mod.
    - Generate new save folders with custom organization names (up to 5 slots).
  - **NPCs:**
    - Generate NPC files from a pasted log.
    - Recruit all dealers by setting their "Recruited" status to true.
  - **Backups:**
    - Automatically create initial backups of save files.
    - Create feature-specific backups before edits.
    - Revert individual features or all changes using backups.
    - Delete all backups if needed.

## ⚠️ Antivirus Warnings (False Positives & VirusTotal Detection)
Some antivirus programs may flag the executable (`.exe`) version of this application as a virus or malware. This is a **false positive** caused by the application being converted from Python to an executable using **PyInstaller**, which some antivirus software misidentifies as suspicious.

### ⚠️ VirusTotal Detection
If scanned on [VirusTotal](https://www.virustotal.com/), the executable may be flagged by some engines due to PyInstaller’s packaging method, not because of malicious code.

### ✅ How to Use the Application Safely
1. **Review the Source Code**
   - This project is **open-source**; inspect the code yourself to verify its safety.
2. **Use the Python Version**
   - Run the Python script directly instead of the `.exe` by cloning the repository and installing dependencies.
3. **Whitelist the Application**
   - Add an exception in your antivirus if it blocks the executable.

⚠️ *This project contains **no malware or harmful code**. For peace of mind, review the source code or use the Python version.*

## Usage
1. **Select a Save:**
   - Launch the editor to view a table of available saves.
   - Select a save and click "Load Selected Save."

2. **View Save Information:**
   - Review save details such as money, rank, and creation date.
   - Click "Back to Selection" to choose another save or "Edit Save" to modify it.

3. **Edit Save Data:**
   - Use the tabs (Money, Rank, Properties, Products, Unlocks, Misc, NPCs, Backups) to adjust values.
   - Enter data and click "Apply Changes" to save or "Cancel" to discard.
   - Use the "Backups" tab to revert changes if needed.

**Note:** The editor automatically creates backups before applying changes. It’s still recommended to manually back up your save files before editing.

## Requirements
- **Python**
- **PySide6**

## Installation
1. **Ensure Python is Installed:**
   - Download and install Python from [python.org](https://www.python.org/) if not already installed.

2. **Install Dependencies:**
   ```sh
   git clone https://github.com/N0edL/Schedule-1-Save-Editor.git
   cd Schedule-1-Save-Editor
