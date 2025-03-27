# Schedule I Save File Editor

## Overview
The **Schedule I Save File Editor** is a graphical user interface (GUI) tool designed to edit save files for the game "Schedule I." It enables users to select save files, view detailed information, and modify key game data such as money, rank, properties, and miscellaneous settings. Built with PySide6, it features a dark theme and a tabbed interface for a seamless editing experience.

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
  - **Properties:** Update item quantities (0-1,000,000), qualities (Trash to Heavenly), packaging (none, baggie, jar), and apply to weed/items/both across selected or all properties.
  - **Miscellaneous:**
    - Edit organization name.
    - Complete all quests and objectives.
    - Modify variables (booleans to "True," numerics to "999999999").

## ⚠️ Antivirus Warnings (False Positives & VirusTotal Detection)
Some antivirus programs may flag the executable (`.exe`) version of this application as a virus or malware. This is a **false positive** and happens because the application was converted from Python to an executable using **PyInstaller**. Many antivirus programs incorrectly classify such files as malicious, even when they are completely safe.

### ⚠️ VirusTotal Detection
If you scanned the file on [VirusTotal](https://www.virustotal.com/) and it was flagged by some antivirus engines, keep in mind that this is due to how PyInstaller packages the application. Some security software marks all PyInstaller executables as suspicious, even when there is no harmful code.

### ✅ How to Use the Application Safely
1. **Review the Source Code**
   - This project is **open-source**, meaning you can inspect the code yourself before running it.
2. **Use the Python Version**
   - If you prefer, you can run the Python version directly instead of using the `.exe` file. Just clone the repository and install the required dependencies.
3. **Whitelist the Application in Your Antivirus**
   - If your antivirus blocks it, you can manually add an exception to allow it.

⚠️ *This project does **not** contain any malware or harmful code. If you have concerns, please check the source code and run the Python version instead.*



## Usage
1. **Select a Save:**
   - Launch the editor to see a table of available saves.
   - Select a save and click "Load Selected Save."

2. **View Save Information:**
   - Review the save details.
   - Click "Back to Selection" to choose another save or "Edit Save" to modify it.

3. **Edit Save Data:**
   - Use the tabs (Money, Rank, Properties, Misc) to adjust values.
   - Enter data and click "Apply Changes" to save or "Cancel" to discard.

## Requirements
- **Python**
- **PySide6**
- **Rarfile**

## Installation
1. Clone the repository:
   ```sh
   git clone https://github.com/N0edL/Schedule-1-Save-Editor.git
