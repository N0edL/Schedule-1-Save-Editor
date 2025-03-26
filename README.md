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

- **Dark Theme:** Enhances visibility and user experience.

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
