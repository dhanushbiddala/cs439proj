import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, QSpinBox

path = Path("NFL-Data") / "NFL-data-Players"
positions = ["QB", "RB", "WR", "TE"]
scale_min = -3.0
scale_max = 3.0


def load_defense_data(folder):
    all_data = []
    
    if not folder.exists():
        return pd.DataFrame()
    
    for year_folder in folder.iterdir():
        if not year_folder.is_dir():
            continue
        
        season = 0
        try:
            season = int(year_folder.name)
        except ValueError:
            continue
        
        for week_folder in year_folder.iterdir():
            if not week_folder.is_dir():
                continue
            
            week = 0
            try:
                week = int(week_folder.name)
            except ValueError:
                continue
            
            for pos in positions:
                f = week_folder / (pos + ".csv")
                
                if not f.exists():
                    continue
                
                df = pd.read_csv(f)
                df["season"] = season
                df["week"] = week
                df["Pos"] = pos
                
                has_cols = True
                if "PlayerOpponent" not in df.columns:
                    has_cols = False
                if "TotalPoints" not in df.columns:
                    has_cols = False
                
                if has_cols == False:
                    continue
                
                df = df[["PlayerName", "Pos", "PlayerOpponent", "TotalPoints", "season", "week"]]
                all_data.append(df)
    
    if len(all_data) == 0:
        return pd.DataFrame()
    
    combined = pd.concat(all_data, ignore_index=True)
    combined["Opponent"] = combined["PlayerOpponent"].str.replace("@", "", regex=False).str.strip()
    return combined


class DefenseWidget(QWidget):
    def __init__(self, df):
        super().__init__()
        
        self.df = df
        
        self.setup()
        self.init_weeks()
        self.update()
    
    def setup(self):
        layout = QVBoxLayout(self)
        
        controls = QHBoxLayout()
        layout.addLayout(controls)
        
        controls.addWidget(QLabel("Season:"))
        
        self.year_combo = QComboBox()
        yrs = []
        if len(self.df) > 0:
            yrs = sorted(self.df["season"].dropna().unique())
        else:
            yrs = [2024]
        for y in yrs:
            self.year_combo.addItem(str(int(y)))
        if len(yrs) > 0:
            self.year_combo.setCurrentText(str(int(max(yrs))))
        self.year_combo.currentTextChanged.connect(self.on_year_change)
        controls.addWidget(self.year_combo)
        
        controls.addSpacing(20)
        
        controls.addWidget(QLabel("Weeks:"))
        
        self.week_start = QSpinBox()
        self.week_start.setRange(1, 18)
        self.week_start.setValue(1)
        self.week_start.valueChanged.connect(self.update)
        controls.addWidget(self.week_start)
        
        controls.addWidget(QLabel("to"))
        
        self.week_end = QSpinBox()
        self.week_end.setRange(1, 18)
        self.week_end.setValue(18)
        self.week_end.valueChanged.connect(self.update)
        controls.addWidget(self.week_end)
        
        controls.addStretch()
        
        self.fig, self.ax = plt.subplots(figsize=(8, 10))
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)
    
    def init_weeks(self):
        if len(self.df) == 0:
            return
        
        season = int(self.year_combo.currentText())
        weeks = self.df[self.df["season"] == season]["week"].dropna().unique()
        
        if len(weeks) > 0:
            self.week_start.setValue(int(min(weeks)))
            self.week_end.setValue(int(max(weeks)))
    
    def on_year_change(self):
        self.init_weeks()
        self.update()
    
    def update(self):
        self.fig.clear()
        self.ax = self.fig.add_subplot(111)
        
        if len(self.df) == 0:
            self.ax.text(0.5, 0.5, "No data available.", ha="center", va="center", transform=self.ax.transAxes, fontsize=12, color="gray")
            self.canvas.draw_idle()
            return
        
        season = int(self.year_combo.currentText())
        w_start = self.week_start.value()
        w_end = self.week_end.value()
        
        if w_start > w_end:
            w_start, w_end = w_end, w_start
        
        df = self.df[self.df["season"] == season].copy()
        df = df[df["week"] >= w_start]
        df = df[df["week"] <= w_end]
        df = df[~df["Opponent"].str.upper().isin(["BYE", "NONE", ""])]
        df = df.dropna(subset=["Opponent", "TotalPoints"])
        
        if len(df) == 0:
            self.ax.text(0.5, 0.5, "No data for selected filters.", ha="center", va="center", transform=self.ax.transAxes, fontsize=12, color="gray")
            self.canvas.draw_idle()
            return
        
        week_avg = df.groupby(["week", "Pos"])["TotalPoints"].transform("mean")
        df["PointsVsAvg"] = df["TotalPoints"] - week_avg
        
        heat = df.groupby(["Opponent", "Pos"])["PointsVsAvg"].mean().unstack(fill_value=0)
        
        pos_list = []
        for p in positions:
            if p in heat.columns:
                pos_list.append(p)
        heat = heat[pos_list]
        heat = heat.sort_index()
        
        if len(heat) == 0:
            self.ax.text(0.5, 0.5, "No data for selected filters.", ha="center", va="center", transform=self.ax.transAxes, fontsize=12, color="gray")
            self.canvas.draw_idle()
            return
        
        im = self.ax.imshow(heat.values, cmap=plt.cm.RdYlGn, aspect="auto", vmin=scale_min, vmax=scale_max)
        
        self.ax.set_xticks(range(len(heat.columns)))
        self.ax.set_xticklabels(heat.columns, fontsize=11)
        self.ax.set_yticks(range(len(heat.index)))
        self.ax.set_yticklabels(heat.index, fontsize=9)
        
        self.fig.colorbar(im, ax=self.ax, shrink=0.8, label="Points Allowed vs League Average")
        
        for i in range(len(heat.index)):
            for j in range(len(heat.columns)):
                val = heat.iloc[i, j]
                
                if abs(val) > 1.5:
                    txt_col = "white"
                else:
                    txt_col = "black"
                
                if val > 0:
                    sign = "+"
                else:
                    sign = ""
                
                txt = sign + str(round(val, 1))
                self.ax.text(j, i, txt, ha="center", va="center", fontsize=8, color=txt_col)
        
        self.ax.set_xlabel("Position")
        self.ax.set_ylabel("Opponent")
        
        if w_start != w_end:
            label = "Wk " + str(w_start) + "-" + str(w_end)
        else:
            label = "Wk " + str(w_start)
        
        title = "Points Allowed by Position (" + str(season) + ", " + label + ")"
        self.ax.set_title(title, fontsize=12, pad=10)
        
        self.fig.tight_layout()
        self.canvas.draw_idle()


def main():
    app = QApplication(sys.argv)
    
    defense_df = load_defense_data(path)
    
    window = QMainWindow()
    window.setWindowTitle("Fantasy Points Allowed by Opponent")
    window.setGeometry(100, 100, 900, 900)
    window.setCentralWidget(DefenseWidget(defense_df))
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
