from nba_api.stats.endpoints import teamgamelog
import pandas as pd 
from nba_api.stats.endpoints import leaguegamefinder
from nba_api.stats.endpoints.leaguedashteamstats import LeagueDashTeamStats
from datetime import datetime, timedelta
import time
import pandas as pd
import os

class NBAResultsData():
    
    def __init__(self, config):

        self.config = config
        self.seasons_nba = config["YEARS_DATA"]
        self.nba_teams = config["NBA_TEAMS"]
        self.teams_game_data = config["TEAMS_GAME_DATA"]
        self.features = config["FEATURES"]
        self.featureset_extra_columns = config["FEATURESET_EXTRA_COLUMNS"]
        self.game_sample_columns = config["GAME_SAMPLE_COLUMNS"]
        self.today = datetime.today().strftime('%Y-%m-%d')

    def get_team_nba_games(self, team, season):

        team_id = self.nba_teams[team]

        gamefinder = leaguegamefinder.LeagueGameFinder(team_id_nullable = team_id).get_data_frames()[0]

        #Filter by year and after october to have enough sample size
        start_year = season.split("-")[0]
        year_id = f"2{start_year}"
        october_filter = f"{start_year}-11-01"
        

        gamefinder = gamefinder.loc[(gamefinder["SEASON_ID"] == year_id) & (gamefinder["GAME_DATE"] >= october_filter)
                                    & (gamefinder["GAME_DATE"] < self.today)].copy()

        #Get only home games
        gamefinder["LOCAL_TEAM"] = [matchup.split(" ")[0] if matchup.split(" ")[1] == "vs." else matchup.split(" ")[2] for matchup in gamefinder["MATCHUP"]]
        gamefinder["AWAY_TEAM"] = [matchup.split(" ")[2] if matchup.split(" ")[1] == "vs." else matchup.split(" ")[1] for matchup in gamefinder["MATCHUP"]]
        gamefinder = gamefinder.loc[gamefinder["LOCAL_TEAM"] == team, :].copy()

        #Get Win variable
        gamefinder["WIN"] = [1 if result == "W" else 0 for result in gamefinder["WL"]]

        #Get Team points
        gamefinder["TOTAL_POINTS"] = gamefinder["PTS"] * 2 - gamefinder["PLUS_MINUS"]

        gamefinder = gamefinder[self.game_sample_columns].reset_index(drop = True).copy()

        return gamefinder
    
    def featureset_structure(self):

        #Get training set columns
        columns = self.featureset_extra_columns.copy()

        for feature in self.features:

            #addd local and away and global and streak stats
            columns.append(feature + "_L_S")
            columns.append(feature + "_L_G")
            columns.append(feature + "_A_S")
            columns.append(feature + "_A_G")

        #Create dataframe
        df = pd.DataFrame(columns = columns)

        return df
    
    def features_calculator(self, season, local_team, away_team, game_date, win, total_points):

        game_datetime = datetime.strptime(game_date, '%Y-%m-%d') - timedelta(days = 1)
        game_date = game_datetime.strftime('%Y-%m-%d')
        game_date_streak_start = (datetime.strptime(game_date, '%Y-%m-%d') - timedelta(days = 20)).strftime('%Y-%m-%d')

        global_stats = LeagueDashTeamStats(season = season, date_to_nullable = game_datetime, timeout=60).get_data_frames()[0].sort_values("W", ascending = False)
        streak_stats = LeagueDashTeamStats(season = season, date_from_nullable = game_date_streak_start, date_to_nullable = game_datetime, timeout=60).get_data_frames()[0].sort_values("W", ascending = False)
        time.sleep(10)

        #Create row with data
        game_data = [f"{local_team} vs {away_team}", game_date, win, total_points]

        for feature in self.features:

            feature_local_streak = streak_stats.loc[streak_stats["TEAM_ID"] == self.nba_teams[local_team], feature].reset_index(drop = True)[0]
            feature_local_global = global_stats.loc[streak_stats["TEAM_ID"] == self.nba_teams[local_team], feature].reset_index(drop = True)[0]

            feature_away_streak = streak_stats.loc[streak_stats["TEAM_ID"] == self.nba_teams[away_team], feature].reset_index(drop = True)[0]
            feature_away_global = global_stats.loc[global_stats["TEAM_ID"] == self.nba_teams[away_team], feature].reset_index(drop = True)[0]

            game_data.append(feature_local_streak)
            game_data.append(feature_local_global)
            game_data.append(feature_away_streak)
            game_data.append(feature_away_global)

        return game_data
    
    def get_featureset(self, games_df, season):

        #Generate the dataframe where data will be appended
        featureset_df = self.featureset_structure()

        #Loop through the games
        for game in range(len(games_df)):

            #Get data of the game
            local_team =  games_df["LOCAL_TEAM"][game]
            away_team = games_df["AWAY_TEAM"][game]
            game_date = games_df["GAME_DATE"][game]
            win = games_df["WIN"][game]
            total_points = games_df["TOTAL_POINTS"][game]

            #Enrich with features
            features = self.features_calculator(season, local_team, away_team, game_date, win, total_points)

            #Append features to team featureset
            featureset_df.loc[len(featureset_df)] = features

            #Sleep some time for no timeout because of too many requests
            time.sleep(5)

        return featureset_df
    
    def save_team_data(self, team, season, df):

        global_path = os.getcwd()
        data_folder = self.config["DATA"]["FOLDER_NAME"]
        year_folder = season.split("-")[0]
        file_name = self.config["DATA"]["NBA_RAW_FILENAME"].format(TEAM = team)

        path_to_save_df = os.path.join(global_path, data_folder, year_folder, file_name)
        df.to_csv(path_to_save_df, index = False)


    def get_nba_results_data(self):

        #Get the data for each season
        for season in self.seasons_nba:

            #Loop through the NBA teams
            for team in self.teams_game_data:

                print(f"-------------------{team}---------------------{season}--------------------")

                #Get the games played by the team
                team_games = self.get_team_nba_games(team, season)

                #Get featureset
                featureset_df = self.get_featureset(team_games, season)

                #Save team year featureset
                self.save_team_data(team, season, featureset_df)


