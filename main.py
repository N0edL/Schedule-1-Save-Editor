import os
from typing import Optional

from lib.manager import SaveManager

class SaveEditorMenu:
    def __init__(self):
        self.manager = SaveManager()
        self.current_save: Optional[str] = None

    def clear_screen(self):
        """Clear the console screen"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def display_header(self, title: str):
        """Display a consistent header for each screen"""
        self.clear_screen()
        print("=" * 50)
        print(f"SCHEDULE I SAVE EDITOR - {title.upper()}")
        print("=" * 50)
        print()

    def press_enter_to_continue(self):
        """Utility method to pause execution"""
        input("\nPress Enter to continue...")

    def main_menu(self):
        while True:
            self.display_header("Main Menu")
            print("1. Select Save Game")
            print("2. View Save Information")
            print("3. Edit Save Data")
            print("4. Exit")
            print()

            choice = input("Enter your choice (1-4): ")

            if choice == "1":
                self.select_save_menu()
            elif choice == "2":
                self.view_save_info()
            elif choice == "3":
                self.edit_save_menu()
            elif choice == "4":
                print("Goodbye!")
                break
            else:
                print("Invalid choice. Please try again.")
                self.press_enter_to_continue()

    def select_save_menu(self):
        self.display_header("Select Save Game")
        saves = self.manager.get_save_folders()

        if not saves:
            print("No save games found!")
            self.press_enter_to_continue()
            return

        for i, save in enumerate(saves, 1):
            print(f"{i}. {save['name']}")

        print("\n0. Back to Main Menu")
        print()

        while True:
            choice = input(f"Select save (1-{len(saves)} or 0 to cancel): ")
            
            if choice == "0":
                return
                
            if choice.isdigit() and 1 <= int(choice) <= len(saves):
                selected_save = saves[int(choice)-1]
                if self.manager.load_save(selected_save['path']):
                    self.current_save = selected_save['name']
                    print(f"\nSuccessfully loaded save: {self.current_save}")
                else:
                    print("\nFailed to load save file!")
                self.press_enter_to_continue()
                return
            else:
                print("Invalid selection. Please try again.")

    def view_save_info(self):
        if not self.current_save:
            print("No save game loaded! Please select one first.")
            self.press_enter_to_continue()
            return

        self.display_header(f"Save Info - {self.current_save}")
        info = self.manager.get_save_info()

        if not info:
            print("No information available for this save.")
            self.press_enter_to_continue()
            return

        print(f"Game Version: {info.get('game_version', 'Unknown')}")
        print(f"Money: ${info.get('money', 0):,.2f}")
        print(f"Rank: {info.get('rank', 'Unknown')}")
        print(f"Play Time: {self.format_playtime(info.get('play_time', 0))}")
        print(f"Properties Owned: {info.get('properties_owned', 0)}")
        print(f"Vehicles Owned: {info.get('vehicles_owned', 0)}")
        print(f"Businesses Owned: {info.get('businesses_owned', 0)}")

        self.press_enter_to_continue()

    def format_playtime(self, seconds: int) -> str:
        """Convert seconds to hours:minutes:seconds format"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def edit_save_menu(self):
        if not self.current_save:
            print("No save game loaded! Please select one first.")
            self.press_enter_to_continue()
            return

        while True:
            self.display_header(f"Edit Save - {self.current_save}")
            info = self.manager.get_save_info()
            
            print("1. Edit Money")
            print("2. Edit Rank")
            print("3. Edit Play Time")
            print("0. Back to Main Menu")
            print()

            choice = input("Enter your choice (0-3): ")

            if choice == "0":
                return
            elif choice == "1":
                self.edit_money(info['money'])
            elif choice == "2":
                self.edit_rank(info['rank'])
            elif choice == "3":
                self.edit_playtime(info['play_time'])
            else:
                print("Invalid choice. Please try again.")
                self.press_enter_to_continue()

    def edit_money(self, current_amount: float):
        self.display_header(f"Edit Money - Current: ${current_amount:,.2f}")
        
        while True:
            new_amount = input("Enter new money amount (or 'cancel' to abort): $")
            
            if new_amount.lower() == 'cancel':
                return
                
            try:
                new_amount = float(new_amount)
                if new_amount < 0:
                    print("Amount cannot be negative!")
                    continue
                    
                # Here you would implement the actual save modification
                # For now we'll just show what would happen
                print(f"\nMoney would be changed from ${current_amount:,.2f} to ${new_amount:,.2f}")
                confirm = input("Confirm this change? (y/n): ").lower()
                
                if confirm == 'y':
                    # manager.update_save_data({"money": new_amount})
                    print("Money updated successfully! (Simulated)")
                    self.press_enter_to_continue()
                    return
                else:
                    print("Change cancelled.")
                    self.press_enter_to_continue()
                    return
                    
            except ValueError:
                print("Please enter a valid number!")

    def edit_rank(self, current_rank: str):
        self.display_header(f"Edit Rank - Current: {current_rank}")
        
        # This would be replaced with actual rank options from the game
        rank_options = ["Street", "Dealer", "Supplier", "Distributor", "Kingpin"]
        
        print("Available ranks:")
        for i, rank in enumerate(rank_options, 1):
            print(f"{i}. {rank}")
        print("0. Cancel")
        print()

        while True:
            choice = input(f"Select new rank (1-{len(rank_options)} or 0 to cancel): ")
            
            if choice == "0":
                return
                
            if choice.isdigit() and 1 <= int(choice) <= len(rank_options):
                new_rank = rank_options[int(choice)-1]
                
                print(f"\nRank would be changed from {current_rank} to {new_rank}")
                confirm = input("Confirm this change? (y/n): ").lower()
                
                if confirm == 'y':
                    # manager.update_save_data({"rank": new_rank})
                    print("Rank updated successfully! (Simulated)")
                    self.press_enter_to_continue()
                    return
                else:
                    print("Change cancelled.")
                    self.press_enter_to_continue()
                    return
            else:
                print("Invalid selection. Please try again.")

    def edit_playtime(self, current_seconds: int):
        self.display_header(f"Edit Play Time - Current: {self.format_playtime(current_seconds)}")
        
        print("Enter new play time in hours (or 'cancel' to abort)")
        print("Example: 12.5 = 12 hours and 30 minutes")
        
        while True:
            new_hours = input("New play time (hours): ")
            
            if new_hours.lower() == 'cancel':
                return
                
            try:
                new_hours = float(new_hours)
                if new_hours < 0:
                    print("Time cannot be negative!")
                    continue
                    
                new_seconds = int(new_hours * 3600)
                
                print(f"\nPlay time would be changed from {self.format_playtime(current_seconds)} to {self.format_playtime(new_seconds)}")
                confirm = input("Confirm this change? (y/n): ").lower()
                
                if confirm == 'y':
                    # manager.update_save_data({"play_time": new_seconds})
                    print("Play time updated successfully! (Simulated)")
                    self.press_enter_to_continue()
                    return
                else:
                    print("Change cancelled.")
                    self.press_enter_to_continue()
                    return
                    
            except ValueError:
                print("Please enter a valid number!")


if __name__ == "__main__":
    editor = SaveEditorMenu()
    editor.main_menu()