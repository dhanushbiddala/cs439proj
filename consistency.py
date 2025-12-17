import os
import pandas as pd
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import ttk


class DataHandler:
    def __init__(self, base_dir):
        self.base_dir = os.path.abspath(base_dir)

    def load_all_weeks(self, position="DB"):
        """
        Loads ALL weekly files for all years.
        Structure assumed:
            base_dir/
                2022/
                    1/DB.csv
                    2/DB.csv
                2021/
                    1/DB.csv
                    2/DB.csv
        """
        data = {}

        for year_folder in os.listdir(self.base_dir):
            if year_folder.isdigit():  # Only folders like "2022"
                year_path = os.path.join(self.base_dir, year_folder)
                if not os.path.isdir(year_path):
                    continue

                week_data = {}

                # Loop over week folders (1,2,3...)
                for week_folder in os.listdir(year_path):
                    week_path = os.path.join(year_path, week_folder)

                    if week_folder.isdigit():  # Week numbers
                        csv_file = os.path.join(week_path, f"{position}.csv")

                        if os.path.exists(csv_file):
                            try:
                                df = pd.read_csv(csv_file)
                                week_data[int(week_folder)] = df
                            except:
                                pass

                if week_data:
                    data[int(year_folder)] = week_data

        return data


def normalize_columns(df):
    df = df.copy()
    rename_map = {
        "PlayerName": "player",
        "TotalPoints": "points",
        "FantasyPoints": "points"   # just in case
    }
    df.rename(columns=rename_map, inplace=True)
    return df


def plot_player_weekly_boxplot(all_data, player_name):
    weekly_points = []

    for year, weeks in sorted(all_data.items()):
        for week, df in sorted(weeks.items()):
            df = normalize_columns(df)

            row = df[df["player"] == player_name]

            if not row.empty:
                pts = float(row["points"].values[0])
                weekly_points.append(pts)

    if not weekly_points:
        print("Player not found.")
        return

    plt.figure(figsize=(7, 5))
    plt.boxplot(weekly_points, labels=["Weekly Points"])
    plt.title(f"Consistency vs Ceiling (Weekly)\n{player_name}")
    plt.ylabel("Fantasy Points")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.show()


# ====================
# MAIN EXECUTION
# ====================

base_path = r"C:/Users/rsun2/Downloads/NFL-data-Players/NFL-data-Players"
dh = DataHandler(base_dir=base_path)

all_data = dh.load_all_weeks("DB")

# Build player list
players = set()
for year, weeks in all_data.items():
    for week, df in weeks.items():
        df = normalize_columns(df)
        players.update(df["player"].dropna().unique())

players = sorted(players)

# ====================
# TKINTER UI DROPDOWN
# ====================

root = tk.Tk()
root.title("Select Player")

label = ttk.Label(root, text="Choose a player:")
label.pack(pady=5)

player_var = tk.StringVar()
dropdown = ttk.Combobox(root, textvariable=player_var, values=players, width=40)
dropdown.pack(pady=5)

def on_select(event=None):
    player = player_var.get()
    if player:
        plot_player_weekly_boxplot(all_data, player)

button = ttk.Button(root, text="Generate Plot", command=on_select)
button.pack(pady=10)

root.mainloop()
