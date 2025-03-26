import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Union
from lib.manager import SaveManager

class SaveEditorMenu:
    def __init__(self):
        self.manager = SaveManager()
        self.current_save: Optional[str] = None

    def clear_screen(self):
        """Clear the console screen"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def display_header(self, title: str):
        """Display a consistent header"""
        self.clear_screen()
        print("=" * 50)
        print(f"SCHEDULE I SAVE EDITOR - {title.upper()}")
        print("=" * 50)
        print()

    def press_enter_to_continue(self):
        """Pause execution until Enter is pressed"""
        input("\nPress Enter to continue...")

    def main_menu(self):
        """Main application menu"""
        while True:
            self.display_header("Main Menu")
            print("1. Select Save Game")
            print("2. View Save Information")
            print("3. Player Management")
            print("4. Edit Finances")
            print("5. Exit")
            print()

            choice = input("Enter your choice (1-5): ")

            if choice == "1":
                self.select_save_menu()
            elif choice == "2":
                self.view_save_info()
            elif choice == "3":
                self.player_info_menu()
            elif choice == "4":
                self.edit_finances_menu()
            elif choice == "5":
                print("Goodbye!")
                break
            else:
                print("Invalid choice. Please try again.")
                self.press_enter_to_continue()

    def select_save_menu(self):
        """Menu for selecting a save game"""
        self.display_header("Select Save Game")
        saves = self.manager.get_save_folders()

        if not saves:
            print("No save games found!")
            self.press_enter_to_continue()
            return

        print(f"{'#':<3} {'Save Name':<15} {'Organization':<25}")
        print("-" * 45)
        for i, save in enumerate(saves, 1):
            print(f"{i:<3} {save['name']:<15} {save['organisation_name']:<25}")

        print("\n0. Back to Main Menu")
        print()

        while True:
            choice = input(f"Select save (1-{len(saves)} or 0 to cancel): ")
            
            if choice == "0":
                return
                
            if choice.isdigit() and 1 <= int(choice) <= len(saves):
                selected_save = saves[int(choice)-1]
                if self.manager.load_save(selected_save['path']):
                    self.current_save = f"{selected_save['name']} ({selected_save['organisation_name']})"
                    print(f"\nSuccessfully loaded: {self.current_save}")
                else:
                    print("\nFailed to load save file!")
                self.press_enter_to_continue()
                return
            else:
                print("Invalid selection. Please try again.")

    def view_save_info(self):
        """Display overview of save information"""
        if not self.current_save:
            print("No save game loaded! Please select one first.")
            self.press_enter_to_continue()
            return

        self.display_header("Save Information")
        info = self.manager.get_save_info()
        players = self.manager.get_players_info()

        print(f"Organization: {info.get('organisation_name', 'Unknown')}")
        print(f"Game Version: {info.get('game_version', 'Unknown')}")
        print(f"Created: {info.get('creation_date', 'Unknown')}\n")

        print("[ FINANCIAL STATUS ]")
        print(f"Online Balance: ${info.get('online_balance', 0):,.2f}")
        print(f"Total Net Worth: ${info.get('networth', 0):,.2f}")
        print(f"Lifetime Earnings: ${info.get('lifetime_earnings', 0):,.2f}\n")

        print("[ ASSETS ]")
        print(f"Properties: {info.get('properties_owned', 0)}")
        print(f"Vehicles: {info.get('vehicles_owned', 0)}")
        print(f"Businesses: {info.get('businesses_owned', 0)}")
        print(f"Players: {len(players)}")

        self.press_enter_to_continue()

    def player_info_menu(self):
        """Main player management menu"""
        if not self.current_save:
            print("No save game loaded! Please select one first.")
            self.press_enter_to_continue()
            return

        while True:
            self.display_header("Player Management")
            players = self.manager.get_players_info()
            
            if not players:
                print("No players found in this save!")
                self.press_enter_to_continue()
                return
                
            print(f"\nFound {len(players)} player(s):\n")
            for idx, player in enumerate(players, 1):
                print(f"{idx}. {player['name']:20} | Bank: ${player['bank_balance']:,.2f} | Items: {len(player['inventory'])}")
            
            print("\n0. Back to Main Menu")
            
            choice = input("\nSelect player (1-{} or 0): ".format(len(players)))
            if choice == "0":
                return
            elif choice.isdigit() and 1 <= int(choice) <= len(players):
                self._view_player_details(players[int(choice)-1])
            else:
                print("Invalid selection!")
                self.press_enter_to_continue()

    def _view_player_details(self, player: dict):
        """View detailed information about a specific player"""
        while True:
            self.display_header(f"Player: {player['name']}")
            
            print("\n[ BASIC INFO ]")
            print(f"Player ID:   {player['id']}")
            print(f"Steam ID:    {player['steam_id'] or 'Local Player'}")
            print(f"Bank Balance: ${player['bank_balance']:,.2f}")
            
            if player.get('appearance'):
                print("\n[ APPEARANCE ]")
                print(f"Gender:    {player['appearance'].get('Gender', 'Unknown')}")
                print(f"Body Type: {player['appearance'].get('BodyType', 'Unknown')}")
            
            print("\n[ INVENTORY ]")
            total_value = sum(item['value'] for item in player['inventory'])
            print(f"Total items: {len(player['inventory'])} | Total value: ${total_value:,.2f}\n")
            
            for item in player['inventory']:
                print(f"- {item['name']:20} x{item['quantity']:<3}", end=" ")
                if item['quality']:
                    print(f"(Quality: {item['quality']})", end=" ")
                if item['value'] > 0:
                    print(f"[${item['value']:,.2f}]", end="")
                print()
            
            print("\n1. Edit Bank Balance  2. Edit Inventory  0. Back")
            choice = input("\nSelect option: ")
            
            if choice == "0":
                return
            elif choice == "1":
                self._edit_bank_balance(player)
            elif choice == "2":
                self._edit_inventory(player)
            else:
                print("Invalid option!")
                self.press_enter_to_continue()

    def _edit_bank_balance(self, player: dict):
        """Edit a player's bank balance"""
        self.display_header(f"Edit Bank: {player['name']}")
        print(f"Current balance: ${player['bank_balance']:,.2f}\n")
        
        while True:
            try:
                new_balance = float(input("Enter new balance: $"))
                if new_balance < 0:
                    print("Balance cannot be negative!")
                    continue
                    
                print(f"\nBalance will be updated to ${new_balance:,.2f}")
                confirm = input("Confirm change? (y/n): ").lower()
                
                if confirm == 'y':
                    # Actual save implementation would go here
                    player['bank_balance'] = new_balance
                    print("Balance updated successfully! (Simulated)")
                    self.press_enter_to_continue()
                    return
                else:
                    print("Change cancelled.")
                    self.press_enter_to_continue()
                    return
                    
            except ValueError:
                print("Please enter a valid number!")

    def _edit_inventory(self, player: dict):
        """Edit a player's inventory"""
        self.display_header(f"Edit Inventory: {player['name']}")
        print("Inventory editing not yet implemented!")
        self.press_enter_to_continue()

    def edit_finances_menu(self):
        """Menu for editing financial data"""
        if not self.current_save:
            print("No save game loaded! Please select one first.")
            self.press_enter_to_continue()
            return

        self.display_header("Edit Finances")
        print("Financial editing not yet implemented!")
        self.press_enter_to_continue()

if __name__ == "__main__":
    editor = SaveEditorMenu()
    editor.main_menu()