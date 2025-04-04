from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QComboBox, QMessageBox
)
import json
import sys

# De XP per tier in volgorde, bijvoorbeeld: Street Rat I t/m Baron V
XP_PER_TIER = [
    0, 200, 200, 200, 200,           # Street Rat I-V
    400, 400, 400, 400, 400,         # Hoodlum I-V
    625, 625, 625, 625, 625,         # Peddler I-V
    825, 825, 825, 825, 825,         # Hustler I-V
    1025, 1025, 1025, 1025, 1025,    # Bagman I-V
    1050, 1050, 1050, 1050, 1050,    # Enforcer I-V
    1450, 1450, 1450, 1450, 1450,    # Shot Caller I-V
    1675, 1675, 1675, 1675, 1675,    # Block Boss I-V
    1875, 1875, 1875, 1875, 1875,    # Underlord I-V
    2075, 2075, 2075, 2075, 2075     # Baron I-V
]

RANK_NAMES = [
    "Street Rat", "Hoodlum", "Peddler", "Hustler",
    "Bagman", "Enforcer", "Shot Caller", "Block Boss",
    "Underlord", "Baron"
]

class RankEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Schedule 1 Rank Editor")
        self.resize(300, 150)

        layout = QVBoxLayout()

        # Rank select
        rank_layout = QHBoxLayout()
        rank_label = QLabel("Rank:")
        self.rank_combo = QComboBox()

        # Voeg tiers toe per rank
        for rank_index, rank in enumerate(RANK_NAMES):
            for tier in range(1, 6):
                self.rank_combo.addItem(f"{rank} {tier}", userData=(rank_index, tier))

        rank_layout.addWidget(rank_label)
        rank_layout.addWidget(self.rank_combo)
        layout.addLayout(rank_layout)

        # Opslaan knop
        save_btn = QPushButton("Save rank.json")
        save_btn.clicked.connect(self.save_file)
        layout.addWidget(save_btn)

        self.setLayout(layout)

    def save_file(self):
        rank_index, tier = self.rank_combo.currentData()

        # Bereken total XP tot deze tier (XP_PER_TIER is 0-indexed)
        tier_index = rank_index * 5 + (tier - 1)
        total_xp = sum(XP_PER_TIER[:tier_index])

        data = {
            "DataType": "RankData",
            "DataVersion": 0,
            "GameVersion": "0.3.3f15",
            "Rank": rank_index,
            "Tier": tier - 1,
            "XP": 0,
            "TotalXP": total_xp
        }

        with open("rank.json", "w") as f:
            json.dump(data, f, indent=4)

        QMessageBox.information(self, "Saved", "rank.json is bijgewerkt!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RankEditor()
    window.show()
    sys.exit(app.exec())
