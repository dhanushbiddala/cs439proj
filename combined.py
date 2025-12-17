import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from scipy.stats import gaussian_kde
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, QCheckBox, QGroupBox, QSpinBox, QTabWidget

path = Path("NFL-Data") / "NFL-data-Players"
years = [2021, 2022, 2023, 2024]
positions = ["QB", "RB", "WR", "TE"]
flex_pos = ["RB", "WR", "TE"]
starter_count = {"QB": 1, "RB": 2, "WR": 2, "TE": 1}
team_sizes = [8, 10, 12, 14]
scale_min = -3.0
scale_max = 3.0

pos_colors = {
    "QB": "purple",
    "RB": "blue",
    "WR": "red",
    "TE": "green",
}

pos_colors_rgba = {
    "QB": (0.502, 0.000, 0.502, 0.8),
    "RB": (0, 0, 1, 0.8), # (1.000, 0.498, 0.055, 0.8)
    "WR": (0.839, 0.153, 0.157, 0.8), # (0.173, 0.627, 0.173, 0.8)
    "TE": (0.173, 0.627, 0.173, 0.8), # (0.839, 0.153, 0.157, 0.8)
}

years_str = [str(y) for y in range(2015, 2026)]
weeks_str = [str(w) for w in range(1, 18)] + ["full season"]

# Data Handling
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


def load_efficiency_data(folder, year, week, pos):
    if week == "full season":
        f = folder / year / (pos + "_season.csv")
    else:
        f = folder / year / week / (pos + ".csv")
    
    if not f.exists():
        return None
    
    return pd.read_csv(f)


# Positional Scarcity Chart

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


# Flex Analysis Chart

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


# Defense Analysis Chart

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


# Individual Performance Density Chart

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

# Opportunity vs Efficiency Plot

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
    
    season_df = load_season_data(path, years, positions)
    week_df = load_week_data(path)
    defense_df = load_defense_data(path)
    
    tabs = QTabWidget()
    
    scarcity = ScarcityWidget(season_df)
    flex = FlexWidget(season_df)
    defense = DefenseWidget(defense_df)
    density = DensityWidget()
    efficiency = EfficiencyWidget(week_df, density, tabs)
    
    tabs.addTab(scarcity, "Positional Scarcity")
    tabs.addTab(flex, "Flex Analysis")
    tabs.addTab(defense, "Defense Analysis")
    tabs.addTab(efficiency, "Opportunity vs Efficiency")
    tabs.addTab(density, "Player Density")
    
    window = QMainWindow()
    window.setWindowTitle("NFL Fantasy Football Dashboard")
    window.setGeometry(100, 100, 1100, 800)
    window.setCentralWidget(tabs)
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
