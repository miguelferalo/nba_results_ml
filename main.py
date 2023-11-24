from config import config_variables
from src.components.nbaresultsdata import NBAResultsData

nba_results_data = NBAResultsData(config_variables)
nba_results_data.get_nba_results_data()
