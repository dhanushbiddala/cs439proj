import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from scipy.stats import gaussian_kde
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, QTabWidget

path = Path("NFL-Data") / "NFL-data-Players"
positions = ["QB", "RB", "WR", "TE"]
years_str = [str(y) for y in range(2015, 2026)]
weeks_str = [str(w) for w in range(1, 18)] + ["full season"]

pos_colors_rgba = {
    "QB": (0.502, 0.000, 0.502, 0.8),
    "RB": (1.000, 0.498, 0.055, 0.8),
    "WR": (0.173, 0.627, 0.173, 0.8),
    "TE": (0.839, 0.153, 0.157, 0.8),
}


def load_week_data(folder):
    all_data = []
    
    if not folder.exists():
        return pd.DataFrame()
    
    for year_folder in folder.iterdir():
        if not year_folder.is_dir():
            continue
        
        for week_folder in year_folder.iterdir():
            if not week_folder.is_dir():
                continue
            
            if not week_folder.name.isdigit():
                continue
            
            for pos_file in week_folder.iterdir():
                if not pos_file.suffix == ".csv":
                    continue
                
                try:
                    df = pd.read_csv(pos_file)
                    
                    has_cols = True
                    for col in ["PlayerName", "Team", "Pos", "TotalPoints"]:
                        if col not in df.columns:
                            has_cols = False
                            break
                    
                    if has_cols == False:
                        continue
                    
                    df = df[["PlayerName", "Team", "Pos", "TotalPoints"]]
                    all_data.append(df)
                except:
                    continue
    
    if len(all_data) == 0:
        return pd.DataFrame()
    
    return pd.concat(all_data, ignore_index=True)


def load_efficiency_data(folder, year, week, pos):
    if week == "full season":
        f = folder / year / (pos + "_season.csv")
    else:
        f = folder / year / week / (pos + ".csv")
    
    if not f.exists():
        return None
    
    return pd.read_csv(f)


class DensityWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setup()
    
    def setup(self):
        layout = QVBoxLayout(self)
        
        self.fig, self.ax = plt.subplots(figsize=(8, 5))
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)
    
    def update(self, name, pos, player_vals, pos_vals):
        self.ax.clear()
        
        kde_player = gaussian_kde(player_vals)
        kde_pos = gaussian_kde(pos_vals)
        
        xmin = min(player_vals.min(), pos_vals.min())
        xmax = max(player_vals.max(), pos_vals.max())
        xs = np.linspace(xmin, xmax, 200)
        
        self.ax.plot(xs, kde_player(xs), label=name, linewidth=2)
        self.ax.plot(xs, kde_pos(xs), label="All " + pos + "s", linewidth=2, linestyle="--")
        
        self.ax.set_xlabel("Total Fantasy Points per Week")
        self.ax.set_ylabel("Density")
        self.ax.set_title("Weekly Point Distribution: " + name + " vs " + pos + " Position")
        self.ax.legend()
        self.ax.spines["top"].set_visible(False)
        self.ax.spines["right"].set_visible(False)
        self.ax.grid(True, alpha=0.3)
        
        self.fig.tight_layout()
        self.canvas.draw_idle()


