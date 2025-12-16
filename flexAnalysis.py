import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QCheckBox, QLabel, QGroupBox

path = Path("NFL-Data") / "NFL-data-Players"
years = [2021, 2022, 2023, 2024]
positions = ["QB", "RB", "WR", "TE"]
flex_pos = ["RB", "WR", "TE"]
starter_count = {"QB": 1, "RB": 2, "WR": 2, "TE": 1}
team_sizes = [8, 10, 12, 14]

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


class FlexWidget(QWidget):
    def __init__(self, df):
        super().__init__()
        
        self.df = df
        self.max_y = 300
        
        self.setup()
        self.update()
    
    def setup(self):
        layout = QHBoxLayout(self)
        
        controls = QVBoxLayout()
        layout.addLayout(controls, stretch=0)
        
        settings = QGroupBox("Settings")
        s_layout = QVBoxLayout(settings)
        
        s_layout.addWidget(QLabel("League size:"))
        
        self.size_combo = QComboBox()
        for size in team_sizes:
            self.size_combo.addItem(str(size))
        self.size_combo.setCurrentText("8")
        self.size_combo.currentIndexChanged.connect(self.update)
        s_layout.addWidget(self.size_combo)
        
        self.superflex_check = QCheckBox("Superflex (include QB)")
        self.superflex_check.stateChanged.connect(self.update)
        s_layout.addWidget(self.superflex_check)
        
        s_layout.addStretch()
        controls.addWidget(settings)
        controls.addStretch()
        
        self.fig, self.ax = plt.subplots(figsize=(7, 5))
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas, stretch=1)
    
    def tier_range(self, pos, size):
        if pos in starter_count:
            n = starter_count[pos]
        else:
            n = 1
        
        start = n * size + 1
        end = start + size
        return start, end
    
    def update(self):
        self.ax.clear()
        
        if len(self.df) == 0:
            self.ax.text(0.5, 0.5, "No data available.", ha="center", va="center", transform=self.ax.transAxes, fontsize=12, color="gray")
            self.canvas.draw_idle()
            return
        
        size = int(self.size_combo.currentText())
        
        flex = []
        if self.superflex_check.isChecked() == True:
            flex = flex_pos + ["QB"]
        else:
            flex = flex_pos
        
        means = []
        all_pts = []
        
        for pos in flex:
            start, end = self.tier_range(pos, size)
            
            sub = self.df[self.df["Pos"] == pos]
            sub = sub[sub["Rank"] >= start]
            sub = sub[sub["Rank"] <= end]
            
            pts = sub["TotalPoints"].dropna()
            
            if len(pts) == 0:
                means.append(0)
            else:
                means.append(pts.mean())
                for val in pts.values:
                    all_pts.append(val)
        
        x = np.arange(len(flex))
        
        colors = []
        for pos in flex:
            if pos in pos_colors:
                col = pos_colors[pos]
            else:
                col = "gray"
            colors.append(col)
        
        self.ax.bar(x, means, color=colors, edgecolor="white", linewidth=1.2)
        
        if len(all_pts) > 0:
            avg = np.mean(all_pts)
            self.ax.axhline(avg, linestyle="--", color="gray", linewidth=1.5, alpha=0.7, label="Flex Avg")
            self.ax.text(len(x) - 0.5, avg + self.max_y * 0.02, str(int(avg)), fontsize=9)
        
        for i in range(len(means)):
            mean = means[i]
            if mean > 0:
                self.ax.text(x[i], mean + self.max_y * 0.02, str(int(mean)), ha="center", fontsize=10)
        
        self.ax.set_xticks(x)
        self.ax.set_xticklabels(flex)
        self.ax.set_ylabel("Avg Season Points")
        self.ax.set_xlabel("Position")
        
        if self.superflex_check.isChecked() == True:
            sflex = " (Superflex)"
        else:
            sflex = ""
        
        title = "Flex-Level Production – " + str(size) + "-Team League" + sflex
        self.ax.set_title(title)
        
        self.ax.set_ylim(0, self.max_y)
        self.ax.spines["top"].set_visible(False)
        self.ax.spines["right"].set_visible(False)
        self.ax.yaxis.grid(True, alpha=0.3)
        self.ax.legend(loc="upper right")
        
        self.fig.tight_layout()
        self.canvas.draw_idle()


def main():
    app = QApplication(sys.argv)
    
    season_df = load_season_data(path, years, positions)
    
    window = QMainWindow()
    window.setWindowTitle("Flex-Level Production")
    window.setGeometry(100, 100, 1000, 600)
    window.setCentralWidget(FlexWidget(season_df))
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
