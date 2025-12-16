import pandas as pd
import os

class DataHandler:
    def __init__(self):
        self.file_path = 'NFL-Data/NFL-data-Players'
        self.aggregate_week_df = self.get_aggregate_week_data()

    def extract_data(self, year: str = '2025', week: str = 'full season', projected: bool = False, position: str = 'QB'):
        """
        Extracts the season data from NFL players in a data frame format. 

        Args:
            year (string): Season year
            week (string): Season week. Select 'full season' if you want data for the entire season.
            projected (bool): If set to True, it will return projected values instead of actual.
            position (string): Data is separated by position. You must select the position to get the data.
        Returns:
            pd.DataFrame: Player data from season.
        """
        
        file_path = self.file_path
        if week == 'full season' or year in ('2020', '2019', '2018', '2017', '2016', '2015'):
            file_path += f'/{year}/{position}_season.csv'
        elif year in ('2021', '2022', '2023', '2024', '2025'):
            if not projected:
                file_path += f'/{year}/{week}/{position}.csv'
                if not os.path.exists(file_path):
                    file_path = self.file_path
                    projected = True
            if projected:
                file_path += f'/{year}/{week}/projected/{position}_projected.csv'
                print(file_path)
        else:
            print('INVALID EXTRACTION')
            return None
        
        if os.path.exists(file_path):
            return pd.read_csv(file_path)
        else:
            print(f'File does not exist: {file_path}')
            return None
        
    def get_aggregate_week_data(self):
        df = pd.DataFrame(columns=['PlayerName', 'Team', 'Pos', 'TotalPoints'])
        for year_folder in os.listdir(self.file_path):
            year_file_path = os.path.join(self.file_path, year_folder)
            for week_folder in os.listdir(year_file_path):
                if week_folder.isdigit():
                    week_file_path = os.path.join(year_file_path, week_folder)
                    for position_file in os.listdir(week_file_path):
                        if position_file.endswith('.csv'):
                            full_path = os.path.join(week_file_path, position_file)
                            rows = pd.read_csv(full_path)[['PlayerName', 'Team', 'Pos', 'TotalPoints']]
                            df = pd.concat([df, rows], ignore_index=True)
        return df
    
    def get_specific_player_data(self, player_name):
        return self.aggregate_week_df[self.aggregate_week_df['PlayerName'] == player_name]

if __name__ == '__main__':
    datahandler = DataHandler()
    my_data = datahandler.extract_data(year='2025', week='1', projected=False, position='QB')
    # print(my_data.head(10))
    # my_other_data = datahandler.get_aggregate_week_data()
    my_data = datahandler.get_specific_player_data('Tom Brady')
    print(my_data.head(10))
