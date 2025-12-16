import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, QCheckBox

path = Path("NFL-Data") / "NFL-data-Players"
years = [2021, 2022, 2023, 2024]
positions = ["QB", "RB", "WR", "TE"]
team_sizes = [8, 10, 12, 14]
starter_count = {"QB": 1, "RB": 2, "WR": 2, "TE": 1}

pos_colors = {
    "QB": "purple",
    "RB": "blue",
    "WR": "red",
    "TE": "green",
}

def load_season_data(base, years, pos_list):
    all_data = []
    
    for y in years:
        for pos in pos_list:
            f = Path(base) / str(y) / (pos + "_season.csv")
            
            if not f.exists():
                continue
            
            df = pd.read_csv(f)
            df["season"] = y
            
            required = ["PlayerName", "Pos", "Rank", "TotalPoints"]
            has_all = True
            for col in required:
                if col not in df.columns:
                    has_all = False
                    break
            
            if has_all == False:
                continue
            
            df = df[["season", "PlayerName", "Pos", "Rank", "TotalPoints"]]
            all_data.append(df)
    
    if len(all_data) == 0:
        return pd.DataFrame()
    
    return pd.concat(all_data, ignore_index=True)

class ScarcityWidget(QWidget):
    def __init__(self, df):
        super().__init__()
        
        self.df = df[df["Rank"] <= 50].copy()
        self.max_y = self.y_max()
        
        self.setup()
        self.update()

    def y_max(self):
        if len(self.df) == 0:
            return 500
        
        maxx = self.df["TotalPoints"].max()
        return maxx * 1.1

    def setup(self):
        layout = QHBoxLayout(self)

        controls = QVBoxLayout()
        layout.addLayout(controls, stretch=0)

        controls.addWidget(QLabel("Season:"))
        
        self.season_combo = QComboBox()
        for y in years:
            self.season_combo.addItem(str(y))
        self.season_combo.addItem("Average")
        self.season_combo.setCurrentText("Average")
        self.season_combo.currentIndexChanged.connect(self.update)
        controls.addWidget(self.season_combo)

        controls.addSpacing(10)
        
        controls.addWidget(QLabel("Team Size:"))
        
        self.team_combo = QComboBox()
        for size in team_sizes:
            self.team_combo.addItem(str(size))
        self.team_combo.setCurrentText("8")
        self.team_combo.currentIndexChanged.connect(self.update)
        controls.addWidget(self.team_combo)

        controls.addSpacing(10)
        
        controls.addWidget(QLabel("Positions:"))
        
        self.pos_checks = {}
        for pos in positions:
            check = QCheckBox(pos)
            check.setChecked(True)
            check.stateChanged.connect(self.update)
            controls.addWidget(check)
            self.pos_checks[pos] = check

        controls.addStretch()

        self.fig, self.ax = plt.subplots(figsize=(7, 5))
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas, stretch=1)

    def cutoff(self, pos, size):
        if pos in starter_count:
            n = starter_count[pos]
        else:
            n = 1
        
        return n * size

    def get_data(self):
        choice = self.season_combo.currentText()
        
        if choice == "Average":
            df = self.df.groupby(["Pos", "Rank"], as_index=False)["TotalPoints"].mean()
            names = self.df.groupby(["Pos", "Rank"], as_index=False)["PlayerName"].first()
            df = df.merge(names, on=["Pos", "Rank"])
            df["season"] = "Average"
            return df
        else:
            y = int(choice)
            return self.df[self.df["season"] == y]

    def update(self):
        df = self.get_data()
        size = int(self.team_combo.currentText())

        self.ax.clear()

        selected = []
        for pos in self.pos_checks:
            check = self.pos_checks[pos]
            if check.isChecked() == True:
                selected.append(pos)

        has_data = False

        for pos in selected:
            cut = self.cutoff(pos, size)
            
            sub = df[df["Pos"] == pos]
            sub = sub[sub["Rank"] <= cut]
            sub = sub.sort_values("Rank")
            
            if len(sub) == 0:
                continue

            has_data = True

            if pos in pos_colors:
                col = pos_colors[pos]
            else:
                col = "gray"
            
            if pos in starter_count:
                n = starter_count[pos]
            else:
                n = 1
            
            label = pos + " (Top " + str(n * size) + ")"

            self.ax.plot(sub["Rank"], sub["TotalPoints"], marker="o", markersize=5, label=label, color=col, linewidth=2)

        yr = self.season_combo.currentText()
        title = "Positional Scarcity in Fantasy Football (" + yr + ", " + str(size) + "-Team League)"

        self.ax.set_xlabel("Positional Rank")
        self.ax.set_ylabel("Total Fantasy Points")
        self.ax.set_ylim(0, self.max_y)
        self.ax.set_title(title)
        self.ax.spines["top"].set_visible(False)
        self.ax.spines["right"].set_visible(False)
        self.ax.grid(True, alpha=0.3)
        
        if has_data == True:
            self.ax.legend()
        
        self.fig.tight_layout()
        self.canvas.draw_idle()

def main():
    app = QApplication(sys.argv)
    
    season_df = load_season_data(path, years, positions)
    
    window = QMainWindow()
    window.setWindowTitle("Positional Scarcity in Fantasy Football")
    window.setGeometry(100, 100, 1000, 700)
    window.setCentralWidget(ScarcityWidget(season_df))
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
