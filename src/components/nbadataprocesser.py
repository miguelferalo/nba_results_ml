import pandas as pd
from datetime import datetime, timedelta
import os

class NBADataProcesser():

    def __init__(self, config):

        self.config = config
        self.seasons_nba = config["YEARS_DATA"]
        self.nba_teams = config["NBA_TEAMS"]
        self.teams_game_data = config["TEAMS_GAME_DATA"]
        self.features = config["FEATURES"]
        self.featureset_extra_columns = config["FEATURESET_EXTRA_COLUMNS"]
        self.game_sample_columns = config["GAME_SAMPLE_COLUMNS"]
        self.today = datetime.today().strftime('%Y-%m-%d')
        self.training_years = config["MODELING"]["TRAINING_YEARS"]
        self.test_years = config["MODELING"]["TEST_YEARS"]

        self.global_path = os.getcwd()
        self.data_folder = config["DATA"]["FOLDER_NAME"]
        self.raw_data_file_name = config["DATA"]["NBA_RAW_FILENAME"]

        

    def load_training_set(self):

        #Create a dataframe to store all data
        training_df = pd.DataFrame()

        for year in self.training_years:

            for team in self.nba_teams:

                file_name = self.raw_data_file_name.format(TEAM = team)
                path_to_raw_df = os.path.join(self.global_path, self.data_folder, str(year), file_name)

                team_df = pd.read_csv(path_to_raw_df)

                training_df = pd.concat([training_df, team_df], ignore_index = True)

        return training_df
        