class EfficiencyWidget(QWidget):
    def __init__(self, week_df, density_widget, tabs):
        super().__init__()
        
        self.week_df = week_df
        self.density_widget = density_widget
        self.tabs = tabs
        self.df = None
        self.scatter = None
        self.annot = None
        self.sizes = None
        self.colors = None
        
        self.setup()
        self.update()
    
    def setup(self):
        layout = QVBoxLayout(self)
        
        self.fig, self.ax = plt.subplots(figsize=(8, 5))
        self.canvas = FigureCanvas(self.fig)
        
        toolbar = NavigationToolbar(self.canvas, self)
        layout.addWidget(toolbar)
        layout.addWidget(self.canvas)
        
        controls = QHBoxLayout()
        layout.addLayout(controls)
        
        controls.addWidget(QLabel("Position:"))
        
        self.pos_combo = QComboBox()
        for pos in positions:
            self.pos_combo.addItem(pos)
        self.pos_combo.setCurrentText("QB")
        self.pos_combo.currentIndexChanged.connect(self.update)
        controls.addWidget(self.pos_combo)
        
        controls.addWidget(QLabel("Year:"))
        
        self.year_combo = QComboBox()
        for y in years_str:
            self.year_combo.addItem(y)
        self.year_combo.setCurrentText("2022")
        self.year_combo.currentIndexChanged.connect(self.on_year_change)
        controls.addWidget(self.year_combo)
        
        controls.addWidget(QLabel("Week:"))
        
        self.week_combo = QComboBox()
        for w in weeks_str:
            self.week_combo.addItem(w)
        self.week_combo.setCurrentText("full season")
        self.week_combo.currentIndexChanged.connect(self.update)
        controls.addWidget(self.week_combo)
        
        controls.addStretch()
        
        self.canvas.mpl_connect("motion_notify_event", self.on_hover)
        self.canvas.mpl_connect("button_press_event", self.on_click)
    
    def on_year_change(self):
        self.update_weeks()
        self.update()
    
    def update_weeks(self):
        year = self.year_combo.currentText()
        
        self.week_combo.blockSignals(True)
        self.week_combo.clear()
        
        if year in ["2015", "2016", "2017", "2018", "2019", "2020"]:
            self.week_combo.addItem("full season")
        else:
            for w in weeks_str:
                self.week_combo.addItem(w)
            
            if year == "2025":
                for w in range(6, 18):
                    idx = self.week_combo.findText(str(w))
                    if idx >= 0:
                        self.week_combo.removeItem(idx)
            
            if year == "2024":
                idx = self.week_combo.findText("17")
                if idx >= 0:
                    self.week_combo.removeItem(idx)
        
        self.week_combo.blockSignals(False)
    
    def update(self):
        self.ax.clear()
        
        year = self.year_combo.currentText()
        week = self.week_combo.currentText()
        pos = self.pos_combo.currentText()
        
        self.df = load_efficiency_data(path, year, week, pos)
        
        if self.df is None or len(self.df) == 0:
            self.ax.text(0.5, 0.5, "No data available.", ha="center", va="center", transform=self.ax.transAxes, fontsize=12, color="gray")
            self.canvas.draw_idle()
            return
        
        self.df = self.df[self.df["TotalPoints"] >= 0]
        
        if pos in ["QB", "RB"]:
            if "Touches" not in self.df.columns:
                self.ax.text(0.5, 0.5, "Missing 'Touches' column.", ha="center", va="center", transform=self.ax.transAxes, fontsize=12, color="gray")
                self.canvas.draw_idle()
                return
            
            opp = self.df["Touches"]
            x_label = "Opportunities (Touches)"
        else:
            if "Targets" not in self.df.columns:
                self.ax.text(0.5, 0.5, "Missing 'Targets' column.", ha="center", va="center", transform=self.ax.transAxes, fontsize=12, color="gray")
                self.canvas.draw_idle()
                return
            
            opp = self.df["Targets"]
            x_label = "Opportunities (Targets)"
        
        eff = self.df["TotalPoints"] / opp
        
        self.sizes = np.full(len(self.df), 40.0)
        
        if pos in pos_colors_rgba:
            col = pos_colors_rgba[pos]
        else:
            col = (0.5, 0.5, 0.5, 0.8)
        
        self.colors = np.full((len(self.df), 4), col)
        
        self.scatter = self.ax.scatter(opp, eff, s=self.sizes, c=self.colors)
        
        self.ax.set_xlabel(x_label)
        self.ax.set_ylabel("Efficiency (Points per Opportunity)")
        self.ax.grid(True, linestyle=":")
        
        self.annot = self.ax.annotate("", xy=(0, 0), xytext=(10, 10), textcoords="offset points", bbox=dict(boxstyle="round", fc="w"), arrowprops=dict(arrowstyle="->"))
        self.annot.set_visible(False)
        
        self.fig.tight_layout()
        self.canvas.draw_idle()
    
    def on_hover(self, event):
        if event.inaxes != self.ax:
            return
        
        if self.scatter is None:
            return
        
        cont, ind = self.scatter.contains(event)
        
        if cont == True:
            idx = ind["ind"][0]
            
            self.annot.xy = self.scatter.get_offsets()[idx]
            
            row = self.df.iloc[idx]
            txt = "Name: " + str(row["PlayerName"]) + "\n"
            txt = txt + "Team: " + str(row["Team"]) + "\n"
            txt = txt + "Season Rank: " + str(row["Rank"])
            self.annot.set_text(txt)
            self.annot.set_visible(True)
            
            current_colors = self.colors.copy()
            current_sizes = self.sizes.copy()
            current_colors[idx] = (1.0, 0.843, 0.0, 1.0)
            current_sizes[idx] = current_sizes[idx] * 2
            
            self.scatter.set_facecolors(current_colors)
            self.scatter.set_sizes(current_sizes)
        else:
            self.annot.set_visible(False)
            self.scatter.set_facecolors(self.colors)
            self.scatter.set_sizes(self.sizes)
        
        self.canvas.draw_idle()
    
    def on_click(self, event):
        if event.inaxes != self.ax:
            return
        
        if self.scatter is None:
            return
        
        cont, ind = self.scatter.contains(event)
        
        if cont == False:
            return
        
        idx = ind["ind"][0]
        row = self.df.iloc[idx]
        name = row["PlayerName"]
        pos = row["Pos"]
        
        player_data = self.week_df[self.week_df["PlayerName"] == name]["TotalPoints"]
        pos_data = self.week_df[self.week_df["Pos"] == pos]["TotalPoints"]
        
        player_vals = player_data.dropna().to_numpy()
        pos_vals = pos_data.dropna().to_numpy()
        
        if len(player_vals) < 2:
            return
        
        if len(pos_vals) < 2:
            return
        
        self.density_widget.update(name, pos, player_vals, pos_vals)
        
        if self.tabs is not None:
            idx = self.tabs.indexOf(self.density_widget)
            if idx >= 0:
                self.tabs.setCurrentIndex(idx)


def main():
    app = QApplication(sys.argv)
    
    week_df = load_week_data(path)
    
    tabs = QTabWidget()
    
    density = DensityWidget()
    efficiency = EfficiencyWidget(week_df, density, tabs)
    
    tabs.addTab(efficiency, "Opportunity vs Efficiency")
    tabs.addTab(density, "Player Density")
    
    window = QMainWindow()
    window.setWindowTitle("NFL Fantasy – Opportunity vs Efficiency")
    window.setGeometry(100, 100, 1000, 700)
    window.setCentralWidget(tabs)
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
