# CS 439 Final Project: Fantasy Football

Dhanush Biddala, Vihaan Vajpayee, Rick Sun

Interactive tool for analyzing Fantasy Football draft and week-to-week management strategy.

## Setup

Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Run Application:

```
python combined.py
```

## Features

- Positional Scarcity Plot:
  - Line chart showing how production changes across players of different rank in each position
   - Interactive Features:
      - Dropdowns for:
         - Year (2021 - 2024) and average over all years
         - Team Size (8, 10, 12, 14)
         - Checkbox for each position
- Flex Analysis:
   - Bar chart showing which position produces most points on average in the flex-spot (players ranked outside of the starting ranks)
   - Interactive Features:
     - Dropdown for Team Size (8, 10, 12, 14)
     - Checkbox for Superflex (Leagues that allow Quarterbacks in the flex spot)
- Defense Analysis:
   - Heatmap showing how many points a team's defense gives up on average to each position centered on the league average
   - Interactive Features:
      - Dropdown for Year (2021 - 2025)
      - Range selector for desired weeks (1 - 18)
- Opportunity vs Efficiency Plot:
   - Scatterplot plotting player efficiency (points per opportunity) against total opportunities
   - Interactive Features:
      - Tooltip on hover detailing player name, team, and season rank
      - On click produces Player Performance Density Plot
      - Dropdowns for:
         - Year (2015 - 2025)
         - Week (1 - 18) and totals over all games in the season
         - Position (QB, RB, WR, TE)
- Player Performance Density Plot:
   - Kernel Density Estimate (KDE) plot showing the distribution of weekly fantasy points for an individual player compared to the distribution for all players in their position
   - Interactive Features:
      - Generates on click from point in Opportunity vs Efficiency Plot 
